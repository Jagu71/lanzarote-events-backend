from sqlalchemy.orm import Session

from app.models.category import Category, CategoryTranslation
from app.repositories.categories import CategoryRepository
from app.schemas.category import CategoryPublic


DEFAULT_CATEGORIES = [
    {
        "slug": "music",
        "icon": "music",
        "sort_order": 10,
        "translations": {
            "es": {"name": "Música", "description": "Conciertos, festivales y sesiones en directo."},
            "en": {"name": "Music", "description": "Concerts, festivals and live sessions."},
            "de": {"name": "Musik", "description": "Konzerte, Festivals und Live-Sessions."},
            "fr": {"name": "Musique", "description": "Concerts, festivals et sessions live."},
        },
    },
    {
        "slug": "exhibition",
        "icon": "palette",
        "sort_order": 20,
        "translations": {
            "es": {"name": "Exposiciones", "description": "Arte, fotografía, patrimonio y muestras temporales."},
            "en": {"name": "Exhibitions", "description": "Art, photography, heritage and temporary exhibitions."},
            "de": {"name": "Ausstellungen", "description": "Kunst, Fotografie, Kulturerbe und Sonderausstellungen."},
            "fr": {"name": "Expositions", "description": "Art, photographie, patrimoine et expositions temporaires."},
        },
    },
    {
        "slug": "theatre",
        "icon": "theatre",
        "sort_order": 30,
        "translations": {
            "es": {"name": "Teatro y escena", "description": "Teatro, danza y artes escénicas."},
            "en": {"name": "Stage", "description": "Theatre, dance and performing arts."},
            "de": {"name": "Bühne", "description": "Theater, Tanz und darstellende Kunst."},
            "fr": {"name": "Scène", "description": "Théâtre, danse et arts de la scène."},
        },
    },
    {
        "slug": "cinema",
        "icon": "film",
        "sort_order": 35,
        "translations": {
            "es": {"name": "Cine", "description": "Cine, documentales, cortometrajes y proyecciones."},
            "en": {"name": "Cinema", "description": "Films, documentaries, shorts and screenings."},
            "de": {"name": "Kino", "description": "Filme, Dokumentarfilme, Kurzfilme und Vorführungen."},
            "fr": {"name": "Cinéma", "description": "Films, documentaires, courts-métrages et projections."},
        },
    },
    {
        "slug": "sports",
        "icon": "sport",
        "sort_order": 40,
        "translations": {
            "es": {"name": "Deporte", "description": "Competiciones, rutas y actividades deportivas."},
            "en": {"name": "Sports", "description": "Competitions, routes and sporting activities."},
            "de": {"name": "Sport", "description": "Wettkämpfe, Touren und Sportaktivitäten."},
            "fr": {"name": "Sport", "description": "Compétitions, parcours et activités sportives."},
        },
    },
    {
        "slug": "gastronomy",
        "icon": "food",
        "sort_order": 50,
        "translations": {
            "es": {"name": "Gastronomía", "description": "Catas, cenas especiales y experiencias gastronómicas."},
            "en": {"name": "Gastronomy", "description": "Tastings, special dinners and food experiences."},
            "de": {"name": "Gastronomie", "description": "Verkostungen, besondere Abendessen und Genuss-Erlebnisse."},
            "fr": {"name": "Gastronomie", "description": "Dégustations, dîners spéciaux et expériences culinaires."},
        },
    },
    {
        "slug": "festivities",
        "icon": "party",
        "sort_order": 60,
        "translations": {
            "es": {"name": "Fiestas", "description": "Fiestas populares, celebraciones y ocio nocturno."},
            "en": {"name": "Festivities", "description": "Local celebrations, parties and nightlife."},
            "de": {"name": "Feste", "description": "Volksfeste, Feiern und Nachtleben."},
            "fr": {"name": "Fêtes", "description": "Fêtes populaires, célébrations et vie nocturne."},
        },
    },
    {
        "slug": "workshop",
        "icon": "workshop",
        "sort_order": 70,
        "translations": {
            "es": {"name": "Talleres", "description": "Talleres, clases y actividades participativas."},
            "en": {"name": "Workshops", "description": "Workshops, classes and participatory activities."},
            "de": {"name": "Workshops", "description": "Workshops, Kurse und Mitmach-Aktivitäten."},
            "fr": {"name": "Ateliers", "description": "Ateliers, cours et activités participatives."},
        },
    },
    {
        "slug": "literature",
        "icon": "book",
        "sort_order": 80,
        "translations": {
            "es": {"name": "Literatura", "description": "Libros, poesía, clubes de lectura y encuentros literarios."},
            "en": {"name": "Literature", "description": "Books, poetry, reading clubs and literary events."},
            "de": {"name": "Literatur", "description": "Bücher, Poesie, Lesekreise und Literaturveranstaltungen."},
            "fr": {"name": "Littérature", "description": "Livres, poésie, clubs de lecture et rencontres littéraires."},
        },
    },
    {
        "slug": "family",
        "icon": "family",
        "sort_order": 90,
        "translations": {
            "es": {"name": "Familiar", "description": "Planes para público familiar, niños y niñas."},
            "en": {"name": "Family", "description": "Plans for families, children and young audiences."},
            "de": {"name": "Familie", "description": "Angebote für Familien, Kinder und junges Publikum."},
            "fr": {"name": "Famille", "description": "Activités pour les familles, enfants et jeune public."},
        },
    },
]


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CategoryRepository(db)

    def ensure_default_categories(self) -> None:
        existing = {category.slug: category for category in self.repository.list_all()}
        for item in DEFAULT_CATEGORIES:
            category = existing.get(item["slug"])
            if category is None:
                category = Category(
                    slug=item["slug"],
                    icon=item["icon"],
                    sort_order=item["sort_order"],
                )
                self.db.add(category)
                self.db.flush()
            category.icon = item["icon"]
            category.sort_order = item["sort_order"]
            current = {translation.language: translation for translation in category.translations}
            for language, payload in item["translations"].items():
                translation = current.get(language)
                if translation is None:
                    translation = CategoryTranslation(
                        category_id=category.id,
                        language=language,
                        name=payload["name"],
                        description=payload["description"],
                    )
                    category.translations.append(translation)
                else:
                    translation.name = payload["name"]
                    translation.description = payload["description"]

    def list_categories(self, lang: str) -> list[CategoryPublic]:
        categories = self.repository.list_all()
        return [self._to_public(category, lang) for category in categories]

    @staticmethod
    def _to_public(category: Category, lang: str) -> CategoryPublic:
        translations = {item.language: item for item in category.translations}
        translation = translations.get(lang) or translations.get("es") or next(iter(translations.values()))
        return CategoryPublic(
            slug=category.slug,
            name=translation.name,
            description=translation.description,
            icon=category.icon,
        )
