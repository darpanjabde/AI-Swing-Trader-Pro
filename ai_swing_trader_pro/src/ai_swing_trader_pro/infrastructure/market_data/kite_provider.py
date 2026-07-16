"""Kite Connect implementation of the `MarketDataProvider` port.

Scope (Sprint 3.1): authentication and connection verification only.
Instrument download, historical data, live quotes, and scanner logic are
explicitly out of scope and will be added to this class (or extracted into
sibling classes) in later sprints.

This module is the *translation layer* between the raw `kiteconnect` SDK
(wrapped by `KiteClient`) and the rest of the application: it validates
configuration, raises domain-specific exceptions instead of letting SDK or
generic exceptions leak out, and emits structured log events for every
significant authentication step.
"""

from __future__ import annotations

from ai_swing_trader_pro.core.config import Settings, get_settings
from ai_swing_trader_pro.core.logger import logger
from ai_swing_trader_pro.domain.exceptions import (
    AuthenticationError,
    ConnectionVerificationError,
    InvalidCredentialsError,
    SessionNotInitializedError,
)
from ai_swing_trader_pro.domain.interfaces.market_data_provider import (
    MarketDataProvider,
)
from ai_swing_trader_pro.infrastructure.market_data.kite_client import KiteClient

_log = logger.bind(component="KiteMarketDataProvider")


class KiteMarketDataProvider(MarketDataProvider):
    """Zerodha Kite Connect authentication provider.

    Args:
        settings: Application settings to read `KITE_*` credentials from.
            Defaults to the process-wide cached settings via
            `get_settings()`.
        client: Optional pre-built `KiteClient` (or compatible test
            double). When omitted, a real `KiteClient` is constructed from
            validated credentials in `settings.kite`.

    Raises:
        InvalidCredentialsError: If `settings.kite.api_key` or
            `settings.kite.api_secret` are missing or blank. Raised
            eagerly at construction time so failures surface immediately
            rather than on the first authentication attempt.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        client: KiteClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        api_key, api_secret = self._validate_credentials(self._settings)

        cached_token = self._secret_value(self._settings.kite.access_token)

        self._client = client or KiteClient(
            api_key=api_key,
            api_secret=api_secret,
            access_token=cached_token,
            timeout=self._settings.kite.request_timeout,
        )
        # Local-only flag: reflects whether we believe we hold a usable
        # token, not whether the broker has actually confirmed it yet.
        self._authenticated: bool = cached_token is not None

        if self._authenticated:
            _log.debug("Initialized with a cached access token from configuration.")
        else:
            _log.debug("Initialized without a cached access token.")

    @staticmethod
    def _secret_value(secret: object) -> str | None:
        """Extract a plain string from a Pydantic `SecretStr`, or None."""

        if secret is None:
            return None
        value = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
        return value.strip() or None

    @classmethod
    def _validate_credentials(cls, settings: Settings) -> tuple[str, str]:
        """Ensure `api_key` / `api_secret` are present and non-blank.

        Returns:
            A `(api_key, api_secret)` tuple of plain strings, ready to pass
            to the SDK.

        Raises:
            InvalidCredentialsError: If either value is missing or blank.
        """

        api_key = cls._secret_value(settings.kite.api_key)
        api_secret = cls._secret_value(settings.kite.api_secret)

        missing = [
            name
            for name, value in (("KITE_API_KEY", api_key), ("KITE_API_SECRET", api_secret))
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            _log.error("Missing required Kite credential(s): {}", joined)
            raise InvalidCredentialsError(
                f"Missing or blank Kite Connect credential(s): {joined}. "
                "Set them in your .env file (see .env.example)."
            )

        # mypy/type-checkers can't see the "no None after the check above"
        # narrowing across the comprehension, so we assert explicitly.
        assert api_key is not None
        assert api_secret is not None
        return api_key, api_secret

    def get_login_url(self) -> str:
        """Return the Kite Connect login URL for the interactive OAuth flow.

        Raises:
            ConnectionVerificationError: If the SDK fails to build the URL
                (e.g. due to a malformed API key).
        """

        try:
            url = self._client.login_url()
        except Exception as exc:  # noqa: BLE001 - translated to a domain error below
            _log.exception("Failed to build Kite login URL.")
            raise ConnectionVerificationError(
                "Could not generate the Kite Connect login URL."
            ) from exc

        _log.info("Generated Kite login URL for interactive authentication.")
        return url

    def authenticate(self, request_token: str | None = None) -> None:
        """Establish an authenticated session with Kite Connect.

        If `request_token` is provided, it is exchanged for a fresh access
        token via `generate_session`. Otherwise, this method relies on an
        access token already cached in configuration (validated at
        construction time); if none exists, authentication fails.

        Args:
            request_token: The one-time token from the Kite login redirect.

        Raises:
            AuthenticationError: If the token exchange fails, the broker
                returns no usable access token, or no request token/cached
                token is available at all.
        """

        if request_token:
            _log.info("Authenticating with a fresh request token.")
            try:
                session_data = self._client.generate_session(request_token)
            except Exception as exc:  # noqa: BLE001 - translated below
                _log.exception("Kite rejected the request token during session generation.")
                raise AuthenticationError(
                    "Kite Connect authentication failed: the broker rejected "
                    "the supplied request token."
                ) from exc

            access_token = session_data.get("access_token")
            if not access_token:
                _log.error("Kite session response did not include an access_token.")
                raise AuthenticationError(
                    "Kite Connect returned a session without an access token."
                )

            self._client.set_access_token(access_token)
            self._authenticated = True
            user_id = session_data.get("user_id", "unknown")
            _log.success("Kite Connect session established for user_id={}.", user_id)
            return

        if self._authenticated:
            _log.info("No request token supplied; reusing cached access token.")
            return

        _log.error("Authentication attempted with no request token and no cached token.")
        raise AuthenticationError(
            "Cannot authenticate: no request_token was provided and no cached "
            "access token is available in configuration."
        )

    def verify_connection(self) -> bool:
        """Verify the current session is authenticated and usable.

        Performs a lightweight `profile()` call against the live Kite API.

        Returns:
            True if the broker confirms a valid session (i.e. returns a
            profile containing a `user_id`).

        Raises:
            SessionNotInitializedError: If `authenticate()` has not
                succeeded yet.
            ConnectionVerificationError: If the live check fails, e.g. due
                to an expired token or a network/API error.
        """

        if not self._authenticated:
            _log.error("verify_connection() called before authenticate() succeeded.")
            raise SessionNotInitializedError(
                "No active Kite session. Call authenticate() before "
                "verify_connection()."
            )

        try:
            profile = self._client.fetch_profile()
        except Exception as exc:  # noqa: BLE001 - translated below
            _log.exception("Kite connection verification failed.")
            raise ConnectionVerificationError(
                "Failed to verify the Kite Connect session against the live API."
            ) from exc

        is_verified = bool(profile.get("user_id"))
        if is_verified:
            _log.success(
                "Kite connection verified for user_id={}.", profile.get("user_id")
            )
        else:
            _log.warning("Kite profile response did not include a user_id.")

        return is_verified

    @property
    def is_authenticated(self) -> bool:
        """Whether this provider currently believes it holds a valid session."""

        return self._authenticated
