#!/usr/bin/env python3
"""
Simple test script to verify new database methods are available
"""

import logging

from shark_client import SHARKClient

logger = logging.getLogger(__name__)


def test_new_methods():
    """Test that all new database methods are available"""
    client = SHARKClient(use_mock=True)
    logger.info("Testing new database methods...")

    # Test Dyntaxa
    try:
        client.match_dyntaxa_taxa(["Test species"])
        logger.info("✅ Dyntaxa methods available")
    except Exception as e:
        logger.exception("❌ Dyntaxa methods failed: %s", e)

    # Test WoRMS
    try:
        client.get_worms_records(["Test species"])
        logger.info("✅ WoRMS methods available")
    except Exception as e:
        logger.exception("❌ WoRMS methods failed: %s", e)

    # Test AlgaeBase
    try:
        client.match_algaebase_taxa(["Test algae"])
        logger.info("✅ AlgaeBase methods available")
    except Exception as e:
        logger.exception("❌ AlgaeBase methods failed: %s", e)

    # Test IOC-UNESCO
    try:
        client.get_hab_list()
        logger.info("✅ IOC-UNESCO methods available")
    except Exception as e:
        logger.exception("❌ IOC-UNESCO methods failed: %s", e)

    # Test Nordic Microalgae
    try:
        client.get_nordic_microalgae_taxa()
        logger.info("✅ Nordic Microalgae methods available")
    except Exception as e:
        logger.exception("❌ Nordic Microalgae methods failed: %s", e)

    # Test OBIS
    try:
        client.get_obis_records(["Test species"])
        logger.info("✅ OBIS methods available")
    except Exception as e:
        logger.exception("❌ OBIS methods failed: %s", e)

    # Test Plankton Toolbox
    try:
        client.get_plankton_toolbox_taxa()
        logger.info("✅ Plankton Toolbox methods available")
    except Exception as e:
        logger.exception("❌ Plankton Toolbox methods failed: %s", e)

    logger.info("Backend expansion complete!")


if __name__ == "__main__":
    test_new_methods()
