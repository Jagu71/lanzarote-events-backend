from dataclasses import dataclass
from typing import Callable

from app.scrapers.base import BaseScraper
from app.scrapers.sources.arrecife_cultura import ArrecifeCulturaScraper
from app.scrapers.sources.cabildo import CabildoScraper
from app.scrapers.sources.cact import CactScraper
from app.scrapers.sources.culturalanzarote_program import CulturalLanzaroteProgramScraper
from app.scrapers.sources.culturalanzarote_tickets import CulturalLanzaroteTicketsScraper
from app.scrapers.sources.ecoentradas_lanzarote import EcoEntradasLanzaroteScraper
from app.scrapers.sources.eventbrite import EventbriteScraper
from app.scrapers.sources.lavoz_lanzarote import LaVozLanzaroteScraper
from app.scrapers.sources.ocio_lanzarote import OcioLanzaroteScraper
from app.scrapers.sources.sanbartolome_eventos import SanBartolomeEventosScraper
from app.scrapers.sources.teguise_cultura import TeguiseCulturaScraper
from app.scrapers.sources.tias_cultura import TiasCulturaScraper
from app.scrapers.sources.tinajo_agenda import TinajoAgendaScraper
from app.scrapers.sources.yaiza_cultura import YaizaCulturaScraper


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
        key="ecoentradas_lanzarote",
        label="EcoEntradas Lanzarote",
        description="Cartelera de venta y reserva de entradas ya filtrada para Lanzarote.",
        enabled_by_default=True,
        scraper_factory=EcoEntradasLanzaroteScraper,
    ),
    SourceDefinition(
        key="lavoz_lanzarote",
        label="La Voz de Lanzarote",
        description="Cobertura editorial de agenda/cultura útil para discovery secundario.",
        enabled_by_default=True,
        scraper_factory=LaVozLanzaroteScraper,
    ),
    SourceDefinition(
        key="tinajo_agenda",
        label="Tinajo Agenda",
        description="Agenda oficial municipal de Tinajo con eventos y actividades públicas.",
        enabled_by_default=True,
        scraper_factory=TinajoAgendaScraper,
    ),
    SourceDefinition(
        key="teguise_cultura",
        label="Teguise Cultura",
        description="Página oficial de Cultura y Patrimonio del Ayuntamiento de Teguise.",
        enabled_by_default=True,
        scraper_factory=TeguiseCulturaScraper,
    ),
    SourceDefinition(
        key="tias_cultura",
        label="Tías Cultura",
        description="Noticias y agenda cultural oficial del Ayuntamiento de Tías.",
        enabled_by_default=True,
        scraper_factory=TiasCulturaScraper,
    ),
    SourceDefinition(
        key="arrecife_cultura",
        label="Arrecife Cultura",
        description="Taxonomía oficial de Cultura Arrecife con publicaciones de agenda y programación.",
        enabled_by_default=True,
        scraper_factory=ArrecifeCulturaScraper,
    ),
    SourceDefinition(
        key="yaiza_cultura",
        label="Yaiza Cultura",
        description="Área oficial de Educación, Cultura y Patrimonio del Ayuntamiento de Yaiza.",
        enabled_by_default=True,
        scraper_factory=YaizaCulturaScraper,
    ),
    SourceDefinition(
        key="sanbartolome_eventos",
        label="San Bartolomé Eventos",
        description="Sección oficial de eventos municipales y agenda del Ayuntamiento de San Bartolomé.",
        enabled_by_default=True,
        scraper_factory=SanBartolomeEventosScraper,
    ),
    SourceDefinition(
        key="haria_cultura",
        label="Haría Cultura",
        description="Fuente municipal pendiente de URL oficial confirmada.",
        enabled_by_default=False,
        scraper_factory=lambda: type(
            "HariaPlaceholderScraper",
            (BaseScraper,),
            {
                "source_name": "haria_cultura",
                "source_url": "",
                "fixture_name": None,
                "parse": lambda self, html: [],
            },
        )(),
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
