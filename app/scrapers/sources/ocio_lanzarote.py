import json
import re
from typing import Any

from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, RawScrapedEvent
from app.scrapers.utils import absolute_url, first_text, plain_text, text_lines


settings = get_settings()

DATE_PATTERN = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december|\d{4})",
    re.IGNORECASE,
)


class OcioLanzaroteScraper(BaseScraper):
    source_name = "ocio_lanzarote"
    source_url = settings.ocio_lanzarote_events_url
    fixture_name = "ocio_lanzarote_listing.html"
    api_url = "https://ociolanzarote.com/wp-json/wp/v2/posts?categories=15091&per_page=70&_embed=1"

    def collect(self) -> list[RawScrapedEvent]:
        try:
            if settings.scraper_use_fixtures:
                return self.parse(self.fixture_text())
            return self._collect_from_api()
        except Exception:
            return super().collect()

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("article, .post, .event-card")
        events: list[RawScrapedEvent] = []
        seen_urls: set[str] = set()

        for card in cards:
            link = card.find("a", href=True)
            headings = [tag.get_text(" ", strip=True) for tag in card.find_all(["h1", "h2", "h3", "h4"])]
            lines = text_lines(card.get_text("\n", strip=True))
            title = first_text(*headings, lines[0] if lines else None)
            if not title or len(title) < 4:
                continue

            event_url = absolute_url(self.source_url, link.get("href")) if link else self.source_url
            if not event_url or event_url in seen_urls:
                continue
            seen_urls.add(event_url)

            starts_at_raw = first_text(*[line for line in lines if DATE_PATTERN.search(line)])
            summary = first_text(lines[1] if len(lines) > 1 else None, lines[2] if len(lines) > 2 else None)
            image = card.find("img")

            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=event_url,
                    external_id=link.get("href") if link else event_url,
                    canonical_url=event_url,
                    title=title,
                    summary=summary,
                    starts_at_raw=starts_at_raw,
                    image_url=image.get("src") if image else None,
                    language_origin="en",
                    category_hints=["shows"],
                    source_payload={"lines": lines[:10]},
                )
            )
        return events

    def _collect_from_api(self) -> list[RawScrapedEvent]:
        posts: list[dict[str, Any]] = json.loads(self.fetch_url(self.api_url))
        events: list[RawScrapedEvent] = []
        for post in posts:
            title = plain_text(post.get("title", {}).get("rendered"))
            if not title:
                continue
            content = plain_text(post.get("content", {}).get("rendered"))
            excerpt = plain_text(post.get("excerpt", {}).get("rendered"))
            starts_at_raw = self._extract_event_date(content or "")
            price_text = self._extract_price(content or "")
            tags = [item.get("label") for item in post.get("tag_info", []) if item.get("label")]
            categories = [item.get("label") for item in post.get("category_info", []) if item.get("label")]
            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=post.get("link") or self.source_url,
                    external_id=str(post.get("id")),
                    canonical_url=post.get("link"),
                    title=title,
                    summary=excerpt,
                    description=content[:2000] if content else None,
                    starts_at_raw=starts_at_raw,
                    is_free=True if content and "free entry" in content.lower() else None,
                    price_text=price_text,
                    image_url=(post.get("featured_image_src_large") or [None])[0],
                    language_origin="en",
                    category_hints=categories,
                    tags=tags,
                    source_payload={"api_id": post.get("id"), "tags": tags, "categories": categories},
                )
            )
        return events

    @staticmethod
    def _extract_event_date(text: str) -> str | None:
        patterns = [
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,\s+\d{4}",
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def _extract_price(text: str) -> str | None:
        match = re.search(r"(€\s?\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s?€|\d+(?:[.,]\d+)?\s?EUR)", text, flags=re.IGNORECASE)
        return first_text(match.group(0) if match else None)
