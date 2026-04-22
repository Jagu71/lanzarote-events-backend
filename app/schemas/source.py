from pydantic import BaseModel


class SourcePublic(BaseModel):
    key: str
    label: str
    description: str | None = None
    source_url: str | None = None
    enabled: bool
    configured: bool
    last_run_status: str | None = None
    last_run_message: str | None = None
    last_run_at: str | None = None
    last_processed: int = 0
    last_created: int = 0
    last_updated: int = 0


class SourceUpdateRequest(BaseModel):
    enabled: bool


class SourceCandidatePublic(BaseModel):
    id: int
    url: str
    label: str | None = None
    status: str
    notes: str | None = None
    created_at: str | None = None


class SourceCandidateCreateRequest(BaseModel):
    url: str
    label: str | None = None
    notes: str | None = None
