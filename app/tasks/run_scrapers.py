import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import engine
from app.scrapers.registry import build_scrapers
from app.services.ingestion import IngestionService
from app.services.sources import SourceService


logger = logging.getLogger(__name__)


def run_ingestion_cycle() -> dict[str, int]:
    init_db()
    with Session(engine) as session:
        source_service = SourceService(session)
        enabled_keys = source_service.runnable_source_keys()

    total_created = 0
    total_updated = 0
    total_processed = 0
    per_source: dict[str, dict[str, int | str | None]] = {}

    for scraper in build_scrapers(enabled_keys):
        raw_events = scraper.collect()
        run_at = datetime.now(UTC)
        with Session(engine) as session:
            result = IngestionService(session).ingest_many(raw_events)
            status = "error" if scraper.last_error_message else ("empty" if result["processed"] == 0 else "success")
            SourceService(session).record_run(
                key=scraper.source_name,
                processed=result["processed"],
                created=result["created"],
                updated=result["updated"],
                status=status,
                message=scraper.last_error_message,
                run_at=run_at,
            )
        total_created += result["created"]
        total_updated += result["updated"]
        total_processed += result["processed"]
        per_source[scraper.source_name] = {
            "processed": result["processed"],
            "created": result["created"],
            "updated": result["updated"],
            "status": status,
            "message": scraper.last_error_message,
        }

    result = {
        "created": total_created,
        "updated": total_updated,
        "processed": total_processed,
        "sources": per_source,
    }
    logger.info("Ingestion cycle completed: %s", result)
    return result
