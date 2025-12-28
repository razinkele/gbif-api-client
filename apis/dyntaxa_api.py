"""
Dyntaxa (SLU Artdatabanken) API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class DyntaxaApi(BaseMarineAPI):
    """
    API client for Dyntaxa (SLU Artdatabanken) taxonomic database.
    """

    def __init__(
        self,
        base_url: str = "https://taxon.artdatabanken.se/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_dyntaxa_records(self, taxon_ids: List[int]) -> pd.DataFrame:
        """
        Get taxonomic information from Dyntaxa for specified taxon IDs.

        Args:
            taxon_ids: List of Dyntaxa taxon IDs

        Returns:
            DataFrame with taxonomic information
        """

        def _api_call():
            results = []
            for taxon_id in taxon_ids:
                response = self._make_request(f"taxa/{taxon_id}")
                data = self._handle_response(response)
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, self._get_mock_dyntaxa_taxa)

    def match_dyntaxa_taxa(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Match Dyntaxa taxon names.

        Args:
            scientific_names: List of scientific names to match

        Returns:
            DataFrame with matching results
        """

        def _api_call():
            results = []
            for name in scientific_names:
                params = {"searchString": name, "includeSynonyms": "true"}
                response = self._make_request("taxa", params=params)
                data = self._handle_response(response)
                if data:
                    results.extend(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call, self._get_mock_dyntaxa_taxa)

    def is_in_dyntaxa(self, scientific_names: List[str]) -> pd.DataFrame:
        """
        Check if taxon names exist in Dyntaxa.

        Args:
            scientific_names: List of scientific names to check

        Returns:
            DataFrame with existence check results
        """

        def _api_call():
            results = []
            for name in scientific_names:
                matches = self.match_dyntaxa_taxa([name])
                results.append(
                    {
                        "scientific_name": name,
                        "exists_in_dyntaxa": len(matches) > 0,
                        "match_count": len(matches),
                    }
                )
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def construct_dyntaxa_table(self, taxon_ids: List[int]) -> pd.DataFrame:
        """
        Construct a hierarchical taxonomy table from Dyntaxa.

        Args:
            taxon_ids: List of Dyntaxa taxon IDs

        Returns:
            DataFrame with hierarchical taxonomy
        """

        def _api_call():
            results = []
            for taxon_id in taxon_ids:
                # Get the taxon record
                response = self._make_request(f"taxa/{taxon_id}")
                data = self._handle_response(response)
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_taxa(
        self,
        scientific_names: Optional[List[str]] = None,
        taxon_ids: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Get taxonomic data from Dyntaxa.

        Args:
            scientific_names: List of scientific names to search for
            taxon_ids: List of taxon IDs to retrieve

        Returns:
            DataFrame with taxonomic information
        """
        if scientific_names:
            return self.match_dyntaxa_taxa(scientific_names)
        elif taxon_ids:
            return self.get_dyntaxa_records(taxon_ids)
        else:
            return pd.DataFrame()

    # Mock data methods
    def _get_mock_dyntaxa_taxa(self) -> pd.DataFrame:
        """Return mock Dyntaxa taxa data for testing."""
        return pd.DataFrame(
            [
                {
                    "scientificName": "Baltic herring",
                    "taxonId": 1001,
                    "rank": "species",
                },
                {"scientificName": "Atlantic cod", "taxonId": 1002, "rank": "species"},
                {
                    "scientificName": "European perch",
                    "taxonId": 1003,
                    "rank": "species",
                },
            ]
        )
