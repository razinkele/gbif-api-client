"""
Utility functions for working with trait data in the Shiny application.

This module provides helper functions to:
- Enrich species data with trait information
- Format trait data for display
- Query traits by various criteria
"""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd
from app_modules.cache import trait_cache, get_or_cache
from app_modules.exceptions import (
    DatabaseError,
    DatabaseQueryError,
    TraitError,
    TraitQueryError,
    CacheError
)

logger = logging.getLogger(__name__)


def get_traits_for_aphia_id(trait_db, aphia_id: int) -> Optional[Dict[str, Any]]:
    """
    Get all trait information for a species by AphiaID (with caching).

    Args:
        trait_db: TraitOntologyDB instance
        aphia_id: WoRMS AphiaID

    Returns:
        Dictionary with trait information or None if not found
    """
    try:
        # Check cache first
        cache_key = f"traits:full:{aphia_id}"
        cached_result = trait_cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for traits:{aphia_id}")
            return cached_result

        # Get species info
        species = trait_db.get_species_by_aphia_id(aphia_id)
        if not species:
            return None

        # Get all traits
        traits = trait_db.get_traits_for_species(aphia_id)

        # Organize traits by category
        traits_by_category = {}
        for trait in traits:
            category = trait.get('category_name', 'other')
            if category not in traits_by_category:
                traits_by_category[category] = []

            # Get the actual value
            value = (
                trait.get('value_numeric') or
                trait.get('value_categorical') or
                trait.get('value_text') or
                trait.get('value_boolean')
            )

            trait_info = {
                'name': trait['trait_name'],
                'value': value,
                'unit': trait.get('unit'),
                'data_type': trait.get('data_type'),
                'size_class': trait.get('size_class_no'),
                'size_range': trait.get('size_range')
            }
            traits_by_category[category].append(trait_info)

        result = {
            'species_info': species,
            'traits_by_category': traits_by_category,
            'total_traits': len(traits)
        }

        # Cache the result
        trait_cache.set(cache_key, result)

        return result

    except CacheError as e:
        logger.error(f"Cache error for AphiaID {aphia_id}: {e}")
        # Continue without cache on cache errors
        return None
    except DatabaseError as e:
        logger.error(f"Database error fetching traits for AphiaID {aphia_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching traits for AphiaID {aphia_id}: {e}")
        return None


def format_trait_value(value: Any, unit: Optional[str] = None, data_type: str = 'text') -> str:
    """
    Format a trait value for display.

    Args:
        value: The trait value
        unit: Optional unit of measurement
        data_type: Type of data (numeric, categorical, text, boolean)

    Returns:
        Formatted string representation
    """
    if value is None:
        return "N/A"

    if data_type == 'numeric':
        # Format numeric values
        if isinstance(value, float):
            formatted = f"{value:.2f}"
        else:
            formatted = str(value)

        if unit:
            return f"{formatted} {unit}"
        return formatted

    elif data_type == 'boolean':
        return "Yes" if value else "No"

    else:
        return str(value)


def create_trait_summary_text(trait_info: Dict[str, Any]) -> str:
    """
    Create a text summary of trait information.

    Args:
        trait_info: Dictionary with trait information from get_traits_for_aphia_id

    Returns:
        Formatted text summary
    """
    if not trait_info:
        return "No trait data available"

    species = trait_info['species_info']
    traits_by_cat = trait_info['traits_by_category']

    lines = [
        f"Species: {species.get('scientific_name', 'Unknown')}",
        f"Data source: {species.get('data_source', 'Unknown')}",
        f"Total traits: {trait_info['total_traits']}",
        ""
    ]

    # Add traits by category
    for category, traits in sorted(traits_by_cat.items()):
        lines.append(f"{category.upper()}:")

        # Group by trait name to handle multiple size classes
        traits_by_name = {}
        for trait in traits:
            name = trait['name']
            if name not in traits_by_name:
                traits_by_name[name] = []
            traits_by_name[name].append(trait)

        for trait_name, trait_list in sorted(traits_by_name.items()):
            if len(trait_list) == 1:
                # Single value
                trait = trait_list[0]
                value_str = format_trait_value(
                    trait['value'],
                    trait.get('unit'),
                    trait.get('data_type', 'text')
                )
                lines.append(f"  {trait_name}: {value_str}")
            else:
                # Multiple size classes
                lines.append(f"  {trait_name}:")
                for trait in trait_list:
                    size_info = ""
                    if trait.get('size_class'):
                        size_info = f" (size class {trait['size_class']}"
                        if trait.get('size_range'):
                            size_info += f": {trait['size_range']}"
                        size_info += ")"

                    value_str = format_trait_value(
                        trait['value'],
                        trait.get('unit'),
                        trait.get('data_type', 'text')
                    )
                    lines.append(f"    {value_str}{size_info}")

        lines.append("")

    return "\n".join(lines)


