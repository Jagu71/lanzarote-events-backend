from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings
from app.utils.date_parsing import parse_localized_datetime
from app.utils.text import compact_spaces


logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class NormalizedEvent:
    source_name: str
    source_url: str
    external_id: str | None
    canonical_url: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    timezone: str
    is_free: bool | None
    price_text: str | None
    currency: str | None
    image_url: str | None
    venue_name: str | None
    venue_address: str | None
    municipality: str | None
    locality: str | None
    organizer_name: str | None
    audience: str | None
    language_origin: str
    translations: dict[str, dict[str, str | None]]
    tags: list[str]
    category_hints: list[str]
    source_payload: dict[str, Any]

    @property
    def primary_language(self) -> str:
        return self.language_origin

    @property
    def primary_translation(self) -> dict[str, str | None]:
        return self.translations[self.primary_language]

    @property
    def primary_title(self) -> str:
        return self.primary_translation["title"] or "Evento sin título"

    @property
    def primary_summary(self) -> str | None:
        return self.primary_translation.get("summary")

    @property
    def primary_description(self) -> str | None:
        return self.primary_translation.get("description")


@dataclass
class RawScrapedEvent:
    source_name: str
    source_url: str
    external_id: str | None = None
    canonical_url: str | None = None
    title: str = ""
    summary: str | None = None
    description: str | None = None
    starts_at_raw: str | None = None
    ends_at_raw: str | None = None
    timezone: str = "Atlantic/Canary"
    is_free: bool | None = None
    price_text: str | None = None
    currency: str | None = None
    image_url: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    municipality: str | None = None
    locality: str | None = None
    organizer_name: str | None = None
    audience: str | None = None
    language_origin: str = "es"
    translations: dict[str, dict[str, str | None]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    category_hints: list[str] = field(default_factory=list)
    source_payload: dict[str, Any] = field(default_factory=dict)

    def normalize(self) -> NormalizedEvent:
        translations = dict(self.translations)
        if self.language_origin not in translations:
            translations[self.language_origin] = {
                "title": compact_spaces(self.title) or "Evento sin título",
                "summary": compact_spaces(self.summary),
                "description": compact_spaces(self.description),
            }

        return NormalizedEvent(
            source_name=self.source_name,
            source_url=self.source_url,
            external_id=self.external_id,
            canonical_url=self.canonical_url,
            starts_at=parse_localized_datetime(self.starts_at_raw, [self.language_origin, "es", "en", "de", "fr"]),
            ends_at=parse_localized_datetime(self.ends_at_raw, [self.language_origin, "es", "en", "de", "fr"]),
            timezone=self.timezone,
            is_free=self.is_free,
            price_text=compact_spaces(self.price_text),
            currency=self.currency,
            image_url=self.image_url,
            venue_name=compact_spaces(self.venue_name),
            venue_address=compact_spaces(self.venue_address),
            municipality=compact_spaces(self.municipality),
            locality=compact_spaces(self.locality),
            organizer_name=compact_spaces(self.organizer_name),
            audience=compact_spaces(self.audience),
            language_origin=self.language_origin,
            translations=translations,
            tags=[compact_spaces(tag) or "" for tag in self.tags if compact_spaces(tag)],
            category_hints=[compact_spaces(tag) or "" for tag in self.category_hints if compact_spaces(tag)],
            source_payload=self.source_payload,
        )


class BaseScraper(ABC):
    source_name: str
    source_url: str
    fixture_name: str | None = None

    def fixture_text(self, fixture_name: str | None = None) -> str:
        target_fixture = fixture_name or self.fixture_name
        if not target_fixture:
            raise ValueError(f"{self.source_name} has no fixture configured")
        fixture_path = settings.fixtures_dir / target_fixture
        return Path(fixture_path).read_text(encoding="utf-8")

    def fetch_url(self, url: str, *, fixture_name: str | None = None) -> str:
        if settings.scraper_use_fixtures and (fixture_name or self.fixture_name):
            return self.fixture_text(fixture_name)
        headers = {"User-Agent": settings.scraper_user_agent}
        with httpx.Client(timeout=settings.scraper_timeout_seconds, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def fetch(self) -> str:
        return self.fetch_url(self.source_url)

    def collect(self) -> list[RawScrapedEvent]:
        try:
            html = self.fetch()
            events = self.parse(html)
            logger.info("%s: extracted %s events", self.source_name, len(events))
            return events
        except Exception:
            logger.exception("%s: scraper failed", self.source_name)
            return []

    @abstractmethod
    def parse(self, html: str) -> list[RawScrapedEvent]:
        raise NotImplementedError
