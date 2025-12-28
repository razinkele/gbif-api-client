"""
Test script for TraitOntologyDB functionality.

This script validates:
1. Database statistics
2. Species lookup by AphiaID
3. Trait value retrieval
4. Query species by trait criteria
5. Category filtering
6. Size class queries
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apis.trait_ontology_db import get_trait_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print('='*70)
    else:
        print('='*70)


def test_statistics():
    """Test 1: Get database statistics."""
    print_separator("TEST 1: Database Statistics")

    db = get_trait_db()
    stats = db.get_statistics()

    print(f"\nTotal species: {stats['total_species']}")
    print(f"Total traits defined: {stats['total_traits']}")
    print(f"Total trait values: {stats['total_trait_values']}")
    print(f"Total categories: {stats['total_categories']}")

    print("\nSpecies by source:")
    for source, count in stats['species_by_source'].items():
        print(f"  {source}: {count}")

    print("\nTraits by category:")
    for category, count in stats['traits_by_category'].items():
        print(f"  {category}: {count}")

    return stats


def test_species_lookup():
    """Test 2: Query species by AphiaID."""
    print_separator("TEST 2: Species Lookup by AphiaID")

    db = get_trait_db()

    # Test phytoplankton species (Aphanocapsa elachista)
    aphia_id = 146564
    print(f"\nLooking up phytoplankton species: AphiaID {aphia_id}")

    species = db.get_species_by_aphia_id(aphia_id)
    if species:
        print(f"  Found: {species['scientific_name']}")
        print(f"  Data source: {species['data_source']}")
        print(f"  Database ID: {species['species_id']}")
    else:
        print(f"  Species not found!")

    # Test enriched species (Abra alba)
    aphia_id = 141433
    print(f"\nLooking up enriched species: AphiaID {aphia_id}")

    species = db.get_species_by_aphia_id(aphia_id)
    if species:
        print(f"  Found: {species['scientific_name']}")
        print(f"  Common name: {species.get('common_name', 'N/A')}")
        print(f"  Data source: {species['data_source']}")
        print(f"  Database ID: {species['species_id']}")
    else:
        print(f"  Species not found!")


def test_trait_values():
    """Test 3: Retrieve trait values for species."""
    print_separator("TEST 3: Trait Value Retrieval")

    db = get_trait_db()

    # Test phytoplankton with multiple size classes
    aphia_id = 146564
    print(f"\nRetrieving all traits for AphiaID {aphia_id}:")

    traits = db.get_traits_for_species(aphia_id)
    print(f"  Total trait values: {len(traits)}")

    # Group by trait type
    trait_types = {}
    for trait in traits:
        trait_name = trait['trait_name']
        if trait_name not in trait_types:
            trait_types[trait_name] = []
        trait_types[trait_name].append(trait)

    print(f"  Unique trait types: {len(trait_types)}")
    print("\n  Trait breakdown:")
    for trait_name, values in sorted(trait_types.items()):
        print(f"    {trait_name}: {len(values)} value(s)")
        # Show first value as example
        first_val = values[0]
        if first_val.get('value_numeric') is not None:
            print(f"      Example: {first_val['value_numeric']} (numeric)")
        elif first_val.get('value_text') is not None:
            print(f"      Example: {first_val['value_text']} (text)")
        elif first_val.get('value_categorical') is not None:
            print(f"      Example: {first_val['value_categorical']} (categorical)")


def test_category_filtering():
    """Test 4: Filter traits by category."""
    print_separator("TEST 4: Category Filtering")

    db = get_trait_db()

    # Test enriched species
    aphia_id = 141433
    print(f"\nRetrieving ecological traits for AphiaID {aphia_id}:")

    eco_traits = db.get_traits_for_species(aphia_id, category='ecological')
    print(f"  Found {len(eco_traits)} ecological trait values:")
    for trait in eco_traits:
        value = trait.get('value_text') or trait.get('value_categorical') or trait.get('value_numeric')
        print(f"    {trait['trait_name']}: {value}")

    print(f"\nRetrieving trophic traits for AphiaID {aphia_id}:")
    trophic_traits = db.get_traits_for_species(aphia_id, category='trophic')
    print(f"  Found {len(trophic_traits)} trophic trait values:")
    for trait in trophic_traits:
        value = trait.get('value_text') or trait.get('value_categorical') or trait.get('value_numeric')
        print(f"    {trait['trait_name']}: {value}")


def test_trait_queries():
    """Test 5: Query species by trait criteria."""
    print_separator("TEST 5: Query Species by Trait")

    db = get_trait_db()

    # Query by numeric trait
    print("\nQuerying species with biovolume between 1.0 and 10.0 um3:")
    results = db.query_species_by_trait('biovolume', min_value=1.0, max_value=10.0)
    print(f"  Found {len(results)} species")

    if results:
        print("\n  First 5 results:")
        for i, species in enumerate(results[:5], 1):
            print(f"    {i}. AphiaID {species['aphia_id']}: {species['scientific_name']}")
            print(f"       Value: {species['trait_value']} um3")

    # Query by categorical trait
    print("\nQuerying species with trophic_type = 'AU' (autotroph):")
    results = db.query_species_by_trait('trophic_type', categorical_value='AU')
    print(f"  Found {len(results)} autotrophic species")

    if results:
        print("\n  First 5 results:")
        for i, species in enumerate(results[:5], 1):
            print(f"    {i}. AphiaID {species['aphia_id']}: {species['scientific_name']}")


def test_size_classes():
    """Test 6: Query size class information."""
    print_separator("TEST 6: Size Class Queries")

    db = get_trait_db()

    # Get species with multiple size classes
    aphia_id = 146564
    print(f"\nRetrieving size classes for AphiaID {aphia_id}:")

    species = db.get_species_by_aphia_id(aphia_id)
    if species:
        species_id = species['species_id']

        # Get size class information
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT size_class_no, size_range, size_range_min, size_range_max
            FROM size_classes
            WHERE species_id = ?
            ORDER BY size_class_no
        """, (species_id,))

        size_classes = cursor.fetchall()
        print(f"  Found {len(size_classes)} size classes:")

        for sc in size_classes:
            size_class_no, size_range, size_min, size_max = sc
            print(f"    Size class {size_class_no}: {size_range}")
            if size_min is not None and size_max is not None:
                print(f"      Range: {size_min} - {size_max}")

        # Get trait values for specific size class
        if size_classes:
            print(f"\n  Trait values for size class 1:")
            cursor.execute("""
                SELECT t.trait_name, tv.value_numeric, tv.value_text
                FROM trait_values tv
                JOIN traits t ON tv.trait_id = t.trait_id
                JOIN size_classes sc ON tv.size_class_id = sc.size_class_id
                WHERE tv.species_id = ? AND sc.size_class_no = 1
            """, (species_id,))

            traits = cursor.fetchall()
            for trait_name, val_num, val_text in traits[:10]:  # Show first 10
                value = val_num if val_num is not None else val_text
                print(f"      {trait_name}: {value}")


