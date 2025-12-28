#!/usr/bin/env python3
"""
Test script for SHARK Client backend functionality.
Tests all major methods to ensure they work correctly.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

import pandas as pd

from shark_client import SHARKClient

logger = logging.getLogger(__name__)


def test_shark_client():  # noqa: C901
    """Test all SHARK client methods."""
    logger.info("🦈 Testing SHARK Client Backend Functionality")
    logger.info("%s", "=" * 50)

    # Test with mock data enabled
    client = SHARKClient(use_mock=True)

    # Test 1: Get datasets
    print("\n1. Testing get_datasets()...")
    try:
        datasets = client.get_datasets()
        print(f"   ✓ Retrieved {len(datasets)} datasets")
        if len(datasets) > 0:
            logger.info(
                "   ✓ Sample dataset: %s",
                datasets.iloc[0].to_dict() if not datasets.empty else "None",
            )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 2: Get stations
    print("\n2. Testing get_stations()...")
    try:
        stations = client.get_stations()
        print(f"   ✓ Retrieved {len(stations)} stations")
        if len(stations) > 0:
            logger.info(
                "   ✓ Sample station: %s",
                stations.iloc[0].to_dict() if not stations.empty else "None",
            )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 3: Get parameters
    print("\n3. Testing get_parameters()...")
    try:
        parameters = client.get_parameters()
        print(f"   ✓ Retrieved {len(parameters)} parameters")
        if len(parameters) > 0:
            logger.info(
                "   ✓ Sample parameter: %s",
                parameters.iloc[0].to_dict() if not parameters.empty else "None",
            )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 4: Get SHARK options
    print("\n4. Testing get_shark_options()...")
    try:
        options = client.get_shark_options()
        logger.info(
            "   ✓ Retrieved options: %s", list(options.keys()) if options else "None"
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 5: Get SHARK codes
    print("\n5. Testing get_shark_codes()...")
    try:
        codes = client.get_shark_codes()
        logger.info("   ✓ Retrieved codes: %s", list(codes.keys()) if codes else "None")
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 6: Get statistics
    print("\n6. Testing get_shark_statistics()...")
    try:
        stats = client.get_shark_statistics()
        logger.info(
            "   ✓ Retrieved statistics: %s", list(stats.keys()) if stats else "None"
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 7: Get table counts
    print("\n7. Testing get_shark_table_counts()...")
    try:
        counts = client.get_shark_table_counts()
        logger.info(
            "   ✓ Retrieved table counts: %s", list(counts.keys()) if counts else "None"
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 8: Search data (with minimal parameters to avoid large responses)
    print("\n8. Testing search_data()...")
    try:
        data = client.search_data(limit=5)  # Small limit for testing
        logger.info("   ✓ Retrieved %s records", len(data))
        if len(data) > 0:
            logger.info("   ✓ Columns: %s", list(data.columns))
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 9: Get data summary
    print("\n9. Testing get_data_summary()...")
    try:
        summary = client.get_data_summary()
        logger.info(
            "   ✓ Retrieved summary: %s", list(summary.keys()) if summary else "None"
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 10: Quality control info
    print("\n10. Testing get_quality_control_info()...")
    try:
        # Try with a sample dataset if available
        datasets = client.get_datasets()
        if not datasets.empty:
            sample_dataset = (
                datasets.iloc[0]["id"] if "id" in datasets.columns else None
            )
            if sample_dataset:
                qc_info = client.get_quality_control_info(sample_dataset)
                logger.info(
                    "   ✓ Retrieved QC info for %s: %s",
                    sample_dataset,
                    list(qc_info.keys()) if qc_info else "None",
                )
            else:
                logger.info("   - No dataset ID available for QC test")
        else:
            logger.info("   - No datasets available for QC test")
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 11: Parameter info
    print("\n11. Testing get_parameter_info()...")
    try:
        # Try with a sample parameter if available
        parameters = client.get_parameters()
        if not parameters.empty:
            sample_param = (
                parameters.iloc[0]["id"] if "id" in parameters.columns else None
            )
            if sample_param:
                param_info = client.get_parameter_info(sample_param)
                logger.info(
                    "   ✓ Retrieved parameter info for %s: %s",
                    sample_param,
                    list(param_info.keys()) if param_info else "None",
                )
            else:
                logger.info("   - No parameter ID available for info test")
        else:
            logger.info("   - No parameters available for info test")
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 12: Station info
    print("\n12. Testing get_station_info()...")
    try:
        # Try with a sample station if available
        stations = client.get_stations()
        if not stations.empty:
            sample_station = (
                stations.iloc[0]["id"] if "id" in stations.columns else None
            )
            if sample_station:
                station_info = client.get_station_info(sample_station)
                logger.info(
                    "   ✓ Retrieved station info for %s: %s",
                    sample_station,
                    list(station_info.keys()) if station_info else "None",
                )
            else:
                logger.info("   - No station ID available for info test")
        else:
            logger.info("   - No stations available for info test")
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 13: Outlier detection
    print("\n13. Testing check_outliers()...")
    try:
        # Create sample data for testing
        sample_data = pd.DataFrame(
            {
                "value": [1, 2, 3, 4, 5, 100],  # 100 is an outlier
                "other_col": ["a", "b", "c", "d", "e", "f"],
            }
        )
        outliers = client.check_outliers(sample_data, "value", method="iqr")
        logger.info(
            "   ✓ Outlier detection completed: %s outliers found",
            outliers["is_outlier"].sum(),
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    # Test 14: Geographic validation
    print("\n14. Testing check_geographic_data()...")
    try:
        # Create sample geographic data
        geo_data = pd.DataFrame(
            {
                "latitude": [55.0, 56.0, 0.0, 57.0],  # 0.0 is invalid
                "longitude": [12.0, 13.0, 0.0, 14.0],  # 0.0 is invalid
                "station": ["A", "B", "C", "D"],
            }
        )
        geo_check = client.check_geographic_data(geo_data)
        logger.info(
            "   ✓ Geographic validation completed: %s records checked", len(geo_check)
        )
    except Exception as e:
        logger.exception("   ✗ Error: %s", e)

    logger.info("%s", "\n" + "=" * 50)
    logger.info("🦈 SHARK Client Backend Testing Complete!")
    logger.info(
        "Note: Some tests may fail if SHARK API is inaccessible."
    )


if __name__ == "__main__":
    test_shark_client()