def enrich_occurrences_with_traits(occurrences_df: pd.DataFrame, trait_db) -> pd.DataFrame:
    """
    Enrich occurrence data with trait information using optimized batch queries.

    This function uses batch queries to fetch all traits in a single database call,
    which is significantly more efficient than the N+1 query pattern.

    Args:
        occurrences_df: DataFrame with occurrence data
        trait_db: TraitOntologyDB instance

    Returns:
        DataFrame with additional trait columns
    """
    if occurrences_df.empty:
        return occurrences_df

    # Check if we have AphiaID column
    aphia_id_cols = [col for col in occurrences_df.columns if 'aphia' in col.lower()]

    if not aphia_id_cols:
        logger.warning("No AphiaID column found in occurrences data")
        return occurrences_df

    aphia_col = aphia_id_cols[0]

    # Get unique AphiaIDs (excluding NaN values)
    unique_aphia_ids = occurrences_df[aphia_col].dropna().unique().tolist()

    # Convert to integers and filter out invalid values
    valid_aphia_ids = []
    for aid in unique_aphia_ids:
        try:
            valid_aphia_ids.append(int(aid))
        except (ValueError, TypeError):
            logger.warning(f"Invalid AphiaID value: {aid}")

    if not valid_aphia_ids:
        logger.info("No valid AphiaIDs found for trait enrichment")
        # Return dataframe with empty trait columns
        result_df = occurrences_df.copy()
        result_df['has_trait_data'] = False
        result_df['trait_count'] = 0
        result_df['trophic_type'] = None
        result_df['biovolume_um3'] = None
        result_df['carbon_pg'] = None
        return result_df

    # Batch query for all traits - SINGLE database call instead of N queries!
    logger.info(f"Fetching traits for {len(valid_aphia_ids)} species in batch")
    try:
        traits_batch = trait_db.get_traits_for_species_batch(valid_aphia_ids)
    except DatabaseQueryError as e:
        logger.error(f"Database query error in batch trait query: {e}")
        traits_batch = {}
    except TraitQueryError as e:
        logger.error(f"Trait query error in batch trait query: {e}")
        traits_batch = {}
    except Exception as e:
        logger.error(f"Unexpected error in batch trait query: {e}")
        traits_batch = {}

    # Extract trait information for each species
    def extract_traits(aphia_id):
        """Extract specific traits for a species from batch results."""
        if pd.isna(aphia_id):
            return False, 0, None, None, None

        try:
            aphia_id_int = int(aphia_id)
        except (ValueError, TypeError):
            return False, 0, None, None, None

        traits = traits_batch.get(aphia_id_int, [])

        if not traits:
            return False, 0, None, None, None

        # Extract common traits
        trophic = None
        biovolume = None
        carbon = None

        for trait in traits:
            trait_name = trait.get('trait_name')
            if trait_name == 'trophic_type':
                trophic = trait.get('value_categorical')
            elif trait_name == 'biovolume':
                biovolume = trait.get('value_numeric')
            elif trait_name == 'carbon_content':
                carbon = trait.get('value_numeric')

        return True, len(traits), trophic, biovolume, carbon

    # Apply trait extraction to all rows efficiently using vectorized operations
    result_df = occurrences_df.copy()

    trait_data = result_df[aphia_col].apply(extract_traits)

    result_df['has_trait_data'] = trait_data.apply(lambda x: x[0])
    result_df['trait_count'] = trait_data.apply(lambda x: x[1])
    result_df['trophic_type'] = trait_data.apply(lambda x: x[2])
    result_df['biovolume_um3'] = trait_data.apply(lambda x: x[3])
    result_df['carbon_pg'] = trait_data.apply(lambda x: x[4])

    logger.info(f"Enriched {len(result_df)} occurrences with trait data")

    return result_df


def query_species_by_trait_range(
    trait_db,
    trait_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query species by trait value range.

    Args:
        trait_db: TraitOntologyDB instance
        trait_name: Name of the trait to query
        min_value: Minimum value (for numeric traits)
        max_value: Maximum value (for numeric traits)
        limit: Maximum number of results

    Returns:
        List of species matching criteria
    """
    try:
        results = trait_db.query_species_by_trait(
            trait_name=trait_name,
            min_value=min_value,
            max_value=max_value
        )
        return results[:limit]
    except DatabaseQueryError as e:
        logger.error(f"Database query error querying species by trait '{trait_name}': {e}")
        return []
    except TraitQueryError as e:
        logger.error(f"Trait query error querying species by trait '{trait_name}': {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying species by trait '{trait_name}': {e}")
        return []


def get_trait_statistics(trait_db) -> Dict[str, Any]:
    """
    Get statistics about the trait database.

    Args:
        trait_db: TraitOntologyDB instance

    Returns:
        Dictionary with statistics
    """
    try:
        return trait_db.get_statistics()
    except DatabaseQueryError as e:
        logger.error(f"Database query error getting trait statistics: {e}")
        return {}
    except DatabaseError as e:
        logger.error(f"Database error getting trait statistics: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting trait statistics: {e}")
        return {}
