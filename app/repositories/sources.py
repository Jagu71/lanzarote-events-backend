from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import SourceCandidate, SourceConfig


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

    def list_candidates(self) -> list[SourceCandidate]:
        stmt = select(SourceCandidate).order_by(SourceCandidate.created_at.desc(), SourceCandidate.id.desc())
        return list(self.db.scalars(stmt).all())

    def get_candidate_by_url(self, url: str) -> SourceCandidate | None:
        stmt = select(SourceCandidate).where(SourceCandidate.url == url)
        return self.db.scalar(stmt)

    def save_candidate(self, candidate: SourceCandidate) -> SourceCandidate:
        self.db.add(candidate)
        self.db.flush()
        return candidate
