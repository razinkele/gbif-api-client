"""
Test script for trait database integration with the main application.

This script verifies:
1. Trait database can be imported
2. Trait utilities work correctly
3. Sample trait queries return expected results
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apis.trait_ontology_db import get_trait_db
from app_modules.trait_utils import (
    get_traits_for_aphia_id,
    create_trait_summary_text,
    query_species_by_trait_range,
    get_trait_statistics,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_database_initialization():
    """Test 1: Verify trait database can be initialized."""
    print("=" * 70)
    print("TEST 1: Database Initialization")
    print("=" * 70)

    try:
        trait_db = get_trait_db()
        print("[PASS] Trait database initialized successfully")
        return trait_db
    except Exception as e:
        print(f"[FAIL] Failed to initialize trait database: {e}")
        return None


def test_statistics(trait_db):
    """Test 2: Get database statistics."""
    print("\n" + "=" * 70)
    print("TEST 2: Database Statistics")
    print("=" * 70)

    try:
        stats = get_trait_statistics(trait_db)
        print(f"[PASS] Total Species: {stats.get('total_species', 0):,}")
        print(f"[PASS] Total Traits: {stats.get('total_traits', 0)}")
        print(f"[PASS] Total Trait Values: {stats.get('total_trait_values', 0):,}")

        print("\nSpecies by Source:")
        for source, count in stats.get('species_by_source', {}).items():
            print(f"  • {source}: {count:,}")

        return True
    except Exception as e:
        print(f"[FAIL] Failed to get statistics: {e}")
        return False


def test_trait_lookup(trait_db):
    """Test 3: Look up traits for a specific species."""
    print("\n" + "=" * 70)
    print("TEST 3: Trait Lookup by AphiaID")
    print("=" * 70)

    # Test with phytoplankton species
    aphia_id = 146564  # Aphanocapsa elachista
    print(f"\nLooking up traits for AphiaID {aphia_id}...")

    try:
        trait_info = get_traits_for_aphia_id(trait_db, aphia_id)

        if trait_info:
            species = trait_info['species_info']
            print(f"[PASS] Found species: {species.get('scientific_name')}")
            print(f"[PASS] Data source: {species.get('data_source')}")
            print(f"[PASS] Total traits: {trait_info['total_traits']}")

            # Create summary
            summary = create_trait_summary_text(trait_info)
            print("\nTrait Summary (first 500 chars):")
            print(summary[:500] + "...")

            return True
        else:
            print(f"[FAIL] No traits found for AphiaID {aphia_id}")
            return False

    except Exception as e:
        print(f"[FAIL] Error during trait lookup: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trait_query(trait_db):
    """Test 4: Query species by trait value range."""
    print("\n" + "=" * 70)
    print("TEST 4: Query Species by Trait Range")
    print("=" * 70)

    try:
        # Query biovolume
        print("\nQuerying species with biovolume 1.0-10.0 µm³...")
        results = query_species_by_trait_range(
            trait_db,
            trait_name='biovolume',
            min_value=1.0,
            max_value=10.0,
            limit=5
        )

        if results:
            print(f"[PASS] Found {len(results)} species")
            print("\nFirst 3 results:")
            for i, species in enumerate(results[:3], 1):
                print(f"  {i}. AphiaID {species['aphia_id']}: {species['scientific_name']}")
                print(f"     Biovolume: {species['trait_value']} µm³")
            return True
        else:
            print("[FAIL] No species found in the specified range")
            return False

    except Exception as e:
        print(f"[FAIL] Error during trait query: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_categorical_query(trait_db):
    """Test 5: Query species by categorical trait."""
    print("\n" + "=" * 70)
    print("TEST 5: Query Species by Categorical Trait")
    print("=" * 70)

    try:
        # Query trophic type
        print("\nQuerying autotrophic species (trophic_type = 'AU')...")
        results = trait_db.query_species_by_trait(
            trait_name='trophic_type',
            categorical_value='AU'
        )[:5]

        if results:
            print(f"[PASS] Found {len(results)} autotrophic species (showing 5)")
            print("\nFirst 3 results:")
            for i, species in enumerate(results[:3], 1):
                print(f"  {i}. AphiaID {species['aphia_id']}: {species['scientific_name']}")
            return True
        else:
            print("[FAIL] No autotrophic species found")
            return False

    except Exception as e:
        print(f"[FAIL] Error during categorical query: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    logger.info("Starting trait integration tests")

    print("\n" + "=" * 70)
    print(" TRAIT DATABASE INTEGRATION TEST SUITE")
    print("=" * 70 + "\n")

    # Initialize database
    trait_db = test_database_initialization()
    if not trait_db:
        print("\n[FAIL] FAILED: Could not initialize database")
        return

    # Run tests
    tests_passed = 0
    total_tests = 5

    if test_statistics(trait_db):
        tests_passed += 1

    if test_trait_lookup(trait_db):
        tests_passed += 1

    if test_trait_query(trait_db):
        tests_passed += 1

    if test_categorical_query(trait_db):
        tests_passed += 1

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)
    print(f"\nTests Passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("\n[PASS] ALL TESTS PASSED - Integration successful!")
    else:
        print(f"\n[FAIL] {total_tests - tests_passed} test(s) failed")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
