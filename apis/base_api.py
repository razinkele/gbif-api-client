"""
Base API class for marine database integrations.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd
import requests

from .exceptions import (
    APIConnectionError,
    APIRequestError,
    APIResponseError,
    APITimeoutError,
    APIRateLimitError,
    DataValidationError,
    MarineAPIError,
)

# HTTP Configuration Constants
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRY_TOTAL = 3
DEFAULT_RETRY_BACKOFF_FACTOR = 0.3
DEFAULT_RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]
DEFAULT_ALLOWED_METHODS = ["HEAD", "GET", "OPTIONS", "POST"]
MAX_429_RETRIES = 3
CHUNK_SIZE_BYTES = 8192  # 8KB chunks for downloads


class BaseMarineAPI(ABC):
    """
    Base class for marine database API implementations.
    """

    def __init__(self, base_url: str, session: Optional[requests.Session] = None):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            session: Optional requests session to use
        """
        self.base_url = base_url
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            # Configure a retry strategy for transient errors
            try:
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                retry_strategy = Retry(
                    total=DEFAULT_RETRY_TOTAL,
                    status_forcelist=DEFAULT_RETRY_STATUS_FORCELIST,
                    backoff_factor=DEFAULT_RETRY_BACKOFF_FACTOR,
                    allowed_methods=DEFAULT_ALLOWED_METHODS,
                    respect_retry_after_header=True,
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self.session.mount("https://", adapter)
                self.session.mount("http://", adapter)
            except ImportError as e:
                # If urllib3 is not available, continue without retries
                self.logger.debug("Retry libraries not available: %s", e)
            except (ValueError, TypeError) as e:
                # If configuration values are invalid, continue without retries
                self.logger.debug("Retry configuration invalid: %s", e)
            except Exception as e:
                # Unexpected error in retry configuration
                self.logger.warning("Unexpected error configuring retries: %s", e)
        self.timeout = DEFAULT_TIMEOUT
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_taxa(self, *args, **kwargs) -> pd.DataFrame:
        """
        Get taxonomic data from the database.
        Must be implemented by subclasses.
        """
        pass

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make an HTTP request to the API.

        Args:
            endpoint: API endpoint (relative to base_url)
            method: HTTP method
            params: Query parameters
            data: Request body data
            headers: Optional headers to include

        Returns:
            Response object
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Implement a small retry loop for 429 (Too Many Requests)
        # to respect Retry-After headers when present.
        attempt = 0
        while True:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response is None:
                    raise APIConnectionError("No response from session.request")

                if (
                    getattr(response, "status_code", None) == 429
                    and attempt < MAX_429_RETRIES
                ):
                    # Respect Retry-After header when present
                    retry_after = (
                        response.headers.get("Retry-After")
                        if hasattr(response, "headers")
                        else None
                    )
                    wait = 0.1 * (2**attempt)  # small exponential backoff for tests
                    if retry_after is not None:
                        try:
                            wait = max(wait, float(retry_after))
                        except Exception:
                            pass
                    self.logger.warning(
                        "Received 429 for %s; retrying in %.2fs (attempt %s)",
                        url,
                        wait,
                        attempt + 1,
                    )
                    attempt += 1
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                # Network-level error; expose to caller for fallback handling
                raise APIRequestError(f"API request failed: {e}") from e

    def _safe_dataframe(self, data: Any) -> pd.DataFrame:
        """
        Safely create a DataFrame from API response data.
        """
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        else:
            raise DataValidationError(f"Cannot create DataFrame from {type(data)}")
    def _handle_response(self, response):
        """
        Handle API response, converting to appropriate format.

        Args:
            response: Response object

        Returns:
            Parsed response data
        """
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                return response.json()
            except ValueError as e:
                raise APIResponseError(f"Invalid JSON response: {e}") from e
        else:
            text = response.text
            # Try to parse as JSON anyway
            try:
                return response.json()
            except ValueError:
                raise APIResponseError(f"Non-JSON response: {text[:100]}...")

    def _safe_api_call(self, api_func, fallback_func=None, *args, **kwargs):
        """
        Safely call an API function with fallback to mock data.

        Args:
            api_func: Function to call for real API
            fallback_func: Fallback function for mock data
            *args, **kwargs: Arguments for the functions

        Returns:
            DataFrame or result from API call or fallback
        """
        try:
            result = api_func(*args, **kwargs)
            # Ensure dataframes have metadata flags even on success
            try:
                if isinstance(result, pd.DataFrame):
                    result.attrs.setdefault("api_fallback", False)
                    result.attrs.setdefault("api_error", None)
            except (AttributeError, KeyError, TypeError):
                # non-critical metadata attachment failed (some pandas versions may not support attrs)
                pass
            return result
        except (APIConnectionError, APIRequestError, APITimeoutError) as e:
            # Network-level errors - use fallback if available
            if fallback_func:
                self.logger.warning(f"API unavailable ({type(e).__name__}: {e}), using fallback data.")
                try:
                    fallback = fallback_func(*args, **kwargs)
                    if isinstance(fallback, pd.DataFrame):
                        fallback.attrs["api_fallback"] = True
                        fallback.attrs["api_error"] = str(e)
                    return fallback
                except MarineAPIError as fe:
                    # Fallback also failed with API error
                    self.logger.error(f"Fallback function failed with API error: {fe}")
                    empty = pd.DataFrame()
                    empty.attrs["api_fallback"] = False
                    empty.attrs["api_error"] = f"{str(e)}; fallback failed: {fe}"
                    return empty
                except Exception as fe:
                    # Fallback failed with unexpected error
                    self.logger.error(f"Fallback function failed unexpectedly: {fe}")
                    empty = pd.DataFrame()
                    empty.attrs["api_fallback"] = False
                    empty.attrs["api_error"] = f"{str(e)}; fallback failed: {fe}"
                    return empty
            else:
                self.logger.error(f"API connection error: {e}")
                empty = pd.DataFrame()
                empty.attrs["api_fallback"] = False
                empty.attrs["api_error"] = str(e)
                return empty
        except (APIResponseError, DataValidationError) as e:
            # Response/data errors - may indicate API changes or invalid data
            if fallback_func:
                self.logger.warning(f"API response error ({type(e).__name__}: {e}), using fallback data.")
                try:
                    fallback = fallback_func(*args, **kwargs)
                    if isinstance(fallback, pd.DataFrame):
                        fallback.attrs["api_fallback"] = True
                        fallback.attrs["api_error"] = str(e)
                    return fallback
                except Exception as fe:
                    self.logger.error(f"Fallback function failed: {fe}")
                    empty = pd.DataFrame()
                    empty.attrs["api_fallback"] = False
                    empty.attrs["api_error"] = f"{str(e)}; fallback failed: {fe}"
                    return empty
            else:
                self.logger.error(f"API response/validation error: {e}")
                empty = pd.DataFrame()
                empty.attrs["api_fallback"] = False
                empty.attrs["api_error"] = str(e)
                return empty
        except MarineAPIError as e:
            # Other marine API errors
            if fallback_func:
                self.logger.warning(f"Marine API error ({type(e).__name__}: {e}), using fallback data.")
                try:
                    fallback = fallback_func(*args, **kwargs)
                    if isinstance(fallback, pd.DataFrame):
                        fallback.attrs["api_fallback"] = True
                        fallback.attrs["api_error"] = str(e)
                    return fallback
                except Exception as fe:
                    self.logger.error(f"Fallback function failed: {fe}")
                    empty = pd.DataFrame()
                    empty.attrs["api_fallback"] = False
                    empty.attrs["api_error"] = f"{str(e)}; fallback failed: {fe}"
                    return empty
            else:
                self.logger.error(f"Marine API error: {e}")
                empty = pd.DataFrame()
                empty.attrs["api_fallback"] = False
                empty.attrs["api_error"] = str(e)
                return empty
        except Exception as e:
            # Unexpected errors (not MarineAPIError)
            self.logger.error(f"Unexpected error in API call: {type(e).__name__}: {e}")
            if fallback_func:
                try:
                    fallback = fallback_func(*args, **kwargs)
                    if isinstance(fallback, pd.DataFrame):
                        fallback.attrs["api_fallback"] = True
                        fallback.attrs["api_error"] = str(e)
                    return fallback
                except Exception as fe:
                    self.logger.error(f"Fallback function also failed: {fe}")
                    empty = pd.DataFrame()
                    empty.attrs["api_fallback"] = False
                    empty.attrs["api_error"] = f"{str(e)}; fallback failed: {fe}"
                    return empty
            else:
                empty = pd.DataFrame()
                empty.attrs["api_fallback"] = False
                empty.attrs["api_error"] = str(e)
                return empty
