from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.models.event import Event, EventTranslation


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_events(
        self,
        *,
        category: str | None = None,
        starts_after: datetime | None = None,
        starts_before: datetime | None = None,
        free_only: bool | None = None,
        text: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Event], int]:
        stmt = select(Event).options(
            selectinload(Event.translations),
            selectinload(Event.categories).selectinload(Category.translations),
        )
        count_stmt = select(func.count(func.distinct(Event.id)))

        if category:
            category_filter = Event.categories.any(Category.slug == category)
            stmt = stmt.where(category_filter)
            count_stmt = count_stmt.select_from(Event).where(category_filter)
        else:
            count_stmt = count_stmt.select_from(Event)

        if starts_after:
            stmt = stmt.where(Event.starts_at >= starts_after)
            count_stmt = count_stmt.where(Event.starts_at >= starts_after)
        if starts_before:
            stmt = stmt.where(Event.starts_at <= starts_before)
            count_stmt = count_stmt.where(Event.starts_at <= starts_before)
        if free_only is not None:
            stmt = stmt.where(Event.is_free == free_only)
            count_stmt = count_stmt.where(Event.is_free == free_only)
        if text:
            pattern = f"%{text.lower()}%"
            translation_filter = or_(
                func.lower(EventTranslation.title).like(pattern),
                func.lower(EventTranslation.summary).like(pattern),
                func.lower(EventTranslation.description).like(pattern),
            )
            text_filter = or_(
                Event.translations.any(translation_filter),
                func.lower(func.coalesce(Event.venue_name, "")).like(pattern),
            )
            stmt = stmt.where(text_filter)
            count_stmt = count_stmt.where(text_filter)

        stmt = stmt.order_by(Event.starts_at.asc().nullslast(), Event.created_at.desc()).limit(limit).offset(offset)
        total = self.db.scalar(count_stmt) or 0
        events = list(self.db.scalars(stmt).all())
        return events, total

    def get_event(self, event_id: str) -> Event | None:
        stmt = (
            select(Event)
            .options(
                selectinload(Event.translations),
                selectinload(Event.categories).selectinload(Category.translations),
            )
            .where(Event.id == event_id)
        )
        return self.db.scalar(stmt)

    def get_by_source_external(self, source_name: str, external_id: str | None) -> Event | None:
        if not external_id:
            return None
        stmt = (
            select(Event)
            .options(selectinload(Event.translations), selectinload(Event.categories))
            .where(Event.source_name == source_name, Event.external_id == external_id)
        )
        return self.db.scalar(stmt)

    def get_by_fingerprint(self, fingerprint: str) -> Event | None:
        stmt = (
            select(Event)
            .options(selectinload(Event.translations), selectinload(Event.categories))
            .where(Event.fingerprint == fingerprint)
        )
        return self.db.scalar(stmt)

    def save(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()
        return event
