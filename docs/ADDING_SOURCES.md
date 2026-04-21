# Añadir Nuevas Fuentes

## 1. Crear el scraper

Crea un fichero nuevo en `app/scrapers/sources/`.

Ejemplo mínimo:

```python
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawScrapedEvent


class MySourceScraper(BaseScraper):
    source_name = "my_source"
    source_url = "https://example.com/events"
    fixture_name = "my_source.html"

    def parse(self, html: str) -> list[RawScrapedEvent]:
        soup = BeautifulSoup(html, "lxml")
        events = []
        for card in soup.select("article"):
            events.append(
                RawScrapedEvent(
                    source_name=self.source_name,
                    source_url=self.source_url,
                    title=card.select_one("h2").get_text(strip=True),
                    starts_at_raw=card.select_one("time").get_text(strip=True),
                    venue_name="Arrecife",
                    language_origin="es",
                )
            )
        return events
```

## 2. Registrar la fuente

Añádela en `app/scrapers/registry.py`.

## 3. Normalización

El scraper solo devuelve `RawScrapedEvent`. El resto del pipeline ya hace:

- parseo de fecha
- slug
- fingerprint
- categorización
- enriquecimiento geográfico
- deduplicación
- merge

## 4. Recomendaciones

- Prioriza `JSON-LD` cuando exista.
- Guarda el HTML real en `data/fixtures/` para tests.
- No mezcles lógica de negocio con selectores.
- Si una fuente necesita JavaScript, crea un scraper separado con Playwright.
- Si la fuente tiene paginación, resuélvela dentro de `fetch()` o en un scraper específico.

## 5. Campos mínimos útiles

- `title`
- `source_url`
- `starts_at_raw`
- `language_origin`

Campos muy recomendables:

- `external_id`
- `canonical_url`
- `summary`
- `description`
- `venue_name`
- `price_text`
- `image_url`
- `tags`
- `category_hints`
