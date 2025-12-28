#!/usr/bin/env python3
"""
SHARK4R Python Client - Complete Marine Data Integration

A comprehensive Python implementation of the SHARK4R R package functionality.
Provides access to multiple marine and taxonomic databases:

Core Databases:
- SHARK (Swedish Ocean Archive) - Marine monitoring data
- Dyntaxa (SLU Artdatabanken) - Swedish taxonomic database
- WoRMS (World Register of Marine Species) - Global marine taxonomy
- AlgaeBase - Algal taxonomy and biodiversity
- IOC-UNESCO HAB - Harmful microalgae taxonomy
- IOC-UNESCO Toxins - Marine biotoxins database
- OBIS xylookup - Ocean Biodiversity Information System
- Nordic Microalgae - Nordic microalgae database

Additional Features:
- Quality control and validation
- Geographic data checking
- Outlier detection
- File reading and processing
- Mock data for offline testing
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Import the separate API implementations
from apis import (
    AlgaeBaseApi,
    DyntaxaApi,
    IocHabApi,
    IocToxinsApi,
    NordicMicroalgaeApi,
    ObisApi,
    PlanktonToolboxApi,
    SharkApi,
    WormsApi,
)
from apis.mock_data import (
    get_mock_shark_datasets,
    get_mock_shark_parameters,
    get_mock_shark_stations,
    get_mock_algaebase_genus,
    get_mock_algaebase_taxa,
    get_mock_dyntaxa_taxa,
    get_mock_worms_taxa,
)


class SHARKClient:
    """
    Client for accessing marine data from multiple databases.

    This is a Python implementation of the SHARK4R R package functionality.
    Provides access to:
    - SHARK (Swedish Ocean Archive)
    - Dyntaxa (SLU Artdatabanken)
    - WoRMS (World Register of Marine Species)
    - AlgaeBase
    - IOC-UNESCO HAB (Harmful Algae)
    - IOC-UNESCO Toxins
    - OBIS xylookup
    - Nordic Microalgae
    """

    def __init__(
        self, base_url: str = "https://sharkdata.smhi.se/api/", use_mock: bool = False
    ):
        """
        Initialize SHARK client.

        Args:
            base_url: Base URL for SHARK API
            use_mock: Whether to use mock data for testing when API is unavailable
        """
        self.base_url = base_url
        self.use_mock = use_mock
        self.session = requests.Session()

        # API endpoints for different databases
        self.endpoints = {
            "shark": base_url,
            "dyntaxa": "https://taxon.artdatabanken.se/api/",
            "worms": "https://www.marinespecies.org/rest/",
            "algaebase": "https://www.algaebase.org/api/",
            "ioc_hab": "https://www.marinespecies.org/hab/api/",  # Updated HAB endpoint
            "ioc_toxins": "https://toxins.hais.ioc-unesco.org/api/",
            "obis": "https://api.obis.org/",
            "nordic_microalgae": "https://nordicmicroalgae.org/api/",
        }

        # Initialize API clients
        self.shark_api = SharkApi(base_url, self.session)
        self.dyntaxa_api = DyntaxaApi(self.endpoints["dyntaxa"], self.session)
        self.worms_api = WormsApi(self.endpoints["worms"], self.session)
        self.algaebase_api = AlgaeBaseApi(self.endpoints["algaebase"], self.session)
        self.ioc_hab_api = IocHabApi(self.endpoints["ioc_hab"], self.session)
        self.ioc_toxins_api = IocToxinsApi(self.endpoints["ioc_toxins"], self.session)
        self.obis_api = ObisApi(self.endpoints["obis"], self.session)
        self.nordic_microalgae_api = NordicMicroalgaeApi(
            self.endpoints["nordic_microalgae"], self.session
        )
        self.plankton_toolbox_api = PlanktonToolboxApi()  # No specific base URL yet

        # Freshwater Ecology (freshwaterecology.info) integration
        try:
            from apis.freshwater_ecology_api import FreshwaterEcologyApi

            self.fwe_api = FreshwaterEcologyApi()
        except Exception:
            # If import fails (e.g., during packaging), provide a placeholder attribute
            self.fwe_api = None

    def _get_mock_datasets(self) -> pd.DataFrame:
        """Return mock dataset data for testing."""
        return pd.DataFrame(
            [
                {
                    "id": "PHYTO",
                    "name": "Phytoplankton",
                    "description": "Phytoplankton monitoring data",
                },
                {
                    "id": "ZOOBENTHOS",
                    "name": "Zoobenthos",
                    "description": "Benthic fauna monitoring data",
                },
                {
                    "id": "EPIPHYTIC",
                    "name": "Epiphytic",
                    "description": "Epiphytic algae monitoring data",
                },
                {
                    "id": "SEDIMENT",
                    "name": "Sediment",
                    "description": "Sediment chemistry data",
                },
                {
                    "id": "PHYSCHEM",
                    "name": "Physical Chemical",
                    "description": "Physical and chemical parameters",
                },
            ]
        )

    def _get_mock_stations(self) -> pd.DataFrame:
        """Return mock station data for testing."""
        return pd.DataFrame(
            [
                {
                    "id": "BY1",
                    "name": "Byfjorden 1",
                    "latitude": 58.4,
                    "longitude": 11.3,
                },
                {
                    "id": "BY2",
                    "name": "Byfjorden 2",
                    "latitude": 58.3,
                    "longitude": 11.2,
                },
                {
                    "id": "BY5",
                    "name": "Byfjorden 5",
                    "latitude": 58.2,
                    "longitude": 11.1,
                },
                {
                    "id": "BY10",
                    "name": "Byfjorden 10",
                    "latitude": 58.1,
                    "longitude": 11.0,
                },
            ]
        )

    def _get_mock_parameters(self) -> pd.DataFrame:
        """Return mock parameter data for testing."""
        return pd.DataFrame(
            [
                {"id": "TEMP", "name": "Temperature", "unit": "°C"},
                {"id": "SAL", "name": "Salinity", "unit": "PSU"},
                {"id": "CHL", "name": "Chlorophyll a", "unit": "µg/L"},
                {"id": "PH", "name": "pH", "unit": ""},
                {"id": "O2", "name": "Oxygen", "unit": "mg/L"},
            ]
        )

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

    def _get_mock_algaebase_taxa(self) -> pd.DataFrame:
        """Return mock AlgaeBase taxa data for testing."""
        return pd.DataFrame(
            [
                {
                    "name": "Skeletonema costatum",
                    "genus": "Skeletonema",
                    "class": "Bacillariophyceae",
                },
                {
                    "name": "Thalassiosira rotula",
                    "genus": "Thalassiosira",
                    "class": "Bacillariophyceae",
                },
                {
                    "name": "Chaetoceros curvisetus",
                    "genus": "Chaetoceros",
                    "class": "Bacillariophyceae",
                },
            ]
        )

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

    # ============================================================================
    # SHARK (Swedish Ocean Archive) Methods
    # ============================================================================

    def get_datasets(self) -> pd.DataFrame:
        """Get list of available datasets in SHARK."""
        return self.shark_api.get_datasets()

    def get_stations(self) -> pd.DataFrame:
        """Get list of monitoring stations."""
        return self.shark_api.get_stations()

    def get_parameters(self) -> pd.DataFrame:
        """Get list of available parameters."""
        return self.shark_api.get_parameters()

    def get_shark_options(self) -> Dict[str, Any]:
        """Retrieve available search options from SHARK."""
        return self.shark_api.get_shark_options()

    def get_shark_codes(self) -> Dict[str, Any]:
        """Get SHARK code lists and classifications."""
        return self.shark_api.get_shark_codes()

    def search_data(
        self,
        parameter: Optional[str] = None,
        station: Optional[str] = None,
        dataset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Search for data in SHARK database."""
        return self.shark_api.search_data(
            parameter, station, dataset, start_date, end_date, limit
        )

    def get_quality_control_info(self, dataset: str) -> Dict[str, Any]:
        """Get quality control information for a dataset."""
        return self.shark_api.get_quality_control_info(dataset)

    def get_data_summary(self, dataset: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for datasets."""
        return self.shark_api.get_data_summary(dataset)

    def download_dataset(self, dataset: str, output_file: str) -> bool:
        """Download a complete dataset."""
        return self.shark_api.download_dataset(dataset, output_file)

    def validate_data(self, data: pd.DataFrame, datatype: str) -> Dict[str, Any]:
        """Validate data against SHARK datatype requirements."""
        return self.shark_api.validate_data(data, datatype)

    # Taxonomic database methods
    def match_dyntaxa_taxa(self, taxa_list: List[str]) -> pd.DataFrame:
        """Match taxa against Dyntaxa database."""
        return self.dyntaxa_api.match_dyntaxa_taxa(taxa_list)

    def construct_dyntaxa_table(self, taxon_ids: List[int]) -> pd.DataFrame:
        """Construct Dyntaxa table for given taxa."""
        return self.dyntaxa_api.construct_dyntaxa_table(taxon_ids)

    def get_worms_records(self, taxa_list: List[str]) -> pd.DataFrame:
        """Get WoRMS records for taxa."""
        return self.worms_api.get_worms_records(taxa_list)

    def add_worms_taxonomy(self, aphia_ids: List[int]) -> pd.DataFrame:
        """Add WoRMS taxonomy to data."""
        return self.worms_api.add_worms_taxonomy(aphia_ids)

    def get_worms_taxa(
        self,
        scientific_name: Optional[str] = None,
        aphia_id: Optional[int] = None,
        marine_only: bool = True,
        offset: int = 1,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Get WoRMS taxa information."""
        return self.worms_api.get_worms_taxa(
            scientific_name, aphia_id, marine_only, offset, limit
        )

    def match_algaebase_taxa(self, search_terms: List[str]) -> pd.DataFrame:
        """Match taxa against AlgaeBase."""
        return self.algaebase_api.match_algaebase_taxa(search_terms)

    def match_algaebase_genus(self, genus_names: List[str]) -> pd.DataFrame:
        """Match genera against AlgaeBase."""
        return self.algaebase_api.match_algaebase_genus(genus_names)

    def get_hab_list(self) -> pd.DataFrame:
        """Get HAB species list."""
        return self.ioc_hab_api.get_hab_list()

    def get_toxin_list(self) -> pd.DataFrame:
        """Get marine toxins list."""
        return self.ioc_toxins_api.get_toxin_list()

    def get_nordic_microalgae_taxa(
        self, search_params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Get Nordic microalgae taxa."""
        return self.nordic_microalgae_api.get_nordic_microalgae_taxa(search_params)

    def get_nua_harmfulness(self, taxon_ids: List[int]) -> pd.DataFrame:
        """Get NUA harmfulness information."""
        return self.nordic_microalgae_api.get_nua_harmfulness(taxon_ids)

    # ------------------------------------------------------------------
    # Freshwater Ecology accessors
    # ------------------------------------------------------------------
    def search_fwe_taxa(self, q: str, limit: int = 50) -> pd.DataFrame:
        """Search taxa via freshwaterecology.info (if configured)."""
        if not getattr(self, "fwe_api", None):
            self.logger.warning("FreshwaterEcology API client not initialized")
            return pd.DataFrame()
        return self.fwe_api.search_taxa(q, limit=limit)

    def get_fwe_occurrences(self, taxon_id: int, limit: int = 100) -> pd.DataFrame:
        """Fetch occurrence records from Freshwater Ecology for a given taxon id."""
        if not getattr(self, "fwe_api", None):
            self.logger.warning("FreshwaterEcology API client not initialized")
            return pd.DataFrame()
        return self.fwe_api.get_occurrences(taxon_id, limit=limit)

    # ------------------------------------------------------------------
    def get_obis_records(
        self, taxa_list: List[str], geometry: Optional[str] = None
    ) -> pd.DataFrame:
        """Get OBIS occurrence records."""
        # Note: geometry parameter not currently supported in OBISAPI
        return self.obis_api.get_obis_records(taxa_list)

    def lookup_xy(self, data: pd.DataFrame) -> pd.DataFrame:
        """Lookup coordinates for OBIS data."""
        return self.obis_api.lookup_xy(data)

    def get_nomp_list(self) -> pd.DataFrame:
        """Get NOMP biovolume list."""
        return self.plankton_toolbox_api.get_nomp_list()

    def read_ptbx(self, file_path: str) -> pd.DataFrame:
        """Read Plankton Toolbox files."""
        return self.plankton_toolbox_api.read_ptbx(file_path)
