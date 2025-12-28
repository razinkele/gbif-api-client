"""
Plankton Toolbox API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI
from .exceptions import APIResponseError


class PlanktonToolboxApi(BaseMarineAPI):
    """
    API client for Plankton Toolbox.
    """

    def __init__(
        self,
        base_url: str = "https://planktontoolbox.org/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_nomp_list(self) -> pd.DataFrame:
        """
        Get the latest NOMP biovolume Excel list.

        Returns:
            DataFrame with NOMP biovolume data
        """

        def _api_call():
            # This would typically download from a specific URL
            # For now, return empty DataFrame as placeholder
            self.logger.info(
                "NOMP list download not implemented - requires specific endpoint"
            )
            return pd.DataFrame()

        return self._safe_api_call(_api_call)

    def get_peg_list(self) -> pd.DataFrame:
        """
        Get the latest EG-Phyto/PEG biovolume Excel list.

        Returns:
            DataFrame with PEG biovolume data
        """

        def _api_call():
            # This would typically download from a specific URL
            # For now, return empty DataFrame as placeholder
            self.logger.info(
                "PEG list download not implemented - requires specific endpoint"
            )
            return pd.DataFrame()

        return self._safe_api_call(_api_call)

    def get_plankton_toolbox_taxa(self) -> pd.DataFrame:
        """
        Get taxa information from Plankton Toolbox.

        Returns:
            DataFrame with plankton taxa information
        """

        def _api_call():
            # Attempt taxa endpoint; on failure raise to trigger fallback
            response = self._make_request("taxa")
            data = self._handle_response(response)

            if not data:
                raise APIResponseError("No data returned from Plankton Toolbox taxa endpoint")

            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict) and "results" in data:
                return pd.DataFrame(data["results"])
            else:
                return pd.DataFrame([data])

        return self._safe_api_call(_api_call, self._get_mock_plankton_toolbox_taxa)

    def read_ptbx(self, file_path: str) -> pd.DataFrame:
        """
        Read a Plankton Toolbox export file.

        Args:
            file_path: Path to the Plankton Toolbox file

        Returns:
            DataFrame with plankton data
        """
        try:
            # Plankton Toolbox files are typically Excel or CSV
            if file_path.endswith((".xlsx", ".xls")):
                return pd.read_excel(file_path)
            else:
                return pd.read_csv(file_path, delimiter="\t")
        except Exception as e:
            self.logger.error(f"Error reading Plankton Toolbox file: {e}")
            return pd.DataFrame()

    def get_taxa(
        self, scientific_names: Optional[List[str]] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Get taxonomic data from Plankton Toolbox.

        Args:
scientific_names: Optional list of scientific names (ignored)

        Returns:
            DataFrame with plankton taxa information
        """
        return self.get_plankton_toolbox_taxa()

    # Mock data methods
    def _get_mock_plankton_toolbox_taxa(self) -> pd.DataFrame:
        """Return mock Plankton Toolbox taxa for testing."""
        return pd.DataFrame(
            [
                {
                    "name": "Skeletonema costatum",
                    "biovolume": 1500,
                    "category": "Diatom",
                },
                {
                    "name": "Thalassiosira rotula",
                    "biovolume": 1200,
                    "category": "Diatom",
                },
                {
                    "name": "Chaetoceros curvisetus",
                    "biovolume": 1800,
                    "category": "Diatom",
                },
            ]
        )
