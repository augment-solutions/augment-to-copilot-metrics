"""
Unit tests for Analytics API Client.
"""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime

from augment_metrics.analytics_client import (
    AnalyticsClient,
    AnalyticsAPIError,
    PaginationError,
)
from augment_metrics.http import HTTPError, AuthenticationError


class TestAnalyticsClient:
    """Tests for AnalyticsClient class."""

    def test_init(self):
        """Test AnalyticsClient initialization."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
            base_url="https://api.example.com",
            timeout=60,
            max_retries=5,
            page_size=50,
        )

        assert client.enterprise_id == "ent-123"
        assert client.page_size == 50
        assert client.http_client.api_token == "test-token"
        assert client.http_client.base_url == "https://api.example.com"

    def test_init_invalid_page_size_zero(self):
        """Test AnalyticsClient initialization with page_size=0."""
        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            AnalyticsClient(
                api_token="test-token",
                enterprise_id="ent-123",
                page_size=0,
            )

    def test_init_invalid_page_size_negative(self):
        """Test AnalyticsClient initialization with negative page_size."""
        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            AnalyticsClient(
                api_token="test-token",
                enterprise_id="ent-123",
                page_size=-10,
            )

    def test_validate_date_valid(self):
        """Test date validation with valid dates."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        assert client._validate_date("2026-01-15") == "2026-01-15"
        assert client._validate_date("2025-12-31") == "2025-12-31"
        assert client._validate_date("2026-02-28") == "2026-02-28"

    def test_validate_date_invalid(self):
        """Test date validation with invalid dates."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_date("01/15/2026")  # Wrong format

        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_date("not-a-date")  # Invalid format

        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_date("2026-15-01")  # Invalid month

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_single_page(self, mock_get):
        """Test pagination with single page response."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
            page_size=10,
        )

        # Mock single page response
        mock_get.return_value = {
            "data": [{"id": 1}, {"id": 2}, {"id": 3}],
            "pagination": {"next_cursor": None},
        }

        results = list(client._paginate("/test-endpoint", {"param": "value"}))

        assert len(results) == 3
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}
        assert results[2] == {"id": 3}

        # Verify API was called once
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/test-endpoint"
        assert call_args[1]["params"]["limit"] == 10
        assert call_args[1]["params"]["param"] == "value"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_multiple_pages(self, mock_get):
        """Test pagination with multiple pages."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
            page_size=2,
        )

        # Mock multiple page responses
        mock_get.side_effect = [
            {"data": [{"id": 1}, {"id": 2}], "pagination": {"next_cursor": "cursor-1"}},
            {"data": [{"id": 3}, {"id": 4}], "pagination": {"next_cursor": "cursor-2"}},
            {"data": [{"id": 5}], "pagination": {"next_cursor": None}},
        ]

        results = list(client._paginate("/test-endpoint", {}))

        assert len(results) == 5
        assert [r["id"] for r in results] == [1, 2, 3, 4, 5]

        # Verify API was called 3 times
        assert mock_get.call_count == 3

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_empty_response(self, mock_get):
        """Test pagination with empty response."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {"data": [], "pagination": {"next_cursor": None}}

        results = list(client._paginate("/test-endpoint"))

        assert len(results) == 0

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_http_error(self, mock_get):
        """Test pagination with HTTP error."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.side_effect = HTTPError("Connection failed")

        with pytest.raises(PaginationError, match="Failed to fetch page"):
            list(client._paginate("/test-endpoint"))

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_invalid_response_type(self, mock_get):
        """Test pagination with invalid response type."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = ["not", "a", "dict"]

        with pytest.raises(PaginationError, match="Invalid response type"):
            list(client._paginate("/test-endpoint"))

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_invalid_data_type(self, mock_get):
        """Test pagination with invalid data type."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {"data": "not a list", "pagination": {"next_cursor": None}}

        with pytest.raises(PaginationError, match="Invalid data type"):
            list(client._paginate("/test-endpoint"))

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_paginate_invalid_pagination_type(self, mock_get):
        """Test pagination with invalid pagination type (not a dict)."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {"data": [{"id": 1}], "pagination": None}  # Should be a dict

        with pytest.raises(PaginationError, match="Invalid pagination type"):
            list(client._paginate("/test-endpoint"))

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_user_activity_single_date(self, mock_get):
        """Test fetching user activity for a single date."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [
                {"user_email": "user1@example.com", "total_edits": 10},
                {"user_email": "user2@example.com", "total_edits": 20},
            ],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_user_activity(date="2026-01-15")

        assert len(results) == 2
        assert results[0]["user_email"] == "user1@example.com"

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[0][0] == "/analytics/v0/user-activity"
        assert call_args[1]["params"]["enterprise_id"] == "ent-123"
        assert call_args[1]["params"]["date"] == "2026-01-15"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_user_activity_date_range(self, mock_get):
        """Test fetching user activity for a date range."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [{"user_email": "user@example.com"}],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_user_activity(start_date="2026-01-01", end_date="2026-01-15")

        assert len(results) == 1

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[1]["params"]["start_date"] == "2026-01-01"
        assert call_args[1]["params"]["end_date"] == "2026-01-15"

    def test_fetch_user_activity_invalid_params(self):
        """Test fetch_user_activity with invalid parameters."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        # Cannot specify both date and start_date/end_date
        with pytest.raises(ValueError, match="Cannot specify both"):
            client.fetch_user_activity(date="2026-01-15", start_date="2026-01-01")

        # Must specify both start_date and end_date
        with pytest.raises(ValueError, match="Both 'start_date' and 'end_date'"):
            client.fetch_user_activity(start_date="2026-01-01")

        with pytest.raises(ValueError, match="Both 'start_date' and 'end_date'"):
            client.fetch_user_activity(end_date="2026-01-15")

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_daily_usage(self, mock_get):
        """Test fetching daily usage metrics."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [
                {"date": "2026-01-01", "total_edits": 100},
                {"date": "2026-01-02", "total_edits": 150},
            ],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_daily_usage(start_date="2026-01-01", end_date="2026-01-02")

        assert len(results) == 2
        assert results[0]["date"] == "2026-01-01"

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[0][0] == "/analytics/v0/daily-usage"
        assert call_args[1]["params"]["enterprise_id"] == "ent-123"
        assert call_args[1]["params"]["start_date"] == "2026-01-01"
        assert call_args[1]["params"]["end_date"] == "2026-01-02"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_dau_count(self, mock_get):
        """Test fetching DAU count metrics."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [
                {"date": "2026-01-01", "active_users": 50},
                {"date": "2026-01-02", "active_users": 55},
            ],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_dau_count(start_date="2026-01-01", end_date="2026-01-02")

        assert len(results) == 2
        assert results[0]["active_users"] == 50

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[0][0] == "/analytics/v0/dau-count"
        assert call_args[1]["params"]["enterprise_id"] == "ent-123"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_editor_language_breakdown(self, mock_get):
        """Test fetching editor/language breakdown."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [
                {
                    "user_email": "user@example.com",
                    "editor": "vscode",
                    "language": "python",
                    "total_edits": 10,
                },
            ],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_editor_language_breakdown(date="2026-01-15")

        assert len(results) == 1
        assert results[0]["editor"] == "vscode"
        assert results[0]["language"] == "python"

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[0][0] == "/analytics/v0/daily-user-activity-by-editor-language"
        assert call_args[1]["params"]["date"] == "2026-01-15"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_fetch_editor_language_breakdown_date_range(self, mock_get):
        """Test fetching editor/language breakdown for date range."""
        client = AnalyticsClient(
            api_token="test-token",
            enterprise_id="ent-123",
        )

        mock_get.return_value = {
            "data": [{"editor": "vscode"}],
            "pagination": {"next_cursor": None},
        }

        results = client.fetch_editor_language_breakdown(
            start_date="2026-01-01", end_date="2026-01-15"
        )

        assert len(results) == 1

        # Verify API call
        call_args = mock_get.call_args
        assert call_args[1]["params"]["start_date"] == "2026-01-01"
        assert call_args[1]["params"]["end_date"] == "2026-01-15"
