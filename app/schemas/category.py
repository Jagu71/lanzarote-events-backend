from pydantic import BaseModel


class CategoryPublic(BaseModel):
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
