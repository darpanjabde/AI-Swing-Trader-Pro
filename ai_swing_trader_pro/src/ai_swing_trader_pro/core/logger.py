"""Centralized logging setup using Loguru.

Single Responsibility: configure and expose one `logger` object for the
entire application. All other modules should `from ai_swing_trader_pro.core.logger
import logger` rather than configuring their own handlers.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _logger

from ai_swing_trader_pro.core.config import Settings, get_settings

_CONFIGURED: bool = False


def _console_format(record: dict) -> str:
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )


def configure_logging(settings: Settings | None = None, force: bool = False) -> None:
    """Configure Loguru sinks (console + rotating file).

    Idempotent by default: repeated calls are no-ops unless `force=True`,
    which is useful in tests that need a fresh configuration.
    """

    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    settings = settings or get_settings()
    log_cfg = settings.logging

    log_dir: Path = log_cfg.directory
    log_dir.mkdir(parents=True, exist_ok=True)

    _logger.remove()  # drop Loguru's default handler

    _logger.add(
        sys.stderr,
        level=log_cfg.level,
        format=_console_format,
        colorize=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    _logger.add(
        log_dir / "app.log",
        level=log_cfg.level,
        rotation=log_cfg.rotation,
        retention=log_cfg.retention,
        serialize=log_cfg.serialize or log_cfg.json_logs,
        backtrace=False,
        diagnose=False,
        enqueue=True,  # process/thread-safe writes
    )

    _logger.bind(app=settings.app_name).info(
        "Logging configured (env={env}, level={level})",
        env=settings.environment,
        level=log_cfg.level,
    )

    _CONFIGURED = True


# Configure eagerly on import so `from ...core.logger import logger` always
# yields a ready-to-use logger, mirroring Loguru's own ergonomics.
configure_logging()

logger = _logger

__all__ = ["logger", "configure_logging"]
