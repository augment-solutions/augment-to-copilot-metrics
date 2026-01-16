"""
Unit tests for CLI module.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from augment_metrics.cli import (
    parse_args,
    validate_date,
    get_date_range,
    setup_logging,
    ensure_output_dir,
    write_json_file,
    write_csv_file,
    run_export,
    main,
)


class TestParseArgs:
    """Tests for parse_args function."""
    
    def test_parse_args_last_28_days(self):
        """Test parsing --last-28-days argument."""
        args = parse_args(["--last-28-days"])
        assert args.last_28_days is True
        assert args.start_date is None
        assert args.end_date is None
    
    def test_parse_args_date_range(self):
        """Test parsing --start-date and --end-date arguments."""
        args = parse_args(["--start-date", "2026-01-01", "--end-date", "2026-01-31"])
        assert args.start_date == "2026-01-01"
        assert args.end_date == "2026-01-31"
        assert args.last_28_days is False
    
    def test_parse_args_output_dir(self):
        """Test parsing --output-dir argument."""
        args = parse_args(["--last-28-days", "--output-dir", "./custom"])
        assert args.output_dir == "./custom"
    
    def test_parse_args_aggregate(self):
        """Test parsing --aggregate argument."""
        args = parse_args(["--last-28-days", "--aggregate"])
        assert args.aggregate is True
    
    def test_parse_args_csv_only(self):
        """Test parsing --csv-only argument."""
        args = parse_args(["--last-28-days", "--csv-only"])
        assert args.csv_only is True
        assert args.json_only is False
    
    def test_parse_args_json_only(self):
        """Test parsing --json-only argument."""
        args = parse_args(["--last-28-days", "--json-only"])
        assert args.json_only is True
        assert args.csv_only is False
    
    def test_parse_args_verbose(self):
        """Test parsing --verbose argument."""
        args = parse_args(["--last-28-days", "--verbose"])
        assert args.verbose is True
    
    def test_parse_args_no_date_range_error(self):
        """Test error when no date range is provided."""
        with pytest.raises(SystemExit):
            parse_args([])
    
    def test_parse_args_start_date_without_end_date_error(self):
        """Test error when --start-date is provided without --end-date."""
        with pytest.raises(SystemExit):
            parse_args(["--start-date", "2026-01-01"])
    
    def test_parse_args_end_date_without_start_date_error(self):
        """Test error when --end-date is provided without --start-date."""
        with pytest.raises(SystemExit):
            parse_args(["--end-date", "2026-01-31"])
    
    def test_parse_args_csv_only_and_json_only_error(self):
        """Test error when both --csv-only and --json-only are provided."""
        with pytest.raises(SystemExit):
            parse_args(["--last-28-days", "--csv-only", "--json-only"])


class TestValidateDate:
    """Tests for validate_date function."""
    
    def test_validate_date_valid(self):
        """Test validation of valid date."""
        assert validate_date("2026-01-15") == "2026-01-15"
    
    def test_validate_date_invalid_format(self):
        """Test validation of invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2026-13-45")
    
    def test_validate_date_invalid_format_wrong_separator(self):
        """Test validation of date with wrong separator."""
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2026/01/15")


class TestGetDateRange:
    """Tests for get_date_range function."""
    
    def test_get_date_range_last_28_days(self):
        """Test getting date range for last 28 days."""
        args = argparse.Namespace(last_28_days=True, start_date=None, end_date=None)
        start_date, end_date = get_date_range(args)
        
        # Verify format
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        # Verify range is 28 days
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        assert (end - start).days == 27  # 28 days total including both dates
    
    def test_get_date_range_custom_range(self):
        """Test getting custom date range."""
        args = argparse.Namespace(
            last_28_days=False,
            start_date="2026-01-01",
            end_date="2026-01-31"
        )
        start_date, end_date = get_date_range(args)
        assert start_date == "2026-01-01"
        assert end_date == "2026-01-31"
    
    def test_get_date_range_start_after_end_error(self):
        """Test error when start date is after end date."""
        args = argparse.Namespace(
            last_28_days=False,
            start_date="2026-01-31",
            end_date="2026-01-01"
        )
        with pytest.raises(ValueError, match="Start date.*must be before"):
            get_date_range(args)


class TestEnsureOutputDir:
    """Tests for ensure_output_dir function."""

    def test_ensure_output_dir_creates_directory(self, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "test_output"
        assert not output_dir.exists()

        ensure_output_dir(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_ensure_output_dir_existing_directory(self, tmp_path):
        """Test that existing directory is not modified."""
        output_dir = tmp_path / "existing"
        output_dir.mkdir()

        ensure_output_dir(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()


class TestWriteJsonFile:
    """Tests for write_json_file function."""

    def test_write_json_file(self, tmp_path):
        """Test writing JSON file."""
        data = {"test": "data", "number": 42}
        filepath = tmp_path / "test.json"

        write_json_file(data, filepath)

        assert filepath.exists()
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data


class TestWriteCsvFile:
    """Tests for write_csv_file function."""

    def test_write_csv_file(self, tmp_path):
        """Test writing CSV file."""
        rows = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        filepath = tmp_path / "test.csv"

        write_csv_file(rows, filepath)

        assert filepath.exists()
        content = filepath.read_text()
        assert "name,age" in content
        assert "Alice,30" in content
        assert "Bob,25" in content

    def test_write_csv_file_empty_rows(self, tmp_path, caplog):
        """Test writing CSV file with empty rows."""
        filepath = tmp_path / "test.csv"

        write_csv_file([], filepath)

        assert not filepath.exists()
        assert "No data to write to CSV" in caplog.text


class TestRunExport:
    """Tests for run_export function."""

    @patch("augment_metrics.cli.AnalyticsClient")
    @patch("augment_metrics.cli.MetricsTransformer")
    def test_run_export_success(
        self,
        mock_transformer_class,
        mock_analytics_class,
        tmp_path,
        monkeypatch
    ):
        """Test successful export."""
        # Setup mocks
        mock_analytics = MagicMock()
        mock_analytics.fetch_user_activity.return_value = [
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
            }
        ]
        mock_analytics.fetch_dau_count.return_value = [{"active_user_count": 1}]
        mock_analytics_class.return_value = mock_analytics

        mock_transformer = MagicMock()
        mock_transformer.transform_user_metrics.return_value = {
            "date": "2026-01-01",
            "total_active_users": 1,
            "total_engaged_users": 1,
            "breakdown": []
        }
        mock_transformer.transform_to_csv_row.return_value = {
            "User": "alice@example.com",
            "Active Days": 5
        }
        mock_transformer_class.return_value = mock_transformer

        # Set environment variables
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-enterprise")
        monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))

        # Run export
        args = argparse.Namespace(
            last_28_days=False,
            start_date="2026-01-01",
            end_date="2026-01-01",
            output_dir=str(tmp_path),
            aggregate=False,
            csv_only=False,
            json_only=False,
            verbose=False
        )

        exit_code = run_export(args)

        assert exit_code == 0
        assert mock_analytics.fetch_user_activity.called
        assert mock_analytics.fetch_dau_count.called

