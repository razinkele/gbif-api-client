"""
OBIS (Ocean Biodiversity Information System) API implementation.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class ObisApi(BaseMarineAPI):
    """
    API client for OBIS (Ocean Biodiversity Information System).
    """

    def __init__(
        self, base_url: str = "https://api.obis.org/", session: Optional[Any] = None
    ):
        super().__init__(base_url, session)

    def get_obis_records(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Retrieve OBIS records for species.

        Args:
            scientific_names: List of scientific names

        Returns:
            DataFrame with OBIS occurrence records
        """

        def _api_call():
            results = []
            for name in scientific_names:
                params = {"scientificname": name}
                response = self._make_request("occurrence", params=params)
                data = self._handle_response(response)
                results.extend(data.get("results", []))
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, self._get_mock_obis_records)

    def lookup_xy(self, coordinates: List[Dict[str, float]]) -> pd.DataFrame:
        """
        Lookup spatial information for geographic points.

        Args:
            coordinates: List of dicts with 'latitude' and 'longitude' keys

        Returns:
            DataFrame with spatial information
        """

        def _api_call():
            results = []
            for coord in coordinates:
                params = {
                    "geometry": f"POINT({coord['longitude']} {coord['latitude']})"
                }
                response = self._make_request("occurrence", params=params)
                data = self._handle_response(response)
                results.extend(data.get("results", []))
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_taxa(
        self,
        scientific_names: Optional[List[str]] = None,
        coordinates: Optional[List[Dict[str, float]]] = None,
    ) -> pd.DataFrame:
        """
        Get occurrence data from OBIS.

        Args:
            scientific_names: List of scientific names
            coordinates: List of coordinate dictionaries

        Returns:
            DataFrame with occurrence records
        """
        if scientific_names:
            return self.get_obis_records(scientific_names)
        elif coordinates:
            return self.lookup_xy(coordinates)
        else:
            return pd.DataFrame()

    # Mock data methods
    def _get_mock_obis_records(self) -> pd.DataFrame:
        """Return mock OBIS records for testing."""
        return pd.DataFrame(
            [
                {
                    "species": "Clupea harengus",
                    "longitude": 11.3,
                    "latitude": 58.4,
                    "depth": 10,
                },
                {
                    "species": "Gadus morhua",
                    "longitude": 11.2,
                    "latitude": 58.3,
                    "depth": 15,
                },
                {
                    "species": "Perca fluviatilis",
                    "longitude": 11.1,
                    "latitude": 58.2,
                    "depth": 5,
                },
            ]
        )
