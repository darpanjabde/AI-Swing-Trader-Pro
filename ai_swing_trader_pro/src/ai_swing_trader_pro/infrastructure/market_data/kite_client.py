"""Thin wrapper around the official `kiteconnect` (pykiteconnect) SDK.

Single Responsibility: this class's only job is to talk to the
`kiteconnect.KiteConnect` object. It performs no credential validation, no
domain-exception translation, and no logging of business events — that
belongs to `KiteMarketDataProvider`, which depends on this class.

Keeping this separation means:
    - If Zerodha's SDK API changes, only this file needs to change.
    - `KiteMarketDataProvider` (and its tests) can depend on this class's
      small interface instead of the full `KiteConnect` surface.
    - Tests can substitute a fake/mock `KiteClient` without needing the
      real `kiteconnect` package installed at all.
"""

from __future__ import annotations

from typing import Any, Protocol

from kiteconnect import KiteConnect


class SupportsKiteConnect(Protocol):
    """Structural type describing the subset of `KiteConnect` we use.

    Declared as a `Protocol` so `KiteClient` can be type-checked against
    the real SDK or a test double without either depending on the other.
    """

    def login_url(self) -> str: ...

    def set_access_token(self, access_token: str) -> None: ...

    def generate_session(
        self, request_token: str, api_secret: str
    ) -> dict[str, Any]: ...

    def profile(self) -> dict[str, Any]: ...


class KiteClient:
    """Thin, testable wrapper around a `KiteConnect` instance.

    Args:
        api_key: The Kite Connect API key.
        api_secret: The Kite Connect API secret, used only for the
            request-token-to-access-token exchange in `generate_session`.
        access_token: An optional, previously issued access token to seed
            the underlying SDK client with (skips the login flow).
        timeout: Request timeout, in seconds, passed through to the SDK.
        sdk_client: Optional pre-built SDK client (or test double). When
            omitted, a real `kiteconnect.KiteConnect` instance is created.
            Injecting this is the primary seam used by unit tests.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str | None = None,
        timeout: int = 7,
        sdk_client: SupportsKiteConnect | None = None,
    ) -> None:
        self._api_secret = api_secret
        self._sdk: SupportsKiteConnect = sdk_client or KiteConnect(
            api_key=api_key, timeout=timeout
        )
        if access_token:
            self._sdk.set_access_token(access_token)

    def login_url(self) -> str:
        """Return the Kite Connect login URL for the interactive OAuth flow."""

        return self._sdk.login_url()

    def generate_session(self, request_token: str) -> dict[str, Any]:
        """Exchange a request token for a full session (incl. access token).

        Args:
            request_token: The one-time token returned by Kite after the
                user completes login and is redirected back to the app.

        Returns:
            The raw session dictionary returned by the SDK, which includes
            (among other fields) `access_token` and `user_id`.

        Raises:
            Exception: Whatever the underlying `kiteconnect` SDK raises on
                failure (e.g. `kiteconnect.exceptions.TokenException`).
                Translation into domain exceptions happens one layer up,
                in `KiteMarketDataProvider`.
        """

        return self._sdk.generate_session(request_token, api_secret=self._api_secret)

    def set_access_token(self, access_token: str) -> None:
        """Set (or replace) the access token used for subsequent API calls."""

        self._sdk.set_access_token(access_token)

    def fetch_profile(self) -> dict[str, Any]:
        """Fetch the authenticated user's profile from the Kite API.

        Used exclusively as a lightweight "is this session actually
        usable?" probe by `KiteMarketDataProvider.verify_connection()`.

        Raises:
            Exception: Whatever the underlying SDK raises (e.g. an
                expired-token or network error). Translation into domain
                exceptions happens in `KiteMarketDataProvider`.
        """

        return self._sdk.profile()
