"""Unit tests for ai_swing_trader_pro.infrastructure.market_data.kite_provider.

`KiteMarketDataProvider` is tested with a mocked `KiteClient` (injected via
its `client=` constructor parameter), so no real Kite Connect account,
network access, or the `kiteconnect` package's runtime behavior is needed
— only its import, which is satisfied by the dependency being installed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_swing_trader_pro.core.config import Settings
from ai_swing_trader_pro.domain.exceptions import (
    AuthenticationError,
    ConnectionVerificationError,
    InvalidCredentialsError,
    SessionNotInitializedError,
)
from ai_swing_trader_pro.infrastructure.market_data.kite_provider import (
    KiteMarketDataProvider,
)


def _settings(
    api_key: str | None = "test-api-key",
    api_secret: str | None = "test-api-secret",
    access_token: str | None = None,
) -> Settings:
    """Build a Settings instance with the given Kite credential overrides."""

    settings = Settings(environment="test")
    settings.kite.api_key = api_key
    settings.kite.api_secret = api_secret
    settings.kite.access_token = access_token
    return settings


@pytest.fixture
def fake_client() -> MagicMock:
    return MagicMock(name="FakeKiteClient")


class TestCredentialValidation:
    def test_raises_when_api_key_missing(self, fake_client: MagicMock) -> None:
        settings = _settings(api_key=None)
        with pytest.raises(InvalidCredentialsError, match="KITE_API_KEY"):
            KiteMarketDataProvider(settings=settings, client=fake_client)

    def test_raises_when_api_secret_missing(self, fake_client: MagicMock) -> None:
        settings = _settings(api_secret=None)
        with pytest.raises(InvalidCredentialsError, match="KITE_API_SECRET"):
            KiteMarketDataProvider(settings=settings, client=fake_client)

    def test_raises_when_api_key_is_blank_whitespace(self, fake_client: MagicMock) -> None:
        settings = _settings(api_key="   ")
        with pytest.raises(InvalidCredentialsError, match="KITE_API_KEY"):
            KiteMarketDataProvider(settings=settings, client=fake_client)

    def test_lists_both_missing_credentials(self, fake_client: MagicMock) -> None:
        settings = _settings(api_key=None, api_secret=None)
        with pytest.raises(InvalidCredentialsError) as exc_info:
            KiteMarketDataProvider(settings=settings, client=fake_client)
        assert "KITE_API_KEY" in str(exc_info.value)
        assert "KITE_API_SECRET" in str(exc_info.value)

    def test_valid_credentials_construct_successfully(self, fake_client: MagicMock) -> None:
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)
        assert provider.is_authenticated is False


class TestCachedAccessToken:
    def test_is_authenticated_true_when_cached_token_present(
        self, fake_client: MagicMock
    ) -> None:
        settings = _settings(access_token="cached-token")
        provider = KiteMarketDataProvider(settings=settings, client=fake_client)
        assert provider.is_authenticated is True

    def test_authenticate_without_request_token_reuses_cached(
        self, fake_client: MagicMock
    ) -> None:
        settings = _settings(access_token="cached-token")
        provider = KiteMarketDataProvider(settings=settings, client=fake_client)

        provider.authenticate()  # no request_token supplied

        assert provider.is_authenticated is True
        fake_client.generate_session.assert_not_called()


class TestAuthenticate:
    def test_success_with_request_token(self, fake_client: MagicMock) -> None:
        fake_client.generate_session.return_value = {
            "access_token": "brand-new-token",
            "user_id": "AB1234",
        }
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        provider.authenticate(request_token="req-token")

        fake_client.generate_session.assert_called_once_with("req-token")
        fake_client.set_access_token.assert_called_once_with("brand-new-token")
        assert provider.is_authenticated is True

    def test_raises_authentication_error_when_sdk_rejects_token(
        self, fake_client: MagicMock
    ) -> None:
        fake_client.generate_session.side_effect = RuntimeError("bad token")
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        with pytest.raises(AuthenticationError):
            provider.authenticate(request_token="bad-token")
        assert provider.is_authenticated is False

    def test_raises_authentication_error_when_no_access_token_returned(
        self, fake_client: MagicMock
    ) -> None:
        fake_client.generate_session.return_value = {"user_id": "AB1234"}  # no token
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        with pytest.raises(AuthenticationError, match="access token"):
            provider.authenticate(request_token="req-token")

    def test_raises_authentication_error_with_no_token_at_all(
        self, fake_client: MagicMock
    ) -> None:
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        with pytest.raises(AuthenticationError):
            provider.authenticate()  # no request_token, no cached token


class TestVerifyConnection:
    def test_raises_when_not_authenticated(self, fake_client: MagicMock) -> None:
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)
        with pytest.raises(SessionNotInitializedError):
            provider.verify_connection()

    def test_returns_true_on_valid_profile(self, fake_client: MagicMock) -> None:
        fake_client.fetch_profile.return_value = {"user_id": "AB1234"}
        settings = _settings(access_token="cached-token")
        provider = KiteMarketDataProvider(settings=settings, client=fake_client)

        assert provider.verify_connection() is True

    def test_returns_false_when_profile_missing_user_id(
        self, fake_client: MagicMock
    ) -> None:
        fake_client.fetch_profile.return_value = {}
        settings = _settings(access_token="cached-token")
        provider = KiteMarketDataProvider(settings=settings, client=fake_client)

        assert provider.verify_connection() is False

    def test_raises_connection_verification_error_on_sdk_failure(
        self, fake_client: MagicMock
    ) -> None:
        fake_client.fetch_profile.side_effect = ConnectionError("timeout")
        settings = _settings(access_token="cached-token")
        provider = KiteMarketDataProvider(settings=settings, client=fake_client)

        with pytest.raises(ConnectionVerificationError):
            provider.verify_connection()


class TestGetLoginUrl:
    def test_returns_url_from_client(self, fake_client: MagicMock) -> None:
        fake_client.login_url.return_value = "https://kite.zerodha.com/connect/login"
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        assert provider.get_login_url() == "https://kite.zerodha.com/connect/login"

    def test_raises_connection_verification_error_on_failure(
        self, fake_client: MagicMock
    ) -> None:
        fake_client.login_url.side_effect = RuntimeError("malformed key")
        provider = KiteMarketDataProvider(settings=_settings(), client=fake_client)

        with pytest.raises(ConnectionVerificationError):
            provider.get_login_url()
