from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text


settings = get_settings()


class TeguiseCulturaScraper(BaseScraper):
    source_name = "teguise_cultura"
    source_url = settings.teguise_cultura_url
    fixture_name = "teguise_cultura_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for article in soup.select("h2 a[href], h4 a[href]"):
            title = first_text(article.get_text(" ", strip=True))
            href = absolute_url(self.source_url, article.get("href"))
            if not title or not href or href in seen_urls:
                continue
            seen_urls.add(href)
            if self._should_skip_title(title):
                continue

            container = article.find_parent(["article", "div", "li"]) or article.parent
            nearby_text = container.get_text(" ", strip=True) if container else title
            starts_at_raw = self._extract_date(nearby_text)
            summary = None
            if container:
                summary = first_text(container.get_text(" ", strip=True))
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
                    municipality="Teguise",
                    locality="Teguise",
                    language_origin="es",
                    category_hints=["agenda municipal", "teguise", "cultura"],
                )
            )

        return events

    @staticmethod
    def _should_skip_title(title: str) -> bool:
        lowered = title.lower()
        return lowered in {"read more", "cultura", "galería", "galeria"} or len(lowered) < 4

    @staticmethod
    def _extract_date(text: str) -> str | None:
        parts = text.split("|", 1)
        if len(parts) < 2:
            return None
        left = parts[0].strip()
        if any(char.isdigit() for char in left):
            return left
        return None
