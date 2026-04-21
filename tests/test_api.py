from datetime import datetime
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.category import Category, CategoryTranslation
from app.models.event import Event, EventTranslation


SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        music = Category(slug="music", icon="music", sort_order=1)
        music.translations = [CategoryTranslation(language="en", name="Music", description="Music events")]
        db.add(music)
        event = Event(
            slug="sunset-soundscapes-20261107",
            source_name="eventbrite",
            external_id="123",
            source_url="https://example.com/event",
            fingerprint="fp-1",
            starts_at=datetime.fromisoformat("2026-11-07T20:00:00+00:00"),
            is_free=True,
            venue_name="Jameos del Agua",
        )
        event.translations = [
            EventTranslation(language="en", title="Sunset Soundscapes Lanzarote", summary="Live set", description="A live set."),
        ]
        event.categories = [music]
        db.add(event)
        broken_event = Event(
            slug="evento-roto-20261108",
            source_name="lavoz_lanzarote",
            external_id="broken-1",
            source_url="https://example.com/broken-event",
            fingerprint="fp-broken-1",
            starts_at=datetime.fromisoformat("2026-11-07T10:00:00+00:00"),
            is_free=False,
            venue_name="Arrecife",
        )
        broken_event.categories = [music]
        db.add(broken_event)
        db.commit()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_list_events_filter_by_text():
    response = client.get("/api/v1/events", params={"lang": "en", "q": "sunset"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "Sunset Soundscapes Lanzarote"


def test_frontend_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Lanzarote en Vivo" in response.text


def test_categories_are_localized():
    response = client.get("/api/v1/categories", params={"lang": "en"})
    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["name"] == "Music"


def test_events_support_days_window():
    response = client.get("/api/v1/events", params={"lang": "en", "starts_after": "2026-11-01", "days": 7})
    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    assert any(item["title"] == "Evento sin título" for item in payload["items"])


def test_events_reject_ranges_over_seven_days():
    response = client.get("/api/v1/events", params={"starts_after": "2026-11-01", "starts_before": "2026-11-10"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Date range cannot exceed 7 days"
