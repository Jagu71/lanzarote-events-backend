# API

## `GET /health`

Comprueba si la aplicación está levantada.

Respuesta:

```json
{
  "status": "ok"
}
```

## `GET /api/v1/events`

Lista eventos con filtros.

Query params:

- `lang`: idioma de respuesta. `es`, `en`, `de`, `fr`
- `category`: slug de categoría
- `starts_after`: fecha mínima
- `starts_before`: fecha máxima
- `days`: ventana desde `starts_after` o desde hoy. Máximo `7`
- `free_only`: `true` o `false`
- `q`: búsqueda de texto libre
- `limit`: máximo 100
- `offset`: desplazamiento

Notas:

- Si envías `starts_after` y `starts_before`, el rango no puede superar `7` días.
- Si envías `days`, el backend calcula `starts_before` automáticamente.

Respuesta resumida:

```json
{
  "items": [
    {
      "id": "uuid",
      "slug": "jameos-night-20260502",
      "title": "Jameos Night",
      "summary": "Live music and dinner",
      "translation_language": "en",
      "available_languages": ["en"],
      "starts_at": "2026-05-02T20:00:00+00:00",
      "is_free": false,
      "price_text": "49 EUR",
      "source_name": "cact_lanzarote",
      "source_url": "https://example.com/event",
      "venue_name": "Jameos del Agua",
      "municipality": "Haria",
      "categories": [
        {
          "slug": "music",
          "name": "Music"
        }
      ]
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## `GET /api/v1/events/search`

Atajo para búsqueda textual. Requiere `q`.

Ejemplo:

```text
/api/v1/events/search?q=jameos&lang=en
```

## `GET /api/v1/events/{event_id}`

Devuelve el detalle completo del evento, incluyendo traducciones disponibles y `source_payload`.

## `GET /api/v1/categories`

Devuelve las categorías localizadas para el idioma solicitado.
