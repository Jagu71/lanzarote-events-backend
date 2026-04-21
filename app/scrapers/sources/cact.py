from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, extract_json_ld_events, first_text, image_src, meta_description


settings = get_settings()


class CactScraper(BaseScraper):
    source_name = "cact_lanzarote"
    source_url = settings.cact_events_url
    fixture_name = "cact_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
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
        for card in soup.select(".listatickets .cell[id] .callout"):
            button = card.select_one("a.button.expanded[href]")
            title = first_text(card.select_one("h6.title").get_text(" ", strip=True) if card.select_one("h6.title") else None)
            if not title or len(title) < 4 or "agenda cultural" in title.lower():
                continue

            date_heading = first_text(
                card.select_one(".small-6.large-12.cell h6").get_text(" ", strip=True)
                if card.select_one(".small-6.large-12.cell h6")
                else None
            )
            hour_text = first_text(card.select_one(".hora").get_text(" ", strip=True) if card.select_one(".hora") else None)
            venue_name = first_text(card.select_one("p.lugar span").get_text(" ", strip=True) if card.select_one("p.lugar span") else None)
            event_url = absolute_url(self.source_url, button.get("href")) if button else self.source_url
            summary = button.get_text(" ", strip=True) if button else None

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=event_url or self.source_url,
                    external_id=button.get("href") if button else title,
                    canonical_url=event_url,
                    title=title,
                    summary=summary,
                    starts_at_raw=first_text(f"{date_heading} {hour_text}" if date_heading or hour_text else None),
                    venue_name=venue_name,
                    image_url=image_src(card.select_one("img")),
                    language_origin="es",
                    category_hints=["cact", venue_name] if venue_name else ["cact"],
                )
            )

        if not settings.scraper_use_fixtures:
            for event in events:
                self._enrich_detail(event)
        return events

    def _enrich_detail(self, event: RawScrapedEvent) -> None:
        if not event.source_url:
            return
        try:
            soup = BeautifulSoup(self.fetch_url(event.source_url), "lxml")
        except Exception:
            return
        description = meta_description(soup)
        if description:
            event.summary = description
            event.description = description
