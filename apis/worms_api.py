"""
WoRMS (World Register of Marine Species) API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class WormsApi(BaseMarineAPI):
    """
    API client for WoRMS (World Register of Marine Species) database.
    """

    def __init__(
        self,
        base_url: str = "https://www.marinespecies.org/rest/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_worms_records(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Retrieve WoRMS records.

        Args:
            scientific_names: List of scientific names

        Returns:
            DataFrame with WoRMS records
        """

        def _api_call():
            results = []
            for name in scientific_names:
                response = self._make_request(f"AphiaRecordsByName/{name}")
                data = self._handle_response(response)
                if data:
                    results.extend(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, self._get_mock_worms_records)

    def match_worms_taxa(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Retrieve WoRMS records by taxonomic names with retry logic.

        Args:
            scientific_names: List of scientific names

        Returns:
            DataFrame with matching results
        """
        return self.get_worms_records(scientific_names)

    def add_worms_taxonomy(self, aphia_ids: List[int]) -> pd.DataFrame:
        """
        Add WoRMS taxonomy hierarchy to AphiaIDs.

        Args:
            aphia_ids: List of WoRMS AphiaIDs

        Returns:
            DataFrame with taxonomy hierarchy
        """

        def _api_call():
            results = []
            for aphia_id in aphia_ids:
                response = self._make_request(
                    f"AphiaClassificationByAphiaID/{aphia_id}"
                )
                data = self._handle_response(response)
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_worms_classification(self, aphia_ids: List[int]) -> pd.DataFrame:
        """
        Retrieve hierarchical classification from WoRMS.

        Args:
            aphia_ids: List of WoRMS AphiaIDs

        Returns:
            DataFrame with classification
        """
        return self.add_worms_taxonomy(aphia_ids)

    def assign_phytoplankton_group(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Assign phytoplankton group to scientific names.

        Args:
            scientific_names: List of scientific names

        Returns:
            DataFrame with phytoplankton group assignments
        """
        worms_data = self.get_worms_records(scientific_names)
        # This would require additional logic to assign phytoplankton groups
        # For now, return the WoRMS data with a placeholder group column
        if not worms_data.empty:
            worms_data["phytoplankton_group"] = "Unknown"  # Placeholder
        return worms_data

    def get_worms_taxa(
        self,
        scientific_name: Optional[str] = None,
        aphia_id: Optional[int] = None,
        marine_only: bool = True,
        offset: int = 1,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        Get taxonomic information from WoRMS (World Register of Marine Species)
        """

        def _api_call():
            if aphia_id:
                # Get specific record by AphiaID
                response = self._make_request(f"AphiaRecordsByAphiaID/{aphia_id}")
                data = self._handle_response(response)
                return pd.DataFrame([data])
            elif scientific_name:
                # Search by scientific name
                params = {"marine_only": marine_only, "offset": offset, "limit": limit}
                response = self._make_request(
                    f"AphiaRecordsByName/{scientific_name}", params=params
                )
                data = self._handle_response(response)
                return pd.DataFrame(data)
            else:
                # Get all records (limited)
                params = {"marine_only": marine_only, "offset": offset, "limit": limit}
                response = self._make_request("AphiaRecords", params=params)
                data = self._handle_response(response)
                return pd.DataFrame(data)

        return self._safe_api_call(_api_call, self._get_mock_worms_records)

    def get_taxa(
        self,
        scientific_names: Optional[List[str]] = None,
        aphia_ids: Optional[List[int]] = None,
        scientific_name: Optional[str] = None,
        aphia_id: Optional[int] = None,
        marine_only: bool = True,
        offset: int = 1,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        Get taxonomic data from WoRMS.

        Args:
            scientific_names: List of scientific names
            aphia_ids: List of AphiaIDs
            scientific_name: Single scientific name
            aphia_id: Single AphiaID
            marine_only: Whether to return only marine species
            offset: Pagination offset
            limit: Maximum number of results

        Returns:
            DataFrame with taxonomic information
        """
        if scientific_names:
            return self.get_worms_records(scientific_names)
        elif aphia_ids:
            return self.add_worms_taxonomy(aphia_ids)
        else:
            return self.get_worms_taxa(
                scientific_name, aphia_id, marine_only, offset, limit
            )

    # Mock data methods
    def _get_mock_worms_records(self) -> pd.DataFrame:
        """Return mock WoRMS records for testing."""
        return pd.DataFrame(
            [
                {
                    "AphiaID": 126436,
                    "scientificname": "Clupea harengus",
                    "rank": "Species",
                },
                {
                    "AphiaID": 126439,
                    "scientificname": "Gadus morhua",
                    "rank": "Species",
                },
                {
                    "AphiaID": 154641,
                    "scientificname": "Perca fluviatilis",
                    "rank": "Species",
                },
            ]
        )
