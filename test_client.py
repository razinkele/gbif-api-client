#!/usr/bin/env python3
"""
Test script for GBIF API client
"""

import logging

from gbif_client import GBIFClient

logger = logging.getLogger(__name__)


def test_client():
    client = GBIFClient()

    # Test species search
    logger.info("Testing species search for 'Ursus arctos'...")
    species = client.search_species("Ursus arctos", limit=5)
    logger.info("Found %s species", len(species))
    if species:
        logger.info("First result: %s", species[0]["scientificName"])

    # Test occurrences
    if species:
        taxon_key = species[0]["key"]
        logger.info("\nTesting occurrences for taxon key %s...", taxon_key)
        occ = client.search_occurrences(taxon_key=taxon_key, limit=5)
        logger.info("Found %s occurrences", len(occ.get("results", [])))
        if occ.get("results"):
            logger.info("Total count: %s", occ["count"])

    logger.info("\nAPI client test completed successfully!")


if __name__ == "__main__":
    test_client()