def test_taxonomy():
    """Test 7: Taxonomic hierarchy queries."""
    print_separator("TEST 7: Taxonomic Hierarchy")

    db = get_trait_db()

    aphia_id = 146564
    print(f"\nRetrieving taxonomy for AphiaID {aphia_id}:")

    species = db.get_species_by_aphia_id(aphia_id)
    if species:
        species_id = species['species_id']

        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT kingdom, phylum, class, "order", family, genus, species, rank
            FROM taxonomic_hierarchy
            WHERE species_id = ?
        """, (species_id,))

        taxonomy = cursor.fetchone()
        if taxonomy:
            kingdom, phylum, class_name, order, family, genus, species_name, rank = taxonomy
            print(f"  Kingdom: {kingdom or 'N/A'}")
            print(f"  Phylum: {phylum or 'N/A'}")
            print(f"  Class: {class_name or 'N/A'}")
            print(f"  Order: {order or 'N/A'}")
            print(f"  Family: {family or 'N/A'}")
            print(f"  Genus: {genus or 'N/A'}")
            print(f"  Species: {species_name or 'N/A'}")
            print(f"  Rank: {rank or 'N/A'}")


def test_geographic_distribution():
    """Test 8: Geographic distribution queries."""
    print_separator("TEST 8: Geographic Distribution")

    db = get_trait_db()

    # Find species in HELCOM area
    print("\nQuerying species in HELCOM area:")

    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT DISTINCT s.aphia_id, s.scientific_name, gd.area_type, gd.area_value
        FROM species s
        JOIN geographic_distribution gd ON s.species_id = gd.species_id
        WHERE gd.area_type = 'HELCOM'
        LIMIT 10
    """)

    results = cursor.fetchall()
    print(f"  Found {len(results)} species (showing first 10):")
    for aphia_id, sci_name, area_type, area_value in results:
        print(f"    AphiaID {aphia_id}: {sci_name}")
        print(f"      {area_type} area: {area_value}")


def main():
    """Run all tests."""
    logger.info("Starting TraitOntologyDB tests")

    try:
        # Run all test functions
        test_statistics()
        test_species_lookup()
        test_trait_values()
        test_category_filtering()
        test_trait_queries()
        test_size_classes()
        test_taxonomy()
        test_geographic_distribution()

        print_separator("ALL TESTS COMPLETED SUCCESSFULLY")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print_separator("TESTS FAILED")
        raise


if __name__ == "__main__":
    main()
