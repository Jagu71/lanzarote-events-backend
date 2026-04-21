from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, extract_json_ld_events, first_text


settings = get_settings()


class CabildoScraper(BaseScraper):
    source_name = "cabildo_lanzarote"
    source_url = settings.cabildo_events_url
    fixture_name = "cabildo_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        if not self.source_url:
            return []

        json_ld_events = extract_json_ld_events(
            html,
            source_name=self.source_name,
            source_url=self.source_url,
            language="es",
        )
        if json_ld_events:
            return json_ld_events

        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        for link in soup.select("article a, .event a, .agenda a"):
            title = first_text(
                link.get_text(" ", strip=True),
                link.find_previous(["h2", "h3", "h4"]).get_text(" ", strip=True) if link.find_previous(["h2", "h3", "h4"]) else None,
            )
            if not title:
                continue
            container = link.parent
            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=absolute_url(self.source_url, link.get("href")) or self.source_url,
                    external_id=link.get("href"),
                    canonical_url=absolute_url(self.source_url, link.get("href")),
                    title=title,
                    summary=first_text(container.get_text(" ", strip=True)),
                    starts_at_raw=first_text(
                        next((node.get_text(" ", strip=True) for node in container.find_all(["time", "span", "p"]) if node.get_text(strip=True)), None)
                    ),
                    venue_name=first_text(
                        next(
                            (
                                node.get_text(" ", strip=True)
                                for node in container.find_all(["span", "p"])
                                if any(term in node.get_text(" ", strip=True).lower() for term in ["arrecife", "haria", "teguise", "san bartolome", "yaiza"])
                            ),
                            None,
                        )
                    ),
                    image_url=container.find("img").get("src") if container.find("img") else None,
                    language_origin="es",
                    category_hints=["cabildo"],
                )
            )
        return events
