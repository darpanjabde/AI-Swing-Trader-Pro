"""Application configuration.

Centralizes all environment-driven configuration using Pydantic Settings.
Follows the Single Responsibility Principle: this module's only job is to
load, validate, and expose configuration values. No other module should
read `os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Path = Path(__file__).resolve().parents[3]


class DatabaseSettings(BaseSettings):
    """Database connection configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: str = Field(
        default="sqlite:///./ai_swing_trader_pro.db",
        description="SQLAlchemy database URL.",
    )
    echo: bool = Field(default=False, description="Echo raw SQL statements.")
    pool_size: int = Field(default=5, ge=1, description="Connection pool size.")
    pool_pre_ping: bool = Field(
        default=True, description="Verify connections before use."
    )


class LoggingSettings(BaseSettings):
    """Logging configuration for Loguru."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Minimum log level."
    )
    directory: Path = Field(
        default=BASE_DIR / "logs", description="Directory where log files are stored."
    )
    rotation: str = Field(
        default="10 MB", description="Log rotation policy (size or time based)."
    )
    retention: str = Field(
        default="14 days", description="How long to keep rotated log files."
    )
    serialize: bool = Field(
        default=False, description="Emit logs as structured JSON."
    )
    json_logs: bool = Field(
        default=False, description="Alias kept for backward compatibility."
    )


class Settings(BaseSettings):
    """Top-level application settings.

    Values are sourced (in order of precedence) from:
        1. Explicit constructor arguments
        2. Environment variables
        3. A `.env` file in the project root
        4. Field defaults defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core app metadata -------------------------------------------------
    app_name: str = Field(default="AI Swing Trader Pro")
    environment: Literal["development", "staging", "production", "test"] = Field(
        default="development"
    )
    debug: bool = Field(default=True)

    # --- Secrets (placeholders for future sprints, e.g. Kite Connect) ------
    secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-.env"),
        description="Generic app secret. Broker API keys arrive in a later sprint.",
    )

    # --- Sub-settings --------------------------------------------------------
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @field_validator("environment", mode="before")
    @classmethod
    def _lowercase_environment(cls, value: str) -> str:
        return value.lower() if isinstance(value, str) else value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached, process-wide Settings instance.

    Cached via `lru_cache` so the environment/`.env` file is parsed once.
    Tests can bypass this by calling `Settings()` directly or by clearing
    the cache with `get_settings.cache_clear()`.
    """

    return Settings()
