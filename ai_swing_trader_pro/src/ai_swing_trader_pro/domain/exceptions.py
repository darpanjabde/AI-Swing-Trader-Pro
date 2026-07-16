"""Domain-specific exception hierarchy for market data providers.

These exceptions are deliberately framework-agnostic: they know nothing
about `kiteconnect`, HTTP status codes, or SQLAlchemy. Infrastructure-layer
code (e.g. `KiteMarketDataProvider`) is responsible for catching
lower-level/library exceptions and re-raising one of these instead, so
that callers in the application layer never need to import a broker SDK
just to handle its errors.

All exceptions here extend `ai_swing_trader_pro.core.exceptions.AppError`,
keeping a single root for `except AppError` catch-alls at the outermost
layer (e.g. a future CLI or API error handler).
"""

from __future__ import annotations

from ai_swing_trader_pro.core.exceptions import AppError


class MarketDataProviderError(AppError):
    """Base class for all market-data-provider related errors."""


class InvalidCredentialsError(MarketDataProviderError):
    """Raised when required broker credentials are missing or malformed.

    This is a configuration-time error: it means the provider could not
    even attempt to talk to the broker, because `.env` / environment
    variables did not supply usable values (e.g. an empty `KITE_API_KEY`).
    """


class AuthenticationError(MarketDataProviderError):
    """Raised when the broker rejects an authentication/login attempt.

    Typical causes: an invalid or expired `request_token`, a mismatched
    `api_secret`, or an unexpected/empty response from the broker's
    session-generation endpoint.
    """


class SessionNotInitializedError(MarketDataProviderError):
    """Raised when an operation requires an authenticated session.

    For example, calling `verify_connection()` before `authenticate()`
    has ever succeeded.
    """


class ConnectionVerificationError(MarketDataProviderError):
    """Raised when a live connection check to the broker fails.

    This covers network errors, timeouts, or the broker reporting the
    current access token as invalid/expired during a verification call.
    """
