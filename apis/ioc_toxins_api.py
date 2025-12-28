"""
IOC-UNESCO Toxins API implementation.
"""

from typing import Any, List, Optional

import pandas as pd

from .base_api import BaseMarineAPI


class IocToxinsApi(BaseMarineAPI):
    """
    API client for IOC-UNESCO Toxins database.
    """

    def __init__(
        self,
        base_url: str = "https://toxins.hais.ioc-unesco.org/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_toxin_list(self) -> pd.DataFrame:
        """
        Retrieve marine biotoxin data from IOC-UNESCO Toxins Database.

        Returns:
            DataFrame with toxin information
        """

        def _api_call():
            response = self._make_request("toxins")
            data = self._handle_response(response)
            return pd.DataFrame(data)

        return self._safe_api_call(_api_call, self._get_mock_toxin_list)

    def get_taxa(
        self, scientific_names: Optional[List[str]] = None, **kwargs
    ) -> pd.DataFrame:
        """
        Get toxin data from IOC database.

        Args:
            scientific_names: Optional list of scientific names (ignored for IOC toxins)

        Returns:
            DataFrame with toxin information
        """
        return self.get_toxin_list()

    # Mock data methods
    def _get_mock_toxin_list(self) -> pd.DataFrame:
        """Return mock IOC-UNESCO toxin list for testing."""
        return pd.DataFrame(
            [
                {
                    "toxin": "Saxitoxin",
                    "type": "Neurotoxin",
                    "source": "Dinoflagellates",
                },
                {
                    "toxin": "Okadaic acid",
                    "type": "Diarrhetic",
                    "source": "Dinoflagellates",
                },
                {"toxin": "Domoic acid", "type": "Neurotoxin", "source": "Diatoms"},
            ]
        )
