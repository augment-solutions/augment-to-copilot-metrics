"""
Tests for the __main__.py entry point.
"""

import sys
from unittest.mock import patch

import pytest


class TestMain:
    """Tests for the __main__ module entry point."""

    def test_main_module_exists(self):
        """Test that __main__.py module exists and can be imported."""
        import augment_metrics.__main__

        # Verify the module has the expected structure
        assert hasattr(augment_metrics.__main__, "main")

    def test_main_module_execution_with_help(self):
        """Test executing the module with --help flag."""
        # Simulate running: python -m augment_metrics --help
        with patch.object(sys, "argv", ["augment_metrics", "--help"]):
            try:
                import runpy

                runpy.run_module("augment_metrics", run_name="__main__")
            except SystemExit as e:
                # --help causes sys.exit(0)
                assert e.code == 0

    def test_main_module_execution_with_version(self):
        """Test executing the module with --version flag."""
        # Simulate running: python -m augment_metrics --version
        with patch.object(sys, "argv", ["augment_metrics", "--version"]):
            try:
                import runpy

                runpy.run_module("augment_metrics", run_name="__main__")
            except SystemExit as e:
                # --version causes sys.exit(0)
                assert e.code == 0
