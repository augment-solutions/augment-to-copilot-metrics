"""
Augment Analytics to Copilot Metrics Converter

A tool to extract usage metrics from Augment's Analytics API and convert them
to GitHub Copilot Metrics API format.
"""

from .config import Config, get_config
from .http import HTTPClient, HTTPError, AuthenticationError, RateLimitError
from .token_auth import TokenAuth, TokenAuthError
from .analytics_client import (
    AnalyticsClient,
    AnalyticsAPIError,
    PaginationError,
)

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "Config",
    "get_config",
    # HTTP Client
    "HTTPClient",
    "HTTPError",
    "AuthenticationError",
    "RateLimitError",
    # Token Authentication
    "TokenAuth",
    "TokenAuthError",
    # Analytics API Client
    "AnalyticsClient",
    "AnalyticsAPIError",
    "PaginationError",
]
