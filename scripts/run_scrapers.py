from pprint import pprint

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.tasks.run_scrapers import run_ingestion_cycle


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    pprint(run_ingestion_cycle())


if __name__ == "__main__":
    main()
