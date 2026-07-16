"""Unit tests for ai_swing_trader_pro.infrastructure.market_data.kite_client.

All tests inject a fake SDK object via `KiteClient(sdk_client=...)` so no
real `kiteconnect.KiteConnect` instance, network call, or Kite account is
ever needed.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai_swing_trader_pro.infrastructure.market_data.kite_client import KiteClient


@pytest.fixture
def fake_sdk() -> MagicMock:
    """A MagicMock standing in for a `kiteconnect.KiteConnect` instance."""

    sdk = MagicMock(name="FakeKiteConnectSDK")
    sdk.login_url.return_value = "https://kite.zerodha.com/connect/login?api_key=test"
    sdk.generate_session.return_value = {
        "access_token": "fake-access-token",
        "user_id": "AB1234",
    }
    sdk.profile.return_value = {"user_id": "AB1234", "user_name": "Test Trader"}
    return sdk


class TestKiteClientConstruction:
    def test_sets_access_token_when_provided(self, fake_sdk: MagicMock) -> None:
        KiteClient(
            api_key="key",
            api_secret="secret",
            access_token="cached-token",
            sdk_client=fake_sdk,
        )
        fake_sdk.set_access_token.assert_called_once_with("cached-token")

    def test_does_not_set_access_token_when_absent(self, fake_sdk: MagicMock) -> None:
        KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)
        fake_sdk.set_access_token.assert_not_called()


class TestKiteClientLoginUrl:
    def test_returns_sdk_login_url(self, fake_sdk: MagicMock) -> None:
        client = KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)
        assert client.login_url() == "https://kite.zerodha.com/connect/login?api_key=test"


class TestKiteClientGenerateSession:
    def test_passes_request_token_and_api_secret(self, fake_sdk: MagicMock) -> None:
        client = KiteClient(api_key="key", api_secret="the-secret", sdk_client=fake_sdk)

        result = client.generate_session("req-token-123")

        fake_sdk.generate_session.assert_called_once_with(
            "req-token-123", api_secret="the-secret"
        )
        assert result["access_token"] == "fake-access-token"

    def test_propagates_sdk_exceptions(self, fake_sdk: MagicMock) -> None:
        fake_sdk.generate_session.side_effect = RuntimeError("invalid token")
        client = KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)

        with pytest.raises(RuntimeError, match="invalid token"):
            client.generate_session("bad-token")


class TestKiteClientSetAccessToken:
    def test_forwards_to_sdk(self, fake_sdk: MagicMock) -> None:
        client = KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)
        client.set_access_token("new-token")
        fake_sdk.set_access_token.assert_called_with("new-token")


class TestKiteClientFetchProfile:
    def test_returns_sdk_profile(self, fake_sdk: MagicMock) -> None:
        client = KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)
        profile = client.fetch_profile()
        assert profile["user_id"] == "AB1234"

    def test_propagates_sdk_exceptions(self, fake_sdk: MagicMock) -> None:
        fake_sdk.profile.side_effect = ConnectionError("network down")
        client = KiteClient(api_key="key", api_secret="secret", sdk_client=fake_sdk)

        with pytest.raises(ConnectionError, match="network down"):
            client.fetch_profile()
