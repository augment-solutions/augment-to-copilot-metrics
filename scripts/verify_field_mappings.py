#!/usr/bin/env python3
"""
Field Mapping Verification Script

This script helps verify that field mappings are correct by:
1. Fetching real data from the Augment Analytics API
2. Transforming it using our transformer
3. Showing the calculations step-by-step for manual verification

Usage:
    python scripts/verify_field_mappings.py --date 2026-01-15

Environment variables required:
    AUGMENT_API_TOKEN - Your Augment API token
    ANALYTICS_API_BASE_URL - (Optional) API base URL
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from augment_metrics.analytics_client import AnalyticsClient
from augment_metrics.transformer import MetricsTransformer


def verify_user_calculations(user_input: dict, user_output: dict) -> None:
    """
    Print step-by-step verification of field mappings for a single user.
    """
    metrics = user_input.get("metrics", {})
    
    print(f"\n{'='*80}")
    print(f"User: {user_input.get('user_email') or user_input.get('service_account_name')}")
    print(f"{'='*80}")
    
    # Direct mappings
    print("\n📋 DIRECT MAPPINGS:")
    print(f"  active_days: {user_input.get('active_days')} → {user_output['active_days']}")
    print(f"  completions_count: {metrics.get('completions_count', 0)} → code_generation_activity_count: {user_output['code_generation_activity_count']}")
    print(f"  completions_accepted: {metrics.get('completions_accepted', 0)} → code_acceptance_activity_count: {user_output['code_acceptance_activity_count']}")
    print(f"  total_modified_lines_of_code: {metrics.get('total_modified_lines_of_code', 0)} → loc_added_sum: {user_output['loc_added_sum']}")
    print(f"  chat_messages: {metrics.get('chat_messages', 0)} → chat_panel.user_initiated_interaction_count: {user_output['chat_panel']['user_initiated_interaction_count']}")
    print(f"  completions_lines_of_code: {metrics.get('completions_lines_of_code', 0)} → code_completions.loc_added_sum: {user_output['code_completions']['loc_added_sum']}")
    
    # Agent aggregations
    print("\n🤖 AGENT AGGREGATIONS:")
    
    # Interaction count
    remote_msgs = metrics.get('remote_agent_messages', 0)
    ide_msgs = metrics.get('ide_agent_messages', 0)
    cli_interactive_msgs = metrics.get('cli_agent_interactive_messages', 0)
    cli_non_interactive_msgs = metrics.get('cli_agent_non_interactive_messages', 0)
    
    print(f"\n  agent_edit.user_initiated_interaction_count:")
    print(f"    remote_agent_messages:              {remote_msgs:>6}")
    print(f"    ide_agent_messages:                 {ide_msgs:>6}")
    print(f"    cli_agent_interactive_messages:     {cli_interactive_msgs:>6}")
    print(f"    cli_agent_non_interactive_messages: {cli_non_interactive_msgs:>6}")
    print(f"    {'─'*45}")
    expected_interactions = remote_msgs + ide_msgs + cli_interactive_msgs + cli_non_interactive_msgs
    actual_interactions = user_output['agent_edit']['user_initiated_interaction_count']
    print(f"    TOTAL (expected):                   {expected_interactions:>6}")
    print(f"    TOTAL (actual):                     {actual_interactions:>6}")
    print(f"    ✅ MATCH" if expected_interactions == actual_interactions else f"    ❌ MISMATCH")
    
    # LOC
    remote_loc = metrics.get('remote_agent_lines_of_code', 0)
    ide_loc = metrics.get('ide_agent_lines_of_code', 0)
    cli_interactive_loc = metrics.get('cli_agent_interactive_lines_of_code', 0)
    cli_non_interactive_loc = metrics.get('cli_agent_non_interactive_lines_of_code', 0)
    
    print(f"\n  agent_edit.loc_added_sum:")
    print(f"    remote_agent_lines_of_code:              {remote_loc:>8}")
    print(f"    ide_agent_lines_of_code:                 {ide_loc:>8}")
    print(f"    cli_agent_interactive_lines_of_code:     {cli_interactive_loc:>8}")
    print(f"    cli_agent_non_interactive_lines_of_code: {cli_non_interactive_loc:>8}")
    print(f"    {'─'*53}")
    expected_loc = remote_loc + ide_loc + cli_interactive_loc + cli_non_interactive_loc
    actual_loc = user_output['agent_edit']['loc_added_sum']
    print(f"    TOTAL (expected):                        {expected_loc:>8}")
    print(f"    TOTAL (actual):                          {actual_loc:>8}")
    print(f"    ✅ MATCH" if expected_loc == actual_loc else f"    ❌ MISMATCH")


def main():
    parser = argparse.ArgumentParser(description="Verify field mappings against real API data")
    parser.add_argument("--date", help="Date to fetch (YYYY-MM-DD), defaults to yesterday")
    parser.add_argument("--user", help="Filter to specific user email")
    parser.add_argument("--limit", type=int, default=3, help="Max users to show (default: 3)")
    args = parser.parse_args()
    
    # Get date
    if args.date:
        date_str = args.date
    else:
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
    
    print(f"🔍 Verifying field mappings for date: {date_str}")
    print(f"{'='*80}\n")
    
    # Initialize client
    api_token = os.environ.get("AUGMENT_API_TOKEN")
    if not api_token:
        print("❌ Error: AUGMENT_API_TOKEN environment variable not set")
        sys.exit(1)
    
    client = AnalyticsClient(api_token=api_token)
    transformer = MetricsTransformer()
    
    # Fetch data
    print("📥 Fetching user activity from API...")
    try:
        user_activity = client.fetch_user_activity(date=date_str)
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        sys.exit(1)
    
    if not user_activity:
        print(f"⚠️  No user activity found for {date_str}")
        sys.exit(0)
    
    print(f"✅ Fetched {len(user_activity)} users\n")
    
    # Filter if requested
    if args.user:
        user_activity = [u for u in user_activity if u.get("user_email") == args.user]
        if not user_activity:
            print(f"❌ No data found for user: {args.user}")
            sys.exit(1)
    
    # Transform
    print("🔄 Transforming to Copilot format...")
    result = transformer.transform_user_metrics(user_activity, date_str)
    print("✅ Transformation complete\n")
    
    # Verify each user (up to limit)
    users_to_check = user_activity[:args.limit] if not args.user else user_activity
    
    for i, user_input in enumerate(users_to_check):
        user_output = result["breakdown"][i]
        verify_user_calculations(user_input, user_output)
    
    if len(user_activity) > args.limit and not args.user:
        print(f"\n... and {len(user_activity) - args.limit} more users")
        print(f"    (use --limit to see more, or --user to filter)")
    
    print(f"\n{'='*80}")
    print("✅ Verification complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

