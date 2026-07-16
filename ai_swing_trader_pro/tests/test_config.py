"""Unit tests for ai_swing_trader_pro.core.config."""

from __future__ import annotations

import os

from ai_swing_trader_pro.core.config import Settings, get_settings


class TestSettingsDefaults:
    def test_default_app_name(self) -> None:
        settings = Settings()
        assert settings.app_name == "AI Swing Trader Pro"

    def test_default_environment_is_development(self) -> None:
        settings = Settings()
        assert settings.environment == "development"
        assert settings.is_production is False

    def test_default_database_url_is_sqlite(self) -> None:
        settings = Settings()
        assert settings.database.url.startswith("sqlite:///")

    def test_default_log_level_is_info(self) -> None:
        settings = Settings()
        assert settings.logging.level == "INFO"


class TestSettingsOverrides:
    def test_environment_is_lowercased(self) -> None:
        settings = Settings(environment="PRODUCTION")
        assert settings.environment == "production"
        assert settings.is_production is True

    def test_env_var_override(self, monkeypatch) -> None:
        monkeypatch.setenv("APP_NAME", "Custom Bot")
        monkeypatch.setenv("DEBUG", "false")
        settings = Settings()
        assert settings.app_name == "Custom Bot"
        assert settings.debug is False

    def test_nested_db_env_var_override(self, monkeypatch) -> None:
        monkeypatch.setenv("DB_URL", "sqlite:///./custom.db")
        monkeypatch.setenv("DB_POOL_SIZE", "10")
        settings = Settings()
        assert settings.database.url == "sqlite:///./custom.db"
        assert settings.database.pool_size == 10

    def test_secret_key_is_not_exposed_in_repr(self) -> None:
        settings = Settings(secret_key="super-secret-value")
        assert "super-secret-value" not in repr(settings.secret_key)
        assert settings.secret_key.get_secret_value() == "super-secret-value"


class TestGetSettingsCaching:
    def test_get_settings_returns_same_instance(self) -> None:
        get_settings.cache_clear()
        first = get_settings()
        second = get_settings()
        assert first is second

    def test_cache_clear_produces_new_instance(self) -> None:
        get_settings.cache_clear()
        first = get_settings()
        get_settings.cache_clear()
        second = get_settings()
        assert first is not second
