import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import get_settings
from app.tasks.run_scrapers import run_ingestion_cycle


logger = logging.getLogger(__name__)
settings = get_settings()


def run_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="Atlantic/Canary")
    scheduler.add_job(
        run_ingestion_cycle,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="scrape_events",
        replace_existing=True,
    )
    logger.info("Scheduler started with %s minute interval", settings.scrape_interval_minutes)
    scheduler.start()
