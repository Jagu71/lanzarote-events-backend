import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, plain_text


settings = get_settings()

MONTH_MAP = {
    "ene": "enero",
    "feb": "febrero",
    "mar": "marzo",
    "abr": "abril",
    "may": "mayo",
    "jun": "junio",
    "jul": "julio",
    "ago": "agosto",
    "sep": "septiembre",
    "oct": "octubre",
    "nov": "noviembre",
    "dic": "diciembre",
}


class TinajoAgendaScraper(BaseScraper):
    source_name = "tinajo_agenda"
    source_url = settings.tinajo_agenda_url
    fixture_name = "tinajo_agenda_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        content = soup.select_one("main") or soup
        lines = [line.strip() for line in content.get_text("\n", strip=True).splitlines() if line.strip()]

        events: list[RawScrapedEvent] = []
        i = 0
        while i < len(lines):
            if not lines[i].isdigit():
                i += 1
                continue

            day = lines[i]
            if i + 2 >= len(lines):
                break
            month = lines[i + 1]
            title = lines[i + 2]
            if len(title) < 4 or title.lower() in {"leer más", "leer mas"}:
                i += 1
                continue

            summary = None
            if i + 3 < len(lines) and not self._looks_like_new_card(lines[i + 3]):
                summary = lines[i + 3]

            starts_at_raw = self._build_date(day, month)
            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=self.source_url,
                    external_id=f"{title}-{starts_at_raw or day}",
                    canonical_url=self.source_url,
                    title=title,
                    summary=summary,
                    starts_at_raw=starts_at_raw,
                    municipality="Tinajo",
                    locality="Tinajo",
                    language_origin="es",
                    category_hints=["agenda municipal", "tinajo"],
                )
            )
            i += 1

        return self._dedupe(events)

    @staticmethod
    def _build_date(day: str, month: str) -> str | None:
        month_token = month.split()[0].lower()[:3]
        month_name = MONTH_MAP.get(month_token)
        if not month_name:
            return None
        first_day = re.split(r"\s+", day.strip())[0]
        return f"{first_day} de {month_name}"

    @staticmethod
    def _looks_like_new_card(line: str) -> bool:
        return bool(re.fullmatch(r"\d+(?:\s+\d+)?", line)) or line[:3].lower() in MONTH_MAP

    @staticmethod
    def _dedupe(events: list[RawScrapedEvent]) -> list[RawScrapedEvent]:
        deduped: dict[tuple[str, str | None], RawScrapedEvent] = {}
        for event in events:
            key = (event.title.lower(), event.starts_at_raw)
            deduped.setdefault(key, event)
        return list(deduped.values())
