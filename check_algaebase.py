import logging
import re

import requests

logger = logging.getLogger(__name__)

# Check AlgaeBase main site for API information
response = requests.get("https://www.algaebase.org/", timeout=10)
logger.info("AlgaeBase main site status: %s", response.status_code)
if response.status_code == 200:
    content = response.text.lower()
    if "api" in content:
        logger.info("API mentioned on main site")
        # Look for API links
        api_links = re.findall(r'href="([^"]*api[^"]*)"', content)
        logger.info("Potential API links: %s", api_links[:5])
    else:
        logger.info("No API mentioned on main site")

# Also check if there's a search API
search_url = "https://www.algaebase.org/search/?q=test"
try:
    response = requests.get(search_url, timeout=10)
    logger.info("Search URL status: %s", response.status_code)
    if "json" in response.headers.get("content-type", ""):
        logger.info("Search returns JSON")
    else:
        logger.info("Search returns HTML")
except Exception as e:
    logger.error("Search error: %s", e)
