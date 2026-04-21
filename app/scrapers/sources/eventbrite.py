import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, extract_json_ld_events, first_text


settings = get_settings()


class EventbriteScraper(BaseScraper):
    source_name = "eventbrite"
    source_url = settings.eventbrite_events_url
    fixture_name = "eventbrite_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        json_ld_events = extract_json_ld_events(
            html,
            source_name=self.source_name,
            source_url=self.source_url,
            language="en",
        )
        if json_ld_events:
            return json_ld_events

        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        for card in soup.select('[data-testid="event-card"], article'):
            link = card.select_one('a[href*="/e/"]') or card.find("a", href=re.compile(r"/e/"))
            title = first_text(
                card.select_one('[data-testid="event-card__formatted-name--content"]').get_text(" ", strip=True)
                if card.select_one('[data-testid="event-card__formatted-name--content"]')
                else None,
                link.get_text(" ", strip=True) if link else None,
            )
            if not link or not title:
                continue

            time_text = first_text(
                card.select_one("time").get_text(" ", strip=True) if card.select_one("time") else None,
                next((node.get_text(" ", strip=True) for node in card.find_all(["div", "p", "span"]) if "," in node.get_text(" ", strip=True)), None),
            )
            venue_text = first_text(
                next(
                    (
                        node.get_text(" ", strip=True)
                        for node in card.find_all(["div", "p", "span"])
                        if any(keyword in node.get_text(" ", strip=True).lower() for keyword in ["arrecife", "jameos", "lanzarote"])
                    ),
                    None,
                )
            )
            price_text = first_text(
                next(
                    (
                        node.get_text(" ", strip=True)
                        for node in card.find_all(["div", "p", "span"])
                        if any(keyword in node.get_text(" ", strip=True).lower() for keyword in ["free", "ticket", "price", "entry"])
                    ),
                    None,
                )
            )
            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=absolute_url(self.source_url, link.get("href")) or self.source_url,
                    external_id=link.get("href"),
                    canonical_url=absolute_url(self.source_url, link.get("href")),
                    title=title,
                    summary=first_text(card.get_text(" ", strip=True)),
                    starts_at_raw=time_text,
                    venue_name=venue_text,
                    price_text=price_text,
                    is_free=True if price_text and "free" in price_text.lower() else None,
                    image_url=card.find("img").get("src") if card.find("img") else None,
                    language_origin="en",
                    category_hints=["eventbrite"],
                )
            )
        return events
