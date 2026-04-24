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
        family = Category(slug="family", icon="family", sort_order=2)
        family.translations = [CategoryTranslation(language="en", name="Family", description="Family events")]
        db.add(music)
        db.add(family)
        event = Event(
            slug="sunset-soundscapes-20261107",
            source_name="eventbrite",
            external_id="123",
            source_url="https://example.com/event",
            fingerprint="fp-1",
            starts_at=datetime.fromisoformat("2026-11-07T20:00:00+00:00"),
            is_free=True,
            venue_name="Jameos del Agua",
            image_url="https://example.com/sunset.jpg",
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
        unknown_free_event = Event(
            slug="cine-al-aire-libre-20261106",
            source_name="culturalanzarote_program",
            external_id="unknown-free-1",
            source_url="https://example.com/cine-aire-libre",
            fingerprint="fp-unknown-free-1",
            starts_at=datetime.fromisoformat("2026-11-06T19:30:00+00:00"),
            is_free=None,
            price_text=None,
            venue_name="Arrecife",
        )
        unknown_free_event.translations = [
            EventTranslation(language="en", title="Cinema under the stars", summary="Outdoor screening", description="Family outdoor screening."),
        ]
        unknown_free_event.categories = [family]
        db.add(unknown_free_event)
        priced_by_text_event = Event(
            slug="paid-talk-20261106",
            source_name="eventbrite",
            external_id="priced-by-text-1",
            source_url="https://example.com/paid-talk",
            fingerprint="fp-priced-by-text-1",
            starts_at=datetime.fromisoformat("2026-11-06T21:00:00+00:00"),
            is_free=None,
            price_text=None,
            venue_name="Arrecife",
        )
        priced_by_text_event.translations = [
            EventTranslation(language="en", title="Paid talk", summary="Entry 12€", description="Ticket price 12€."),
        ]
        priced_by_text_event.categories = [music]
        db.add(priced_by_text_event)
        alternative_event = Event(
            slug="creative-morning-20261107",
            source_name="tinajo_agenda",
            external_id="alternative-1",
            source_url="https://example.com/creative-morning",
            fingerprint="fp-alternative-1",
            starts_at=datetime.fromisoformat("2026-11-07T10:00:00+00:00"),
            is_free=True,
            venue_name="Tinajo",
        )
        alternative_event.translations = [
            EventTranslation(language="en", title="Creative morning for families", summary="Hands-on workshop", description="A family workshop."),
        ]
        alternative_event.categories = [family]
        db.add(alternative_event)
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
    assert "¿Qué hacemos el fin de semana?" in response.text


def test_categories_are_localized():
    response = client.get("/api/v1/categories", params={"lang": "en"})
    payload = response.json()
    assert response.status_code == 200
    assert payload[0]["name"] == "Music"


def test_events_support_days_window():
    response = client.get("/api/v1/events", params={"lang": "en", "starts_after": "2026-11-01", "days": 7})
    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 5
    assert len(payload["items"]) == 5
    assert any(item["title"] == "Evento sin título" for item in payload["items"])


def test_events_reject_ranges_over_seven_days():
    response = client.get("/api/v1/events", params={"starts_after": "2026-11-01", "starts_before": "2026-11-10"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Date range cannot exceed 7 days"


def test_free_only_includes_unknown_price_but_excludes_paid_signals():
    response = client.get("/api/v1/events", params={"lang": "en", "free_only": "true"})
    payload = response.json()
    assert response.status_code == 200
    titles = {item["title"] for item in payload["items"]}
    assert "Sunset Soundscapes Lanzarote" in titles
    assert "Cinema under the stars" in titles
    assert "Paid talk" not in titles
    assert "Evento sin título" not in titles


def test_next_48h_returns_editorial_featured_slots():
    response = client.get(
        "/api/v1/events/next-48h",
        params={"lang": "en", "search_at": "2026-11-06T18:00:00+00:00"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["total"] == 5
    featured = {item["slot"]: item["event"]["title"] if item["event"] else None for item in payload["featured"]}
    assert featured["imminent"] == "Cinema under the stars"
    assert featured["popular"] == "Sunset Soundscapes Lanzarote"
    assert featured["alternative"] == "Creative morning for families"


def test_admin_sources_are_listed():
    response = client.get("/api/v1/admin/sources")
    payload = response.json()
    assert response.status_code == 200
    keys = {item["key"] for item in payload}
    assert "culturalanzarote_program" in keys
    assert "cact_lanzarote" in keys
    assert "eventbrite" in keys
    assert "ecoentradas_lanzarote" in keys
    assert "tinajo_agenda" in keys
    assert "teguise_cultura" in keys
    assert "tias_cultura" in keys
    assert "arrecife_cultura" in keys
    assert "yaiza_cultura" in keys
    assert "sanbartolome_eventos" in keys
    assert "haria_cultura" in keys


def test_admin_sources_can_be_toggled():
    response = client.patch("/api/v1/admin/sources/eventbrite", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["enabled"] is True

    response = client.patch("/api/v1/admin/sources/eventbrite", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False


def test_admin_source_candidates_can_be_created():
    response = client.post(
        "/api/v1/admin/sources/candidates",
        json={
            "url": "https://example.com/agenda-cultural",
            "label": "Ejemplo Agenda",
            "notes": "Posible fuente a revisar",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["url"] == "https://example.com/agenda-cultural"
    assert payload["label"] == "Ejemplo Agenda"
    assert payload["status"] == "pending"


def test_admin_source_candidates_are_listed():
    response = client.get("/api/v1/admin/sources/candidates")
    payload = response.json()
    assert response.status_code == 200
    assert any(item["url"] == "https://example.com/agenda-cultural" for item in payload)
