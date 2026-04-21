from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.events import EventRepository
from app.schemas.event import EventDetail, EventListResponse, EventSummary
from app.services.categories import CategoryService
from app.services.translations import pick_event_translation
from app.utils.date_parsing import parse_date_filter, range_exceeds_days


@dataclass
class EventQuery:
    lang: str = "es"
    category: str | None = None
    starts_after: str | None = None
    starts_before: str | None = None
    free_only: bool | None = None
    text: str | None = None
    days: int | None = None
    limit: int = 20
    offset: int = 0


class EventService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EventRepository(db)
        self.category_service = CategoryService(db)

    def list_events(self, query: EventQuery) -> EventListResponse:
        starts_after = parse_date_filter(query.starts_after)
        starts_before = parse_date_filter(query.starts_before)
        if query.days is not None:
            starts_after = starts_after or datetime.now(ZoneInfo("Atlantic/Canary"))
            starts_before = starts_after + timedelta(days=query.days)
        elif range_exceeds_days(starts_after, starts_before, max_days=7):
            raise HTTPException(status_code=400, detail="Date range cannot exceed 7 days")
        events, total = self.repository.list_events(
            category=query.category,
            starts_after=starts_after,
            starts_before=starts_before,
            free_only=query.free_only,
            text=query.text,
            limit=query.limit,
            offset=query.offset,
        )
        return EventListResponse(
            items=[self._to_summary(event, query.lang) for event in events],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get_event(self, event_id: str, lang: str) -> EventDetail | None:
        event = self.repository.get_event(event_id)
        if event is None:
            return None
        summary = self._to_summary(event, lang)
        translations = {
            translation.language: {
                "title": translation.title,
                "summary": translation.summary,
                "description": translation.description,
            }
            for translation in event.translations
        }
        return EventDetail(
            **summary.model_dump(),
            organizer_name=event.organizer_name,
            audience=event.audience,
            canonical_url=event.canonical_url,
            language_origin=event.language_origin,
            translations=translations,
            source_payload=event.source_payload or {},
        )

    def _to_summary(self, event: Event, lang: str) -> EventSummary:
        translation = pick_event_translation(event.translations, lang)
        categories = [self.category_service._to_public(category, lang) for category in event.categories]
        return EventSummary(
            id=event.id,
            slug=event.slug,
            title=translation.title,
            summary=translation.summary,
            description=translation.description,
            translation_language=translation.language,
            available_languages=sorted([item.language for item in event.translations]),
            starts_at=self._isoformat(event.starts_at),
            ends_at=self._isoformat(event.ends_at),
            is_free=event.is_free,
            price_text=event.price_text,
            source_name=event.source_name,
            source_url=event.source_url,
            image_url=event.image_url,
            venue_name=event.venue_name,
            venue_address=event.venue_address,
            municipality=event.municipality,
            locality=event.locality,
            latitude=event.latitude,
            longitude=event.longitude,
            categories=categories,
        )

    @staticmethod
    def _isoformat(value: datetime | None) -> str | None:
        return value.isoformat() if value else None
