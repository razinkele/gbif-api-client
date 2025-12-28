"""
Centralized mock data for marine API clients.

This module provides mock/fallback data for all marine API implementations,
eliminating duplication across individual API files.
"""

import functools
from typing import Any, Dict

import pandas as pd


# SHARK Mock Data
@functools.lru_cache(maxsize=1)
def get_mock_shark_datasets() -> pd.DataFrame:
    """Return mock SHARK dataset data for testing."""
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


@functools.lru_cache(maxsize=1)
def get_mock_shark_stations() -> pd.DataFrame:
    """Return mock SHARK station data for testing."""
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
                "id": "B1",
                "name": "Bornholm Basin",
                "latitude": 55.15,
                "longitude": 15.59,
            },
        ]
    )


@functools.lru_cache(maxsize=1)
def get_mock_shark_parameters() -> pd.DataFrame:
    """Return mock SHARK parameter data for testing."""
    return pd.DataFrame(
        [
            {
                "id": "TEMP",
                "name": "Temperature",
                "unit": "°C",
            },
            {
                "id": "SALN",
                "name": "Salinity",
                "unit": "PSU",
            },
            {
                "id": "DOXY",
                "name": "Dissolved Oxygen",
                "unit": "ml/l",
            },
            {
                "id": "CPHL",
                "name": "Chlorophyll-a",
                "unit": "µg/l",
            },
        ]
    )


# AlgaeBase Mock Data
@functools.lru_cache(maxsize=1)
def get_mock_algaebase_taxa() -> pd.DataFrame:
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


@functools.lru_cache(maxsize=1)
def get_mock_algaebase_genus() -> pd.DataFrame:
    """Return mock AlgaeBase genus data for testing."""
    return pd.DataFrame(
        [
            {
                "genus": "Skeletonema",
                "family": "Skeletonemataceae",
                "class": "Bacillariophyceae",
            },
            {
                "genus": "Thalassiosira",
                "family": "Thalassiosiraceae",
                "class": "Bacillariophyceae",
            },
            {
                "genus": "Chaetoceros",
                "family": "Chaetocerotaceae",
                "class": "Bacillariophyceae",
            },
        ]
    )


# Dyntaxa Mock Data
@functools.lru_cache(maxsize=1)
def get_mock_dyntaxa_taxa() -> pd.DataFrame:
    """Return mock Dyntaxa taxa data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificName": "Fucus vesiculosus",
                "taxonId": 12345,
                "rank": "species",
                "kingdom": "Chromista",
            },
            {
                "scientificName": "Laminaria digitata",
                "taxonId": 12346,
                "rank": "species",
                "kingdom": "Chromista",
            },
        ]
    )


# WoRMS Mock Data
@functools.lru_cache(maxsize=1)
def get_mock_worms_taxa() -> pd.DataFrame:
    """Return mock WoRMS taxa data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificname": "Fucus vesiculosus",
                "AphiaID": 144121,
                "rank": "Species",
                "kingdom": "Chromista",
            },
            {
                "scientificname": "Laminaria digitata",
                "AphiaID": 145729,
                "rank": "Species",
                "kingdom": "Chromista",
            },
        ]
    )


# OBIS Mock Data
def get_mock_obis_occurrences() -> pd.DataFrame:
    """Return mock OBIS occurrence data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificName": "Fucus vesiculosus",
                "decimalLatitude": 58.5,
                "decimalLongitude": 11.5,
                "eventDate": "2023-06-15",
            },
            {
                "scientificName": "Laminaria digitata",
                "decimalLatitude": 58.6,
                "decimalLongitude": 11.6,
                "eventDate": "2023-06-16",
            },
        ]
    )


# Nordic Microalgae Mock Data
def get_mock_nordic_microalgae() -> pd.DataFrame:
    """Return mock Nordic Microalgae data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificName": "Skeletonema marinoi",
                "genus": "Skeletonema",
                "class": "Bacillariophyceae",
            },
            {
                "scientificName": "Chaetoceros socialis",
                "genus": "Chaetoceros",
                "class": "Bacillariophyceae",
            },
        ]
    )


# IOC-HAB Mock Data
def get_mock_ioc_hab_taxa() -> pd.DataFrame:
    """Return mock IOC-HAB taxa data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificName": "Alexandrium tamarense",
                "genus": "Alexandrium",
                "harmfulType": "PSP",
            },
            {
                "scientificName": "Dinophysis acuta",
                "genus": "Dinophysis",
                "harmfulType": "DSP",
            },
        ]
    )


# IOC Toxins Mock Data
def get_mock_ioc_toxins() -> Dict[str, Any]:
    """Return mock IOC toxins data for testing."""
    return {
        "toxins": [
            {"name": "Saxitoxin", "type": "PSP", "severity": "high"},
            {"name": "Okadaic Acid", "type": "DSP", "severity": "medium"},
        ]
    }


# Plankton Toolbox Mock Data
def get_mock_plankton_toolbox_taxa() -> pd.DataFrame:
    """Return mock Plankton Toolbox taxa data for testing."""
    return pd.DataFrame(
        [
            {
                "scientificName": "Skeletonema costatum",
                "genus": "Skeletonema",
                "biovolume": 250.5,
            },
            {
                "scientificName": "Thalassiosira rotula",
                "genus": "Thalassiosira",
                "biovolume": 150.2,
            },
        ]
    )
