import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, image_src


settings = get_settings()

DATE_PATTERN = re.compile(
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|\d{1,2}\s+de\s+\w+|\d{1,2}\s+y\s+\d{1,2}|fecha y hora)",
    re.IGNORECASE,
)
MONTHS_ES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"


class CulturalLanzaroteTicketsScraper(BaseScraper):
    source_name = "culturalanzarote_tickets"
    source_url = settings.culturalanzarote_tickets_url
    fixture_name = "culturalanzarote_tickets_listing.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".productos > .col.s12[data-fecha], article")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for card in cards:
            info_link = card.select_one("a.mas-info")
            if info_link is None:
                info_link = card.select_one("a[href]")
            buy_link = next(
                (
                    anchor
                    for anchor in card.select(".enlaces a[href]")
                    if "comprar" in anchor.get_text(" ", strip=True).lower()
                ),
                None,
            )
            title = first_text(
                card.select_one("h2.titulo").get_text(" ", strip=True) if card.select_one("h2.titulo") else None,
                card.select_one("h2").get_text(" ", strip=True) if card.select_one("h2") else None,
            )
            if not title or len(title) < 4:
                continue

            event_url = absolute_url(self.source_url, info_link.get("href")) if info_link else self.source_url
            if not event_url or event_url in seen_urls:
                continue
            seen_urls.add(event_url)

            description_node = card.select_one(".descripcion")
            description_text = description_node.get_text(" | ", strip=True) if description_node else card.get_text(" | ", strip=True)
            starts_at_field = self._extract_field(description_text, "Fecha y hora")
            starts_at_raw = self._extract_first_date(starts_at_field)
            venue_name = first_text(
                card.select_one(".lugar .font-bold").get_text(" ", strip=True) if card.select_one(".lugar .font-bold") else None,
                next((line.replace("Lugar:", "").strip() for line in description_text.split("|") if "Lugar:" in line), None),
                self._extract_field(description_text, "Lugar"),
            )
            price_text = self._extract_field(description_text, "Precio")
            audience = self._extract_field(description_text, "Público")
            category_hint = first_text(card.select_one(".categoria p").get_text(" ", strip=True) if card.select_one(".categoria p") else None)
            subtitle = first_text(
                card.select_one("h3.subtitulo").get_text(" ", strip=True) if card.select_one("h3.subtitulo") else None,
                card.select_one("h3").get_text(" ", strip=True) if card.select_one("h3") else None,
            )
            image = card.select_one(".imagen img")
            if image is None:
                image = card.select_one("img")

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=event_url,
                    external_id=info_link.get("href") if info_link else event_url,
                    canonical_url=event_url,
                    title=title,
                    summary=subtitle,
                    description=description_text,
                    starts_at_raw=starts_at_raw,
                    venue_name=venue_name,
                    price_text=price_text,
                    audience=audience,
                    is_free=True if price_text and "gratuit" in price_text.lower() else None,
                    image_url=image_src(image),
                    language_origin="es",
                    category_hints=[category_hint] if category_hint else [],
                    source_payload={
                        "buy_url": absolute_url(self.source_url, buy_link.get("href")) if buy_link else None,
                        "date_bucket": card.get("data-fecha"),
                    },
                )
            )
        return events

    @staticmethod
    def _extract_field(description_text: str, field_name: str) -> str | None:
        stop_words = ["Duración", "Público", "Lugar", "Precio", "Dirección"]
        stops = [word for word in stop_words if word != field_name]
        normalized_text = description_text.replace("| :", ":").replace("\xa0", " ")
        pattern = rf"{field_name}\s*[:|]?\s*(.*?)(?=\s*(?:{'|'.join(stops)})\s*:|$)"
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        value = first_text(match.group(1) if match else None)
        if not value:
            return None
        value = re.split(r"\s*\|\s*(?:\+?\s*info|comprar)\b", value, flags=re.IGNORECASE)[0].strip()
        return first_text(value)

    @staticmethod
    def _extract_first_date(value: str | None) -> str | None:
        if not value:
            return None
        normalized = value.replace("\xa0", " ")
        range_match = re.search(
            rf"(\d{{1,2}})\s+y\s+\d{{1,2}}\s+de\s+({MONTHS_ES})(.*?)(?=$| y \d{{1,2}}\s+de )",
            normalized,
            flags=re.IGNORECASE,
        )
        if range_match:
            return first_text(f"{range_match.group(1)} de {range_match.group(2)}{range_match.group(3)}".strip())
        full_match = re.search(
            rf"((?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+)?\d{{1,2}}\s+de\s+({MONTHS_ES})(?:\s+de\s+\d{{4}})?(?:\s+a\s+las\s+\d{{1,2}}[:.]\d{{2}}\s*horas?)?",
            normalized,
            flags=re.IGNORECASE,
        )
        return first_text(full_match.group(0) if full_match else value)
