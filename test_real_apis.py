#!/usr/bin/env python3
"""
Test real APIs for all databases
"""

import logging

import requests

logger = logging.getLogger(__name__)


def test_worms():
    logger.info("Testing WoRMS API...")
    try:
        response = requests.get(
            "https://www.marinespecies.org/rest/AphiaRecordsByName/Salmo%20salar"
        )
        logger.info("WoRMS API Status: %s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            logger.info("WoRMS API Response: %s results", (len(data) if data else 0))
            if data:
                logger.debug("First result keys: %s", list(data[0].keys())[:5])
        else:
            logger.error("WoRMS API Error: %s", response.text)
    except Exception as e:
        logger.exception("WoRMS API Error: %s", e)


def test_obis():
    logger.info("\nTesting OBIS API...")
    try:
        response = requests.get(
            "https://api.obis.org/occurrence", params={"scientificname": "Salmo salar"}
        )
        logger.info("OBIS API Status: %s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            logger.info("OBIS API Response structure: %s", list(data.keys()))
            if "results" in data:
                logger.info("OBIS API Results: %s records", len(data["results"]))
                if data["results"]:
                    logger.debug(
                        "First result keys: %s", list(data["results"][0].keys())[:5]
                    )
        else:
            logger.error("OBIS API Error: %s", response.text)
    except Exception as e:
        logger.exception("OBIS API Error: %s", e)


def test_algaebase():
    logger.info("\nTesting AlgaeBase API...")
    try:
        # Try different AlgaeBase endpoints
        endpoints = [
            "https://www.algaebase.org/search/",
            "https://www.algaebase.org/api/",
            "https://www.algaebase.org/webservices/",
        ]
        for url in endpoints:
            try:
                response = requests.get(url, timeout=5)
                logger.info("AlgaeBase %s: Status %s", url, response.status_code)
                if response.status_code == 200:
                    logger.debug("Content preview: %s", response.text[:200])
                    break
            except Exception as e:
                logger.debug("AlgaeBase endpoint %s failed to respond: %s", url, e)
                continue
    except Exception as e:
        logger.exception("AlgaeBase API Error: %s", e)


def test_ioc_hab():
    logger.info("\nTesting IOC HAB API...")
    try:
        response = requests.get("https://www.marinespecies.org/hab/")
        logger.info("IOC HAB Status: %s", response.status_code)
        if response.status_code == 200:
            logger.debug("Content length: %s", len(response.text))
            # Look for API endpoints in the page
            if "api" in response.text.lower():
                logger.info("Found API references in HAB page")
    except Exception as e:
        logger.exception("IOC HAB API Error: %s", e)


def test_dyntaxa():
    logger.info("\nTesting Dyntaxa API...")
    try:
        # Try different Dyntaxa endpoints
        endpoints = [
            "https://species-environment.smhi.se/taxa/",
            "https://taxon.artdatabanken.se/",
            "https://api.artdatabanken.se/",
        ]
        for url in endpoints:
            try:
                response = requests.get(url, timeout=5)
                logger.info("Dyntaxa %s: Status %s", url, response.status_code)
                if response.status_code == 200:
                    logger.debug("Content preview: %s", response.text[:200])
                    break
            except Exception as e:
                logger.debug("Dyntaxa endpoint %s failed to respond: %s", url, e)
                continue
    except Exception as e:
        logger.exception("Dyntaxa API Error: %s", e)


if __name__ == "__main__":
    test_worms()
    test_obis()
    test_algaebase()
    test_ioc_hab()
    test_dyntaxa()
