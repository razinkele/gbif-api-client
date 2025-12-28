"""
Example usage of the TraitLookup module for marine species trait data.

This script demonstrates how to:
1. Initialize the trait lookup
2. Query phytoplankton traits
3. Query enriched species traits
4. Search for species by name
5. Get statistics about the databases
"""

from apis import get_trait_lookup


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 70 + "\n")


def main():
    # Initialize the trait lookup
    print("Initializing TraitLookup...")
    lookup = get_trait_lookup()

    # Get database statistics
    print_separator()
    print("DATABASE STATISTICS")
    print_separator()

    stats = lookup.get_statistics()

    print("Phytoplankton Database (bvol_nomp_version_2024):")
    print(f"  Total records: {stats['phytoplankton']['total_records']}")
    print(f"  Unique species (AphiaIDs): {stats['phytoplankton']['unique_aphia_ids']}")
    print(f"  File loaded: {stats['phytoplankton']['file_loaded']}")

    print("\nEnriched Species Database (species_enriched):")
    print(f"  Total records: {stats['enriched_species']['total_records']}")
    print(f"  Unique species (AphiaIDs): {stats['enriched_species']['unique_aphia_ids']}")
    print(f"  File loaded: {stats['enriched_species']['file_loaded']}")

    # Example 1: Phytoplankton with multiple size classes
    print_separator()
    print("EXAMPLE 1: Phytoplankton with Multiple Size Classes")
    print_separator()

    aphia_id = 146564  # Aphanocapsa elachista
    print(f"Looking up AphiaID: {aphia_id}")

    phyto_traits = lookup.get_phytoplankton_traits(aphia_id)

    if phyto_traits:
        print(f"\nSpecies found in: {phyto_traits['source']}")
        print(f"Multiple size classes: {phyto_traits['multiple_size_classes']}")

        if phyto_traits['multiple_size_classes']:
            print(f"Number of size classes: {len(phyto_traits['size_classes'])}")

            # Show first size class details
            first_class = phyto_traits['size_classes'][0]
            print(f"\nFirst Size Class Details:")
            print(f"  Species: {first_class.get('species')}")
            print(f"  Genus: {first_class.get('genus')}")
            print(f"  Division: {first_class.get('division')}")
            print(f"  Trophic type: {first_class.get('trophic_type')}")
            print(f"  Geometric shape: {first_class.get('geometric_shape')}")
            print(f"  Size class: {first_class.get('size_class_no')}")
            print(f"  Size range: {first_class.get('size_range')}")

            if first_class.get('calculated_volume_um3'):
                print(f"  Volume: {first_class['calculated_volume_um3']:.2f} μm³")
            if first_class.get('calculated_carbon_pg'):
                print(f"  Carbon: {first_class['calculated_carbon_pg']:.2f} pg")

    # Example 2: Phytoplankton with single size class
    print_separator()
    print("EXAMPLE 2: Phytoplankton with Single Size Class")
    print_separator()

    aphia_id = 162699  # Chroococcus cumulatus
    print(f"Looking up AphiaID: {aphia_id}")

    phyto_traits = lookup.get_phytoplankton_traits(aphia_id)

    if phyto_traits:
        print(f"\nSpecies found in: {phyto_traits['source']}")
        print(f"Multiple size classes: {phyto_traits['multiple_size_classes']}")
        print(f"\nSpecies Details:")
        print(f"  Species: {phyto_traits.get('species')}")
        print(f"  Genus: {phyto_traits.get('genus')}")
        print(f"  Division: {phyto_traits.get('division')}")
        print(f"  Class: {phyto_traits.get('class')}")
        print(f"  Trophic type: {phyto_traits.get('trophic_type')}")
        print(f"  Geometric shape: {phyto_traits.get('geometric_shape')}")

        if phyto_traits.get('calculated_volume_um3'):
            print(f"  Volume: {phyto_traits['calculated_volume_um3']:.2f} μm³")
        if phyto_traits.get('calculated_carbon_pg'):
            print(f"  Carbon: {phyto_traits['calculated_carbon_pg']:.2f} pg")

        if phyto_traits.get('geographic_areas'):
            print(f"\nGeographic Distribution:")
            if phyto_traits['geographic_areas'].get('helcom'):
                print(f"  HELCOM area: {phyto_traits['geographic_areas']['helcom']}")
            if phyto_traits['geographic_areas'].get('ospar'):
                print(f"  OSPAR area: {phyto_traits['geographic_areas']['ospar']}")

    # Example 3: Enriched species traits
    print_separator()
    print("EXAMPLE 3: Enriched Species Traits")
    print_separator()

    aphia_id = 141433  # Abra alba (White furrow shell)
    print(f"Looking up AphiaID: {aphia_id}")

    species_traits = lookup.get_species_traits(aphia_id)

    if species_traits:
        print(f"\nSpecies found in: {species_traits['source']}")
        print(f"\nBasic Information:")
        print(f"  Species: {species_traits.get('taxonomy_name')}")
        print(f"  Common name: {species_traits.get('common_name')}")
        print(f"  Authority: {species_traits.get('taxonomy_authority')}")

        if species_traits.get('morphology'):
            print(f"\nMorphological Traits:")
            for trait, value in species_traits['morphology'].items():
                print(f"  {trait.replace('_', ' ').title()}: {value}")

        if species_traits.get('ecology'):
            print(f"\nEcological Traits:")
            for trait, value in species_traits['ecology'].items():
                print(f"  {trait.replace('_', ' ').title()}: {value}")

        if species_traits.get('trophic'):
            print(f"\nTrophic Traits:")
            for trait, value in species_traits['trophic'].items():
                print(f"  {trait.replace('_', ' ').title()}: {value}")

        if species_traits.get('is_harmful'):
            print(f"\nIs Harmful: {species_traits['is_harmful']}")

    # Example 4: Search by species name
    print_separator()
    print("EXAMPLE 4: Search by Species Name")
    print_separator()

    search_term = "Coscinodiscus"
    print(f"Searching for: '{search_term}'")

    results = lookup.search_by_species_name(search_term)
    print(f"\nFound {len(results)} matches")

    # Show first 5 unique species
    seen_ids = set()
    unique_results = []
    for result in results:
        if result['aphia_id'] not in seen_ids:
            seen_ids.add(result['aphia_id'])
            unique_results.append(result)
        if len(unique_results) >= 5:
            break

    print(f"\nFirst 5 unique matches:")
    for i, result in enumerate(unique_results, 1):
        print(f"{i}. AphiaID {result['aphia_id']}: {result['species']}")
        print(f"   Source: {result['source']}")
        if 'genus' in result:
            print(f"   Genus: {result['genus']}")

    # Example 5: Get all traits (combines both databases)
    print_separator()
    print("EXAMPLE 5: Get All Traits from Both Databases")
    print_separator()

    aphia_id = 146564
    print(f"Looking up all traits for AphiaID: {aphia_id}")

    all_traits = lookup.get_all_traits(aphia_id)

    print(f"\nData sources found: {all_traits['data_sources']}")
    print(f"Has phytoplankton traits: {all_traits['phytoplankton_traits'] is not None}")
    print(f"Has enriched species traits: {all_traits['species_traits'] is not None}")

    if all_traits['phytoplankton_traits']:
        print("\nPhytoplankton data is available")
        phyto = all_traits['phytoplankton_traits']
        if phyto['multiple_size_classes']:
            print(f"  - {len(phyto['size_classes'])} size classes")

    if all_traits['species_traits']:
        print("\nEnriched species data is available")

    print_separator()
    print("EXAMPLES COMPLETE")
    print_separator()


if __name__ == "__main__":
    main()
