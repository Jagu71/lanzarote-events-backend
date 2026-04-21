import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import dateparser


DATE_SETTINGS = {
    "TIMEZONE": "Atlantic/Canary",
    "RETURN_AS_TIMEZONE_AWARE": True,
    "PREFER_DATES_FROM": "current_period",
}

MONTHS_ES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
WEEKDAYS_ES = "lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo"
SPANISH_DATE_PATTERN = re.compile(
    rf"((?:{WEEKDAYS_ES})\s+)?(\d{{1,2}})(?:\s+y\s+\d{{1,2}})?\s+(?:de\s+)?({MONTHS_ES})(?:\s+de\s+(\d{{4}}))?(?:\s+(?:a\s+las\s+)?(\d{{1,2}}(?::\d{{2}})?))?",
    re.IGNORECASE,
)


def parse_localized_datetime(value: str | None, default_languages: list[str] | None = None) -> datetime | None:
    if not value:
        return None
    prepared = _prepare_datetime_value(value)
    parsed = dateparser.parse(prepared, languages=default_languages, settings=DATE_SETTINGS)
    if parsed and parsed.year > _now_canary().year + 2:
        reparsed = dateparser.parse(_append_current_year(prepared), languages=default_languages, settings=DATE_SETTINGS)
        if reparsed:
            return reparsed
    return parsed


def parse_date_filter(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_localized_datetime(value, default_languages=["es", "en", "de", "fr"])


def range_exceeds_days(start: datetime | None, end: datetime | None, max_days: int) -> bool:
    if not start or not end:
        return False
    return end - start > timedelta(days=max_days)


def _prepare_datetime_value(value: str) -> str:
    normalized = _normalize_datetime_text(value)
    candidate = _extract_first_spanish_date(normalized) or normalized
    return _append_current_year(candidate)


def _normalize_datetime_text(value: str) -> str:
    normalized = value.replace("\xa0", " ").replace(">", " ").replace("–", "-").replace("—", "-")
    normalized = re.sub(r"(?<=\d)\.(?=\d{2}\b)", ":", normalized)
    normalized = re.sub(r"(\d{1,2})\s*h\b", r"\1:00", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\d{1,2}:\d{2})\s*h\b", r"\1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bhoras?\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,;|-")
    return normalized


def _extract_first_spanish_date(value: str) -> str | None:
    match = SPANISH_DATE_PATTERN.search(value)
    if not match:
        return None
    weekday, day, month, year, time_part = match.groups()
    pieces = [weekday.strip() if weekday else None, f"{int(day)} de {month.lower()}"]
    if year:
        pieces.append(f"de {year}")
    if time_part:
        pieces.append(f"a las {time_part}")
    return " ".join(piece for piece in pieces if piece)


def _append_current_year(value: str) -> str:
    if re.search(r"\b\d{4}\b", value):
        return value
    if not re.search(rf"\b({MONTHS_ES})\b", value, flags=re.IGNORECASE):
        return value
    return re.sub(
        rf"(\d{{1,2}}\s+de\s+(?:{MONTHS_ES}))(?!\s+de\s+\d{{4}})",
        rf"\1 de {_now_canary().year}",
        value,
        count=1,
        flags=re.IGNORECASE,
    )


def _now_canary() -> datetime:
    return datetime.now(ZoneInfo("Atlantic/Canary"))
