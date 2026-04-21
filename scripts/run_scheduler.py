from app.core.config import get_settings
from app.core.logging import configure_logging
from app.tasks.scheduler import run_scheduler


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    run_scheduler()


if __name__ == "__main__":
    main()
