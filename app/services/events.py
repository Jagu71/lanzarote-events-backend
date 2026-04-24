from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from math import inf
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.events import EventRepository
from app.schemas.event import EventDetail, EventListResponse, EventNowResponse, EventSummary, FeaturedEvent
from app.services.categories import CategoryService
from app.services.translations import pick_event_translation
from app.utils.date_parsing import parse_date_filter, range_exceeds_days


logger = logging.getLogger(__name__)


@dataclass
class EventQuery:
    lang: str = "es"
    category: str | None = None
    starts_after: str | None = None
    starts_before: str | None = None
    free_only: bool | None = None
    text: str | None = None
    days: int | None = None
    limit: int = 20
    offset: int = 0


class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EventRepository(db)
        self.category_service = CategoryService(db)

    def list_events(self, query: EventQuery) -> EventListResponse:
        starts_after = parse_date_filter(query.starts_after)
        starts_before = parse_date_filter(query.starts_before)
        if query.days is not None:
            starts_after = starts_after or datetime.now(ZoneInfo("Atlantic/Canary"))
            starts_before = starts_after + timedelta(days=query.days)
        elif range_exceeds_days(starts_after, starts_before, max_days=7):
            raise HTTPException(status_code=400, detail="Date range cannot exceed 7 days")
        events, total = self.repository.list_events(
            category=query.category,
            starts_after=starts_after,
            starts_before=starts_before,
            free_only=query.free_only,
            text=query.text,
            limit=query.limit,
            offset=query.offset,
        )
        items = []
        skipped = 0
        for event in events:
            try:
                items.append(self._to_summary(event, query.lang))
            except Exception:
                skipped += 1
                logger.exception("Skipping malformed event during list serialization: %s", event.id)
        return EventListResponse(
            items=items,
            total=max(0, total - skipped),
            limit=query.limit,
            offset=query.offset,
        )

    def get_now_plan(
        self,
        *,
        lang: str,
        free_only: bool | None = None,
        category: str | None = None,
        search_at: str | None = None,
    ) -> EventNowResponse:
        search_time = parse_date_filter(search_at) or datetime.now(ZoneInfo("Atlantic/Canary"))
        ends_at = search_time + timedelta(hours=48)
        events, _ = self.repository.list_events(
            category=category,
            starts_after=search_time,
            starts_before=ends_at,
            free_only=free_only,
            limit=120,
            offset=0,
        )
        items = [self._to_summary(event, lang) for event in events]
        featured = self._build_featured(items, search_time)
        return EventNowResponse(
            search_at=self._isoformat(search_time) or "",
            window_hours=48,
            featured=featured,
            items=items,
            total=len(items),
        )

    def get_event(self, event_id: str, lang: str) -> EventDetail | None:
        event = self.repository.get_event(event_id)
        if event is None:
            return None
        summary = self._to_summary(event, lang)
        translations = {
            translation.language: {
                "title": translation.title,
                "summary": translation.summary,
                "description": translation.description,
            }
            for translation in event.translations
        }
        return EventDetail(
            **summary.model_dump(),
            organizer_name=event.organizer_name,
            audience=event.audience,
            canonical_url=event.canonical_url,
            language_origin=event.language_origin,
            translations=translations,
            source_payload=event.source_payload or {},
        )

    def _to_summary(self, event: Event, lang: str) -> EventSummary:
        translation = pick_event_translation(event.translations, lang) or SimpleNamespace(
            language=lang or event.language_origin or "es",
            title="Evento sin título",
            summary=None,
            description=None,
        )
        categories = [self.category_service._to_public(category, lang) for category in event.categories]
        return EventSummary(
            id=event.id,
            slug=event.slug,
            title=translation.title,
            summary=translation.summary,
            description=translation.description,
            translation_language=translation.language,
            available_languages=sorted([item.language for item in event.translations if item.language]),
            starts_at=self._isoformat(event.starts_at),
            ends_at=self._isoformat(event.ends_at),
            is_free=event.is_free,
            price_text=event.price_text,
            source_name=event.source_name,
            source_url=event.source_url,
            image_url=event.image_url,
            venue_name=event.venue_name,
            venue_address=event.venue_address,
            municipality=event.municipality,
            locality=event.locality,
            latitude=event.latitude,
            longitude=event.longitude,
            categories=categories,
        )

    def _build_featured(self, items: list[EventSummary], search_at: datetime) -> list[FeaturedEvent]:
        selected_ids: set[str] = set()
        imminent = self._pick_imminent(items, selected_ids)
        popular = self._pick_ranked(items, selected_ids, lambda item: self._popular_score(item, search_at))
        alternative = self._pick_ranked(items, selected_ids, lambda item: self._alternative_score(item, search_at))
        return [
            FeaturedEvent(
                slot="imminent",
                label="Empieza antes",
                rationale="La opción más inmediata para decidir sin pensar demasiado.",
                event=imminent,
            ),
            FeaturedEvent(
                slot="popular",
                label="Plan potente",
                rationale="El evento más redondo por timing, categoría y ficha completa.",
                event=popular,
            ),
            FeaturedEvent(
                slot="alternative",
                label="Plan alternativo",
                rationale="Una propuesta distinta para salir del concierto o la fiesta de siempre.",
                event=alternative,
            ),
        ]

    @staticmethod
    def _pick_imminent(items: list[EventSummary], selected_ids: set[str]) -> EventSummary | None:
        for item in items:
            if item.id not in selected_ids:
                selected_ids.add(item.id)
                return item
        return None

    def _pick_ranked(
        self,
        items: list[EventSummary],
        selected_ids: set[str],
        scorer,
    ) -> EventSummary | None:
        best: EventSummary | None = None
        best_score = -inf
        for item in items:
            if item.id in selected_ids:
                continue
            score = scorer(item)
            if score > best_score:
                best = item
                best_score = score
        if best is not None:
            selected_ids.add(best.id)
        return best

    def _popular_score(self, item: EventSummary, search_at: datetime) -> float:
        score = 0.0
        category_slugs = {category.slug for category in item.categories}
        if category_slugs & {"music", "festivities", "gastronomy"}:
            score += 4.0
        if category_slugs & {"theatre", "cinema"}:
            score += 2.5
        if item.image_url:
            score += 4.0
        if item.venue_name:
            score += 1.0
        if item.summary:
            score += 1.0
        if item.is_free is not None or item.price_text:
            score += 0.5
        if self._has_paid_signal(item):
            score -= 3.0
        hours_until = self._hours_until(item.starts_at, search_at)
        if hours_until is not None:
            score += max(0, 24 - min(hours_until, 24)) / 8
        return score

    def _alternative_score(self, item: EventSummary, search_at: datetime) -> float:
        score = 0.0
        category_slugs = {category.slug for category in item.categories}
        if category_slugs & {"family", "literature", "exhibition", "workshop", "cinema", "theatre"}:
            score += 4.0
        if category_slugs & {"music", "festivities", "gastronomy"}:
            score += 0.5
        if item.is_free is True or (item.is_free is None and not item.price_text):
            score += 1.0
        if self._has_paid_signal(item):
            score -= 2.0
        starts_at = self._parse_iso(item.starts_at)
        if starts_at and starts_at.hour < 19:
            score += 1.0
        hours_until = self._hours_until(item.starts_at, search_at)
        if hours_until is not None:
            score += max(0, 36 - min(hours_until, 36)) / 12
        return score

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _hours_until(self, value: str | None, search_at: datetime) -> float | None:
        starts_at = self._parse_iso(value)
        if starts_at is None:
            return None
        if starts_at.tzinfo is None and search_at.tzinfo is not None:
            starts_at = starts_at.replace(tzinfo=search_at.tzinfo)
        return max(0.0, (starts_at - search_at).total_seconds() / 3600)

    @staticmethod
    def _has_paid_signal(item: EventSummary) -> bool:
        blob = " ".join(
            part.lower()
            for part in [item.title, item.summary or "", item.description or "", item.price_text or ""]
            if part
        )
        return any(token in blob for token in ["€", "precio", "price", "euro", "euros", "entry ", "ticket"])

    @staticmethod
    def _isoformat(value: datetime | None) -> str | None:
        return value.isoformat() if value else None
