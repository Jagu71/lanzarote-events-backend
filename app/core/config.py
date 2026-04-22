from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Lanzarote Events Backend", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(default="sqlite:///./lanzarote_events.db", alias="DATABASE_URL")
    default_locale: str = Field(default="es", alias="DEFAULT_LOCALE")
    supported_locales: list[str] = Field(default=["es", "en", "de"], alias="SUPPORTED_LOCALES")
    scraper_timeout_seconds: int = Field(default=20, alias="SCRAPER_TIMEOUT_SECONDS")
    scraper_user_agent: str = Field(default="LanzaroteEventsBot/0.1", alias="SCRAPER_USER_AGENT")
    scraper_use_fixtures: bool = Field(default=False, alias="SCRAPER_USE_FIXTURES")
    scrape_interval_minutes: int = Field(default=180, alias="SCRAPE_INTERVAL_MINUTES")
    cact_events_url: str = Field(
        default="https://cactlanzarote.com/tipo_entrada/eventos/",
        alias="CACT_EVENTS_URL",
    )
    culturalanzarote_program_url: str = Field(
        default="https://culturalanzarote.com/programacion_cultura/",
        alias="CULTURALANZAROTE_PROGRAM_URL",
    )
    culturalanzarote_tickets_url: str = Field(
        default="https://culturalanzarote.sacatuentrada.es/es",
        alias="CULTURALANZAROTE_TICKETS_URL",
    )
    tinajo_agenda_url: str = Field(
        default="https://www.tinajo.es/agenda",
        alias="TINAJO_AGENDA_URL",
    )
    teguise_cultura_url: str = Field(
        default="https://teguise.es/servicios/cultura/",
        alias="TEGUISE_CULTURA_URL",
    )
    tias_cultura_url: str = Field(
        default="https://www.ayuntamientodetias.es/ayuntamiento/servicio-al-ciudadano/cultura/?mode=list",
        alias="TIAS_CULTURA_URL",
    )
    ocio_lanzarote_events_url: str = Field(
        default="https://ociolanzarote.com/en/events",
        alias="OCIO_LANZAROTE_EVENTS_URL",
    )
    lavoz_lanzarote_url: str = Field(
        default="https://www.lavozdelanzarote.com/actualidad/cultura",
        alias="LAVOZ_LANZAROTE_URL",
    )
    eventbrite_events_url: str = Field(
        default="https://www.eventbrite.com/d/spain--arrecife--222299/lanzarote/",
        alias="EVENTBRITE_EVENTS_URL",
    )
    cooltura_lanzarote_url: str = Field(
        default="https://www.coolturalanzarote.com/",
        alias="COOLTURA_LANZAROTE_URL",
    )
    cabildo_events_url: str = Field(default="", alias="CABILDO_EVENTS_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("supported_locales", mode="before")
    @classmethod
    def split_locales(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def fixtures_dir(self) -> Path:
        return self.base_dir / "data" / "fixtures"


@lru_cache
def get_settings() -> Settings:
    return Settings()
