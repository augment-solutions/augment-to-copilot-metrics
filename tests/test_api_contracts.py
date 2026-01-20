"""
API Contract Tests

These tests validate that our code's expectations match the actual API response structures.
They use real API response examples to ensure our mocks stay in sync with reality.

Run with: pytest tests/test_api_contracts.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

from augment_metrics.analytics_client import AnalyticsClient


class TestAPIContracts:
    """
    Test that our code correctly handles actual API response structures.
    
    These tests use REAL API response examples (captured from staging API)
    to ensure our mocks and code stay in sync with the actual API.
    """

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_user_activity_response_structure(self, mock_get):
        """
        Test that user-activity endpoint response is correctly parsed.
        
        Real API response structure:
        {
            "users": [...],
            "metadata": {...},
            "pagination": {...}
        }
        """
        client = AnalyticsClient(api_token="test-token")

        # This is the ACTUAL response structure from staging API
        mock_get.return_value = {
            "users": [
                {
                    "user_email": "test@example.com",
                    "active_days": 5,
                    "metrics": {
                        "chat_messages": 10,
                        "completions_accepted": 50,
                        "total_messages": 100,
                    },
                }
            ],
            "metadata": {
                "effective_start_date": "2026-01-01",
                "effective_end_date": "2026-01-15",
                "returned_user_count": 1,
                "total_days": 15,
            },
            "pagination": {"has_more": False, "next_cursor": None},
        }

        results = client.fetch_user_activity(date="2026-01-15")

        # Verify we correctly extracted data from "users" field
        assert len(results) == 1
        assert results[0]["user_email"] == "test@example.com"
        assert results[0]["active_days"] == 5

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_daily_usage_response_structure(self, mock_get):
        """
        Test that daily-usage endpoint response is correctly parsed.
        
        Real API response structure:
        {
            "daily_usage": [...],
            "metadata": {...}
        }
        """
        client = AnalyticsClient(api_token="test-token")

        # This is the ACTUAL response structure from staging API
        mock_get.return_value = {
            "daily_usage": [
                {"date": "2026-01-15", "total_edits": 1000, "total_users": 50}
            ],
            "metadata": {
                "effective_start_date": "2026-01-15",
                "effective_end_date": "2026-01-15",
            },
        }

        results = client.fetch_daily_usage(start_date="2026-01-15", end_date="2026-01-15")

        # Verify we correctly extracted data from "daily_usage" field
        assert len(results) == 1
        assert results[0]["date"] == "2026-01-15"

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_dau_count_response_structure(self, mock_get):
        """
        Test that dau-count endpoint response is correctly parsed.
        
        Real API response structure:
        {
            "daily_active_user_counts": [...],
            "metadata": {...}
        }
        
        NOTE: This endpoint does NOT use pagination!
        """
        client = AnalyticsClient(api_token="test-token")

        # This is the ACTUAL response structure from staging API
        mock_get.return_value = {
            "daily_active_user_counts": [
                {"date": "2026-01-09", "user_count": 75},
                {"date": "2026-01-10", "user_count": 45},
            ],
            "metadata": {
                "effective_end_date": "2026-01-10",
                "effective_start_date": "2026-01-09",
                "generated_at": "2026-01-17T00:17:59.723335985Z",
                "total_days": 2,
            },
        }

        results = client.fetch_dau_count(start_date="2026-01-09", end_date="2026-01-10")

        # Verify we correctly extracted data from "daily_active_user_counts" field
        assert len(results) == 2
        assert results[0]["user_count"] == 75
        assert results[1]["user_count"] == 45

    @patch("augment_metrics.analytics_client.HTTPClient.get")
    def test_editor_language_breakdown_response_structure(self, mock_get):
        """
        Test that daily-user-activity-by-editor-language endpoint response is correctly parsed.
        
        Real API response structure:
        {
            "records": [...],
            "metadata": {...},
            "pagination": {...}
        }
        """
        client = AnalyticsClient(api_token="test-token")

        # This is the ACTUAL response structure from staging API
        mock_get.return_value = {
            "records": [
                {
                    "user_email": "test@example.com",
                    "editor": "vscode",
                    "language": "python",
                    "metrics": {"total_edits": 100},
                }
            ],
            "metadata": {"date": "2026-01-15"},
            "pagination": {"has_more": False, "next_cursor": None},
        }

        results = client.fetch_editor_language_breakdown(date="2026-01-15")

        # Verify we correctly extracted data from "records" field
        assert len(results) == 1
        assert results[0]["editor"] == "vscode"
        assert results[0]["language"] == "python"

