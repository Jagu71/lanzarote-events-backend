from datetime import datetime
from difflib import SequenceMatcher
import re
import unicodedata

from app.models.event import Event, EventTranslation
from app.utils.text import build_fingerprint, compact_spaces

GENERIC_TITLE_PREFIXES = (
    "taller para ninos y ninas",
    "taller para niños y niñas",
    "danza familiar",
    "exposicion",
    "exposición",
    "documental",
    "cine de autor",
)
GENERIC_TITLE_SUFFIXES = (
    "el documental",
    "cena y espectaculo",
    "cena y espectáculo",
    "muestra de danza",
)


def build_event_fingerprint(
    *,
    title: str,
    starts_at: datetime | None,
    venue_name: str | None,
) -> str:
    return build_fingerprint(title, starts_at.isoformat() if starts_at else None, venue_name)


def titles_are_similar(left: str, right: str, threshold: float = 0.9) -> bool:
    left_normalized = _normalize_comparison_text(left)
    right_normalized = _normalize_comparison_text(right)
    return SequenceMatcher(a=left_normalized.lower(), b=right_normalized.lower()).ratio() >= threshold


def venues_are_similar(left: str | None, right: str | None, threshold: float = 0.75) -> bool:
    left_normalized = _normalize_venue(left)
    right_normalized = _normalize_venue(right)
    if not left_normalized or not right_normalized:
        return False
    if left_normalized == right_normalized:
        return True
    if left_normalized in right_normalized or right_normalized in left_normalized:
        return True
    return SequenceMatcher(a=left_normalized, b=right_normalized).ratio() >= threshold


def merge_event_records(target: Event, incoming: Event) -> Event:
    scalar_fields = [
        "source_url",
        "canonical_url",
        "starts_at",
        "ends_at",
        "is_free",
        "price_text",
        "currency",
        "image_url",
        "venue_name",
        "venue_address",
        "municipality",
        "locality",
        "latitude",
        "longitude",
        "organizer_name",
        "audience",
        "source_payload",
        "last_seen_at",
    ]
    for field in scalar_fields:
        current_value = getattr(target, field)
        incoming_value = getattr(incoming, field)
        if current_value in (None, "", {}) and incoming_value not in (None, "", {}):
            setattr(target, field, incoming_value)

    translations = {item.language: item for item in target.translations}
    for translation in incoming.translations:
        existing = translations.get(translation.language)
        if existing is None:
            target.translations.append(
                EventTranslation(
                    language=translation.language,
                    title=translation.title,
                    summary=translation.summary,
                    description=translation.description,
                )
            )
        else:
            existing.title = existing.title or translation.title
            existing.summary = existing.summary or translation.summary
            existing.description = existing.description or translation.description

    existing_category_slugs = {category.slug for category in target.categories}
    for category in incoming.categories:
        if category.slug not in existing_category_slugs:
            target.categories.append(category)

    return target


def _normalize_comparison_text(value: str | None) -> str:
    normalized = compact_spaces(value or "") or ""
    normalized = unicodedata.normalize("NFKD", normalized).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.replace("&", " y ")
    normalized = _strip_generic_title_parts(normalized)
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", normalized).strip().lower()
    return normalized


def _normalize_venue(value: str | None) -> str:
    normalized = _normalize_comparison_text(value)
    normalized = re.sub(
        r"\b(teatro|cic|centro|insular|cultura|municipal|auditorio|sala|victor|fernandez|gopar|de|del|la|el)\b",
        " ",
        normalized,
    )
    return compact_spaces(normalized) or ""


def _strip_generic_title_parts(value: str) -> str:
    cleaned = compact_spaces(value) or ""
    for separator in [":", "|"]:
        if separator not in cleaned:
            continue
        left, right = [compact_spaces(part) or "" for part in cleaned.split(separator, 1)]
        if any(prefix in left.lower() for prefix in GENERIC_TITLE_PREFIXES) and right:
            cleaned = right
            continue
        if any(suffix in right.lower() for suffix in GENERIC_TITLE_SUFFIXES) and left:
            cleaned = left
    return cleaned
