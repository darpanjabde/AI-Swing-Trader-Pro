"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from ai_swing_trader_pro.core.config import Settings, get_settings
from ai_swing_trader_pro.infrastructure.database.session import Database


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """A Settings instance isolated to a temp dir, using in-memory SQLite."""

    settings = Settings(
        environment="test",
        debug=True,
    )
    settings.database.url = "sqlite:///:memory:"
    settings.logging.directory = tmp_path / "logs"
    return settings


@pytest.fixture
def test_database(test_settings: Settings) -> Generator[Database, None, None]:
    """A throwaway in-memory database for tests."""

    db = Database(settings=test_settings)
    db.create_all()
    yield db
    db.dispose()


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    """Ensure `get_settings()` cache doesn't leak between tests."""

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
