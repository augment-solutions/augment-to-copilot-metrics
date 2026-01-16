"""
Unit tests for MetricsTransformer.
"""

import pytest
from augment_metrics.transformer import MetricsTransformer, TransformationError


class TestMetricsTransformer:
    """Tests for MetricsTransformer class."""
    
    def test_transform_user_metrics_basic(self):
        """Test basic user metrics transformation."""
        transformer = MetricsTransformer()
        
        user_activity = [
            {
                "user_email": "alice@example.com",
                "active_days": 5,
                "metrics": {
                    "total_modified_lines_of_code": 450,
                    "completions_count": 320,
                    "completions_accepted": 280,
                    "completions_lines_of_code": 350,
                    "chat_messages": 25,
                    "remote_agent_messages": 10,
                    "remote_agent_lines_of_code": 45,
                    "ide_agent_messages": 30,
                    "ide_agent_lines_of_code": 40,
                    "cli_agent_interactive_messages": 8,
                    "cli_agent_interactive_lines_of_code": 10,
                    "cli_agent_non_interactive_messages": 5,
                    "cli_agent_non_interactive_lines_of_code": 5,
                    "total_tool_calls": 120,
                    "total_messages": 65,
                }
            }
        ]
        
        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        
        # Check top-level fields
        assert result["date"] == "2026-01-15"
        assert result["total_active_users"] == 1
        assert result["total_engaged_users"] == 1
        
        # Check feature engagement
        assert result["copilot_ide_code_completions"]["total_engaged_users"] == 1
        assert result["copilot_ide_chat"]["total_engaged_users"] == 1
        assert result["copilot_dotcom_chat"]["total_engaged_users"] == 0
        assert result["copilot_dotcom_pull_requests"]["total_engaged_users"] == 0
        
        # Check breakdown
        assert len(result["breakdown"]) == 1
        user = result["breakdown"][0]
        
        assert user["user_email"] == "alice@example.com"
        assert user["active_days"] == 5
        assert user["code_generation_activity_count"] == 320
        assert user["code_acceptance_activity_count"] == 280
        assert user["loc_added_sum"] == 450
        assert user["chat_panel"]["user_initiated_interaction_count"] == 25
        
        # Check agent edit aggregation (10 + 30 + 8 + 5 = 53)
        assert user["agent_edit"]["user_initiated_interaction_count"] == 53
        
        # Check agent edit LOC aggregation (45 + 40 + 10 + 5 = 100)
        assert user["agent_edit"]["loc_added_sum"] == 100
        
        # Check code completions LOC
        assert user["code_completions"]["loc_added_sum"] == 350
    
    def test_transform_user_metrics_multiple_users(self):
        """Test transformation with multiple users."""
        transformer = MetricsTransformer()
        
        user_activity = [
            {
                "user_email": "alice@example.com",
                "active_days": 5,
                "metrics": {
                    "completions_count": 100,
                    "completions_accepted": 80,
                    "total_modified_lines_of_code": 200,
                    "chat_messages": 10,
                    "remote_agent_messages": 5,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "completions_lines_of_code": 150,
                    "remote_agent_lines_of_code": 20,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                }
            },
            {
                "user_email": "bob@example.com",
                "active_days": 3,
                "metrics": {
                    "completions_count": 50,
                    "completions_accepted": 40,
                    "total_modified_lines_of_code": 100,
                    "chat_messages": 5,
                    "remote_agent_messages": 0,
                    "ide_agent_messages": 10,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "completions_lines_of_code": 75,
                    "remote_agent_lines_of_code": 0,
                    "ide_agent_lines_of_code": 15,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                }
            }
        ]
        
        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        
        assert result["total_active_users"] == 2
        assert result["total_engaged_users"] == 2
        assert result["copilot_ide_code_completions"]["total_engaged_users"] == 2
        assert result["copilot_ide_chat"]["total_engaged_users"] == 2
        assert len(result["breakdown"]) == 2
        
        # Check first user
        alice = result["breakdown"][0]
        assert alice["user_email"] == "alice@example.com"
        assert alice["agent_edit"]["user_initiated_interaction_count"] == 5
        assert alice["agent_edit"]["loc_added_sum"] == 20
        
        # Check second user
        bob = result["breakdown"][1]
        assert bob["user_email"] == "bob@example.com"
        assert bob["agent_edit"]["user_initiated_interaction_count"] == 10
        assert bob["agent_edit"]["loc_added_sum"] == 15

    def test_transform_user_metrics_with_dau_count(self):
        """Test transformation with explicit DAU count."""
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "alice@example.com",
                "active_days": 1,
                "metrics": {
                    "completions_count": 10,
                    "completions_accepted": 8,
                    "total_modified_lines_of_code": 20,
                    "chat_messages": 2,
                    "remote_agent_messages": 0,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "completions_lines_of_code": 15,
                    "remote_agent_lines_of_code": 0,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                }
            }
        ]

        # DAU count is higher than breakdown (some users had no detailed activity)
        result = transformer.transform_user_metrics(user_activity, "2026-01-15", dau_count=5)

        assert result["total_active_users"] == 5
        assert result["total_engaged_users"] == 1
        assert len(result["breakdown"]) == 1

    def test_transform_user_metrics_service_account(self):
        """Test transformation with service account (no user_email)."""
        transformer = MetricsTransformer()

        user_activity = [
            {
                "service_account_name": "ci-bot",
                "active_days": 10,
                "metrics": {
                    "completions_count": 500,
                    "completions_accepted": 450,
                    "total_modified_lines_of_code": 1000,
                    "chat_messages": 0,
                    "remote_agent_messages": 100,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 50,
                    "completions_lines_of_code": 800,
                    "remote_agent_lines_of_code": 150,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 50,
                }
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")

        user = result["breakdown"][0]
        assert user["user_email"] == "ci-bot"
        assert user["active_days"] == 10
        assert user["agent_edit"]["user_initiated_interaction_count"] == 150  # 100 + 0 + 0 + 50
        assert user["agent_edit"]["loc_added_sum"] == 200  # 150 + 0 + 0 + 50

    def test_transform_user_metrics_invalid_date(self):
        """Test transformation with invalid date format."""
        transformer = MetricsTransformer()

        with pytest.raises(TransformationError, match="Invalid date format"):
            transformer.transform_user_metrics([], "2026-13-45")

    def test_transform_user_metrics_empty_list(self):
        """Test transformation with empty user list."""
        transformer = MetricsTransformer()

        result = transformer.transform_user_metrics([], "2026-01-15")

        assert result["total_active_users"] == 0
        assert result["total_engaged_users"] == 0
        assert result["copilot_ide_code_completions"]["total_engaged_users"] == 0
        assert result["copilot_ide_chat"]["total_engaged_users"] == 0
        assert len(result["breakdown"]) == 0

    def test_transform_user_metrics_missing_metrics(self):
        """Test transformation with missing metrics fields."""
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "alice@example.com",
                "active_days": 1,
                "metrics": {}  # Empty metrics
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")

        user = result["breakdown"][0]
        assert user["code_generation_activity_count"] == 0
        assert user["code_acceptance_activity_count"] == 0
        assert user["loc_added_sum"] == 0
        assert user["chat_panel"]["user_initiated_interaction_count"] == 0
        assert user["agent_edit"]["user_initiated_interaction_count"] == 0
        assert user["agent_edit"]["loc_added_sum"] == 0

    def test_transform_user_metrics_data_integrity_warning(self, caplog):
        """Test that data integrity issues trigger warnings."""
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "alice@example.com",
                "active_days": 1,
                "metrics": {
                    "completions_count": 100,
                    "completions_accepted": 150,  # More accepted than generated!
                    "total_modified_lines_of_code": 200,
                    "chat_messages": 0,
                    "remote_agent_messages": 0,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "completions_lines_of_code": 0,
                    "remote_agent_lines_of_code": 0,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                }
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")

        # Should still transform but log a warning
        assert result["breakdown"][0]["code_acceptance_activity_count"] == 150
        assert "code_acceptance_activity_count" in caplog.text

    def test_transform_to_csv_row(self):
        """Test CSV row transformation."""
        transformer = MetricsTransformer()

        user = {
            "user_email": "alice@example.com",
            "active_days": 5,
            "metrics": {
                "total_modified_lines_of_code": 450,
                "completions_count": 320,
                "completions_accepted": 280,
                "completions_lines_of_code": 350,
                "chat_messages": 25,
                "remote_agent_messages": 10,
                "remote_agent_lines_of_code": 45,
                "ide_agent_messages": 30,
                "ide_agent_lines_of_code": 40,
                "cli_agent_interactive_messages": 8,
                "cli_agent_interactive_lines_of_code": 10,
                "cli_agent_non_interactive_messages": 5,
                "cli_agent_non_interactive_lines_of_code": 5,
                "total_tool_calls": 120,
                "total_messages": 65,
            }
        }

        row = transformer.transform_to_csv_row(user)

        # Check all CSV columns
        assert row["User"] == "alice@example.com"
        assert row["Active Days"] == 5
        assert row["Completions"] == 320
        assert row["Accepted Completions"] == 280
        assert row["Chat Messages"] == 25
        assert row["Remote Agent Messages"] == 10
        assert row["IDE Agent Messages"] == 30
        assert row["CLI Interactive Messages"] == 8
        assert row["CLI Non-Interactive Messages"] == 5
        assert row["Total Tool Calls"] == 120
        assert row["Total Modified LOC"] == 450
        assert row["Completion LOC"] == 350
        assert row["Remote Agent LOC"] == 45
        assert row["IDE Agent LOC"] == 40
        assert row["CLI Agent LOC"] == 15  # 10 + 5
        assert row["Copilot Code Generation"] == 320
        assert row["Copilot Code Acceptance"] == 280
        assert row["Copilot Chat Interactions"] == 25
        assert row["Copilot Agent Interactions"] == 53  # 10 + 30 + 8 + 5

    def test_transform_to_csv_row_service_account(self):
        """Test CSV row transformation for service account."""
        transformer = MetricsTransformer()

        user = {
            "service_account_name": "ci-bot",
            "active_days": 10,
            "metrics": {
                "completions_count": 100,
                "completions_accepted": 90,
                "total_modified_lines_of_code": 200,
                "chat_messages": 0,
                "remote_agent_messages": 50,
                "ide_agent_messages": 0,
                "cli_agent_interactive_messages": 0,
                "cli_agent_non_interactive_messages": 25,
                "completions_lines_of_code": 150,
                "remote_agent_lines_of_code": 40,
                "ide_agent_lines_of_code": 0,
                "cli_agent_interactive_lines_of_code": 0,
                "cli_agent_non_interactive_lines_of_code": 10,
                "total_tool_calls": 200,
            }
        }

        row = transformer.transform_to_csv_row(user)

        assert row["User"] == "ci-bot"
        assert row["Copilot Agent Interactions"] == 75  # 50 + 0 + 0 + 25
        assert row["CLI Agent LOC"] == 10  # 0 + 10

