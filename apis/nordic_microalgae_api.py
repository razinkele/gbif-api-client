"""
Nordic Microalgae API implementation.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class NordicMicroalgaeApi(BaseMarineAPI):
    """
    API client for Nordic Microalgae database.
    """

    def __init__(
        self,
        base_url: str = "https://nordicmicroalgae.org/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_nordic_microalgae_taxa(
        self, search_params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Retrieve taxa information from Nordic Microalgae.

        Args:
            search_params: Optional search parameters

        Returns:
            DataFrame with taxa information
        """

        def _api_call():
            params = search_params or {}
            response = self._make_request("taxa", params=params)
            data = self._handle_response(response)
            return pd.DataFrame(data)

        return self._safe_api_call(_api_call, self._get_mock_nordic_microalgae_taxa)

    def get_nua_harmfulness(self, taxon_ids: List[int]) -> pd.DataFrame:
        """
        Retrieve harmfulness for taxa from Nordic Microalgae.

        Args:
            taxon_ids: List of taxon IDs

        Returns:
            DataFrame with harmfulness information
        """

        def _api_call():
            results = []
            for taxon_id in taxon_ids:
                response = self._make_request(f"taxa/{taxon_id}/harmfulness")
                data = self._handle_response(response)
                data["taxon_id"] = taxon_id
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_nua_external_links(self, taxon_ids: List[int]) -> pd.DataFrame:
        """
        Retrieve external links or facts for taxa from Nordic Microalgae.

        Args:
            taxon_ids: List of taxon IDs

        Returns:
            DataFrame with external links
        """

        def _api_call():
            results = []
            for taxon_id in taxon_ids:
                response = self._make_request(f"taxa/{taxon_id}/links")
                data = self._handle_response(response)
                data["taxon_id"] = taxon_id
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_nua_media_links(self, taxon_ids: List[int]) -> pd.DataFrame:
        """
        Retrieve and extract media URLs from Nordic Microalgae.

        Args:
            taxon_ids: List of taxon IDs

        Returns:
            DataFrame with media links
        """

        def _api_call():
            results = []
            for taxon_id in taxon_ids:
                response = self._make_request(f"taxa/{taxon_id}/media")
                data = self._handle_response(response)
                data["taxon_id"] = taxon_id
                results.append(data)
            return pd.DataFrame(results)

        return self._safe_api_call(_api_call)

    def get_taxa(
        self,
        search_params: Optional[Dict[str, Any]] = None,
        taxon_ids: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Get taxonomic data from Nordic Microalgae.

        Args:
            search_params: Search parameters for taxa
            taxon_ids: Specific taxon IDs to retrieve

        Returns:
            DataFrame with taxa information
        """
        if taxon_ids:
            return self.get_nua_harmfulness(taxon_ids)
        else:
            return self.get_nordic_microalgae_taxa(search_params)

    # Mock data methods
    def _get_mock_nordic_microalgae_taxa(self) -> pd.DataFrame:
        """Return mock Nordic Microalgae taxa for testing."""
        return pd.DataFrame(
            [
                {
                    "name": "Aphanizomenon flos-aquae",
                    "harmfulness": "Toxic",
                    "region": "Nordic",
                },
                {
                    "name": "Microcystis aeruginosa",
                    "harmfulness": "Toxic",
                    "region": "Nordic",
                },
                {
                    "name": "Nodularia spumigena",
                    "harmfulness": "Toxic",
                    "region": "Nordic",
                },
            ]
        )
