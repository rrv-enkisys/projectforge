from __future__ import annotations

"""Configuration settings for AI Service"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/projectforge"

    # Vertex AI
    gcp_project_id: str = "projectforge-4314f"
    gcp_location: str = "us-central1"
    vertex_embedding_model: str = "text-embedding-004"
    vertex_llm_model: str = "gemini-2.0-flash-exp"
    embedding_dimensions: int = 768

    # Document Processing
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_chunks_per_query: int = 5

    # Cloud Storage
    gcs_bucket_name: str = "projectforge-documents"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Logging
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
