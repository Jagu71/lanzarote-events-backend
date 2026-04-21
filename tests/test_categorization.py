from app.scrapers.base import NormalizedEvent
from app.services.ingestion import IngestionService


def build_payload(title: str, summary: str | None = None, description: str | None = None, venue_name: str | None = None) -> NormalizedEvent:
    return NormalizedEvent(
        source_name="test",
        source_url="https://example.com",
        external_id=None,
        canonical_url=None,
        starts_at=None,
        ends_at=None,
        timezone="Atlantic/Canary",
        is_free=None,
        price_text=None,
        currency=None,
        image_url=None,
        venue_name=venue_name,
        venue_address=None,
        municipality=None,
        locality=None,
        organizer_name=None,
        audience=None,
        language_origin="es",
        translations={"es": {"title": title, "summary": summary, "description": description}},
        tags=[],
        category_hints=[],
        source_payload={},
    )


def categorize(payload: NormalizedEvent) -> list[str]:
    service = IngestionService.__new__(IngestionService)
    return IngestionService._categorize(service, payload)


def test_cinema_event_is_categorized_as_cinema():
    payload = build_payload("La ola", "Película de Sebastián Lelio", "Sesión de cine en El Almacén")
    assert categorize(payload) == ["cinema"]


def test_workshop_for_children_adds_family_overlay():
    payload = build_payload(
        "Taller para niños y niñas: Los Gigantes no son lo que creemos que son",
        "Actividad participativa",
        "Especialmente recomendado a partir de 7 años",
    )
    assert categorize(payload) == ["workshop", "family"]


def test_live_music_event_is_not_misclassified_as_family():
    payload = build_payload(
        "Juan Luis Guerra, Nathy Peluso y Nicky Jam actuarán en Lava Live",
        "Concierto en directo",
        "Festival con artistas internacionales y varios DJ",
    )
    assert categorize(payload) == ["music"]
