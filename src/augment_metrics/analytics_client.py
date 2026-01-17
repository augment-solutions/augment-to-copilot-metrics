"""
Analytics API Client for Augment Analytics API.

This module provides a client for interacting with the Augment Analytics API,
including support for cursor-based pagination and date parameter handling.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Iterator

from .http import HTTPClient, HTTPError, AuthenticationError, RateLimitError


logger = logging.getLogger(__name__)


class AnalyticsAPIError(Exception):
    """Base exception for Analytics API errors."""

    pass


class PaginationError(AnalyticsAPIError):
    """Exception raised when pagination fails."""

    pass


class AnalyticsClient:
    """
    Client for Augment Analytics API.

    Provides methods to fetch metrics from various Analytics API endpoints
    with support for cursor-based pagination and date filtering.

    Example:
        >>> client = AnalyticsClient(
        ...     api_token="your-token",
        ...     base_url="https://api.augmentcode.com"
        ... )
        >>>
        >>> # Fetch user activity for a specific date
        >>> activity = client.fetch_user_activity(date="2026-01-15")
        >>>
        >>> # Fetch daily usage metrics
        >>> usage = client.fetch_daily_usage(start_date="2026-01-01", end_date="2026-01-15")
    """

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.augmentcode.com",
        timeout: int = 60,
        max_retries: int = 3,
        page_size: Optional[int] = None,
    ):
        """
        Initialize Analytics API client.

        Args:
            api_token: Augment API token
            base_url: Base URL for Analytics API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            page_size: Number of items per page for paginated requests (None to use API default)
        """
        # Validate page_size if provided
        if page_size is not None and (not isinstance(page_size, int) or page_size <= 0):
            raise ValueError(f"page_size must be a positive integer or None, got {page_size}")

        self.page_size = page_size
        self.http_client = HTTPClient(
            api_token=api_token,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        logger.info("Initialized AnalyticsClient")

    def _validate_date(self, date_str: str) -> str:
        """
        Validate date string is in YYYY-MM-DD format.

        Args:
            date_str: Date string to validate

        Returns:
            Validated date string

        Raises:
            ValueError: If date format is invalid
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError as e:
            raise ValueError(
                f"Invalid date format '{date_str}'. Expected YYYY-MM-DD format."
            ) from e

    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Paginate through API responses using cursor-based pagination.

        Args:
            endpoint: API endpoint to call
            params: Query parameters

        Yields:
            Individual items from paginated response

        Raises:
            PaginationError: If pagination fails
        """
        if params is None:
            params = {}

        # Create a copy to avoid mutating the input
        request_params = params.copy()

        # Only add limit parameter if page_size is configured
        if self.page_size is not None:
            request_params["limit"] = self.page_size

        cursor = None
        page_num = 0

        while True:
            page_num += 1

            # Add cursor to params if we have one
            if cursor:
                request_params["cursor"] = cursor
            elif "cursor" in request_params:
                # Remove cursor from first request if it exists
                del request_params["cursor"]

            logger.debug(f"Fetching page {page_num} from {endpoint} (cursor: {cursor})")

            try:
                response = self.http_client.get(endpoint, params=request_params)
            except (HTTPError, AuthenticationError, RateLimitError) as e:
                raise PaginationError(f"Failed to fetch page {page_num}: {e}") from e

            # Validate response structure
            if not isinstance(response, dict):
                raise PaginationError(f"Invalid response type: expected dict, got {type(response)}")

            # Get data from response
            data = response.get("data", [])
            if not isinstance(data, list):
                raise PaginationError(f"Invalid data type: expected list, got {type(data)}")

            # Yield each item
            for item in data:
                yield item

            # Check if there are more pages
            pagination = response.get("pagination", {})
            if not isinstance(pagination, dict):
                raise PaginationError(
                    f"Invalid pagination type: expected dict, got {type(pagination)}"
                )

            cursor = pagination.get("next_cursor")

            logger.debug(f"Page {page_num}: {len(data)} items, next_cursor: {cursor}")

            # Stop if no more pages
            if not cursor:
                logger.info(f"Pagination complete: {page_num} pages fetched")
                break

    def fetch_user_activity(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch user activity metrics from /analytics/v0/user-activity endpoint.

        Returns per-user metrics including agent interactions, code edits, and tool usage.

        Args:
            date: Single date in YYYY-MM-DD format (mutually exclusive with start_date/end_date)
            start_date: Start date in YYYY-MM-DD format (requires end_date)
            end_date: End date in YYYY-MM-DD format (requires start_date)

        Returns:
            List of user activity records

        Raises:
            ValueError: If date parameters are invalid
            AnalyticsAPIError: If API request fails

        Example:
            >>> client = AnalyticsClient(api_token="token")
            >>>
            >>> # Fetch for a single date
            >>> activity = client.fetch_user_activity(date="2026-01-15")
            >>>
            >>> # Fetch for a date range
            >>> activity = client.fetch_user_activity(
            ...     start_date="2026-01-01",
            ...     end_date="2026-01-15"
            ... )
        """
        params = {}

        # Validate date parameters
        if date and (start_date or end_date):
            raise ValueError("Cannot specify both 'date' and 'start_date/end_date'")

        if (start_date and not end_date) or (end_date and not start_date):
            raise ValueError("Both 'start_date' and 'end_date' must be specified together")

        # Add date parameters
        if date:
            params["date"] = self._validate_date(date)
        elif start_date and end_date:
            params["start_date"] = self._validate_date(start_date)
            params["end_date"] = self._validate_date(end_date)

        logger.info(f"Fetching user activity: {params}")

        # Fetch all pages
        results = list(self._paginate("/analytics/v0/user-activity", params))

        logger.info(f"Fetched {len(results)} user activity records")
        return results

    def fetch_daily_usage(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily usage metrics from /analytics/v0/daily-usage endpoint.

        Returns organization-wide daily metrics aggregated across all users.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of daily usage records

        Raises:
            ValueError: If date parameters are invalid
            AnalyticsAPIError: If API request fails

        Example:
            >>> client = AnalyticsClient(api_token="token")
            >>> usage = client.fetch_daily_usage(
            ...     start_date="2026-01-01",
            ...     end_date="2026-01-15"
            ... )
        """
        params = {
            "start_date": self._validate_date(start_date),
            "end_date": self._validate_date(end_date),
        }

        logger.info(f"Fetching daily usage: {params}")

        # Fetch all pages
        results = list(self._paginate("/analytics/v0/daily-usage", params))

        logger.info(f"Fetched {len(results)} daily usage records")
        return results

    def fetch_dau_count(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily active user counts from /analytics/v0/dau-count endpoint.

        Returns the number of active users per day.

        Note: This endpoint has a different response structure than other endpoints.
        It returns {"daily_active_user_counts": [...], "metadata": {...}} instead of
        the standard {"data": [...], "pagination": {...}} format.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of DAU count records, each with "date" and "user_count" fields

        Raises:
            ValueError: If date parameters are invalid
            AnalyticsAPIError: If API request fails

        Example:
            >>> client = AnalyticsClient(api_token="token")
            >>> dau = client.fetch_dau_count(
            ...     start_date="2026-01-01",
            ...     end_date="2026-01-15"
            ... )
            >>> # Returns: [{"date": "2026-01-01", "user_count": 42}, ...]
        """
        params = {
            "start_date": self._validate_date(start_date),
            "end_date": self._validate_date(end_date),
        }

        logger.info(f"Fetching DAU count: {params}")

        # This endpoint doesn't use the standard pagination format
        # It returns {"daily_active_user_counts": [...], "metadata": {...}}
        try:
            response = self.http_client.get("/analytics/v0/dau-count", params=params)
        except (HTTPError, AuthenticationError, RateLimitError) as e:
            raise AnalyticsAPIError(f"Failed to fetch DAU count: {e}") from e

        # Validate response structure
        if not isinstance(response, dict):
            raise AnalyticsAPIError(f"Invalid response type: expected dict, got {type(response)}")

        # Extract the daily_active_user_counts array
        dau_counts = response.get("daily_active_user_counts", [])
        if not isinstance(dau_counts, list):
            raise AnalyticsAPIError(
                f"Invalid daily_active_user_counts type: expected list, got {type(dau_counts)}"
            )

        logger.info(f"Fetched {len(dau_counts)} DAU count records")
        return dau_counts

    def fetch_editor_language_breakdown(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch editor/language breakdown from /analytics/v0/daily-user-activity-by-editor-language.

        Returns per-user metrics broken down by editor and programming language.

        Args:
            date: Single date in YYYY-MM-DD format (mutually exclusive with start_date/end_date)
            start_date: Start date in YYYY-MM-DD format (requires end_date)
            end_date: End date in YYYY-MM-DD format (requires start_date)

        Returns:
            List of editor/language breakdown records

        Raises:
            ValueError: If date parameters are invalid
            AnalyticsAPIError: If API request fails

        Example:
            >>> client = AnalyticsClient(api_token="token")
            >>> breakdown = client.fetch_editor_language_breakdown(date="2026-01-15")
        """
        params = {}

        # Validate date parameters
        if date and (start_date or end_date):
            raise ValueError("Cannot specify both 'date' and 'start_date/end_date'")

        if (start_date and not end_date) or (end_date and not start_date):
            raise ValueError("Both 'start_date' and 'end_date' must be specified together")

        # Add date parameters
        if date:
            params["date"] = self._validate_date(date)
        elif start_date and end_date:
            params["start_date"] = self._validate_date(start_date)
            params["end_date"] = self._validate_date(end_date)

        logger.info(f"Fetching editor/language breakdown: {params}")

        # Fetch all pages
        results = list(
            self._paginate("/analytics/v0/daily-user-activity-by-editor-language", params)
        )

        logger.info(f"Fetched {len(results)} editor/language breakdown records")
        return results
