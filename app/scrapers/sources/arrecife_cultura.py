import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text


settings = get_settings()

DATE_PATTERN = re.compile(r"\b\d{1,2}\s+de\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+(?:\s+de\s+\d{4})?(?:\s+a\s+partir\s+de\s+las\s+\d{1,2}(?::\d{2})?)?")


class ArrecifeCulturaScraper(BaseScraper):
    source_name = "arrecife_cultura"
    source_url = settings.arrecife_cultura_url
    fixture_name = "arrecife_cultura_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for article in soup.select("h2 a[href], h3 a[href]"):
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
                    municipality="Arrecife",
                    locality="Arrecife",
                    language_origin="es",
                    category_hints=["agenda municipal", "arrecife", "cultura"],
                )
            )
        return events

    @staticmethod
    def _looks_like_event(title: str) -> bool:
        lowered = title.lower()
        hints = (
            "concierto",
            "charla",
            "ciclo",
            "cuento",
            "cuentacuentos",
            "microconcierto",
            "espectáculo",
            "espectaculo",
            "jornadas",
            "sesión",
            "sesion",
            "presentación",
            "presentacion",
            "taller",
            "música",
            "musica",
        )
        return any(hint in lowered for hint in hints)

    @staticmethod
    def _extract_date(text: str) -> str | None:
        match = DATE_PATTERN.search(text)
        return match.group(0) if match else None
