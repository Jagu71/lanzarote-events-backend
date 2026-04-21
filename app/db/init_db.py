from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.models import category, event  # noqa: F401
from app.services.categories import CategoryService


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        CategoryService(session).ensure_default_categories()
        session.commit()
