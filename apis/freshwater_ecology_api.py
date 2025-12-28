from typing import Any, Dict, Optional

import os
import pandas as pd

from .base_api import BaseMarineAPI
from .exceptions import APIResponseError


class FreshwaterEcologyApi(BaseMarineAPI):
    """Client for Freshwater Ecology API (freshwaterecology.info).

    The real service requires an API key. We read it from the environment
    variable FWE_API_KEY. The client tries to send the key as a header
    (X-Api-Key) and will fall back gracefully to an empty result if no key
    is present.
    """

    def __init__(
        self,
        base_url: str = "https://www.freshwaterecology.info/fweapi2/v1/",
        session: Optional[Any] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(base_url, session)
        self.api_key = api_key or os.getenv("FWE_API_KEY")

    def _auth_headers(self, include_key: bool = False) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if include_key and self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers

    def get_status(self) -> Dict[str, Any]:
        def _api_call():
            response = self._make_request("status", method="GET")
            return self._handle_response(response)

        return self._safe_api_call(_api_call, lambda: {"status": "offline (fallback)"})

    def authenticate(self, force: bool = False) -> Optional[str]:
        """Exchange API key for a bearer token and cache it."""
        import time

        if not self.api_key:
            self.logger.warning("No API key configured for FreshwaterEcology API")
            return None

        # If we have a token and it's not expired, return it
        if getattr(self, "token", None) and not force:
            expiry = getattr(self, "token_expiry", None)
            if expiry is None or expiry > time.time():
                return self.token

        def _api_call():
            data = {"apikey": self.api_key}
            response = self._make_request("token", method="POST", data=data, headers=self._auth_headers(True))
            data_resp = self._handle_response(response)
            token = None
            if isinstance(data_resp, dict):
                token = data_resp.get("token") or data_resp.get("access_token")
                expires = data_resp.get("expires_in")
            else:
                token = None
                expires = None

            if token:
                self.token = token
                if expires:
                    self.token_expiry = time.time() + int(expires)
                else:
                    self.token_expiry = None
                return token
            raise APIResponseError("Authentication failed: no token in response")

        result = self._safe_api_call(_api_call)
        # If _safe_api_call returned a DataFrame (fallback), we treat auth as unavailable
        if isinstance(result, pd.DataFrame):
            return None
        return getattr(self, "token", None)

    def get_ecoparam_list(self) -> pd.DataFrame:
        def _api_call():
            response = self._make_request("getecoparamlist", method="GET")
            data = self._handle_response(response)
            if isinstance(data, list):
                return pd.DataFrame(data)
            return pd.DataFrame()

        return self._safe_api_call(_api_call)

    def query(self, **kwargs) -> pd.DataFrame:
        """Query ecological trait data; requires Bearer token."""
        # Ensure we have a token
        token = self.authenticate()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        def _api_call():
            response = self._make_request("query", method="POST", data=kwargs, headers=headers)
            data = self._handle_response(response)
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict) and data.get("results"):
                return pd.DataFrame(data.get("results"))
            return pd.DataFrame()

        return self._safe_api_call(_api_call)

    def get_taxa(self, q: Optional[str] = None, limit: int = 50) -> pd.DataFrame:
        """Compatibility implementation for abstract method from BaseMarineAPI.

        Delegates to search_taxa when possible.
        """
        if q:
            return self.search_taxa(q, limit=limit)
        return pd.DataFrame()
