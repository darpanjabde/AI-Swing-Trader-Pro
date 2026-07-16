"""Abstract market-data provider contract.

This is a *port* in the Clean Architecture sense: the domain/application
layers program against this interface, and concrete brokers (Kite Connect
today, others potentially later) live in `infrastructure/` and implement
it. This module has zero third-party or framework dependencies — only the
standard library — so it can be imported from anywhere without pulling in
`kiteconnect`, SQLAlchemy, or anything else.

Scope note (Sprint 3.1): only the *authentication* surface is defined here.
Methods for instrument lookup, historical candles, and live quotes are
intentionally left out and will be added to this interface (or a sibling
interface) in a later sprint, once those features are implemented.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class MarketDataProvider(ABC):
    """Contract for a broker/market-data integration's authentication layer.

    Implementations are responsible for:
        - Validating that credentials required to authenticate are present.
        - Producing a login URL when an interactive OAuth-style flow is
          required (e.g. Kite Connect's request-token flow).
        - Exchanging a request token (or a cached access token) for an
          authenticated session.
        - Reporting authentication state and verifying that a session is
          actually usable against the live broker API.

    Implementations must raise the domain exceptions defined in
    `ai_swing_trader_pro.domain.exceptions` (or subclasses of them) rather
    than letting broker-SDK-specific or generic exceptions propagate.
    """

    @abstractmethod
    def get_login_url(self) -> str:
        """Return the URL the end user must visit to authorize this app.

        Returns:
            A fully-formed login URL for the broker's OAuth-style flow.

        Raises:
            InvalidCredentialsError: If credentials required to build the
                login URL (e.g. an API key) are missing or invalid.
        """

    @abstractmethod
    def authenticate(self, request_token: str | None = None) -> None:
        """Establish an authenticated session with the broker.

        Args:
            request_token: The one-time token obtained after the user
                completes the broker's login flow and is redirected back
                with this value as a query parameter. If omitted, an
                implementation may fall back to a previously cached
                access token supplied via configuration, if one exists.

        Raises:
            InvalidCredentialsError: If required credentials are missing.
            AuthenticationError: If the broker rejects the token exchange,
                or no usable token (request or cached) is available.
        """

    @abstractmethod
    def verify_connection(self) -> bool:
        """Verify that the current session is authenticated and usable.

        Implementations should perform a lightweight, low-cost call
        against the live broker API (e.g. fetching the user's profile)
        to confirm the access token is actually valid — not just present.

        Returns:
            True if the connection is verified and usable.

        Raises:
            SessionNotInitializedError: If `authenticate()` has not been
                called (or did not succeed) yet.
            ConnectionVerificationError: If the verification call itself
                fails (network error, expired/rejected token, etc.).
        """

    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Whether this provider currently holds a session it believes is valid.

        This reflects local state only (e.g. "an access token was set");
        it does not, by itself, guarantee the broker still honors that
        token. Use `verify_connection()` for a live check.
        """
