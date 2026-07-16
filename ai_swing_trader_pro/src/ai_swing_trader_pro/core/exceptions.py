"""Application-wide exception hierarchy.

Defining these early (Sprint 2) lets later sprints (strategy engine, Kite
Connect client) raise/catch specific, typed errors instead of bare
`Exception`, keeping error handling consistent across layers.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application-specific exceptions."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""


class DatabaseError(AppError):
    """Raised for database connectivity or integrity issues."""
