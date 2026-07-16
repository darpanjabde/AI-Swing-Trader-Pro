"""Unit tests for ai_swing_trader_pro.infrastructure.database."""

from __future__ import annotations

from sqlalchemy import text

from ai_swing_trader_pro.core.config import Settings
from ai_swing_trader_pro.infrastructure.database.session import Database


class TestDatabase:
    def test_engine_is_created(self, test_settings: Settings) -> None:
        db = Database(settings=test_settings)
        assert db.engine is not None
        db.dispose()

    def test_create_all_does_not_raise(self, test_database: Database) -> None:
        # No models are registered yet in Sprint 2 — this just verifies the
        # schema-creation call itself works end-to-end against a live engine.
        test_database.create_all()

    def test_session_scope_executes_query(self, test_database: Database) -> None:
        with test_database.session_scope() as session:
            result = session.execute(text("SELECT 1")).scalar_one()
            assert result == 1

    def test_session_scope_rolls_back_on_error(self, test_database: Database) -> None:
        try:
            with test_database.session_scope() as session:
                session.execute(text("SELECT 1"))
                raise ValueError("boom")
        except ValueError:
            pass  # expected

        # Engine should still be usable after a rollback.
        with test_database.session_scope() as session:
            result = session.execute(text("SELECT 1")).scalar_one()
            assert result == 1
