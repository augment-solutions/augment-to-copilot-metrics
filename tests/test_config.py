"""
Unit tests for configuration management.
"""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from augment_metrics.config import Config, get_config


class TestConfig:
    """Tests for Config class."""

    def test_config_from_env_vars(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token-123")
        monkeypatch.setenv("ENTERPRISE_ID", "test-enterprise-456")

        config = Config()

        assert config.augment_api_token == "test-token-123"
        assert config.enterprise_id == "test-enterprise-456"
        assert config.analytics_api_base_url == "https://api.augmentcode.com"
        assert config.log_level == "INFO"

    def test_config_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(_env_file=None)

        errors = exc_info.value.errors()
        field_names = {error["loc"][0] for error in errors}
        assert "augment_api_token" in field_names
        assert "enterprise_id" in field_names

    def test_config_custom_values(self, monkeypatch):
        """Test config with custom values."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "custom-token")
        monkeypatch.setenv("ENTERPRISE_ID", "custom-id")
        monkeypatch.setenv("ANALYTICS_API_BASE_URL", "https://custom.api.com")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "60")
        monkeypatch.setenv("MAX_RETRIES", "5")

        config = Config()

        assert config.analytics_api_base_url == "https://custom.api.com"
        assert config.log_level == "DEBUG"
        assert config.request_timeout_seconds == 60
        assert config.max_retries == 5

    def test_config_invalid_log_level(self, monkeypatch):
        """Test that invalid log level raises validation error."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-id")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError) as exc_info:
            Config()

        assert "log_level" in str(exc_info.value)

    def test_config_api_url_trailing_slash(self, monkeypatch):
        """Test that trailing slash is removed from API URL."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-id")
        monkeypatch.setenv("ANALYTICS_API_BASE_URL", "https://api.example.com/")

        config = Config()

        assert config.analytics_api_base_url == "https://api.example.com"

    def test_config_output_dir_creation(self, monkeypatch, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "test_output"

        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-id")
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))

        config = Config()

        assert config.output_dir == output_dir
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_get_credentials_path(self, monkeypatch):
        """Test getting credentials path."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-id")

        config = Config()
        creds_path = config.get_credentials_path()

        assert creds_path == Path.home() / ".augment" / "credentials"

    def test_get_config_singleton(self, monkeypatch):
        """Test that get_config returns singleton instance."""
        monkeypatch.setenv("AUGMENT_API_TOKEN", "test-token")
        monkeypatch.setenv("ENTERPRISE_ID", "test-id")

        # Clear global config
        import augment_metrics.config

        augment_metrics.config._config = None

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
