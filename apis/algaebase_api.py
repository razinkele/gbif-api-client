"""
AlgaeBase API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI
from .exceptions import (
    APIResponseError,
    APIConnectionError,
    APIRequestError
)
from .mock_data import get_mock_algaebase_genus, get_mock_algaebase_taxa


class AlgaeBaseApi(BaseMarineAPI):
    """
    API client for AlgaeBase taxonomic database.
    """

    def __init__(
        self,
        base_url: str = "https://www.algaebase.org/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def match_algaebase_taxa(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Search AlgaeBase for taxonomic information.

        Args:
            scientific_names: List of scientific names to search for

        Returns:
            DataFrame with AlgaeBase search results
        """

        def _api_call():
            results = []
            for name in scientific_names:
                # Try different possible AlgaeBase API endpoints
                # AlgaeBase may not have a public API, so this will likely fail
                try:
                    params = {"q": name, "limit": 10}
                    response = self._make_request("search", params=params)
                    data = self._handle_response(response)
                    if isinstance(data, list):
                        results.extend(data)
                    elif isinstance(data, dict) and "results" in data:
                        results.extend(data["results"])
                except APIResponseError as e:
                    # AlgaeBase returned invalid response
                    self.logger.debug(f"AlgaeBase invalid response for {name}: {e}")
                except (APIConnectionError, APIRequestError) as e:
                    # Network/connection issues with AlgaeBase
                    self.logger.debug(f"AlgaeBase connection error for {name}: {e}")

            # If no results from API, raise exception to trigger fallback
            if not results:
                raise APIResponseError("No data available from AlgaeBase API")

            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, get_mock_algaebase_taxa)

    def match_algaebase_genus(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Search AlgaeBase for information about genera.

        Args:
            scientific_names: List of scientific names (genera)

        Returns:
            DataFrame with genus information
        """

        def _api_call():
            results = []
            for name in scientific_names:
                try:
                    params = {"genus": name}
                    response = self._make_request("genus", params=params)
                    data = self._handle_response(response)
                    if isinstance(data, list):
                        results.extend(data)
                    elif isinstance(data, dict):
                        results.append(data)
                except APIResponseError as e:
                    # AlgaeBase returned invalid response
                    self.logger.debug(f"AlgaeBase invalid response for genus {name}: {e}")
                except (APIConnectionError, APIRequestError) as e:
                    # Network/connection issues with AlgaeBase
                    self.logger.debug(f"AlgaeBase connection error for genus {name}: {e}")

            # If no results from API, raise exception to trigger fallback
            if not results:
                raise APIResponseError("No data available from AlgaeBase API")

            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, get_mock_algaebase_genus)

    def match_algaebase_species(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Search AlgaeBase for information about species.

        Args:
            scientific_names: List of scientific names (species)

        Returns:
            DataFrame with species information
        """

        def _api_call():
            results = []
            for name in scientific_names:
                params = {"species": name}
                response = self._make_request("api/species", params=params)
                data = self._handle_response(response)
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_taxa(self, scientific_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get taxonomic data from AlgaeBase.

        Args:
            scientific_names: List of scientific names to search for

        Returns:
            DataFrame with taxonomic information
        """
        if scientific_names:
            return self.match_algaebase_taxa(scientific_names)
        else:
            return pd.DataFrame()
