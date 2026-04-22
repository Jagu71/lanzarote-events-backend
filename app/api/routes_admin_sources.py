from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.source import (
    SourceCandidateCreateRequest,
    SourceCandidatePublic,
    SourcePublic,
    SourceUpdateRequest,
)
from app.services.sources import SourceService


router = APIRouter(prefix="/admin/sources", tags=["admin"])


@router.get("", response_model=list[SourcePublic])
def list_sources(db: Session = Depends(get_db)) -> list[SourcePublic]:
    service = SourceService(db)
    service.ensure_default_sources()
    db.commit()
    return service.list_sources()


@router.post("/sync", response_model=list[SourcePublic])
def sync_sources(db: Session = Depends(get_db)) -> list[SourcePublic]:
    service = SourceService(db)
    service.ensure_default_sources()
    db.commit()
    return service.list_sources()


@router.patch("/{source_key}", response_model=SourcePublic)
def update_source(source_key: str, payload: SourceUpdateRequest, db: Session = Depends(get_db)) -> SourcePublic:
    service = SourceService(db)
    service.ensure_default_sources()
    db.commit()
    return service.set_enabled(source_key, payload.enabled)


@router.get("/candidates", response_model=list[SourceCandidatePublic])
def list_source_candidates(db: Session = Depends(get_db)) -> list[SourceCandidatePublic]:
    return SourceService(db).list_candidates()


@router.post("/candidates", response_model=SourceCandidatePublic)
def create_source_candidate(payload: SourceCandidateCreateRequest, db: Session = Depends(get_db)) -> SourceCandidatePublic:
    return SourceService(db).add_candidate(url=payload.url, label=payload.label, notes=payload.notes)
