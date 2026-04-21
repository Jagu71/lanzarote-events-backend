from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init_db import init_db


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()


if __name__ == "__main__":
    main()
