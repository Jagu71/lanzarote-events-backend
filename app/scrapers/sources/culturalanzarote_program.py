import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, image_src, meta_description


settings = get_settings()


class CulturalLanzaroteProgramScraper(BaseScraper):
    source_name = "culturalanzarote_program"
    source_url = settings.culturalanzarote_program_url
    fixture_name = "culturalanzarote_program_listing.html"

    def collect(self) -> list[RawScrapedEvent]:
        try:
            if settings.scraper_use_fixtures:
                events = self.parse(self.fixture_text())
            else:
                events_by_url: dict[str, RawScrapedEvent] = {}
                for listing_url in self._listing_urls():
                    for event in self.parse(self.fetch_url(listing_url)):
                        events_by_url[event.source_url] = event
                events = list(events_by_url.values())
                for event in events:
                    self._enrich_from_detail(event)
            return events
        except Exception:
            return super().collect()

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".jet-listing-grid__item, article")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for card in cards:
            link = card.select_one("h1.elementor-heading-title a, h2 a, a[href]")
            title = first_text(
                card.select_one("h1.elementor-heading-title a").get_text(" ", strip=True)
                if card.select_one("h1.elementor-heading-title a")
                else None,
                card.select_one("h2").get_text(" ", strip=True) if card.select_one("h2") else None,
                link.get_text(" ", strip=True) if link else None,
            )
            if not title or len(title) < 4:
                continue

            event_url = absolute_url(self.source_url, link.get("href")) if link else self.source_url
            if not event_url or event_url in seen_urls:
                continue
            seen_urls.add(event_url)

            subtitle = first_text(
                card.select_one("h2.elementor-heading-title").get_text(" ", strip=True)
                if card.select_one("h2.elementor-heading-title")
                else None,
                card.select_one("h3").get_text(" ", strip=True) if card.select_one("h3") else None,
            )
            starts_at_raw = first_text(
                card.select_one("span.elementor-heading-title").get_text(" ", strip=True)
                if card.select_one("span.elementor-heading-title")
                else None,
                card.select_one("p").get_text(" ", strip=True) if card.select_one("p") else None,
            )
            category_hint = first_text(
                card.select_one(".jet-listing-dynamic-terms__link").get_text(" ", strip=True)
                if card.select_one(".jet-listing-dynamic-terms__link")
                else None,
                card.select_one("div").get_text(" ", strip=True) if card.select_one("div") else None,
            )
            image = card.select_one(".elementor-widget-image img")
            if image is None:
                image = card.select_one("img")

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=event_url,
                    external_id=link.get("href") if link else event_url,
                    canonical_url=event_url,
                    title=title,
                    summary=subtitle,
                    starts_at_raw=starts_at_raw,
                    image_url=image_src(image),
                    language_origin="es",
                    category_hints=[category_hint] if category_hint else [],
                    source_payload={},
                )
            )
        return events

    def _listing_urls(self) -> list[str]:
        page_two = f"{self.source_url.rstrip('/')}/jsf/jet-engine/pagenum/2/"
        return [self.source_url, page_two]

    def _enrich_from_detail(self, event: RawScrapedEvent) -> None:
        detail_html = self.fetch_url(event.source_url)
        soup = BeautifulSoup(detail_html, "lxml")
        description = meta_description(soup)
        venue_name = first_text(
            soup.select_one(".jet-listing-dynamic-field__content a").get_text(" ", strip=True)
            if soup.select_one(".jet-listing-dynamic-field__content a")
            else None
        )
        ticket_link = soup.select_one(".jet-listing-dynamic-link__link")
        content_blocks = [
            block.get_text(" ", strip=True)
            for block in soup.select(".entry-content p.has-background, .entry-content p")
            if block.get_text(" ", strip=True)
        ]
        organizer_name = first_text(
            soup.select_one('.jet-listing-dynamic-terms__link[href*="/organizadores/"]').get_text(" ", strip=True)
            if soup.select_one('.jet-listing-dynamic-terms__link[href*="/organizadores/"]')
            else None
        )
        event.summary = description or event.summary
        event.description = " ".join(content_blocks[:3]) if content_blocks else event.description
        event.venue_name = venue_name or event.venue_name
        event.organizer_name = organizer_name or event.organizer_name
        if ticket_link and ticket_link.get("href"):
            event.source_payload["ticket_url"] = ticket_link.get("href")
            if "gratuita" in ticket_link.get_text(" ", strip=True).lower():
                event.is_free = True
