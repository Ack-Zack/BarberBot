from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="BarberSaaS API", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field(default="", alias="TELEGRAM_BOT_USERNAME")
    telegram_webapp_url: str = Field(default="http://localhost:5173", alias="TELEGRAM_WEBAPP_URL")
    allow_dev_auth: bool = Field(default=False, alias="ALLOW_DEV_AUTH")
    cors_origins_raw: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    default_timezone: str = Field(default="Europe/Moscow", alias="DEFAULT_TIMEZONE")
    telegram_init_data_ttl_seconds: int = Field(default=86400, alias="TELEGRAM_INIT_DATA_TTL_SECONDS")
    reminder_minutes_before: int = Field(default=120, alias="REMINDER_MINUTES_BEFORE")

    @property
    def cors_origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins_raw.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
