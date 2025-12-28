"""
Custom exceptions for the Marine & Biodiversity Data Explorer.

This module defines a hierarchy of custom exceptions to provide better
error handling and more informative error messages throughout the application.
"""


class BiodiversityExplorerError(Exception):
    """Base exception for all Marine & Biodiversity Data Explorer errors."""
    pass


# Database-related exceptions
class DatabaseError(BiodiversityExplorerError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when the database file is not found."""
    pass


class InvalidDatabaseSchemaError(DatabaseError):
    """Raised when database schema is invalid or corrupted."""
    pass


# Data validation exceptions
class DataValidationError(BiodiversityExplorerError):
    """Base exception for data validation errors."""
    pass


class InvalidFileFormatError(DataValidationError):
    """Raised when uploaded file format is invalid."""
    pass


class InvalidFileContentError(DataValidationError):
    """Raised when file content is invalid or corrupted."""
    pass


class FileTooLargeError(DataValidationError):
    """Raised when uploaded file exceeds size limit."""
    pass


class MissingColumnError(DataValidationError):
    """Raised when required column is missing from data."""
    pass


class InvalidCoordinatesError(DataValidationError):
    """Raised when geographic coordinates are invalid."""
    pass


# API-related exceptions
class APIError(BiodiversityExplorerError):
    """Base exception for API-related errors."""
    pass


class APIConnectionError(APIError):
    """Raised when API connection fails."""
    pass


class APITimeoutError(APIError):
    """Raised when API request times out."""
    pass


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class APIResponseError(APIError):
    """Raised when API returns an error response."""
    pass


class InvalidAPIResponseError(APIError):
    """Raised when API response format is invalid."""
    pass


# Trait-related exceptions
class TraitError(BiodiversityExplorerError):
    """Base exception for trait-related errors."""
    pass


class TraitNotFoundError(TraitError):
    """Raised when trait is not found in database."""
    pass


class InvalidTraitValueError(TraitError):
    """Raised when trait value is invalid for the trait type."""
    pass


class TraitQueryError(TraitError):
    """Raised when trait query fails."""
    pass


# Cache-related exceptions
class CacheError(BiodiversityExplorerError):
    """Base exception for cache-related errors."""
    pass


class CacheKeyError(CacheError):
    """Raised when cache key is invalid."""
    pass


class CacheStorageError(CacheError):
    """Raised when cache storage operation fails."""
    pass


# Export-related exceptions
class ExportError(BiodiversityExplorerError):
    """Base exception for export-related errors."""
    pass


class InvalidExportFormatError(ExportError):
    """Raised when requested export format is not supported."""
    pass


class ExportFileError(ExportError):
    """Raised when export file operation fails."""
    pass


class InvalidExportDataError(ExportError):
    """Raised when data to export is invalid."""
    pass


# Species/Taxonomy exceptions
class SpeciesError(BiodiversityExplorerError):
    """Base exception for species-related errors."""
    pass


class SpeciesNotFoundError(SpeciesError):
    """Raised when species is not found."""
    pass


class InvalidSpeciesNameError(SpeciesError):
    """Raised when species name is invalid."""
    pass


class AmbiguousSpeciesError(SpeciesError):
    """Raised when species name matches multiple taxa."""
    pass


# Configuration exceptions
class ConfigurationError(BiodiversityExplorerError):
    """Base exception for configuration errors."""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration value is invalid."""
    pass


def get_error_message(error: Exception) -> str:
    """
    Get a user-friendly error message from an exception.

    Args:
        error: Exception instance

    Returns:
        Formatted error message string

    Example:
        try:
            raise InvalidFileFormatError("File must be .xlsx format")
        except Exception as e:
            message = get_error_message(e)
            # "Invalid File Format: File must be .xlsx format"
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Format error type nicely (e.g., "InvalidFileFormatError" -> "Invalid File Format")
    formatted_type = error_type.replace("Error", "").replace("_", " ")
    # Add spaces before capitals
    formatted_type = ''.join([' ' + c if c.isupper() else c for c in formatted_type]).strip()

    if error_msg:
        return f"{formatted_type}: {error_msg}"
    else:
        return formatted_type


def wrap_exception(func):
    """
    Decorator to wrap exceptions with more context.

    Usage:
        @wrap_exception
        def my_function():
            # function code
            pass
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BiodiversityExplorerError:
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise BiodiversityExplorerError(
                f"Unexpected error in {func.__name__}: {str(e)}"
            ) from e

    return wrapper
