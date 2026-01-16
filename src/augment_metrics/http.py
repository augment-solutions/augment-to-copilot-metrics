"""
HTTP client for Augment Analytics API.

Handles Bearer token authentication, retries, and error handling.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class HTTPError(Exception):
    """Base exception for HTTP errors."""
    pass


class AuthenticationError(HTTPError):
    """Raised when authentication fails."""
    pass


class RateLimitError(HTTPError):
    """Raised when rate limit is exceeded."""
    pass


class HTTPClient:
    """
    HTTP client with Bearer token authentication and retry logic.
    
    Features:
    - Bearer token authentication
    - Automatic retries with exponential backoff
    - Request/response logging
    - Error handling
    
    Example:
        >>> client = HTTPClient(api_token="my-token", base_url="https://api.example.com")
        >>> response = client.get("/analytics/v0/user-activity")
        >>> print(response["users"])
    """
    
    def __init__(
        self,
        api_token: str,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ):
        """
        Initialize HTTP client.
        
        Args:
            api_token: Augment API token for Bearer authentication
            base_url: Base URL for API (e.g., "https://api.augmentcode.com")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_backoff: Initial backoff time for retries (exponential)
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        
        # Create session with retry strategy
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers including Bearer token.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request to API.
        
        Args:
            endpoint: API endpoint (e.g., "/analytics/v0/user-activity")
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            AuthenticationError: If authentication fails (401)
            RateLimitError: If rate limit exceeded (429)
            HTTPError: For other HTTP errors
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"GET {url} with params: {params}")
        
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout,
            )
            
            # Handle specific error codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your API token."
                )
            
            if response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded. Please try again later."
                )
            
            # Raise for other error status codes
            response.raise_for_status()
            
            logger.debug(f"Response status: {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise HTTPError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise HTTPError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise HTTPError(f"HTTP request failed: {e}")

