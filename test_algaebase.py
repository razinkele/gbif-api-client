import logging

import requests

logger = logging.getLogger(__name__)

# Test AlgaeBase API endpoints
base_url = "https://www.algaebase.org/api/"
endpoints = ["taxa", "search", "genus", "species"]

for endpoint in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=10)
        logger.info("AlgaeBase %s: Status %s", endpoint, response.status_code)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "unknown")
            logger.info("  Content type: %s", content_type)
            if "json" in content_type:
                try:
                    data = response.json()
                    logger.info("  JSON response type: %s", type(data))
                    if isinstance(data, list) and len(data) > 0:
                        logger.info("  Sample keys: %s", list(data[0].keys())[:5])
                    elif isinstance(data, dict):
                        logger.info("  Dict keys: %s", list(data.keys())[:5])
                except Exception as e:
                    logger.debug("  Not valid JSON: %s", e)
    except Exception as e:
        logger.exception("AlgaeBase %s: Error %s", endpoint, e)
