import logging
from datetime import UTC, datetime
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.event import Event, EventTranslation
from app.repositories.events import EventRepository
from app.scrapers.base import NormalizedEvent, RawScrapedEvent
from app.services.categories import DEFAULT_CATEGORIES
from app.services.deduplication import build_event_fingerprint, merge_event_records, titles_are_similar, venues_are_similar
from app.services.enrichment import enrich_location
from app.utils.text import slugify


logger = logging.getLogger(__name__)


CATEGORY_RULES = {
    "music": {
        "title": ["concierto", "music", "música", "musica", "dj", "orquesta", "recital", "festival de música", "festival de musica"],
        "body": ["live", "sesión musical", "sesion musical", "merengue", "banda", "cantautor", "cantadora", "cantador"],
    },
    "theatre": {
        "title": ["teatro", "danza", "escena", "performance", "microteatro", "artes escénicas", "artes escenicas", "espectáculo"],
        "body": ["obra", "bailaores", "teatro-danza", "artes escénicas", "sala teatro", "teatro municipal"],
    },
    "cinema": {
        "title": ["cine", "película", "pelicula", "film", "documental", "cortometraje", "proyección", "proyeccion"],
        "body": ["director", "pantalla", "festival de cine"],
    },
    "exhibition": {
        "title": ["exposición", "exposicion", "instalación", "instalacion", "arte", "fotografía", "fotografia"],
        "body": ["galería", "galeria", "comisariada", "museo", "serie fotográfica", "serie fotografica"],
    },
    "sports": {
        "title": ["deporte", "trail", "race", "regata", "surf", "torneo", "carrera", "competición", "competicion"],
        "body": ["prueba deportiva", "actividad deportiva", "campeonato"],
    },
    "gastronomy": {
        "title": ["gastronom", "vino", "wine", "cata", "degust", "chef", "saborea"],
        "body": ["cena", "maridaje", "restaurante", "tasting"],
    },
    "festivities": {
        "title": ["carnaval", "fiesta", "fiestas", "verbena", "romería", "romeria", "celebración", "celebracion"],
        "body": ["pasacalle", "comparsa", "murga", "batucada", "noche de", "tradicional"],
    },
    "workshop": {
        "title": ["taller", "workshop", "masterclass", "curso", "formación", "formacion", "inscripción", "inscripcion", "jornada formativa"],
        "body": ["actividad participativa", "plazas limitadas", "formativa"],
    },
    "literature": {
        "title": ["libro", "libros", "lectura", "literatura", "poesía", "poesia", "poema", "club de lectura", "podcast"],
        "body": ["autora", "autor", "escritora", "escritor", "presentación del libro", "presentacion del libro"],
    },
    "family": {
        "title": ["infantil", "familiar", "niños", "niñas", "ninos", "ninas"],
        "body": ["a partir de 7 años", "público familiar", "publico familiar", "especialmente recomendado"],
    },
}


