from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text


settings = get_settings()

EVENT_HINTS = (
    "festival",
    "teatro",
    "charla",
    "concierto",
    "danza",
    "música",
    "musica",
    "poesía",
    "poesia",
    "literatura",
    "encuentro",
    "certamen",
    "presentación",
    "presentacion",
)


class TiasCulturaScraper(BaseScraper):
    source_name = "tias_cultura"
    source_url = settings.tias_cultura_url
    fixture_name = "tias_cultura_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()
        current_date: str | None = None

        for node in soup.select("h3 a[href], h3, p"):
            text = first_text(node.get_text(" ", strip=True))
            if not text:
                continue

            if self._looks_like_date(text):
                current_date = text
                continue

            link = node if node.name == "a" else node.select_one("a[href]")
            title = text
            if not self._looks_like_event(title):
                continue

            href = absolute_url(self.source_url, link.get("href")) if link else self.source_url
            if href in seen_urls:
                continue
            seen_urls.add(href)

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=href or self.source_url,
                    external_id=(link.get("href") if link else title) or title,
                    canonical_url=href,
                    title=title,
                    starts_at_raw=current_date,
                    municipality="Tías",
                    locality="Tías",
                    language_origin="es",
                    category_hints=["agenda municipal", "tías", "cultura"],
                )
            )

        return events

    @staticmethod
    def _looks_like_date(text: str) -> bool:
        stripped = text.strip()
        return len(stripped) == 10 and stripped[2] == "/" and stripped[5] == "/"

    @staticmethod
    def _looks_like_event(text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in EVENT_HINTS)
