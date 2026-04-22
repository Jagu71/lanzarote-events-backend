from dataclasses import dataclass
from typing import Callable

from app.scrapers.base import BaseScraper
from app.scrapers.sources.cabildo import CabildoScraper
from app.scrapers.sources.cact import CactScraper
from app.scrapers.sources.culturalanzarote_program import CulturalLanzaroteProgramScraper
from app.scrapers.sources.culturalanzarote_tickets import CulturalLanzaroteTicketsScraper
from app.scrapers.sources.eventbrite import EventbriteScraper
from app.scrapers.sources.lavoz_lanzarote import LaVozLanzaroteScraper
from app.scrapers.sources.ocio_lanzarote import OcioLanzaroteScraper


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    label: str
    description: str
    enabled_by_default: bool
    scraper_factory: Callable[[], BaseScraper]

    def build(self) -> BaseScraper:
        return self.scraper_factory()


SOURCE_DEFINITIONS: list[SourceDefinition] = [
    SourceDefinition(
        key="culturalanzarote_program",
        label="Cultura Lanzarote Programación",
        description="Fuente principal de agenda cultural del Cabildo y sus espacios.",
        enabled_by_default=True,
        scraper_factory=CulturalLanzaroteProgramScraper,
    ),
    SourceDefinition(
        key="culturalanzarote_tickets",
        label="Cultura Lanzarote Entradas",
        description="Cartelera de Sacatuentrada con fichas y datos de compra.",
        enabled_by_default=True,
        scraper_factory=CulturalLanzaroteTicketsScraper,
    ),
    SourceDefinition(
        key="cact_lanzarote",
        label="CACT Lanzarote",
        description="Eventos y actividades publicadas por los Centros de Arte, Cultura y Turismo.",
        enabled_by_default=True,
        scraper_factory=CactScraper,
    ),
    SourceDefinition(
        key="lavoz_lanzarote",
        label="La Voz de Lanzarote",
        description="Cobertura editorial de agenda/cultura útil para discovery secundario.",
        enabled_by_default=True,
        scraper_factory=LaVozLanzaroteScraper,
    ),
    SourceDefinition(
        key="cabildo_lanzarote",
        label="Cabildo de Lanzarote",
        description="Fuente opcional pendiente de URL/agenda concreta.",
        enabled_by_default=False,
        scraper_factory=CabildoScraper,
    ),
    SourceDefinition(
        key="eventbrite",
        label="Eventbrite Lanzarote",
        description="Fuente secundaria de eventos comerciales y tickets.",
        enabled_by_default=False,
        scraper_factory=EventbriteScraper,
    ),
    SourceDefinition(
        key="ocio_lanzarote",
        label="Ocio Lanzarote",
        description="Agenda secundaria menos prioritaria; disponible pero desactivada por defecto.",
        enabled_by_default=False,
        scraper_factory=OcioLanzaroteScraper,
    ),
]

SOURCE_DEFINITIONS_BY_KEY = {item.key: item for item in SOURCE_DEFINITIONS}


def list_source_definitions() -> list[SourceDefinition]:
    return list(SOURCE_DEFINITIONS)


def build_scrapers(enabled_keys: set[str] | None = None) -> list[BaseScraper]:
    scrapers: list[BaseScraper] = []
    for definition in SOURCE_DEFINITIONS:
        if enabled_keys is not None and definition.key not in enabled_keys:
            continue
        scraper = definition.build()
        if scraper.source_url:
            scrapers.append(scraper)
    return scrapers
