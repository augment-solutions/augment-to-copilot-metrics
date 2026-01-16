"""
Augment Analytics to Copilot Metrics Converter

A tool to extract usage metrics from Augment's Analytics API and convert them
to GitHub Copilot Metrics API format.
"""

from .analytics_client import AnalyticsClient, AnalyticsAPIError, PaginationError
from .cli import main, parse_args, run_export
from .config import Config, get_config
from .http import AuthenticationError, HTTPClient, HTTPError, RateLimitError
from .token_auth import TokenAuth, TokenAuthError
from .transformer import MetricsTransformer, TransformationError

__version__ = "0.1.0"
__author__ = "Augment Solutions"
__license__ = "MIT"

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
    # Data Transformation
    "MetricsTransformer",
    "TransformationError",
    # CLI
    "main",
    "parse_args",
    "run_export",
]
