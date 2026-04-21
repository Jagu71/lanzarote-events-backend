from app.scrapers.base import BaseScraper
from app.scrapers.sources.cabildo import CabildoScraper
from app.scrapers.sources.cact import CactScraper
from app.scrapers.sources.culturalanzarote_program import CulturalLanzaroteProgramScraper
from app.scrapers.sources.culturalanzarote_tickets import CulturalLanzaroteTicketsScraper
from app.scrapers.sources.lavoz_lanzarote import LaVozLanzaroteScraper


def build_scrapers() -> list[BaseScraper]:
    scrapers: list[BaseScraper] = [
        CulturalLanzaroteProgramScraper(),
        CulturalLanzaroteTicketsScraper(),
        CactScraper(),
        LaVozLanzaroteScraper(),
    ]
    cabildo = CabildoScraper()
    if cabildo.source_url:
        scrapers.append(cabildo)
    return scrapers
