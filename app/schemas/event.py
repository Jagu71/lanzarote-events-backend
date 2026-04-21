from pydantic import BaseModel

from app.schemas.category import CategoryPublic


class EventSummary(BaseModel):
    id: str
    slug: str
    title: str
    summary: str | None = None
    description: str | None = None
    translation_language: str
    available_languages: list[str]
    starts_at: str | None = None
    ends_at: str | None = None
    is_free: bool | None = None
    price_text: str | None = None
    source_name: str
    source_url: str
    image_url: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    municipality: str | None = None
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    categories: list[CategoryPublic]


class EventDetail(EventSummary):
    organizer_name: str | None = None
    audience: str | None = None
    canonical_url: str | None = None
    language_origin: str
    translations: dict[str, dict[str, str | None]]
    source_payload: dict


class EventListResponse(BaseModel):
    items: list[EventSummary]
    total: int
    limit: int
    offset: int
