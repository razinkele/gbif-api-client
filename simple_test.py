#!/usr/bin/env python3
import sys

sys.path.insert(0, r"c:\Users\DELL\OneDrive - ku.lt\HORIZON_EUROPE\Net\gbif-api-client")

import logging

logger = logging.getLogger(__name__)

try:
    from shark_client import SHARKClient

    logger.info("Import successful")
    client = SHARKClient(use_mock=True)
    logger.info("Client created successfully")
    logger.info("Endpoints available: %s", len(client.endpoints))
    logger.info("Test completed successfully")
except Exception as e:
    logger.exception("Error: %s", e)
