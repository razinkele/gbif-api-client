#!/usr/bin/env python3
"""
Test script to simulate the analyze button click and check debug output.
"""

import logging
import os
import sys

import pandas as pd

logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import gbif_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gbif_client import GBIFClient  # noqa: E402


def test_button_click_simulation():
    """Simulate what happens when the analyze button is clicked."""

    logger.info("=== Simulating Analyze Button Click ===\n")

    # Check if sample file exists
    file_path = "sample_species.xlsx"
    if not os.path.exists(file_path):
        logger.error("ERROR: Sample file %s does not exist!", file_path)
        return

    logger.info("File exists: %s", file_path)

    # Simulate the file upload structure that Shiny creates
    file_info = [{"datapath": file_path}]
    logger.debug("Simulated file_info: %s", file_info)

    # Read the Excel file (this is what the reactive effect does)
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=None)
        species_list = df.iloc[1:, 0].dropna().tolist()  # Skip header row, first column

        logger.info("Successfully read Excel file")
        logger.info("DataFrame shape: %s", df.shape)
        logger.info("Species list (%s items): %s", len(species_list), species_list[:5])

        # Simulate progress state initialization
        progress_state = {
            "is_running": True,
            "current_species": "",
            "completed": 0,
            "total": len(species_list),
            "status": f"Starting analysis of {len(species_list)} species...",
        }

        logger.info("Progress state would be initialized: %s", progress_state)

        # Test GBIF client
        client = GBIFClient()
        logger.info("\nTesting GBIF client...")

        # Test with first species
        if species_list:
            first_species = species_list[0]
            logger.info("Testing with first species: %s", first_species)

            try:
                species_data = client.search_species(first_species, limit=1)
                if species_data:
                    logger.info(
                        "✅ Found species: %s", species_data[0]["scientificName"]
                    )
                else:
                    logger.info("❌ Species not found")
            except Exception as e:
                logger.exception("❌ Error searching species: %s", e)

    except Exception as e:
        logger.exception("ERROR during simulation: %s", e)


def test_reactive_values():
    """Test if reactive values work correctly."""
    logger.info("\n=== Testing Reactive Values ===")

    # Simulate reactive values
    progress_state = {
        "is_running": False,
        "current_species": "",
        "completed": 0,
        "total": 0,
        "status": "Ready",
    }
    logger.debug("Initial progress_state: %s", progress_state)

    # Simulate what happens when button is clicked
    progress_state = {
        "is_running": True,
        "current_species": "",
        "completed": 0,
        "total": 8,
        "status": "Starting analysis of 8 species...",
    }

    logger.debug("After button click: %s", progress_state)

    # Simulate progress updates
    for i in range(3):
        progress_state = {
            "is_running": True,
            "current_species": f"Species {i+1}",
            "completed": i,
            "total": 8,
            "status": f"Processing species {i+1}/8: Species {i+1}",
        }
        logger.debug("Progress update %s: %s", i + 1, progress_state)

    # Simulate completion
    progress_state = {
        "is_running": False,
        "current_species": "",
        "completed": 8,
        "total": 8,
        "status": "Analysis completed! Processed 8 species.",
    }

    logger.debug("Final state: %s", progress_state)


def test_progress_display():
    """Test the progress display logic."""
    logger.info("\n=== Testing Progress Display ===")

    # Test initial state
    state = {
        "is_running": False,
        "current_species": "",
        "completed": 0,
        "total": 0,
        "status": "Ready",
    }
    logger.info("Initial display should show: Upload file message")

    # Test running state
    state = {
        "is_running": True,
        "current_species": "Panthera leo",
        "completed": 2,
        "total": 8,
        "status": "Processing species 3/8: Panthera leo",
    }
    progress_percent = (
        (state["completed"] / state["total"]) * 100 if state["total"] > 0 else 0
    )
    logger.info(
        "Running display: %.1f%% complete, current: %s",
        progress_percent,
        state["current_species"],
    )


if __name__ == "__main__":
    test_button_click_simulation()
    test_reactive_values()
    test_progress_display()
