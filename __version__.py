"""
Marine & Biodiversity Data Explorer version information.
"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# Release information
__title__ = "Marine & Biodiversity Data Explorer"
__description__ = "Comprehensive marine biodiversity data integration platform with trait ontology database"
__author__ = "Marine Biodiversity Team"
__license__ = "MIT"
__copyright__ = "Copyright 2024-2025 Marine Biodiversity Team"

# Build information
__build_date__ = "2025-12-26"
__python_requires__ = ">=3.10"

# Feature flags
FEATURES = {
    "trait_database": True,
    "multi_database_integration": True,
    "bulk_analysis": True,
    "size_data_detection": True,
    "interactive_maps": True,
}

# Database versions
DATABASE_VERSIONS = {
    "trait_ontology": "1.0.0",
    "schema_version": "1.0",
}

def get_version():
    """Return the version string."""
    return __version__

def get_version_info():
    """Return the version as a tuple."""
    return __version_info__

def get_full_version():
    """Return full version information."""
    return f"{__title__} v{__version__} ({__build_date__})"
