"""Database engine and session management.

Provides a single, configurable SQLAlchemy engine plus a context-managed
session factory. No trading models or repositories live here yet — this
sprint only establishes the plumbing so future sprints can add ORM models
without touching this module (Open/Closed Principle).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ai_swing_trader_pro.core.config import Settings, get_settings
from ai_swing_trader_pro.core.logger import logger
from ai_swing_trader_pro.infrastructure.database.base import Base


class Database:
    """Owns the engine + session factory for a given configuration.

    Wrapping engine creation in a class (rather than module-level globals)
    makes the database swappable and testable: tests can instantiate a
    `Database` pointed at an in-memory SQLite URL without touching global
    state.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._engine: Engine = self._build_engine()
        self._session_factory: sessionmaker[Session] = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def _build_engine(self) -> Engine:
        db_cfg = self._settings.database
        connect_args = {}
        engine_kwargs: dict = {"echo": db_cfg.echo, "pool_pre_ping": db_cfg.pool_pre_ping}

        if db_cfg.url.startswith("sqlite"):
            # SQLite has no real connection pool and needs this flag for
            # multi-threaded access (e.g. from a scheduler thread later on).
            connect_args["check_same_thread"] = False
        else:
            engine_kwargs["pool_size"] = db_cfg.pool_size

        engine = create_engine(db_cfg.url, connect_args=connect_args, **engine_kwargs)
        logger.debug("Database engine created for URL scheme: {}", engine.url.drivername)
        return engine

    @property
    def engine(self) -> Engine:
        return self._engine

    def create_all(self) -> None:
        """Create all tables registered on `Base.metadata`.

        Placeholder for now — no models are registered yet in Sprint 2.
        Safe to call repeatedly; SQLAlchemy skips existing tables.
        """

        Base.metadata.create_all(bind=self._engine)
        logger.info("Database schema ensured (create_all executed).")

    def dispose(self) -> None:
        """Dispose of the engine's connection pool, e.g. on shutdown."""

        self._engine.dispose()
        logger.debug("Database engine disposed.")

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Session rolled back due to an unhandled error.")
            raise
        finally:
            session.close()


_db_instance: Database | None = None


def get_database() -> Database:
    """Return the process-wide `Database` singleton, creating it lazily."""

    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def get_db() -> Generator[Session, None, None]:
    """FastAPI/CLI-friendly dependency that yields a request-scoped session."""

    with get_database().session_scope() as session:
        yield session
