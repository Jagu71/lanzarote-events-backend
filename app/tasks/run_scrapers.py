import logging

from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import engine
from app.scrapers.registry import build_scrapers
from app.services.ingestion import IngestionService


logger = logging.getLogger(__name__)


def run_ingestion_cycle() -> dict[str, int]:
    init_db()
    raw_events = []
    for scraper in build_scrapers():
        raw_events.extend(scraper.collect())

    with Session(engine) as session:
        result = IngestionService(session).ingest_many(raw_events)
        logger.info("Ingestion cycle completed: %s", result)
        return result
