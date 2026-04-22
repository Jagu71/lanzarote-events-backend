from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import SourceConfig


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[SourceConfig]:
        stmt = select(SourceConfig).order_by(SourceConfig.label.asc(), SourceConfig.key.asc())
        return list(self.db.scalars(stmt).all())

    def get(self, key: str) -> SourceConfig | None:
        return self.db.get(SourceConfig, key)

    def save(self, source: SourceConfig) -> SourceConfig:
        self.db.add(source)
        self.db.flush()
        return source
