# Lanzarote Events Backend

Backend completo para un agregador de eventos culturales y de ocio de Lanzarote. Incluye scraping modular, normalización, deduplicación, enriquecimiento geográfico local, API REST multiidioma y scripts de ejecución periódica.

## Stack recomendado

Sí, estoy de acuerdo con tu propuesta: **Python + FastAPI + SQLAlchemy + PostgreSQL/SQLite** es el stack correcto para este problema.

Motivos:

- Python tiene el mejor ecosistema para scraping, parsing y limpieza de datos.
- FastAPI permite exponer la API rápido, con validación fuerte y documentación automática.
- SQLAlchemy mantiene el dominio desacoplado de la base de datos.
- SQLite sirve para arrancar localmente sin fricción; PostgreSQL encaja mejor en producción.
- APScheduler cubre bien la ejecución periódica sin meter infraestructura extra desde el día uno.

## Qué incluye

- API REST con endpoints de eventos y categorías.
- Frontend básico servido por FastAPI en `/`.
- Filtros por fecha, categoría, texto libre y gratis/pago.
- Ventanas de búsqueda de hasta `7` días para frontend y cliente web.
- Respuesta localizada por idioma con fallback (`es`, `en`, `de`, `fr`).
- Modelo de datos con traducciones por evento y categorías flexibles.
- Pipeline de scraping e ingestión con deduplicación y merge.
- Scrapers iniciales para `Cultura Lanzarote`, `Sacatuentrada`, `CACT`, `La Voz de Lanzarote` y un adaptador `Cabildo` configurable.
- Enriquecimiento geográfico básico para espacios frecuentes de Lanzarote.
- Fixtures y tests para validar la base del sistema.

## Estructura

```text
app/
  api/          Endpoints FastAPI
  core/         Configuración y logging
  db/           Engine, sesión e inicialización
  models/       SQLAlchemy models
  repositories/ Acceso a datos
  schemas/      Contratos de API
  scrapers/     Framework y fuentes
  services/     Ingestión, deduplicación, categorías y enriquecimiento
  tasks/        Ejecución periódica
scripts/        Entrypoints CLI
data/fixtures/  HTML de ejemplo para desarrollo y tests
docs/           API y guía para nuevas fuentes
tests/          Tests básicos
```

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.init_db
```

## Ejecutar la API

```bash
python -m uvicorn app.main:app --reload
```

Documentación automática:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Frontend básico:

- Inicio: `http://127.0.0.1:8000/`
- Incluye filtro por fecha inicial, ventana de `1` a `7` días, categoría, texto libre y gratis/pago.

## Despliegue con dominio fijo

La forma más simple para tener una URL estable es desplegar esta app en un VPS con Docker y usar un subdominio dedicado, por ejemplo `events.tudominio.com`.

### Archivos incluidos

- `Dockerfile`
- `docker-compose.yml`
- `deploy/Caddyfile`
- `.env.deploy.example`

### Pasos

1. Copia el proyecto al servidor.
2. Duplica `.env.deploy.example` como `.env.deploy`.
3. Cambia `DOMAIN=events.tudominio.com` por tu subdominio real.
4. Apunta el DNS del subdominio al IP público del servidor con un registro `A`.
5. Arranca:

```bash
cp .env.deploy.example .env.deploy
make docker-up
```

### Qué levanta

- `app`: FastAPI + frontend estático
- `scheduler`: ejecución periódica de scrapers
- `caddy`: proxy inverso con HTTPS automático

### Requisitos del servidor

- Docker
- Docker Compose plugin
- puertos `80` y `443` abiertos
- DNS del subdominio apuntando al servidor

## Ejecutar scrapers

Una pasada manual:

```bash
python -m scripts.run_scrapers
```

Modo scheduler:

```bash
python -m scripts.run_scheduler
```

## Configuración

Variables principales:

- `DATABASE_URL`: por defecto `sqlite:///./lanzarote_events.db`
- `SUPPORTED_LOCALES`: `es,en,de,fr`
- `SCRAPER_USE_FIXTURES`: `true` para desarrollo offline
- `CACT_EVENTS_URL`
- `CULTURALANZAROTE_PROGRAM_URL`
- `CULTURALANZAROTE_TICKETS_URL`
- `LAVOZ_LANZAROTE_URL`
- `COOLTURA_LANZAROTE_URL`
- `CABILDO_EVENTS_URL`
- `SCRAPE_INTERVAL_MINUTES`

## Endpoints principales

- `GET /health`
- `GET /api/v1/events`
- `GET /api/v1/events/search?q=...`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/categories`

Ejemplo:

```bash
curl "http://127.0.0.1:8000/api/v1/events?lang=en&category=music&starts_after=2026-04-16&days=7"
```

## Notas de producción

- Cambia `DATABASE_URL` a PostgreSQL.
- Añade migraciones con Alembic si el esquema va a evolucionar.
- Para Facebook Events es preferible un scraper separado con navegador automatizado y revisión legal/técnica específica.
- Los selectores de Cabildo deben validarse contra la URL real que quieras usar como fuente oficial.

## Estrategia de fuentes

Se priorizan primero las fuentes canónicas y después las secundarias:

- `culturalanzarote.com/programacion_cultura/`
- `culturalanzarote.sacatuentrada.es/es`
- `cactlanzarote.com/tipo_entrada/eventos/`
- `lavozdelanzarote.com/actualidad/cultura`

Fuentes como `coolturalanzarote.com` y `lancelotdigital.com/cultura` son útiles para descubrimiento o cobertura editorial, pero no deben ser la base principal del agregador porque aumentan la duplicación y la variabilidad del formato.

## Documentación adicional

- [API](./docs/API.md)
- [Añadir nuevas fuentes](./docs/ADDING_SOURCES.md)
- [Deploy en Railway](./docs/RAILWAY.md)
