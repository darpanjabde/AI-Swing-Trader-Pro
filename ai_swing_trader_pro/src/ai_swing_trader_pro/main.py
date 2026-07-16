"""Application entry point.

Sprint 2 responsibility: wire up configuration, logging, and the database,
then confirm the application boots cleanly. No trading logic or Kite
Connect integration is invoked here yet.
"""

from __future__ import annotations

from ai_swing_trader_pro.core.config import Settings, get_settings
from ai_swing_trader_pro.core.logger import logger
from ai_swing_trader_pro.infrastructure.database import get_database


def bootstrap(settings: Settings | None = None) -> Settings:
    """Initialize core services and return the active settings.

    Kept as a standalone function (rather than inline in `main`) so tests
    can call `bootstrap()` and assert on its return value without spinning
    up the full CLI.
    """

    settings = settings or get_settings()

    logger.info("Starting {} [{}]", settings.app_name, settings.environment)
    logger.debug("Debug mode: {}", settings.debug)

    db = get_database()
    db.create_all()
    logger.info("Database ready at: {}", db.engine.url.render_as_string(hide_password=True))

    return settings


def main() -> None:
    settings = bootstrap()
    logger.success(
        "{} v{} started successfully in '{}' mode.",
        settings.app_name,
        __import__("ai_swing_trader_pro").__version__,
        settings.environment,
    )
    logger.info(
        "Sprint 2 complete: configuration, logging, and database are wired up. "
        "Kite Connect and trading logic arrive in a future sprint."
    )


if __name__ == "__main__":
    main()
