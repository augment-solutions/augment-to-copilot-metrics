"""
Configuration management for Augment Metrics.

Uses Pydantic Settings for type-safe configuration from environment variables.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Configuration can be provided via:
    1. Environment variables
    2. .env file in the current directory
    3. .env file in the project root

    Example:
        >>> config = Config()
        >>> print(config.augment_api_token)
        'your-token-here'
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required: API Authentication
    augment_api_token: str = Field(
        ...,
        description="Augment API token from service account",
        min_length=1,
    )

    # Optional: API Configuration
    analytics_api_base_url: str = Field(
        default="https://api.augmentcode.com",
        description="Base URL for Augment Analytics API",
    )

    # Optional: Output Configuration
    output_dir: Path = Field(
        default=Path("./data"),
        description="Directory for output files",
    )

    # Optional: Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Optional: Timezone
    timezone: str = Field(
        default="UTC",
        description="Timezone for date handling",
    )

    # Optional: HTTP Settings
    request_timeout_seconds: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        ge=1,
        le=300,
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of HTTP request retries",
        ge=0,
        le=10,
    )

    retry_backoff_seconds: float = Field(
        default=0.5,
        description="Initial backoff time for retries (exponential)",
        ge=0.1,
        le=10.0,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("analytics_api_base_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Ensure API URL doesn't have trailing slash."""
        return v.rstrip("/")

    def get_credentials_path(self) -> Path:
        """
        Get the path to the credentials file.

        Returns:
            Path to ~/.augment/credentials
        """
        creds_dir = Path.home() / ".augment"
        creds_dir.mkdir(parents=True, exist_ok=True)
        return creds_dir / "credentials"


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    This function lazy-loads the configuration on first access.
    Subsequent calls return the same instance.

    Returns:
        Config: The global configuration instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
