from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import RawScrapedEvent
from app.utils.text import compact_spaces


def extract_json_ld_events(html: str, *, source_name: str, source_url: str, language: str = "es") -> list[RawScrapedEvent]:
    soup = BeautifulSoup(html, "lxml")
    events: list[RawScrapedEvent] = []
    for script in soup.select('script[type="application/ld+json"]'):
        content = compact_spaces(script.get_text())
        if not content:
            continue
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue
        for item in _normalize_json_ld_payload(parsed):
            if item.get("@type") != "Event":
                continue
            location = item.get("location") or {}
            image = item.get("image")
            if isinstance(image, list):
                image = image[0] if image else None
            offers = item.get("offers") or {}
            events.append(
                RawScrapedEvent(
                    source_name=source_name,
                    source_url=source_url,
                    external_id=item.get("@id") or item.get("url"),
                    canonical_url=item.get("url"),
                    title=item.get("name") or "",
                    summary=item.get("description"),
                    description=item.get("description"),
                    starts_at_raw=item.get("startDate"),
                    ends_at_raw=item.get("endDate"),
                    is_free=_json_ld_is_free(offers),
                    price_text=_json_ld_price_text(offers),
                    image_url=image,
                    venue_name=_extract_location_name(location),
                    venue_address=_extract_location_address(location),
                    organizer_name=(item.get("organizer") or {}).get("name"),
                    language_origin=language,
                    category_hints=_to_list(item.get("eventAttendanceMode")) + _to_list(item.get("keywords")),
                    source_payload=item,
                )
            )
    return events


def absolute_url(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    return urljoin(base_url, href)


def first_text(*values: str | None) -> str | None:
    for value in values:
        normalized = compact_spaces(value)
        if normalized:
            return normalized
    return None


def text_lines(value: str) -> list[str]:
    return [line.strip() for line in re.split(r"[\r\n]+", value) if compact_spaces(line)]


def plain_text(value: str | None) -> str | None:
    if not value:
        return None
    return compact_spaces(BeautifulSoup(value, "lxml").get_text(" ", strip=True))


def meta_description(soup: BeautifulSoup) -> str | None:
    for selector in ['meta[name="description"]', 'meta[property="og:description"]']:
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            return compact_spaces(tag.get("content"))
    return None


def image_src(tag: Any) -> str | None:
    if tag is None:
        return None
    for attribute in ["data-src", "data-lazy-src", "src"]:
        value = tag.get(attribute)
        if value and not value.startswith("data:image/svg+xml"):
            return value
    return None


def _normalize_json_ld_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        result: list[dict[str, Any]] = []
        for item in payload:
            result.extend(_normalize_json_ld_payload(item))
        return result
    if isinstance(payload, dict):
        if "@graph" in payload and isinstance(payload["@graph"], list):
            return [item for item in payload["@graph"] if isinstance(item, dict)]
        return [payload]
    return []


def _extract_location_name(location: dict[str, Any]) -> str | None:
    if isinstance(location, dict):
        return location.get("name")
    return None


def _extract_location_address(location: dict[str, Any]) -> str | None:
    if not isinstance(location, dict):
        return None
    address = location.get("address")
    if isinstance(address, str):
        return address
    if isinstance(address, dict):
        return ", ".join(filter(None, [address.get("streetAddress"), address.get("addressLocality")]))
    return None


def _json_ld_is_free(offers: Any) -> bool | None:
    if not offers:
        return None
    if isinstance(offers, list):
        for item in offers:
            value = _json_ld_is_free(item)
            if value is not None:
                return value
        return None
    price = offers.get("price") if isinstance(offers, dict) else None
    if price in ("0", 0, "0.0", "0,00"):
        return True
    return None


def _json_ld_price_text(offers: Any) -> str | None:
    if isinstance(offers, dict):
        price = offers.get("price")
        currency = offers.get("priceCurrency")
        if price and currency:
            return f"{price} {currency}"
        if price:
            return str(price)
    return None


def _to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]
