from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.source import SourceConfig
from app.repositories.sources import SourceRepository
from app.schemas.source import SourcePublic
from app.scrapers.registry import SOURCE_DEFINITIONS_BY_KEY, list_source_definitions


class SourceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SourceRepository(db)

    def ensure_default_sources(self) -> None:
        existing = {item.key: item for item in self.repository.list_all()}
        for definition in list_source_definitions():
            scraper = definition.build()
            source = existing.get(definition.key)
            configured = bool(scraper.source_url)
            if source is None:
                source = SourceConfig(
                    key=definition.key,
                    label=definition.label,
                    description=definition.description,
                    source_url=scraper.source_url or None,
                    enabled=definition.enabled_by_default and configured,
                    configured=configured,
                )
                self.db.add(source)
                self.db.flush()
                continue

            source.label = definition.label
            source.description = definition.description
            source.source_url = scraper.source_url or None
            source.configured = configured
            if not configured:
                source.enabled = False

    def list_sources(self) -> list[SourcePublic]:
        return [self._to_public(item) for item in self.repository.list_all()]

    def runnable_source_keys(self) -> set[str]:
        return {
            item.key
            for item in self.repository.list_all()
            if item.enabled and item.configured and item.key in SOURCE_DEFINITIONS_BY_KEY
        }

    def set_enabled(self, key: str, enabled: bool) -> SourcePublic:
        source = self.repository.get(key)
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        if enabled and not source.configured:
            raise HTTPException(status_code=400, detail="Source is not configured")
        source.enabled = enabled
        self.db.commit()
        self.db.refresh(source)
        return self._to_public(source)

    def record_run(
        self,
        *,
        key: str,
        processed: int,
        created: int,
        updated: int,
        status: str,
        message: str | None = None,
        run_at: datetime | None = None,
    ) -> None:
        source = self.repository.get(key)
        if source is None:
            return
        source.last_processed = processed
        source.last_created = created
        source.last_updated = updated
        source.last_run_status = status
        source.last_run_message = message
        source.last_run_at = run_at or datetime.now(UTC)
        self.db.commit()

    @staticmethod
    def _to_public(source: SourceConfig) -> SourcePublic:
        return SourcePublic(
            key=source.key,
            label=source.label,
            description=source.description,
            source_url=source.source_url,
            enabled=source.enabled,
            configured=source.configured,
            last_run_status=source.last_run_status,
            last_run_message=source.last_run_message,
            last_run_at=source.last_run_at.isoformat() if source.last_run_at else None,
            last_processed=source.last_processed,
            last_created=source.last_created,
            last_updated=source.last_updated,
        )
