"""
Utility functions for the Marine & Biodiversity Data Explorer.

This module contains helper functions for data processing and analysis.
"""

import os
from typing import List, Tuple, Dict, Any, Optional
import pandas as pd

from .constants import (
    SAMPLING_PROTOCOL_KEYWORDS,
    SIZE_FIELDS,
    SIZE_INDICATORS,
)
from .exceptions import (
    DataValidationError,
    InvalidFileFormatError,
    InvalidFileContentError,
    FileTooLargeError
)


def detect_size_data(record: dict) -> Tuple[bool, List[str]]:
    """
    Detect if a GBIF occurrence record contains size-related data.

    Checks multiple sources for size information:
    1. MeasurementOrFact extensions
    2. Traditional size fields (organismQuantity, individualCount, etc.)
    3. Dynamic properties with size indicators
    4. Sampling protocol descriptions

    Args:
        record: GBIF occurrence record dictionary

    Returns:
        Tuple of (has_size_data, size_measurements) where:
        - has_size_data: Boolean indicating if size data was found
        - size_measurements: List of strings describing the found measurements
    """
    has_size_data = False
    size_measurements = []

    # Check for available extensions (MeasurementOrFact)
    if "extensions" in record and record["extensions"]:
        extensions_list = list(record["extensions"].keys())
        for ext_name in extensions_list:
            if "Measurement" in ext_name or "Fact" in ext_name:
                has_size_data = True
                size_measurements.append(f"Has {ext_name.split('/')[-1]} extension")
                return has_size_data, size_measurements

    # Check traditional fields for backward compatibility
    for field in SIZE_FIELDS:
        if field in record and record[field] is not None:
            if field == "dynamicProperties":
                if isinstance(record[field], str) and record[field].strip():
                    # Check for size fraction information
                    dynamic_data = record[field].lower()
                    if any(term in dynamic_data for term in SIZE_INDICATORS):
                        has_size_data = True
                        size_measurements.append(
                            f"Dynamic properties: {record[field][:50]}..."
                        )
                        return has_size_data, size_measurements
            elif record[field] != "" and str(record[field]).lower() not in [
                "null",
                "none",
                "nan",
            ]:
                has_size_data = True
                size_measurements.append(f"{field}: {record[field]}")
                return has_size_data, size_measurements

    # Check samplingProtocol for size fraction info
    if "samplingProtocol" in record and record["samplingProtocol"]:
        protocol = str(record["samplingProtocol"]).lower()
        if any(
            term in protocol for term in SAMPLING_PROTOCOL_KEYWORDS + SIZE_INDICATORS
        ):
            has_size_data = True
            size_measurements.append(
                f"Sampling protocol: {record['samplingProtocol'][:50]}..."
            )
            return has_size_data, size_measurements

    return has_size_data, size_measurements


def validate_upload_file(file_info: List[Dict[str, Any]], max_size_mb: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded file for bulk analysis.

    Args:
        file_info: File information from Shiny input.file()
        max_size_mb: Maximum file size in megabytes

    Returns:
        Tuple of (is_valid, error_message) where:
        - is_valid: Boolean indicating if the file is valid
        - error_message: None if valid, otherwise a string describing the error
    """
    if not file_info:
        return False, "No file provided"

    if len(file_info) == 0:
        return False, "No file provided"

    file_data = file_info[0]

    # Validate file name
    file_name = file_data.get("name", "")
    if not file_name:
        return False, "Invalid file: no filename"

    # Validate file extension
    if not file_name.lower().endswith(('.xlsx', '.xls')):
        return False, f"Invalid file type: {file_name}. Only Excel files (.xlsx, .xls) are accepted."

    # Validate file size
    file_path = file_data.get("datapath", "")
    if not file_path or not os.path.exists(file_path):
        return False, "Invalid file: file not found"

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb > max_size_mb:
        return False, f"File too large: {file_size_mb:.2f}MB (maximum: {max_size_mb}MB)"

    # Validate file content (can be read as Excel)
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=None, nrows=1)
        if df.empty:
            return False, "Invalid file: Excel file is empty"
    except pd.errors.EmptyDataError as e:
        raise InvalidFileContentError(f"Excel file is empty: {str(e)}")
    except pd.errors.ParserError as e:
        raise InvalidFileContentError(f"Cannot parse Excel file: {str(e)}")
    except OSError as e:
        raise InvalidFileContentError(f"File system error reading Excel file: {str(e)}")
    except ValueError as e:
        raise InvalidFileFormatError(f"Invalid Excel file format: {str(e)}")
    except Exception as e:
        raise InvalidFileContentError(f"Cannot read as Excel file: {str(e)}")

    return True, None
