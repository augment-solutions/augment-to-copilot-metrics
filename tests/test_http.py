"""
Unit tests for HTTP client.
"""

import pytest
import requests
from unittest.mock import Mock, patch

from augment_metrics.http import (
    HTTPClient,
    HTTPError,
    AuthenticationError,
    RateLimitError,
)


class TestHTTPClient:
    """Tests for HTTPClient class."""
    
    def test_init(self):
        """Test HTTPClient initialization."""
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
            timeout=60,
            max_retries=5,
        )
        
        assert client.api_token == "test-token"
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60
        assert client.max_retries == 5
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com/",
        )
        
        assert client.base_url == "https://api.example.com"
    
    def test_get_headers(self):
        """Test that headers include Bearer token."""
        client = HTTPClient(
            api_token="test-token-123",
            base_url="https://api.example.com",
        )
        
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer test-token-123"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
    
    @patch("augment_metrics.http.requests.Session.get")
    def test_get_success(self, mock_get):
        """Test successful GET request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
        )

        result = client.get("/test-endpoint", params={"key": "value"})

        assert result == {"data": "test"}
        mock_get.assert_called_once()

        # Check call arguments
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.example.com/test-endpoint"
        assert call_args[1]["params"] == {"key": "value"}
        assert "Authorization" in call_args[1]["headers"]

    @patch("augment_metrics.http.requests.Session.get")
    def test_get_endpoint_normalization(self, mock_get):
        """Test that endpoints without leading slash are normalized."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
        )

        # Test endpoint without leading slash
        result = client.get("analytics/v0/user-activity")

        # Verify the URL was constructed correctly with leading slash added
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.example.com/analytics/v0/user-activity"

    @patch("augment_metrics.http.requests.Session.get")
    def test_get_authentication_error(self, mock_get):
        """Test GET request with 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = HTTPClient(
            api_token="invalid-token",
            base_url="https://api.example.com",
        )
        
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            client.get("/test-endpoint")
    
    @patch("augment_metrics.http.requests.Session.get")
    def test_get_rate_limit_error(self, mock_get):
        """Test GET request with 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
        )
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client.get("/test-endpoint")
    
    @patch("augment_metrics.http.requests.Session.get")
    def test_get_timeout_error(self, mock_get):
        """Test GET request with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
            timeout=30,
        )
        
        with pytest.raises(HTTPError, match="Request timed out after 30 seconds"):
            client.get("/test-endpoint")
    
    @patch("augment_metrics.http.requests.Session.get")
    def test_get_connection_error(self, mock_get):
        """Test GET request with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
        )
        
        with pytest.raises(HTTPError, match="Connection error"):
            client.get("/test-endpoint")
    
    @patch("augment_metrics.http.requests.Session.get")
    def test_get_http_error(self, mock_get):
        """Test GET request with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
        )
        
        with pytest.raises(HTTPError, match="HTTP request failed"):
            client.get("/test-endpoint")
    
    def test_session_retry_configuration(self):
        """Test that session is configured with retry strategy."""
        client = HTTPClient(
            api_token="test-token",
            base_url="https://api.example.com",
            max_retries=5,
        )

        # Check that session has adapters
        assert "http://" in client.session.adapters
        assert "https://" in client.session.adapters

        # Verify retry configuration
        adapter = client.session.get_adapter("https://")
        retry = adapter.max_retries

        # Verify 429 is NOT in status_forcelist (we handle it explicitly)
        assert 429 not in retry.status_forcelist
        # Verify other server errors are in status_forcelist
        assert 500 in retry.status_forcelist
        assert 502 in retry.status_forcelist
        assert 503 in retry.status_forcelist
        assert 504 in retry.status_forcelist
