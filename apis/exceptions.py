"""
Custom exception hierarchy for marine API clients.

This module defines specific exceptions for different error scenarios,
replacing generic Exception usage throughout the codebase.

Note: These exceptions inherit from the main application's APIError hierarchy
defined in app_modules.exceptions for consistency across the codebase.
"""

from app_modules.exceptions import APIError


class MarineAPIError(APIError):
    """Base exception for all marine API related errors.

    Inherits from app_modules.exceptions.APIError for consistency.
    """

    pass


class APIConnectionError(MarineAPIError):
    """Raised when unable to connect to an API."""

    pass


class APIRequestError(MarineAPIError):
    """Raised when an API request fails."""

    pass


class APIResponseError(MarineAPIError):
    """Raised when an API returns an invalid or unexpected response."""

    pass


class APIRateLimitError(MarineAPIError):
    """Raised when API rate limit is exceeded."""

    pass


class APITimeoutError(MarineAPIError):
    """Raised when an API request times out."""

    pass


class DataValidationError(MarineAPIError):
    """Raised when data validation fails."""

    pass


class DatasetNotFoundError(MarineAPIError):
    """Raised when a requested dataset is not found."""

    pass


class DownloadSizeExceededError(MarineAPIError):
    """Raised when a download exceeds the maximum allowed size."""

    pass


class InvalidParameterError(MarineAPIError):
    """Raised when invalid parameters are provided."""

    pass
