import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, image_src


settings = get_settings()

DATE_PATTERN = re.compile(r"\b\d{1,2}\s+de\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+\s+-\s+\d{1,2}:\d{2}\s*h\.")
PRICE_PATTERN = re.compile(r"Desde\s*([0-9]+(?:[.,][0-9]+)?€)")


class EcoEntradasLanzaroteScraper(BaseScraper):
    source_name = "ecoentradas_lanzarote"
    source_url = settings.ecoentradas_lanzarote_url
    fixture_name = "ecoentradas_lanzarote_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for info_link in soup.find_all("a", href=True):
            link_text = info_link.get_text(" ", strip=True).lower()
            if "más información" not in link_text and "más info" not in link_text:
                continue

            card = self._resolve_card(info_link)
            if card is None:
                continue

            title = first_text(
                card.select_one("h4").get_text(" ", strip=True) if card.select_one("h4") else None,
                info_link.get("title"),
            )
            organizer = first_text(card.select_one("h5").get_text(" ", strip=True) if card.select_one("h5") else None)
            if not title:
                continue

            detail_url = absolute_url(self.source_url, info_link.get("href")) or self.source_url
            if detail_url in seen_urls:
                continue
            seen_urls.add(detail_url)

            text = card.get_text(" ", strip=True)
            venue_link = next(
                (
                    anchor
                    for anchor in card.find_all("a", href=True)
                    if anchor is not info_link and "más " not in anchor.get_text(" ", strip=True).lower()
                ),
                None,
            )
            venue_name = first_text(venue_link.get_text(" ", strip=True) if venue_link else None)
            starts_at_raw = self._extract_date(text)
            price_text = self._extract_price(text)

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=detail_url,
                    external_id=info_link.get("href") or detail_url,
                    canonical_url=detail_url,
                    title=title,
                    summary=organizer,
                    starts_at_raw=starts_at_raw,
                    venue_name=venue_name,
                    price_text=price_text,
                    is_free=True if price_text == "0€" else None,
                    image_url=image_src(card.find("img")),
                    language_origin="es",
                    category_hints=["ecoentradas", "tickets", venue_name] if venue_name else ["ecoentradas", "tickets"],
                )
            )

        return events

    @staticmethod
    def _resolve_card(info_link):
        current = info_link
        while current is not None:
            if getattr(current, "name", None) in {"article", "li", "div"}:
                headings = current.find_all(["h4", "h5"])
                if headings:
                    return current
            current = current.parent
        return None

    @staticmethod
    def _extract_date(text: str) -> str | None:
        match = DATE_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_price(text: str) -> str | None:
        match = PRICE_PATTERN.search(text)
        return match.group(1) if match else None
