from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.event import EventDetail, EventListResponse, EventNowResponse
from app.services.events import EventQuery, EventService


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    lang: str = Query("es", description="Idioma preferido de la respuesta."),
    category: str | None = Query(default=None),
    starts_after: str | None = Query(default=None),
    starts_before: str | None = Query(default=None),
    days: int | None = Query(default=None, ge=1, le=7, description="Ventana máxima en días desde starts_after o desde hoy."),
    free_only: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Texto libre para buscar."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> EventListResponse:
    service = EventService(db)
    query = EventQuery(
        lang=lang,
        category=category,
        starts_after=starts_after,
        starts_before=starts_before,
        days=days,
        free_only=free_only,
        text=q,
        limit=limit,
        offset=offset,
    )
    return service.list_events(query)


@router.get("/search", response_model=EventListResponse)
def search_events(
    q: str = Query(..., min_length=2),
    lang: str = Query("es"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> EventListResponse:
    service = EventService(db)
    query = EventQuery(lang=lang, text=q, limit=limit, offset=offset)
    return service.list_events(query)


@router.get("/next-48h", response_model=EventNowResponse)
def get_now_plan(
    lang: str = Query("es"),
    category: str | None = Query(default=None),
    free_only: bool | None = Query(default=None),
    search_at: str | None = Query(default=None, description="Hora de búsqueda en ISO para recomendación editorial."),
    db: Session = Depends(get_db),
) -> EventNowResponse:
    service = EventService(db)
    return service.get_now_plan(lang=lang, free_only=free_only, category=category, search_at=search_at)


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: str,
    lang: str = Query("es"),
    db: Session = Depends(get_db),
) -> EventDetail:
    service = EventService(db)
    event = service.get_event(event_id=event_id, lang=lang)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
