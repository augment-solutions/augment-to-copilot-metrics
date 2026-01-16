"""
Command-line interface for Augment Analytics to Copilot Metrics converter.

This module provides the CLI for exporting Augment Analytics metrics
to GitHub Copilot Metrics API format.
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .analytics_client import AnalyticsClient, AnalyticsAPIError
from .config import Config, get_config
from .http import HTTPError, AuthenticationError, RateLimitError
from .transformer import MetricsTransformer, TransformationError

logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="augment-metrics",
        description="Export Augment Analytics metrics to GitHub Copilot Metrics format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export last 28 days
  augment-metrics --last-28-days
  
  # Export specific date range
  augment-metrics --start-date 2025-01-01 --end-date 2025-01-31
  
  # Export with aggregation
  augment-metrics --last-28-days --aggregate
  
  # Export to custom directory
  augment-metrics --last-28-days --output-dir ./metrics

Environment Variables:
  AUGMENT_API_TOKEN    API token from Augment service account
  ENTERPRISE_ID        Your Augment enterprise ID
  OUTPUT_DIR           Output directory (default: ./data)
  LOG_LEVEL            Logging level (default: INFO)
        """
    )
    
    # Date range options (mutually exclusive)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--last-28-days",
        action="store_true",
        help="Export metrics for the last 28 days"
    )
    date_group.add_argument(
        "--start-date",
        type=str,
        metavar="YYYY-MM-DD",
        help="Start date for export (requires --end-date)"
    )
    
    # End date (required if start-date is provided)
    parser.add_argument(
        "--end-date",
        type=str,
        metavar="YYYY-MM-DD",
        help="End date for export (requires --start-date)"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        metavar="DIR",
        help="Output directory (default: from OUTPUT_DIR env var or ./data)"
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Generate aggregated JSON file combining all days"
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only generate CSV output (skip JSON files)"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only generate JSON output (skip CSV file)"
    )
    
    # Other options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parsed = parser.parse_args(args)
    
    # Validate date arguments
    if parsed.start_date and not parsed.end_date:
        parser.error("--start-date requires --end-date")
    if parsed.end_date and not parsed.start_date:
        parser.error("--end-date requires --start-date")
    
    # Validate mutually exclusive output options
    if parsed.csv_only and parsed.json_only:
        parser.error("--csv-only and --json-only are mutually exclusive")
    
    return parsed


def validate_date(date_str: str) -> str:
    """
    Validate date format and return normalized date string.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Validated date string

    Raises:
        ValueError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}': must be YYYY-MM-DD") from e


def get_date_range(args: argparse.Namespace) -> tuple[str, str]:
    """
    Get start and end dates from arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format

    Raises:
        ValueError: If dates are invalid
    """
    if args.last_28_days:
        # Calculate last 28 days (ending yesterday to avoid partial data)
        end_date = datetime.now().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=27)  # 28 days total including end_date
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    else:
        # Validate provided dates
        start_date = validate_date(args.start_date)
        end_date = validate_date(args.end_date)

        # Ensure start <= end
        if start_date > end_date:
            raise ValueError(f"Start date ({start_date}) must be before or equal to end date ({end_date})")

        return start_date, end_date


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging based on verbosity level.

    Args:
        verbose: If True, set DEBUG level; otherwise use config level
    """
    config = get_config()
    level = logging.DEBUG if verbose else config.log_level

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def ensure_output_dir(output_dir: Path) -> None:
    """
    Ensure output directory exists.

    Args:
        output_dir: Path to output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir.absolute()}")


def write_json_file(data: dict, filepath: Path) -> None:
    """
    Write data to JSON file.

    Args:
        data: Data to write
        filepath: Path to output file
    """
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Wrote JSON: {filepath}")


def write_csv_file(rows: List[dict], filepath: Path) -> None:
    """
    Write data to CSV file.

    Args:
        rows: List of row dictionaries
        filepath: Path to output file
    """
    if not rows:
        logger.warning("No data to write to CSV")
        return

    fieldnames = rows[0].keys()
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"Wrote CSV: {filepath} ({len(rows)} rows)")


def run_export(args: argparse.Namespace) -> int:
    """
    Run the metrics export.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Setup
        setup_logging(args.verbose)
        config = get_config()

        # Override output dir if provided
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = config.output_dir

        ensure_output_dir(output_dir)

        # Get date range
        start_date, end_date = get_date_range(args)
        logger.info(f"Exporting metrics from {start_date} to {end_date}")

        # Initialize clients
        logger.info("Initializing API client...")

        # Get API token and enterprise ID from config
        api_token = config.augment_api_token
        enterprise_id = config.enterprise_id

        # Initialize Analytics client
        analytics_client = AnalyticsClient(
            api_token=api_token,
            enterprise_id=enterprise_id,
            base_url=config.analytics_api_base_url,
            timeout=config.request_timeout_seconds,
            max_retries=config.max_retries,
        )
        transformer = MetricsTransformer()

        logger.info(f"Connected to {config.analytics_api_base_url} (Enterprise: {enterprise_id})")

        # Fetch and transform data
        logger.info("Fetching user activity data...")
        user_activity = analytics_client.fetch_user_activity(
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Fetched data for {len(user_activity)} users")

        # Fetch DAU count for the date range
        logger.info("Fetching DAU count...")
        dau_data = analytics_client.fetch_dau_count(
            start_date=start_date,
            end_date=end_date
        )

        # For simplicity, use the first DAU count if available
        dau_count = dau_data[0]["active_user_count"] if dau_data else None

        # Transform to Copilot format
        logger.info("Transforming metrics to Copilot format...")
        copilot_data = transformer.transform_user_metrics(
            user_activity,
            start_date,  # Use start_date as the primary date
            dau_count=dau_count
        )

        # Generate outputs
        if not args.csv_only:
            # Write JSON file
            json_filename = f"copilot_metrics_{start_date}_to_{end_date}.json"
            json_filepath = output_dir / json_filename
            write_json_file(copilot_data, json_filepath)

        if not args.json_only:
            # Write CSV file
            csv_rows = [transformer.transform_to_csv_row(user) for user in user_activity]
            csv_filename = f"augment_metrics_{start_date}_to_{end_date}.csv"
            csv_filepath = output_dir / csv_filename
            write_csv_file(csv_rows, csv_filepath)

        # Success message
        print(f"\n✅ Export complete!")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   Users: {len(user_activity)}")
        print(f"   Output: {output_dir.absolute()}")

        return 0

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        print(f"\n❌ Authentication Error: {e}", file=sys.stderr)
        print("   Please check your AUGMENT_API_TOKEN and ENTERPRISE_ID", file=sys.stderr)
        return 1

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        print(f"\n❌ Rate Limit Error: {e}", file=sys.stderr)
        print("   Please try again later or reduce the date range", file=sys.stderr)
        return 1

    except HTTPError as e:
        logger.error(f"HTTP error: {e}")
        print(f"\n❌ HTTP Error: {e}", file=sys.stderr)
        return 1

    except TransformationError as e:
        logger.error(f"Transformation error: {e}")
        print(f"\n❌ Data Transformation Error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"\n❌ Validation Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.exception("Unexpected error during export")
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        print("   Run with --verbose for more details", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code
    """
    args = parse_args()
    return run_export(args)


if __name__ == "__main__":
    sys.exit(main())

