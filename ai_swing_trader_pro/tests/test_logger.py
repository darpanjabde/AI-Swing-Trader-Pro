"""Unit tests for ai_swing_trader_pro.core.logger."""

from __future__ import annotations

from pathlib import Path

from ai_swing_trader_pro.core.config import Settings
from ai_swing_trader_pro.core.logger import configure_logging, logger


class TestConfigureLogging:
    def test_creates_log_directory(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "nested" / "logs"
        settings = Settings()
        settings.logging.directory = log_dir

        configure_logging(settings=settings, force=True)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_writes_log_file(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "logs"
        settings = Settings()
        settings.logging.directory = log_dir

        configure_logging(settings=settings, force=True)
        logger.info("test message for log file assertion")

        log_file = log_dir / "app.log"
        assert log_file.exists()
        assert "test message for log file assertion" in log_file.read_text()

    def test_idempotent_without_force(self, tmp_path: Path) -> None:
        settings = Settings()
        settings.logging.directory = tmp_path / "logs"

        # Should not raise, and should not duplicate sinks either way.
        configure_logging(settings=settings, force=True)
        configure_logging(settings=settings, force=False)
