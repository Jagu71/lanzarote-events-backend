from pathlib import Path

from app.scrapers.sources.cact import CactScraper
from app.scrapers.sources.culturalanzarote_program import CulturalLanzaroteProgramScraper
from app.scrapers.sources.culturalanzarote_tickets import CulturalLanzaroteTicketsScraper
from app.scrapers.sources.eventbrite import EventbriteScraper
from app.scrapers.sources.lavoz_lanzarote import LaVozLanzaroteScraper


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_cact_scraper_reads_json_ld_fixture():
    html = (FIXTURES_DIR / "cact_listing.html").read_text(encoding="utf-8")
    events = CactScraper().parse(html)
    assert len(events) == 1
    assert events[0].title == "Jameos Night"
    assert events[0].venue_name == "Jameos del Agua"


def test_eventbrite_scraper_extracts_cards():
    html = (FIXTURES_DIR / "eventbrite_listing.html").read_text(encoding="utf-8")
    events = EventbriteScraper().parse(html)
    assert len(events) == 2
    assert events[1].is_free is True


def test_culturalanzarote_program_scraper_extracts_program_cards():
    html = (FIXTURES_DIR / "culturalanzarote_program_listing.html").read_text(encoding="utf-8")
    events = CulturalLanzaroteProgramScraper().parse(html)
    assert len(events) == 2
    assert events[0].title == "Concierto de Primavera"


def test_culturalanzarote_tickets_scraper_extracts_venue_and_price():
    html = (FIXTURES_DIR / "culturalanzarote_tickets_listing.html").read_text(encoding="utf-8")
    events = CulturalLanzaroteTicketsScraper().parse(html)
    assert len(events) == 1
    assert events[0].venue_name == "Teatro El Salinero"
    assert events[0].price_text == "10€"
    assert events[0].starts_at_raw == "16 de abril a las 19:00 horas"


def test_lavoz_lanzarote_scraper_extracts_future_event_cards():
    html = (FIXTURES_DIR / "lavoz_lanzarote_listing.html").read_text(encoding="utf-8")
    events = LaVozLanzaroteScraper().parse(html)
    assert len(events) == 1
    assert "Jorge Bolaños" in events[0].title
