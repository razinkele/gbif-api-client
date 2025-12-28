#!/usr/bin/env python3
"""
Test script to simulate Shiny reactive system and test progress tracking.
"""

import logging
import os
import sys

import pandas as pd

logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MockInput:
    """Mock Shiny input object"""

    def __init__(self):
        self._analyze_btn = 0
        self._species_file = None

    def analyze_btn(self):
        return self._analyze_btn

    def species_file(self):
        return self._species_file

    def set_analyze_btn(self, value):
        self._analyze_btn = value

    def set_species_file(self, file_info):
        self._species_file = file_info


class MockReactiveValue:
    """Mock reactive.Value"""

    def __init__(self, initial_value):
        self._value = initial_value
        self._listeners = []

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        # Notify listeners
        for listener in self._listeners:
            listener()

    def add_listener(self, listener):
        self._listeners.append(listener)


def test_reactive_system():
    """Test the reactive system manually"""

    logger.info("=== Testing Reactive System ===\n")

    # Create mock objects
    input_mock = MockInput()
    progress_state = MockReactiveValue(
        {
            "is_running": False,
            "current_species": "",
            "completed": 0,
            "total": 0,
            "status": "Ready",
        }
    )

    # Mock the bulk_analysis_trigger
    def bulk_analysis_trigger():
        btn_click = input_mock.analyze_btn()
        file_info = input_mock.species_file()
        logger.debug(
            "bulk_analysis_trigger called - btn_click: %s, file_info: %s",
            btn_click,
            file_info is not None,
        )
        if btn_click > 0 and file_info is not None:
            logger.debug("=== BULK ANALYSIS TRIGGERED ===")
            return True
        return False

    # Mock the run_bulk_analysis
    def run_bulk_analysis():
        if not bulk_analysis_trigger():
            return

        logger.debug("Running bulk analysis...")

        file_info = input_mock.species_file()
        if not file_info:
            logger.debug("No file info - returning")
            return

        # Read the Excel file
        file_content = file_info[0]["datapath"]
        logger.debug("File path: %s", file_content)

        try:
            df = pd.read_excel(file_content, sheet_name=0, header=None)
            species_list = df.iloc[1:, 0].dropna().tolist()
            logger.debug("Found %s species: %s...", len(species_list), species_list[:3])

            # Initialize progress
            progress_state.set(
                {
                    "is_running": True,
                    "current_species": "",
                    "completed": 0,
                    "total": len(species_list),
                    "status": f"Starting analysis of {len(species_list)} species...",
                }
            )
            logger.debug("Progress state set to: %s", progress_state.get())

        except Exception as e:
            logger.exception("Error during bulk analysis: %s", e)

    # Mock progress_display
    def progress_display():
        state = progress_state.get()
        logger.debug("Progress display called - state: %s", state)

        if state["total"] == 0:
            logger.debug("Would show initial message")
            return

        progress_percent = (
            (state["completed"] / state["total"]) * 100 if state["total"] > 0 else 0
        )
        logger.debug("Progress: %.1f%%, Status: %s", progress_percent, state["status"])

    # Test initial state
    logger.info("--- Initial State ---")
    bulk_analysis_trigger()
    progress_display()

    # Simulate file upload
    logger.info("\n--- Simulating File Upload ---")
    file_info = [{"datapath": "sample_species.xlsx"}]
    input_mock.set_species_file(file_info)
    bulk_analysis_trigger()
    progress_display()

    # Simulate button click
    logger.info("\n--- Simulating Button Click ---")
    input_mock.set_analyze_btn(1)
    bulk_analysis_trigger()
    run_bulk_analysis()
    progress_display()

    logger.info("\n=== Test Complete ===")


if __name__ == "__main__":
    test_reactive_system()
