"""
Data transformation from Augment Analytics API to GitHub Copilot Metrics format.

This module handles the conversion of Augment metrics to Copilot-compatible format,
including field mapping, aggregation, and validation.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TransformationError(Exception):
    """Exception raised when data transformation fails."""
    pass


class MetricsTransformer:
    """
    Transform Augment Analytics metrics to GitHub Copilot Metrics format.
    
    Handles:
    - User-level metrics transformation
    - Organization-level aggregation
    - Field mapping per docs/FIELD_MAPPING.md
    - Service account handling
    - Data validation
    
    Example:
        >>> transformer = MetricsTransformer()
        >>> user_data = [{"user_email": "alice@example.com", "metrics": {...}}]
        >>> copilot_data = transformer.transform_user_metrics(user_data, "2026-01-15")
    """
    
    def transform_user_metrics(
        self,
        user_activity: List[Dict[str, Any]],
        date_str: str,
        dau_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Transform user activity data to Copilot metrics format.
        
        Args:
            user_activity: List of user activity records from Analytics API
            date_str: Date in YYYY-MM-DD format
            dau_count: Optional daily active user count
            
        Returns:
            Dictionary in Copilot Metrics API format
            
        Raises:
            TransformationError: If transformation fails
        """
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            raise TransformationError(f"Invalid date format '{date_str}': {e}")
        
        # Transform individual user records
        breakdown = []
        total_engaged_users = 0
        code_completions_engaged = 0
        chat_engaged = 0
        
        for user in user_activity:
            user_metrics = self._transform_user_record(user)
            breakdown.append(user_metrics)
            
            # Count engaged users (users with any activity)
            if self._is_user_engaged(user_metrics):
                total_engaged_users += 1
            
            # Count users engaged with specific features
            if user_metrics.get("code_generation_activity_count", 0) > 0:
                code_completions_engaged += 1
            if user_metrics.get("chat_panel", {}).get("user_initiated_interaction_count", 0) > 0:
                chat_engaged += 1
        
        # Use provided DAU count or fall back to breakdown length
        total_active_users = dau_count if dau_count is not None else len(breakdown)
        
        # Validate data integrity
        if total_active_users < total_engaged_users:
            logger.warning(
                f"total_active_users ({total_active_users}) < total_engaged_users ({total_engaged_users}). "
                f"Setting total_active_users = total_engaged_users"
            )
            total_active_users = total_engaged_users
        
        return {
            "date": date_str,
            "total_active_users": total_active_users,
            "total_engaged_users": total_engaged_users,
            "copilot_ide_code_completions": {
                "total_engaged_users": code_completions_engaged,
                "languages": [],
                "editors": []
            },
            "copilot_ide_chat": {
                "total_engaged_users": chat_engaged,
                "editors": []
            },
            "copilot_dotcom_chat": {
                "total_engaged_users": 0,
                "models": []
            },
            "copilot_dotcom_pull_requests": {
                "total_engaged_users": 0,
                "repositories": []
            },
            "breakdown": breakdown
        }
    
    def _transform_user_record(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a single user activity record.
        
        Args:
            user: User activity record from Analytics API
            
        Returns:
            User metrics in Copilot format
        """
        metrics = user.get("metrics", {})
        
        # Calculate agent edit interactions (sum of all agent messages)
        agent_interactions = (
            metrics.get("remote_agent_messages", 0) +
            metrics.get("ide_agent_messages", 0) +
            metrics.get("cli_agent_interactive_messages", 0) +
            metrics.get("cli_agent_non_interactive_messages", 0)
        )
        
        # Calculate agent edit LOC (sum of all agent LOC)
        agent_loc = (
            metrics.get("remote_agent_lines_of_code", 0) +
            metrics.get("ide_agent_lines_of_code", 0) +
            metrics.get("cli_agent_interactive_lines_of_code", 0) +
            metrics.get("cli_agent_non_interactive_lines_of_code", 0)
        )

        # Build user record in Copilot format
        user_record = {
            "user_email": user.get("user_email") or user.get("service_account_name"),
            "active_days": user.get("active_days", 0),
            "code_generation_activity_count": metrics.get("completions_count", 0),
            "code_acceptance_activity_count": metrics.get("completions_accepted", 0),
            "loc_added_sum": metrics.get("total_modified_lines_of_code", 0),
            "chat_panel": {
                "user_initiated_interaction_count": metrics.get("chat_messages", 0)
            },
            "agent_edit": {
                "user_initiated_interaction_count": agent_interactions,
                "loc_added_sum": agent_loc
            },
            "code_completions": {
                "loc_added_sum": metrics.get("completions_lines_of_code", 0)
            }
        }

        # Validate data integrity
        if user_record["code_acceptance_activity_count"] > user_record["code_generation_activity_count"]:
            logger.warning(
                f"User {user_record['user_email']}: code_acceptance_activity_count "
                f"({user_record['code_acceptance_activity_count']}) > code_generation_activity_count "
                f"({user_record['code_generation_activity_count']})"
            )

        return user_record

    def _is_user_engaged(self, user_metrics: Dict[str, Any]) -> bool:
        """
        Determine if a user is engaged (has any activity).

        Args:
            user_metrics: User metrics in Copilot format

        Returns:
            True if user has any activity, False otherwise
        """
        return (
            user_metrics.get("code_generation_activity_count", 0) > 0 or
            user_metrics.get("chat_panel", {}).get("user_initiated_interaction_count", 0) > 0 or
            user_metrics.get("agent_edit", {}).get("user_initiated_interaction_count", 0) > 0
        )

    def transform_to_csv_row(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform user metrics to CSV row format with all Augment fields.

        Args:
            user: User activity record from Analytics API

        Returns:
            Dictionary with CSV column names and values
        """
        metrics = user.get("metrics", {})

        # Calculate Copilot-format fields
        agent_interactions = (
            metrics.get("remote_agent_messages", 0) +
            metrics.get("ide_agent_messages", 0) +
            metrics.get("cli_agent_interactive_messages", 0) +
            metrics.get("cli_agent_non_interactive_messages", 0)
        )

        cli_agent_loc = (
            metrics.get("cli_agent_interactive_lines_of_code", 0) +
            metrics.get("cli_agent_non_interactive_lines_of_code", 0)
        )

        return {
            "User": user.get("user_email") or user.get("service_account_name", ""),
            "Active Days": user.get("active_days", 0),
            "Completions": metrics.get("completions_count", 0),
            "Accepted Completions": metrics.get("completions_accepted", 0),
            "Chat Messages": metrics.get("chat_messages", 0),
            "Remote Agent Messages": metrics.get("remote_agent_messages", 0),
            "IDE Agent Messages": metrics.get("ide_agent_messages", 0),
            "CLI Interactive Messages": metrics.get("cli_agent_interactive_messages", 0),
            "CLI Non-Interactive Messages": metrics.get("cli_agent_non_interactive_messages", 0),
            "Total Tool Calls": metrics.get("total_tool_calls", 0),
            "Total Modified LOC": metrics.get("total_modified_lines_of_code", 0),
            "Completion LOC": metrics.get("completions_lines_of_code", 0),
            "Remote Agent LOC": metrics.get("remote_agent_lines_of_code", 0),
            "IDE Agent LOC": metrics.get("ide_agent_lines_of_code", 0),
            "CLI Agent LOC": cli_agent_loc,
            "Copilot Code Generation": metrics.get("completions_count", 0),
            "Copilot Code Acceptance": metrics.get("completions_accepted", 0),
            "Copilot Chat Interactions": metrics.get("chat_messages", 0),
            "Copilot Agent Interactions": agent_interactions,
        }

