import logging

import requests

logger = logging.getLogger(__name__)

# Try some known Swedish biodiversity API endpoints
endpoints = [
    "https://www.artdatabanken.se/",
    "https://dyntaxa.artdatabanken.se/",
    "https://taxon.artdatabanken.se/",
    "https://api.artdatabanken.se/taxon/v1/",
    "https://dyntaxa.artdatabanken.se/api/v1/",
]

for endpoint in endpoints:
    try:
        response = requests.get(endpoint, timeout=10)
        logger.info("%s: Status %s", endpoint, response.status_code)
        if response.status_code == 200:
            if "text/html" in response.headers.get("content-type", ""):
                # Try to extract title
                text = response.text
                if "<title>" in text:
                    title = text.split("<title>")[1].split("</title>")[0]
                    logger.info("  Title: %s", title)
                else:
                    logger.info("  Content length: %s", len(text))
            else:
                logger.info("  Content type: %s", response.headers.get("content-type"))
    except Exception as e:
        logger.exception("%s: Error - %s", endpoint, str(e)[:200])
