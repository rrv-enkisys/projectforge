"""
Configuration module using Pydantic Settings.
Loads configuration from environment variables.
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "ProjectForge Core Service"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    port: int = Field(default=8081, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge",
        alias="DATABASE_URL",
    )

    # Firebase
    firebase_project_id: str = Field(..., alias="FIREBASE_PROJECT_ID")
    firebase_credentials_path: Optional[str] = Field(None, alias="FIREBASE_CREDENTIALS_PATH")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # API
    api_prefix: str = "/api/v1"

    # Security
    secret_key: str = Field(
        default="change-this-in-production-use-openssl-rand-hex-32",
        alias="SECRET_KEY",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only create one Settings instance.
    """
    return Settings()


# Convenience export
settings = get_settings()
