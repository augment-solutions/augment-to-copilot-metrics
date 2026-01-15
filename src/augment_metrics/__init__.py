"""
Augment Analytics to Copilot Metrics Converter

Convert Augment Analytics API metrics to GitHub Copilot Metrics API format.
"""

from .config import Config, get_config
from .http import HTTPClient, HTTPError, AuthenticationError, RateLimitError
from .token_auth import TokenAuth, TokenAuthError

__version__ = "0.1.0"
__author__ = "Augment Solutions"
__license__ = "MIT"

__all__ = [
    "Config",
    "get_config",
    "HTTPClient",
    "HTTPError",
    "AuthenticationError",
    "RateLimitError",
    "TokenAuth",
    "TokenAuthError",
]
