#!/usr/bin/env python3
"""
Test SHARK client mock data integration
"""

import logging

from shark_client import SHARKClient

logger = logging.getLogger(__name__)


def test_shark_mock_integration():
    logger.info("🦈 Testing SHARK Client Mock Data Integration...")

    # Initialize client with mock data enabled
    client = SHARKClient(use_mock=True)

    # Test datasets
    datasets = client.get_datasets()
    logger.info("✅ Datasets loaded: %s items", len(datasets))
    logger.info(
        "   Names: %s", list(datasets["name"]) if not datasets.empty else "None"
    )

    # Test stations
    stations = client.get_stations()
    logger.info("✅ Stations loaded: %s items", len(stations))
    logger.info(
        "   Names: %s", list(stations["name"]) if not stations.empty else "None"
    )

    # Test parameters
    parameters = client.get_parameters()
    logger.info("✅ Parameters loaded: %s items", len(parameters))
    logger.info(
        "   Names: %s", list(parameters["name"]) if not parameters.empty else "None"
    )

    # Test that the data can be converted to dict format for Shiny
    try:
        dataset_dict = {row["id"]: row["name"] for _, row in datasets.iterrows()}
        station_dict = {row["id"]: row["name"] for _, row in stations.iterrows()}
        parameter_dict = {row["id"]: row["name"] for _, row in parameters.iterrows()}

        logger.info("✅ Dataset dict: %s", dataset_dict)
        logger.info("✅ Station dict: %s", station_dict)
        logger.info("✅ Parameter dict: %s", parameter_dict)

        logger.info("🎉 SHARK mock data integration test PASSED!")
        return True

    except Exception as e:
        logger.exception("❌ Error converting to dict: %s", e)
        return False


if __name__ == "__main__":
    test_shark_mock_integration()
