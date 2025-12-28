"""
Export utilities for the Marine & Biodiversity Data Explorer.

This module provides functions to export data in various formats:
- CSV (Comma-Separated Values)
- Excel (XLSX)
- JSON (JavaScript Object Notation)
- GeoJSON (for geographic data with coordinates)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd
from app_modules.exceptions import (
    ExportError,
    ExportFileError,
    InvalidExportFormatError,
    InvalidExportDataError,
    InvalidCoordinatesError
)

logger = logging.getLogger(__name__)


def export_to_csv(
    df: pd.DataFrame,
    file_path: str,
    include_index: bool = False
) -> None:
    """
    Export DataFrame to CSV format.

    Args:
        df: DataFrame to export
        file_path: Output file path
        include_index: Whether to include DataFrame index in output

    Raises:
        InvalidExportDataError: If DataFrame is invalid
        ExportFileError: If file operation fails
    """
    if df is None or df.empty:
        raise InvalidExportDataError("Cannot export empty DataFrame")

    try:
        df.to_csv(file_path, index=include_index, encoding='utf-8')
        logger.info(f"Successfully exported {len(df)} rows to CSV: {file_path}")
    except PermissionError as e:
        raise ExportFileError(f"Permission denied writing to {file_path}: {str(e)}")
    except OSError as e:
        raise ExportFileError(f"File system error writing to {file_path}: {str(e)}")
    except Exception as e:
        raise ExportError(f"Failed to export to CSV: {str(e)}")


def export_to_excel(
    df: pd.DataFrame,
    file_path: str,
    sheet_name: str = "Data",
    include_index: bool = False
) -> None:
    """
    Export DataFrame to Excel format.

    Args:
        df: DataFrame to export
        file_path: Output file path
        sheet_name: Name of the Excel sheet
        include_index: Whether to include DataFrame index in output

    Raises:
        InvalidExportDataError: If DataFrame is invalid
        ExportFileError: If file operation fails
    """
    if df is None or df.empty:
        raise InvalidExportDataError("Cannot export empty DataFrame")

    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=include_index)
        logger.info(f"Successfully exported {len(df)} rows to Excel: {file_path}")
    except PermissionError as e:
        raise ExportFileError(f"Permission denied writing to {file_path}: {str(e)}")
    except OSError as e:
        raise ExportFileError(f"File system error writing to {file_path}: {str(e)}")
    except ImportError as e:
        raise ExportError(f"Excel export requires openpyxl library: {str(e)}")
    except Exception as e:
        raise ExportError(f"Failed to export to Excel: {str(e)}")


def export_to_json(
    df: pd.DataFrame,
    file_path: str,
    orient: str = "records",
    indent: int = 2
) -> None:
    """
    Export DataFrame to JSON format.

    Args:
        df: DataFrame to export
        file_path: Output file path
        orient: Format of JSON string ('records', 'split', 'index', 'columns', 'values')
        indent: Number of spaces for indentation (None for compact JSON)

    Raises:
        InvalidExportDataError: If DataFrame is invalid
        ExportFileError: If file operation fails
    """
    if df is None or df.empty:
        raise InvalidExportDataError("Cannot export empty DataFrame")

    valid_orients = ['records', 'split', 'index', 'columns', 'values']
    if orient not in valid_orients:
        raise InvalidExportFormatError(f"Invalid orient '{orient}'. Must be one of: {valid_orients}")

    try:
        df.to_json(file_path, orient=orient, indent=indent)
        logger.info(f"Successfully exported {len(df)} rows to JSON: {file_path}")
    except PermissionError as e:
        raise ExportFileError(f"Permission denied writing to {file_path}: {str(e)}")
    except OSError as e:
        raise ExportFileError(f"File system error writing to {file_path}: {str(e)}")
    except ValueError as e:
        raise InvalidExportDataError(f"Data serialization error: {str(e)}")
    except Exception as e:
        raise ExportError(f"Failed to export to JSON: {str(e)}")


def export_to_geojson(
    df: pd.DataFrame,
    file_path: str,
    lat_col: str = "decimalLatitude",
    lon_col: str = "decimalLongitude",
    properties: Optional[List[str]] = None
) -> None:
    """
    Export DataFrame to GeoJSON format for geographic data.

    Args:
        df: DataFrame to export (must contain latitude and longitude columns)
        file_path: Output file path
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        properties: List of column names to include as properties (None = all columns)

    Raises:
        InvalidExportDataError: If DataFrame or columns are invalid
        InvalidCoordinatesError: If coordinates are missing or invalid
        ExportFileError: If file operation fails
    """
    if df is None or df.empty:
        raise InvalidExportDataError("Cannot export empty DataFrame")

    # Validate required columns
    if lat_col not in df.columns:
        raise InvalidCoordinatesError(f"Latitude column '{lat_col}' not found in DataFrame")
    if lon_col not in df.columns:
        raise InvalidCoordinatesError(f"Longitude column '{lon_col}' not found in DataFrame")

    # Filter out rows with missing coordinates
    valid_coords = df.dropna(subset=[lat_col, lon_col])

    if len(valid_coords) == 0:
        raise InvalidCoordinatesError("No valid coordinates found in DataFrame")

    try

        # Determine which columns to include as properties
        if properties is None:
            properties = [col for col in df.columns if col not in [lat_col, lon_col]]

        # Build GeoJSON structure
        features = []
        for _, row in valid_coords.iterrows():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row[lon_col]), float(row[lat_col])]
                },
                "properties": {}
            }

            # Add properties
            for prop in properties:
                value = row.get(prop)
                # Convert pandas types to JSON-serializable types
                if pd.isna(value):
                    feature["properties"][prop] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    feature["properties"][prop] = value.isoformat()
                else:
                    feature["properties"][prop] = value

            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully exported {len(features)} features to GeoJSON: {file_path}")

    except (InvalidExportDataError, InvalidCoordinatesError):
        raise
    except PermissionError as e:
        raise ExportFileError(f"Permission denied writing to {file_path}: {str(e)}")
    except OSError as e:
        raise ExportFileError(f"File system error writing to {file_path}: {str(e)}")
    except ValueError as e:
        raise InvalidCoordinatesError(f"Invalid coordinate values: {str(e)}")
    except Exception as e:
        raise ExportError(f"Failed to export to GeoJSON: {str(e)}")


def create_export_filename(
    base_name: str,
    format: str,
    include_timestamp: bool = True
) -> str:
    """
    Create a filename for export with optional timestamp.

    Args:
        base_name: Base name for the file (without extension)
        format: File format ('csv', 'excel', 'json', 'geojson')
        include_timestamp: Whether to include timestamp in filename

    Returns:
        Complete filename with extension

    Example:
        create_export_filename("species_data", "csv", True)
        # Returns: "species_data_20251226_143022.csv"
    """
    # Map format to file extension
    extensions = {
        'csv': '.csv',
        'excel': '.xlsx',
        'json': '.json',
        'geojson': '.geojson'
    }

    ext = extensions.get(format.lower(), '.txt')

    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}{ext}"
    else:
        return f"{base_name}{ext}"


def export_data(
    df: pd.DataFrame,
    output_dir: str,
    base_name: str,
    formats: List[str],
    include_timestamp: bool = True,
    **kwargs
) -> Dict[str, str]:
    """
    Export data to multiple formats at once.

    Args:
        df: DataFrame to export
        output_dir: Directory to save exported files
        base_name: Base name for exported files
        formats: List of formats to export ('csv', 'excel', 'json', 'geojson')
        include_timestamp: Whether to include timestamp in filenames
        **kwargs: Additional arguments passed to specific export functions

    Returns:
        Dictionary mapping format to file path

    Raises:
        ExportError: If any export fails

    Example:
        results = export_data(
            df=species_df,
            output_dir="exports",
            base_name="marine_species",
            formats=['csv', 'excel', 'geojson']
        )
        # Returns: {'csv': 'exports/marine_species_timestamp.csv', ...}
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}
    errors = []

    for fmt in formats:
        try:
            filename = create_export_filename(base_name, fmt, include_timestamp)
            file_path = str(output_path / filename)

            if fmt.lower() == 'csv':
                export_to_csv(df, file_path, **kwargs)
            elif fmt.lower() == 'excel':
                export_to_excel(df, file_path, **kwargs)
            elif fmt.lower() == 'json':
                export_to_json(df, file_path, **kwargs)
            elif fmt.lower() == 'geojson':
                export_to_geojson(df, file_path, **kwargs)
            else:
                logger.warning(f"Unknown export format: {fmt}")
                continue

            results[fmt] = file_path

        except Exception as e:
            error_msg = f"Failed to export {fmt}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    if errors and not results:
        raise ExportError(f"All exports failed: {'; '.join(errors)}")

    return results


def get_export_summary(results: Dict[str, str]) -> str:
    """
    Create a human-readable summary of export results.

    Args:
        results: Dictionary mapping format to file path

    Returns:
        Formatted summary string

    Example:
        summary = get_export_summary({'csv': 'data.csv', 'excel': 'data.xlsx'})
        print(summary)
        # Exported 2 files:
        # - CSV: data.csv
        # - Excel: data.xlsx
    """
    if not results:
        return "No files exported"

    lines = [f"Exported {len(results)} file(s):"]
    for fmt, path in results.items():
        lines.append(f"- {fmt.upper()}: {path}")

    return "\n".join(lines)
