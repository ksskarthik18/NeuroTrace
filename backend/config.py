"""
NeuroTrace Configuration
Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "NeuroTrace"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "info"

    # LLM
    groq_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "groq"  # "groq" or "openai"
    llm_model: str = "llama-3.3-70b-versatile"

    # Database
    database_url: str = "sqlite+aiosqlite:///./neurotrace.db"

    # Sandbox
    sandbox_timeout: int = 10  # seconds
    sandbox_max_memory_mb: int = 256

    # Patch Validation
    max_repair_attempts: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
