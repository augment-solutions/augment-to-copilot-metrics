"""
Integration tests for the full augment-metrics workflow.

These tests verify the end-to-end functionality from API calls
through data transformation to file output.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from augment_metrics import AnalyticsClient, MetricsTransformer


class TestIntegration:
    """Integration tests for the full workflow."""

    @pytest.fixture
    def sample_user_data(self):
        """Sample user activity data in the format returned by the API."""
        return [
            {
                "user_email": "user1@example.com",
                "active_days": 5,
                "metrics": {
                    "completions_count": 100,
                    "completions_accepted": 80,
                    "completions_lines_of_code": 400,
                    "chat_messages": 20,
                    "remote_agent_messages": 10,
                    "remote_agent_lines_of_code": 50,
                    "ide_agent_messages": 5,
                    "ide_agent_lines_of_code": 30,
                    "cli_agent_interactive_messages": 3,
                    "cli_agent_interactive_lines_of_code": 15,
                    "cli_agent_non_interactive_messages": 2,
                    "cli_agent_non_interactive_lines_of_code": 5,
                    "total_tool_calls": 15,
                    "total_modified_lines_of_code": 500,
                },
            }
        ]

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_api_client_to_transformer_integration(self, sample_user_data):
        """Test integration between API client and transformer."""
        # Mock the HTTP client
        with patch("augment_metrics.analytics_client.HTTPClient") as MockHTTPClient:
            mock_http = MagicMock()
            MockHTTPClient.return_value = mock_http

            # Set up mock responses
            mock_http.get.side_effect = [
                {"data": sample_user_data, "pagination": {}},
                {"data": [{"date": "2026-01-15", "active_users": 10}], "pagination": {}},
            ]

            # Create client and fetch data
            client = AnalyticsClient(api_token="test-token", enterprise_id="test-enterprise")

            test_date = "2026-01-15"
            user_activity = client.fetch_user_activity(date=test_date)
            dau_count_data = client.fetch_dau_count(start_date=test_date, end_date=test_date)

            # Verify API client returned data
            assert len(user_activity) == 1
            assert user_activity[0]["user_email"] == "user1@example.com"
            assert len(dau_count_data) == 1

            # Transform data
            transformer = MetricsTransformer()
            dau_count = dau_count_data[0].get("active_users", 0)
            copilot_metrics = transformer.transform_user_metrics(
                user_activity, test_date, dau_count
            )

            # Verify transformed data structure
            assert copilot_metrics["date"] == test_date
            assert copilot_metrics["total_active_users"] == 10
            assert "copilot_ide_code_completions" in copilot_metrics
            assert "copilot_ide_chat" in copilot_metrics
            assert "breakdown" in copilot_metrics
            assert len(copilot_metrics["breakdown"]) == 1

    def test_transformer_to_file_output_integration(self, sample_user_data, temp_output_dir):
        """Test integration from transformer to file output."""
        transformer = MetricsTransformer()
        test_date = "2026-01-15"

        # Transform data
        copilot_metrics = transformer.transform_user_metrics(
            sample_user_data, test_date, dau_count=10
        )
        csv_rows = [transformer.transform_to_csv_row(user) for user in sample_user_data]

        # Write JSON file
        json_file = Path(temp_output_dir) / f"copilot_metrics_{test_date}.json"
        with open(json_file, "w") as f:
            json.dump(copilot_metrics, f, indent=2)

        # Write CSV file
        import csv

        csv_file = Path(temp_output_dir) / f"augment_metrics_{test_date}.csv"
        with open(csv_file, "w", newline="") as f:
            if csv_rows:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)

        # Verify files exist
        assert json_file.exists()
        assert csv_file.exists()

        # Verify JSON content
        with open(json_file) as f:
            loaded_json = json.load(f)
            assert loaded_json["date"] == test_date
            assert loaded_json["total_active_users"] == 10

        # Verify CSV content
        with open(csv_file) as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)
            assert len(rows) == 1
            assert rows[0]["User"] == "user1@example.com"
            assert rows[0]["Completions"] == "100"

    def test_end_to_end_workflow(self, sample_user_data, temp_output_dir):
        """Test the complete end-to-end workflow."""
        with patch("augment_metrics.analytics_client.HTTPClient") as MockHTTPClient:
            mock_http = MagicMock()
            MockHTTPClient.return_value = mock_http

            # Set up mock responses
            mock_http.get.side_effect = [
                {"data": sample_user_data, "pagination": {}},
                {"data": [{"date": "2026-01-15", "active_users": 10}], "pagination": {}},
            ]

            # Step 1: Fetch data from API
            client = AnalyticsClient(api_token="test-token", enterprise_id="test-enterprise")
            test_date = "2026-01-15"
            user_activity = client.fetch_user_activity(date=test_date)
            dau_count_data = client.fetch_dau_count(start_date=test_date, end_date=test_date)

            # Step 2: Transform data
            transformer = MetricsTransformer()
            dau_count = dau_count_data[0].get("active_users", 0)
            copilot_metrics = transformer.transform_user_metrics(
                user_activity, test_date, dau_count
            )
            csv_rows = [transformer.transform_to_csv_row(user) for user in user_activity]

            # Step 3: Write output files
            json_file = Path(temp_output_dir) / f"copilot_metrics_{test_date}.json"
            csv_file = Path(temp_output_dir) / f"augment_metrics_{test_date}.csv"

            with open(json_file, "w") as f:
                json.dump(copilot_metrics, f, indent=2)

            import csv

            with open(csv_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
                writer.writeheader()
                writer.writerows(csv_rows)

            # Step 4: Verify complete workflow
            assert json_file.exists()
            assert csv_file.exists()

            with open(json_file) as f:
                data = json.load(f)
                assert data["date"] == test_date
                assert data["total_active_users"] == 10

            with open(csv_file) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["User"] == "user1@example.com"
