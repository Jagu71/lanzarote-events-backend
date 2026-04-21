# Deploy En Railway

Arquitectura recomendada:

- `wordpress.tudominio.com` o `www.tudominio.com` en SiteGround
- `api.tudominio.com` en Railway para FastAPI
- un servicio `cron` en Railway para ejecutar scrapers de forma periódica
- `Postgres` gestionado por Railway como base de datos compartida

## Servicios a crear

### 1. Postgres

Crea una base de datos Postgres dentro del mismo proyecto de Railway.

### 2. API

- Origen: este repositorio
- Runtime: `Dockerfile`
- Start command:

```bash
sh /app/scripts/start_api.sh
```

- Variables:
  - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
  - el resto desde `.env.railway.example`

### 3. Scraper Cron

- Origen: el mismo repositorio
- Runtime: `Dockerfile`
- Start command:

```bash
sh /app/scripts/start_scrape_once.sh
```

- Variables:
  - las mismas que la API
- Programación:
  - por ejemplo cada `3` horas

## Dominio

En Railway:

- añade `api.tudominio.com` como custom domain al servicio `API`

En DNS:

- crea el registro que Railway te indique para ese subdominio

## WordPress

WordPress no debe alojar este backend.

Lo correcto es:

- WordPress como CMS y capa pública principal
- llamadas desde WordPress a `https://api.tudominio.com/api/v1/events`

## Comprobaciones

- `GET /health`
- `GET /api/v1/events?days=7&starts_after=2026-04-21`
- abrir `/` para comprobar el frontend básico servido por FastAPI
