from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Student Record System"
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_expiry_minutes: int = Field(default=30, ge=5, le=1440)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def origin_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
