from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Category]:
        stmt = select(Category).options(selectinload(Category.translations)).order_by(Category.sort_order, Category.slug)
        return list(self.db.scalars(stmt).all())

    def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).options(selectinload(Category.translations)).where(Category.slug == slug)
        return self.db.scalar(stmt)
