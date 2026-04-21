from datetime import datetime

from app.models.event import Event, EventTranslation
from app.services.deduplication import build_event_fingerprint, merge_event_records, titles_are_similar, venues_are_similar


def build_event(title: str, language: str = "es") -> Event:
    event = Event(
        slug="sample",
        source_name="test",
        external_id=None,
        source_url="https://example.com",
        fingerprint="abc",
    )
    event.translations = [EventTranslation(language=language, title=title, summary=None, description=None)]
    return event


def test_titles_are_similar_for_minor_differences():
    assert titles_are_similar("Jameos Night", "Jameos  Night")


def test_titles_are_similar_for_editorial_variants():
    assert titles_are_similar("David y Goliat", "Danza familiar: David & Goliat")
    assert titles_are_similar("Gambia, país de resiliencia", "“Gambia, país de resiliencia” | El documental")


def test_build_event_fingerprint_changes_with_date():
    first = build_event_fingerprint(
        title="Jameos Night",
        starts_at=datetime(2026, 5, 2, 20, 0),
        venue_name="Jameos del Agua",
    )
    second = build_event_fingerprint(
        title="Jameos Night",
        starts_at=datetime(2026, 5, 3, 20, 0),
        venue_name="Jameos del Agua",
    )
    assert first != second


def test_merge_event_records_adds_new_translation():
    target = build_event("Noche en Jameos", "es")
    incoming = build_event("Jameos Night", "en")
    merge_event_records(target, incoming)
    assert {translation.language for translation in target.translations} == {"es", "en"}


def test_venues_are_similar_with_local_variants():
    assert venues_are_similar("Teatro Víctor Fernández Gopar El Salinero", "Teatro El Salinero")
