import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text


settings = get_settings()

DATE_PATTERN = re.compile(r"\b\d{1,2}\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+,\s+\d{4}\b|\b\d{1,2}\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+\s*,?\s*\d{4}\b")


class SanBartolomeEventosScraper(BaseScraper):
    source_name = "sanbartolome_eventos"
    source_url = settings.sanbartolome_eventos_url
    fixture_name = "sanbartolome_eventos_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for article in soup.select("h3 a[href], h2 a[href]"):
            title = first_text(article.get_text(" ", strip=True))
            href = absolute_url(self.source_url, article.get("href"))
            if not title or not href or href in seen_urls:
                continue
            seen_urls.add(href)
            if not self._looks_like_event(title):
                continue

            container = article.find_parent(["article", "div", "li"]) or article.parent
            text = container.get_text(" ", strip=True) if container else title
            starts_at_raw = self._extract_date(text)
            summary = first_text(text)
            if summary == title:
                summary = None

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=href,
                    external_id=article.get("href") or href,
                    canonical_url=href,
                    title=title,
                    summary=summary,
                    starts_at_raw=starts_at_raw,
                    municipality="San Bartolomé",
                    locality="San Bartolomé",
                    language_origin="es",
                    category_hints=["agenda municipal", "san bartolomé", "cultura"],
                )
            )
        return events

    @staticmethod
    def _looks_like_event(title: str) -> bool:
        lowered = title.lower()
        hints = (
            "agenda",
            "festival",
            "carnaval",
            "fiesta",
            "festej",
            "cultural",
            "sonoro",
            "feria",
            "música",
            "musica",
            "supercampeonato",
            "heart lanzarote fest",
        )
        return any(hint in lowered for hint in hints)

    @staticmethod
    def _extract_date(text: str) -> str | None:
        match = DATE_PATTERN.search(text)
        return match.group(0) if match else None
