from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models import category, event, source  # noqa: F401
from app.services.categories import CategoryService
from app.services.sources import SourceService


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _apply_runtime_migrations()
    with Session(engine) as session:
        CategoryService(session).ensure_default_categories()
        SourceService(session).ensure_default_sources()
        session.commit()


def _apply_runtime_migrations() -> None:
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns("events")}
    audience = columns.get("audience")
    if audience is None:
        return

    audience_type = str(audience["type"]).lower()
    if audience_type in {"text"}:
        return

    if "varchar(50)" in audience_type or "character varying(50)" in audience_type:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE events ALTER COLUMN audience TYPE TEXT")
