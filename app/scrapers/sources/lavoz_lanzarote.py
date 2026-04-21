import re

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, image_src, meta_description, plain_text
from app.utils.date_parsing import parse_localized_datetime


settings = get_settings()

MONTHS_ES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
)
FUTURE_HINTS = [
    "agenda cultural",
    "entradas ya están disponibles",
    "entradas ya estan disponibles",
    "la cita será",
    "la cita sera",
    "se celebrará",
    "se celebrara",
    "celebrará",
    "celebrara",
    "actuará",
    "actuara",
    "llega a lanzarote",
    "próximo",
    "proximo",
    "este sábado",
    "este sabado",
    "este domingo",
    "este viernes",
    "programación",
    "programacion",
]
VENUE_PATTERNS = [
    r"(Teatro(?:\s+Municipal)?(?:\s+de)?\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Cines?\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Jameos del Agua)",
    r"(Auditorio\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Sala\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Casa de la Cultura\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Centro(?:\s+Sociocultural|\s+Socio Cultural|\s+Insular)?\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Iglesia de\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Museo\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
    r"(Plaza\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ.' -]+)",
]


class LaVozLanzaroteScraper(BaseScraper):
    source_name = "lavoz_lanzarote"
    source_url = settings.lavoz_lanzarote_url
    fixture_name = "lavoz_lanzarote_listing.html"

    def collect(self) -> list[RawScrapedEvent]:
        try:
            events = self.parse(self.fetch())
            if settings.scraper_use_fixtures:
                return events

            enriched_events: list[RawScrapedEvent] = []
            for event in events:
                if self._enrich_from_detail(event):
                    enriched_events.append(event)
            return enriched_events
        except Exception:
            return super().collect()

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for card in soup.select("article.c-news-list__article"):
            link = card.select_one("h2.c-news-list__title a[href]")
            title = first_text(link.get_text(" ", strip=True) if link else None)
            subtitle = first_text(
                card.select_one("h3.c-news-list__subtitle").get_text(" ", strip=True)
                if card.select_one("h3.c-news-list__subtitle")
                else None
            )
            if not title or not link:
                continue

            event_url = absolute_url(self.source_url, link.get("href"))
            if not event_url or event_url in seen_urls:
                continue
            seen_urls.add(event_url)

            teaser_text = " ".join(part for part in [title, subtitle] if part)
            if not self._looks_like_event(teaser_text):
                continue

            published_raw = first_text(
                card.select_one("time.c-news-list__time").get_text(" ", strip=True)
                if card.select_one("time.c-news-list__time")
                else None
            )

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=event_url,
                    external_id=link.get("href"),
                    canonical_url=event_url,
                    title=title,
                    summary=subtitle,
                    image_url=image_src(card.select_one("img")),
                    language_origin="es",
                    category_hints=["cultura", "agenda"],
                    source_payload={"published_at_raw": published_raw},
                )
            )
        return events

    def _enrich_from_detail(self, event: RawScrapedEvent) -> bool:
        soup = BeautifulSoup(self.fetch_url(event.source_url), "lxml")
        body = soup.select_one(".c-mainarticle__body")
        body_text = plain_text(str(body)) if body else None
        subtitle = first_text(
            soup.select_one("h2.c-mainarticle__subtitle").get_text(" ", strip=True)
            if soup.select_one("h2.c-mainarticle__subtitle")
            else None
        )
        title = first_text(
            soup.select_one("h1").get_text(" ", strip=True) if soup.select_one("h1") else None,
            event.title,
        )
        published_raw = first_text(
            soup.select_one("article time").get_text(" ", strip=True) if soup.select_one("article time") else None,
            event.source_payload.get("published_at_raw"),
        )
        description = first_text(meta_description(soup), subtitle, event.summary)
        combined_text = " ".join(part for part in [title, subtitle, body_text] if part)
        starts_at_raw = self._extract_event_date(combined_text)
        venue_name = self._extract_venue(combined_text)
        ticket_link = self._extract_ticket_link(soup)
        image_url = image_src(soup.select_one(".c-mainarticle__fig img")) or event.image_url
        tags = [
            tag.get_text(" ", strip=True)
            for tag in soup.select('a[href*="/tag/"], a[href*="/etiqueta/"]')
            if tag.get_text(" ", strip=True)
        ]

        if not self._should_keep_event(combined_text, starts_at_raw, published_raw):
            return False

        event.title = title
        event.summary = description
        event.description = body_text or event.description
        event.starts_at_raw = starts_at_raw
        event.venue_name = venue_name or event.venue_name
        event.image_url = image_url
        event.tags = list(dict.fromkeys([*event.tags, *tags]))
        event.category_hints = list(dict.fromkeys([*event.category_hints, *tags]))
        event.source_payload["published_at_raw"] = published_raw
        if ticket_link:
            event.source_payload["ticket_url"] = ticket_link
        return True

    def _should_keep_event(self, text: str, starts_at_raw: str | None, published_raw: str | None) -> bool:
        if starts_at_raw:
            starts_at = parse_localized_datetime(starts_at_raw, ["es"])
            published_at = parse_localized_datetime(published_raw, ["es"]) if published_raw else None
            if starts_at and published_at and starts_at.date() < published_at.date():
                return False
            return True
        return self._looks_like_event(text)

    @staticmethod
    def _looks_like_event(text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in FUTURE_HINTS)

    @staticmethod
    def _extract_event_date(text: str) -> str | None:
        patterns = [
            rf"(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+\d{{1,2}}\s+de\s+(?:{MONTHS_ES})(?:\s+de\s+\d{{4}})?(?:\s+a\s+las\s+\d{{1,2}}[:.]\d{{2}})?",
            rf"\d{{1,2}}\s+de\s+(?:{MONTHS_ES})(?:\s+de\s+\d{{4}})?(?:\s+a\s+las\s+\d{{1,2}}[:.]\d{{2}})?",
            rf"del\s+\d{{1,2}}\s+al\s+\d{{1,2}}\s+de\s+(?:{MONTHS_ES})(?:\s+de\s+\d{{4}})?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0).replace(".", ":")
        return None

    @staticmethod
    def _extract_venue(text: str) -> str | None:
        for pattern in VENUE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return first_text(match.group(1))
        return None

    @staticmethod
    def _extract_ticket_link(soup: BeautifulSoup) -> str | None:
        for anchor in soup.select(".c-mainarticle__body a[href]"):
            href = anchor.get("href")
            text = anchor.get_text(" ", strip=True).lower()
            if "entrad" in text or any(provider in (href or "").lower() for provider in ["ecoentradas", "sacatuentrada", "eventbrite"]):
                return href
        return None
