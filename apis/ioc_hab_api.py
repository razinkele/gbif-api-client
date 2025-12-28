"""
IOC-UNESCO HAB (Harmful Algae) API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class IocHabApi(BaseMarineAPI):
    """
    API client for IOC-UNESCO HAB (Harmful Algae) database.
    """

    def __init__(
        self,
        base_url: str = "https://www.marinespecies.org/hab/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_hab_list(self) -> pd.DataFrame:
        """
        Download the IOC-UNESCO Taxonomic Reference List of Harmful Micro Algae.

        Returns:
            DataFrame with HAB species list
        """

        def _api_call():
            response = self._make_request("list")
            data = self._handle_response(response)
            return pd.DataFrame(data)

        return self._safe_api_call(_api_call, self._get_mock_hab_list)

    def get_taxa(
        self, scientific_names: Optional[List[str]] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Get taxonomic data from HAB database.

        Args:
            scientific_names: Optional list of scientific names (ignored for HAB)

        Returns:
            DataFrame with HAB species information
        """
        return self.get_hab_list()

    # Mock data methods
    def _get_mock_hab_list(self) -> pd.DataFrame:
        """Return mock IOC-UNESCO HAB list for testing."""
        return pd.DataFrame(
            [
                {
                    "species": "Alexandrium catenella",
                    "toxicity": "High",
                    "region": "Global",
                },
                {"species": "Dinophysis acuta", "toxicity": "High", "region": "Global"},
                {
                    "species": "Pseudo-nitzschia multiseries",
                    "toxicity": "Medium",
                    "region": "Global",
                },
            ]
        )
