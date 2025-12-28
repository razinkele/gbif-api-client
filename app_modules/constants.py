"""
Application constants for the Marine & Biodiversity Data Explorer.

This module centralizes all constant values used throughout the application.
"""

# Country codes for filtering
COUNTRY_CODES = [
    "",
    "US",
    "CA",
    "GB",
    "DE",
    "FR",
    "ES",
    "IT",
    "NL",
    "BE",
    "CH",
    "AT",
    "SE",
    "NO",
    "DK",
    "FI",
    "PL",
    "CZ",
    "SK",
    "HU",
    "RO",
    "BG",
    "GR",
    "PT",
    "IE",
    "AU",
    "NZ",
    "BR",
    "AR",
    "MX",
    "JP",
    "CN",
    "IN",
    "ZA",
    "EG",
    "KE",
    "TZ",
    "UG",
    "GH",
    "NG",
    "MA",
    "TN",
    "DZ",
]

# Keywords for detecting size-related data in records
SIZE_INDICATORS = [
    "size",
    "length",
    "width",
    "diameter",
    "volume",
    "biovolume",
    "μm",
    "micrometer",
    "micrometers",
    "cell",
    "biomass",
    "carbon",
]

# Fields that may contain size data
SIZE_FIELDS = [
    "organismQuantity",
    "individualCount",
    "sampleSizeValue",
    "dynamicProperties",
]

# Keywords in sampling protocols that indicate size information
SAMPLING_PROTOCOL_KEYWORDS = ["mesh", "μm", "micrometer", "size fraction", "net size"]

# Application limits
DEFAULT_OCCURRENCE_LIMIT = 100
BULK_ANALYSIS_SAMPLE_SIZE = 10  # Reduced from 20 for faster analysis
MAX_SIZE_MEASUREMENTS_DISPLAY = 3
