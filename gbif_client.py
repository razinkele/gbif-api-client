"""
GBIF API Client using pygbif with error handling
"""

try:
    from pygbif import maps, occurrences, registry, species

    _HAS_PYGBIF = True
except Exception:
    species = occurrences = registry = maps = None
    _HAS_PYGBIF = False

import logging

logger = logging.getLogger(__name__)


class GBIFClient:
    def __init__(self):
        if not _HAS_PYGBIF:
            logger.warning("pygbif not installed; GBIF methods will return defaults")

    def search_species(self, name: str, limit: int = 10) -> list:
        """
        Search for species by name.

        Args:
            name: Species name to search for
            limit: Maximum number of results to return

        Returns:
            List of species matches or empty list on error

        Raises:
            ValueError: If name is empty or invalid
        """
        if not name or not str(name).strip():
            raise ValueError("Species name cannot be empty")

        if not _HAS_PYGBIF:
            logger.debug("pygbif missing; returning empty species list for %s", name)
            return []

        try:
            result = species.name_suggest(q=name, limit=limit)
            return result if result else []
        except Exception as e:
            logger.error(f"Error searching for species '{name}': {e}")
            raise

    def get_species_info(self, taxon_key: int) -> dict:
        """
        Get detailed species information.

        Args:
            taxon_key: GBIF taxon key

        Returns:
            Species information dict or None on error

        Raises:
            ValueError: If taxon_key is invalid
        """
        if not taxon_key:
            raise ValueError("Taxon key cannot be empty")

        if not _HAS_PYGBIF:
            logger.debug("pygbif missing; get_species_info None for %s", taxon_key)
            return None

        try:
            result = species.name_usage(key=taxon_key)
            return result
        except Exception as e:
            logger.error(f"Error getting species info for taxon_key {taxon_key}: {e}")
            raise

    def search_occurrences(
        self, taxon_key: int = None, country: str = None, limit: int = 20, offset: int = 0
    ) -> dict:
        """
        Search for occurrences.

        Args:
            taxon_key: GBIF taxon key (optional)
            country: ISO country code (optional)
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            Dict with occurrence results or empty dict on error
        """
        if not _HAS_PYGBIF:
            logger.debug("pygbif missing; search_occurrences empty for %s", taxon_key)
            return {}

        try:
            result = occurrences.search(
                taxonKey=taxon_key, country=country, limit=limit, offset=offset
            )
            return result if result else {}
        except Exception as e:
            logger.error("Error searching occurrences: %s", e)
            raise

    def get_occurrence_count(self, taxon_key=None, country=None):
        """
        Get count of occurrences.

        Args:
            taxon_key: GBIF taxon key (optional)
            country: ISO country code (optional)

        Returns:
            Integer count or 0 on error
        """
        if not _HAS_PYGBIF:
            logger.debug("pygbif missing; get_occurrence_count=0 for %s", taxon_key)
            return 0

        try:
            result = occurrences.search(taxonKey=taxon_key, country=country, limit=0)
            return result.get("count", 0) if result else 0
        except Exception as e:
            logger.error("Error getting occurrence count: %s", e)
            return 0

    def get_datasets(self, limit: int = 10) -> list:
        """
        Get list of datasets.

        Args:
            limit: Maximum number of datasets to return

        Returns:
            List of datasets or empty list on error
        """
        if not _HAS_PYGBIF:
            logger.debug("pygbif not available; get_datasets returning empty list")
            return []

        try:
            result = registry.dataset(limit=limit)
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return []

    def get_map_url(self, taxon_key: int = None, style: str = "classic.poly") -> str:
        """
        Get map URL for species distribution.

        Args:
            taxon_key: GBIF taxon key (optional)
            style: Map style

        Returns:
            String URL for the map
        """
        base_url = "https://api.gbif.org/v2/map/occurrence/density/{z}/{x}/{y}.png"
        params = (
            f"?taxonKey={taxon_key}&style={style}" if taxon_key else f"?style={style}"
        )
        return base_url + params

    def download_occurrences(self, taxon_key, format="SIMPLE_CSV"):
        """
        Request a download (requires authentication).

        Args:
            taxon_key: GBIF taxon key
            format: Download format

        Returns:
            Information message about download requirements
        """
        return "Download requires GBIF account; use web interface or API with auth."
