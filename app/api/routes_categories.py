from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoryPublic
from app.services.categories import CategoryService


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryPublic])
def list_categories(
    lang: str = Query("es", description="Idioma preferido de la respuesta."),
    db: Session = Depends(get_db),
) -> list[CategoryPublic]:
    return CategoryService(db).list_categories(lang=lang)
