"""Unit tests for ai_swing_trader_pro.main."""

from __future__ import annotations

from pathlib import Path

from ai_swing_trader_pro.core.config import Settings
from ai_swing_trader_pro.main import bootstrap


class TestBootstrap:
    def test_bootstrap_returns_settings(self, tmp_path: Path) -> None:
        settings = Settings(environment="test")
        settings.database.url = "sqlite:///:memory:"
        settings.logging.directory = tmp_path / "logs"

        result = bootstrap(settings=settings)

        assert result is settings
        assert result.environment == "test"