class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EventRepository(db)

    def ingest_many(self, events: list[RawScrapedEvent]) -> dict[str, int]:
        created = 0
        updated = 0
        for raw_event in events:
            normalized = raw_event.normalize()
            result = self.ingest_one(normalized)
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
        self.db.commit()
        return {"created": created, "updated": updated, "processed": len(events)}

    def ingest_one(self, payload: NormalizedEvent) -> str:
        category_slugs = self._categorize(payload)
        categories = self._load_categories(category_slugs)
        enriched = enrich_location(
            venue_name=payload.venue_name,
            venue_address=payload.venue_address,
            locality=payload.locality,
            municipality=payload.municipality,
        )
        fingerprint = build_event_fingerprint(
            title=payload.primary_title,
            starts_at=payload.starts_at,
            venue_name=payload.venue_name,
        )

        existing = self.repository.get_by_source_external(payload.source_name, payload.external_id)
        if existing is None:
            existing = self.repository.get_by_fingerprint(fingerprint)
        if existing is None:
            existing = self._find_fuzzy_duplicate(payload.primary_title, payload.starts_at, payload.venue_name)

        candidate = Event(
            slug=self._build_unique_slug(payload.primary_title, payload.starts_at),
            source_name=payload.source_name,
            external_id=payload.external_id,
            source_url=payload.source_url,
            canonical_url=payload.canonical_url,
            fingerprint=fingerprint,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            timezone=payload.timezone,
            is_free=payload.is_free,
            price_text=payload.price_text,
            currency=payload.currency,
            image_url=payload.image_url,
            venue_name=payload.venue_name,
            venue_address=payload.venue_address,
            municipality=enriched["municipality"],
            locality=enriched["locality"],
            latitude=enriched["latitude"],
            longitude=enriched["longitude"],
            organizer_name=payload.organizer_name,
            audience=payload.audience,
            language_origin=payload.language_origin,
            source_payload=payload.source_payload,
            last_seen_at=datetime.now(UTC),
        )
        candidate.translations = [
            EventTranslation(
                language=language,
                title=translation["title"],
                summary=translation.get("summary"),
                description=translation.get("description"),
            )
            for language, translation in payload.translations.items()
        ]
        candidate.categories = categories

        if existing is None:
            self.repository.save(candidate)
            logger.info("Created event %s from %s", payload.primary_title, payload.source_name)
            return "created"

        merge_event_records(existing, candidate)
        existing.fingerprint = fingerprint
        existing.last_seen_at = datetime.now(UTC)
        self.repository.save(existing)
        logger.info("Updated event %s from %s", payload.primary_title, payload.source_name)
        return "updated"

    def _find_fuzzy_duplicate(self, title: str, starts_at: datetime | None, venue_name: str | None) -> Event | None:
        stmt = select(Event)
        for candidate in self.db.scalars(stmt):
            candidate_title = candidate.translations[0].title if candidate.translations else None
            if starts_at and candidate.starts_at and candidate.starts_at.date() == starts_at.date():
                if candidate_title and titles_are_similar(candidate_title, title):
                    return candidate
            if candidate_title and venues_are_similar(candidate.venue_name, venue_name):
                if titles_are_similar(candidate_title, title, threshold=0.9):
                    return candidate
        return None

    def _categorize(self, payload: NormalizedEvent) -> list[str]:
        fields = {
            "title": self._normalize_text(payload.primary_title),
            "summary": self._normalize_text(payload.primary_summary),
            "description": self._normalize_text(payload.primary_description),
            "tags": self._normalize_text(" ".join(payload.tags)),
            "hints": self._normalize_text(" ".join(payload.category_hints)),
            "venue": self._normalize_text(payload.venue_name),
        }
        scores = {slug: 0 for slug in CATEGORY_RULES}

        for slug, rule in CATEGORY_RULES.items():
            for keyword in rule["title"]:
                if keyword in fields["title"]:
                    scores[slug] += 5
                if keyword in fields["summary"]:
                    scores[slug] += 3
                if keyword in fields["tags"] or keyword in fields["hints"]:
                    scores[slug] += 4
            for keyword in rule["body"]:
                if keyword in fields["summary"]:
                    scores[slug] += 2
                if keyword in fields["description"]:
                    scores[slug] += 1
                if keyword in fields["venue"]:
                    scores[slug] += 1

        if fields["title"].startswith(("taller", "workshop", "masterclass", "curso", "jornada formativa")):
            scores["workshop"] += 4
            if scores["family"] >= scores["workshop"]:
                scores["workshop"] = scores["family"] + 1

        ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        primary_slug, primary_score = ordered[0]
        if primary_score <= 0:
            return ["festivities"]

        selected = [primary_slug]
        for slug, score in ordered[1:]:
            if slug == "family" and score >= 4:
                selected.append(slug)
                continue
            if primary_score >= 3 and score == primary_score and slug in {"music", "theatre", "cinema", "exhibition", "gastronomy"}:
                selected.append(slug)
                if len(selected) == 2:
                    break
                continue
            if primary_score >= 5 and score >= max(5, primary_score - 1) and slug in {"music", "theatre", "cinema", "exhibition", "workshop", "literature"}:
                selected.append(slug)
            if len(selected) == 2:
                break
        return selected

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        return re.sub(r"\s+", " ", (value or "")).strip().lower()

    def _load_categories(self, slugs: list[str]) -> list[Category]:
        stmt = select(Category).where(Category.slug.in_(slugs))
        categories = list(self.db.scalars(stmt).all())
        if categories:
            return categories
        fallback_slug = DEFAULT_CATEGORIES[0]["slug"]
        return list(self.db.scalars(select(Category).where(Category.slug == fallback_slug)).all())

    def _build_unique_slug(self, title: str, starts_at: datetime | None) -> str:
        base = slugify(title)
        suffix = starts_at.strftime("%Y%m%d") if starts_at else "na"
        slug = f"{base}-{suffix}"
        counter = 1
        candidate = slug
        while self.db.scalar(select(Event.id).where(Event.slug == candidate)) is not None:
            counter += 1
            candidate = f"{slug}-{counter}"
        return candidate
