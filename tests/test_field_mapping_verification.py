"""
Field Mapping Verification Tests

These tests verify that the transformer correctly implements the field mappings
documented in docs/FIELD_MAPPING.md. Each test validates a specific mapping
with explicit calculations to ensure correctness.
"""

import pytest
from augment_metrics.transformer import MetricsTransformer


class TestFieldMappingVerification:
    """
    Verify that all field mappings match the documentation.
    
    These tests use the exact example from docs/FIELD_MAPPING.md to ensure
    the code matches the documented behavior.
    """

    def test_complete_user_breakdown_example(self):
        """
        Test the complete example from docs/FIELD_MAPPING.md.
        
        This uses the exact input/output from the documentation to verify
        all field mappings are correct.
        """
        transformer = MetricsTransformer()

        # This is the EXACT input from docs/FIELD_MAPPING.md Example 1
        user_activity = [
            {
                "user_email": "benperlmutter@augmentcode.com",
                "active_days": 11,
                "metrics": {
                    "completions_count": 12,
                    "completions_accepted": 2,
                    "completions_lines_of_code": 2,
                    "chat_messages": 3,
                    "remote_agent_messages": 100,
                    "remote_agent_lines_of_code": 15000,
                    "ide_agent_messages": 120,
                    "ide_agent_lines_of_code": 12000,
                    "cli_agent_interactive_messages": 20,
                    "cli_agent_interactive_lines_of_code": 1500,
                    "cli_agent_non_interactive_messages": 4,
                    "cli_agent_non_interactive_lines_of_code": 440,
                    "total_modified_lines_of_code": 28942,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Verify each field matches the documented output
        assert user["user_email"] == "benperlmutter@augmentcode.com"
        assert user["active_days"] == 11
        assert user["code_generation_activity_count"] == 12
        assert user["code_acceptance_activity_count"] == 2
        assert user["loc_added_sum"] == 28942
        assert user["chat_panel"]["user_initiated_interaction_count"] == 3

        # Verify agent_edit.user_initiated_interaction_count calculation
        # Documentation: 100 + 120 + 20 + 4 = 244
        expected_agent_interactions = 100 + 120 + 20 + 4
        assert user["agent_edit"]["user_initiated_interaction_count"] == 244
        assert user["agent_edit"]["user_initiated_interaction_count"] == expected_agent_interactions

        # Verify agent_edit.loc_added_sum calculation
        # Documentation: 15,000 + 12,000 + 1,500 + 440 = 28,940
        expected_agent_loc = 15000 + 12000 + 1500 + 440
        assert user["agent_edit"]["loc_added_sum"] == 28940
        assert user["agent_edit"]["loc_added_sum"] == expected_agent_loc

        # Verify code_completions.loc_added_sum
        assert user["code_completions"]["loc_added_sum"] == 2

    def test_direct_field_mappings(self):
        """
        Verify all direct field mappings (no calculations).
        
        Tests the mappings documented in the "Direct Mappings" section.
        """
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "test@example.com",
                "active_days": 7,
                "metrics": {
                    "completions_count": 100,
                    "completions_accepted": 85,
                    "total_modified_lines_of_code": 500,
                    "completions_lines_of_code": 400,
                    "chat_messages": 15,
                    "remote_agent_messages": 0,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "remote_agent_lines_of_code": 0,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Direct mappings from docs/FIELD_MAPPING.md
        assert user["user_email"] == "test@example.com"  # user_email → user_email
        assert user["active_days"] == 7  # active_days → active_days
        assert user["code_generation_activity_count"] == 100  # completions_count → code_generation_activity_count
        assert user["code_acceptance_activity_count"] == 85  # completions_accepted → code_acceptance_activity_count
        assert user["loc_added_sum"] == 500  # total_modified_lines_of_code → loc_added_sum
        assert user["chat_panel"]["user_initiated_interaction_count"] == 15  # chat_messages → chat_panel.user_initiated_interaction_count
        assert user["code_completions"]["loc_added_sum"] == 400  # completions_lines_of_code → code_completions.loc_added_sum

    def test_agent_edit_interaction_count_aggregation(self):
        """
        Verify agent_edit.user_initiated_interaction_count aggregation formula.
        
        Formula from docs:
        remote_agent_messages + ide_agent_messages + 
        cli_agent_interactive_messages + cli_agent_non_interactive_messages
        """
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "test@example.com",
                "active_days": 1,
                "metrics": {
                    "remote_agent_messages": 10,
                    "ide_agent_messages": 20,
                    "cli_agent_interactive_messages": 5,
                    "cli_agent_non_interactive_messages": 3,
                    "total_modified_lines_of_code": 0,
                    "completions_count": 0,
                    "completions_accepted": 0,
                    "completions_lines_of_code": 0,
                    "chat_messages": 0,
                    "remote_agent_lines_of_code": 0,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Verify the formula: 10 + 20 + 5 + 3 = 38
        expected = 10 + 20 + 5 + 3
        assert user["agent_edit"]["user_initiated_interaction_count"] == 38
        assert user["agent_edit"]["user_initiated_interaction_count"] == expected

    def test_agent_edit_loc_added_sum_aggregation(self):
        """
        Verify agent_edit.loc_added_sum aggregation formula.

        Formula from docs:
        remote_agent_lines_of_code + ide_agent_lines_of_code +
        cli_agent_interactive_lines_of_code + cli_agent_non_interactive_lines_of_code
        """
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "test@example.com",
                "active_days": 1,
                "metrics": {
                    "remote_agent_lines_of_code": 1000,
                    "ide_agent_lines_of_code": 2000,
                    "cli_agent_interactive_lines_of_code": 500,
                    "cli_agent_non_interactive_lines_of_code": 250,
                    "total_modified_lines_of_code": 3750,
                    "completions_count": 0,
                    "completions_accepted": 0,
                    "completions_lines_of_code": 0,
                    "chat_messages": 0,
                    "remote_agent_messages": 0,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Verify the formula: 1000 + 2000 + 500 + 250 = 3750
        expected = 1000 + 2000 + 500 + 250
        assert user["agent_edit"]["loc_added_sum"] == 3750
        assert user["agent_edit"]["loc_added_sum"] == expected

    def test_all_agent_types_contribute_to_aggregation(self):
        """
        Verify that ALL 4 agent types contribute to both aggregations.

        This test ensures we're not missing any agent type in the calculations.
        """
        transformer = MetricsTransformer()

        # Test with each agent type having a unique value
        user_activity = [
            {
                "user_email": "test@example.com",
                "active_days": 1,
                "metrics": {
                    "remote_agent_messages": 1,
                    "ide_agent_messages": 2,
                    "cli_agent_interactive_messages": 4,
                    "cli_agent_non_interactive_messages": 8,
                    "remote_agent_lines_of_code": 10,
                    "ide_agent_lines_of_code": 20,
                    "cli_agent_interactive_lines_of_code": 40,
                    "cli_agent_non_interactive_lines_of_code": 80,
                    "total_modified_lines_of_code": 150,
                    "completions_count": 0,
                    "completions_accepted": 0,
                    "completions_lines_of_code": 0,
                    "chat_messages": 0,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Verify all 4 agent message types are summed: 1 + 2 + 4 + 8 = 15
        assert user["agent_edit"]["user_initiated_interaction_count"] == 15

        # Verify all 4 agent LOC types are summed: 10 + 20 + 40 + 80 = 150
        assert user["agent_edit"]["loc_added_sum"] == 150

    def test_service_account_name_mapping(self):
        """
        Verify that service_account_name maps to user_email when user_email is missing.

        From docs: "user_email or service_account_name"
        """
        transformer = MetricsTransformer()

        user_activity = [
            {
                "service_account_name": "ci-bot",
                "active_days": 5,
                "metrics": {
                    "completions_count": 100,
                    "completions_accepted": 90,
                    "total_modified_lines_of_code": 200,
                    "completions_lines_of_code": 150,
                    "chat_messages": 0,
                    "remote_agent_messages": 10,
                    "ide_agent_messages": 0,
                    "cli_agent_interactive_messages": 0,
                    "cli_agent_non_interactive_messages": 0,
                    "remote_agent_lines_of_code": 50,
                    "ide_agent_lines_of_code": 0,
                    "cli_agent_interactive_lines_of_code": 0,
                    "cli_agent_non_interactive_lines_of_code": 0,
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Verify service_account_name is used when user_email is missing
        assert user["user_email"] == "ci-bot"

    def test_missing_fields_default_to_zero(self):
        """
        Verify that missing Augment fields default to 0 in calculations.

        From docs: "If a field is missing in Augment response, default to 0"
        """
        transformer = MetricsTransformer()

        user_activity = [
            {
                "user_email": "test@example.com",
                "active_days": 1,
                "metrics": {
                    # Only provide some fields, others should default to 0
                    "completions_count": 50,
                    "chat_messages": 10,
                    # Missing: all agent fields, completions_accepted, etc.
                },
            }
        ]

        result = transformer.transform_user_metrics(user_activity, "2026-01-15")
        user = result["breakdown"][0]

        # Fields with values
        assert user["code_generation_activity_count"] == 50
        assert user["chat_panel"]["user_initiated_interaction_count"] == 10

        # Missing fields should default to 0
        assert user["code_acceptance_activity_count"] == 0
        assert user["loc_added_sum"] == 0
        assert user["agent_edit"]["user_initiated_interaction_count"] == 0
        assert user["agent_edit"]["loc_added_sum"] == 0
        assert user["code_completions"]["loc_added_sum"] == 0

