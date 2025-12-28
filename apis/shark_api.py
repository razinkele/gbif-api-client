"""
SHARK (Swedish Ocean Archive) API implementation.
"""

from typing import Any, Dict, Optional

import pandas as pd

from .base_api import CHUNK_SIZE_BYTES, BaseMarineAPI
from .exceptions import APIResponseError, DownloadSizeExceededError
from .mock_data import (
    get_mock_shark_datasets,
    get_mock_shark_parameters,
    get_mock_shark_stations,
)

# Download Configuration Constants
DEFAULT_MAX_DOWNLOAD_SIZE_MB = 500


class SharkApi(BaseMarineAPI):
    """
    API client for SHARK (Swedish Ocean Archive) database.
    """

    def __init__(
        self,
        base_url: str = "https://sharkdata.smhi.se/api/",
        session: Optional[Any] = None,
    ):
        super().__init__(base_url, session)

    def get_datasets(self) -> pd.DataFrame:
        """
        Get list of available datasets in SHARK.

        Returns:
            DataFrame with dataset information
        """

        def _api_call():
            response = self._make_request("datasets")
            data = self._handle_response(response)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                raise APIResponseError(f"Unexpected response format for datasets: {type(data)}")

        return self._safe_api_call(_api_call, get_mock_shark_datasets)

    def get_stations(self) -> pd.DataFrame:
        """
        Get list of monitoring stations.

        Returns:
            DataFrame with station information
        """

        def _api_call():
            response = self._make_request("stations")
            data = self._handle_response(response)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                raise APIResponseError(f"Unexpected response format for stations: {type(data)}")

        return self._safe_api_call(_api_call, get_mock_shark_stations)

    def get_parameters(self) -> pd.DataFrame:
        """
        Get list of available parameters.

        Returns:
            DataFrame with parameter information
        """

        def _api_call():
            response = self._make_request("parameters")
            data = self._handle_response(response)
            return pd.DataFrame(data)

        return self._safe_api_call(_api_call, get_mock_shark_parameters)

    def get_shark_options(self) -> Dict[str, Any]:
        """
        Retrieve available search options from SHARK.

        Returns:
            Dictionary with available search options
        """

        def _api_call():
            response = self._make_request("options")
            return self._handle_response(response)

        try:
            return _api_call()
        except Exception as e:
            self.logger.error(f"Error fetching SHARK options: {e}")
            return {}

    def get_shark_codes(self) -> Dict[str, Any]:
        """
        Get SHARK code lists and classifications.

        Returns:
            Dictionary with code information
        """

        def _api_call():
            response = self._make_request("codes")
            return self._handle_response(response)

        try:
            return _api_call()
        except Exception as e:
            self.logger.error(f"Error fetching SHARK codes: {e}")
            return {}

    def search_data(
        self,
        parameter: Optional[str] = None,
        station: Optional[str] = None,
        dataset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Search for data in SHARK database.

        Args:
            parameter: Parameter name or code
            station: Station name or code
            dataset: Dataset name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of records to return

        Returns:
            DataFrame with search results
        """

        def _api_call():
            params = {
                "parameter": parameter,
                "station": station,
                "dataset": dataset,
                "from_date": start_date,
                "to_date": end_date,
                "limit": limit,
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = self._make_request("data", params=params)
            data = self._handle_response(response)

            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
            else:
                return pd.DataFrame()

        return self._safe_api_call(_api_call)

    def get_quality_control_info(self, dataset: str) -> Dict[str, Any]:
        """
        Get quality control information for a dataset.

        Args:
            dataset: Dataset name

        Returns:
            Dictionary with quality control information
        """

        def _api_call():
            response = self._make_request(f"datasets/{dataset}/quality")
            return self._handle_response(response)

        try:
            return _api_call()
        except Exception as e:
            self.logger.error(f"Error fetching quality control info: {e}")
            return {}

    def get_data_summary(self, dataset: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary statistics for datasets.

        Args:
            dataset: Optional dataset name

        Returns:
            Dictionary with summary statistics
        """

        def _api_call():
            url = "summary"
            if dataset:
                url += f"/{dataset}"
            response = self._make_request(url)
            return self._handle_response(response)

        try:
            return _api_call()
        except Exception as e:
            self.logger.error(f"Error fetching summary: {e}")
            return {}

    def download_dataset(
        self, dataset: str, output_file: str, max_size_mb: int = DEFAULT_MAX_DOWNLOAD_SIZE_MB
    ) -> bool:
        """
        Download a complete dataset with size limits.

        Args:
            dataset: Dataset name
            output_file: Output file path
            max_size_mb: Maximum file size in megabytes (default: 500MB)

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If download exceeds max_size_mb
        """
        try:
            response = self._make_request(f"datasets/{dataset}/download")
            max_size_bytes = max_size_mb * 1024 * 1024
            downloaded_size = 0

            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
                    if chunk:
                        downloaded_size += len(chunk)
                        if downloaded_size > max_size_bytes:
                            self.logger.error(
                                f"Download aborted: file size exceeds {max_size_mb}MB limit"
                            )
                            raise DownloadSizeExceededError(
                                f"Download size exceeded maximum allowed size of {max_size_mb}MB"
                            )
                        f.write(chunk)

            self.logger.info(f"Successfully downloaded {downloaded_size / 1024 / 1024:.2f}MB to {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading dataset: {e}")
            return False

    def validate_data(self, data: pd.DataFrame, datatype: str) -> Dict[str, Any]:
        """
        Validate data against SHARK datatype requirements.

        Args:
            data: DataFrame to validate
            datatype: SHARK datatype

        Returns:
            Dictionary with validation results
        """
        try:
            # Get required fields for the datatype
            response = self._make_request(f"datatypes/{datatype}/fields")
            required_fields = self._handle_response(response)

            validation_results = {
                "missing_fields": [],
                "invalid_data_types": [],
                "validation_passed": True,
            }

            # Check for missing required fields
            for field in required_fields.get("required", []):
                if field not in data.columns:
                    validation_results["missing_fields"].append(field)
                    validation_results["validation_passed"] = False

            # Check data types
            for field, expected_type in required_fields.get("types", {}).items():
                if field in data.columns:
                    if (
                        expected_type == "numeric"
                        and not pd.api.types.is_numeric_dtype(data[field])
                    ):
                        validation_results["invalid_data_types"].append(field)
                        validation_results["validation_passed"] = False

            return validation_results
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return {"error": str(e), "validation_passed": False}

    def get_taxa(self, *args, **kwargs) -> pd.DataFrame:
        """
        Get taxonomic data - not directly applicable for SHARK.
        Returns empty DataFrame.
        """
        return pd.DataFrame()
