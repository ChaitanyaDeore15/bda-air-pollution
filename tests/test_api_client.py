"""
Unit tests for XKDR API Client.
Tests authentication, URL configuration, and error handling with mocks.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.config import get_api_key, META_ENDPOINT, STATIONS_ENDPOINT
from src.api_client import XKDRAPIClient


def test_api_key_loading():
    """Verify that the API key is retrieved and not a placeholder."""
    key = get_api_key()
    assert key is not None
    assert len(key) > 10
    assert "PASTE_YOUR_REAL_API_KEY_HERE" not in key


def test_client_init_headers():
    """Verify that Authorization Bearer header is properly configured."""
    client = XKDRAPIClient(api_key="test_dummy_key_12345")
    auth_header = client.session.headers.get("Authorization")
    assert auth_header == "Bearer test_dummy_key_12345"
    assert "User-Agent" in client.session.headers


@patch("requests.Session.get")
def test_client_get_meta_mocked(mock_get):
    """Test get_meta with a mock response."""
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "schema_version": "v1",
        "your_tier": "full",
        "stations": 558,
        "measurements": {"rows": 196521834},
    }
    mock_get.return_value = mock_response

    client = XKDRAPIClient(api_key="mock_key")
    meta = client.get_meta()
    assert meta["your_tier"] == "full"
    assert meta["stations"] == 558


@patch("requests.Session.get")
def test_client_error_handling_sanitizes_key(mock_get):
    """Verify that error messages do not leak the secret API key."""
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("Failed connecting with key secret_token_abc")

    client = XKDRAPIClient(api_key="secret_token_abc")
    with pytest.raises(RuntimeError) as exc_info:
        client.get_meta()

    assert "secret_token_abc" not in str(exc_info.value)
    assert "[REDACTED_API_KEY]" in str(exc_info.value)
