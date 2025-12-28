"""
Import traits from Excel files into SQLite database.

This script populates the trait ontology database with data from:
- bvol_nomp_version_2024.xlsx (phytoplankton traits)
- species_enriched.xlsx (enriched marine species traits)
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apis.trait_ontology_db import get_trait_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_size_range(size_range_str: str) -> tuple:
    """
    Parse size range string like '1.3-2' into min and max values.

    Returns:
        (min_value, max_value) tuple
    """
    if not size_range_str or pd.isna(size_range_str):
        return None, None

    try:
        size_range_str = str(size_range_str).strip()
        if '-' in size_range_str:
            parts = size_range_str.split('-')
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())
            return min_val, max_val
        else:
            # Single value
            val = float(size_range_str)
            return val, val
    except (ValueError, IndexError):
        logger.warning(f"Could not parse size range: {size_range_str}")
        return None, None


def import_phytoplankton_data(db, excel_path: str) -> int:
    """
    Import phytoplankton trait data from bvol_nomp_version_2024.xlsx.

    Returns:
        Number of species imported
    """
    logger.info(f"Loading phytoplankton data from {excel_path}")
    df = pd.read_excel(excel_path)

    logger.info(f"Loaded {len(df)} phytoplankton records")

    species_count = 0
    trait_value_count = 0

    # Group by AphiaID to handle multiple size classes
    grouped = df.groupby('AphiaID')

    for aphia_id, group in grouped:
        if pd.isna(aphia_id):
            continue

        aphia_id = int(aphia_id)

        # Use first row for species-level data
        first_row = group.iloc[0]

        # Add species
        species_id = db.add_species(
            aphia_id=aphia_id,
            scientific_name=first_row.get('Species') if pd.notna(first_row.get('Species')) else None,
            genus=first_row.get('Genus') if pd.notna(first_row.get('Genus')) else None,
            author=first_row.get('Author') if pd.notna(first_row.get('Author')) else None,
            data_source='bvol_nomp_version_2024'
        )

        if species_id:
            species_count += 1

            # Add taxonomy
            db.add_taxonomy(
                species_id=species_id,
                kingdom='Chromista' if first_row.get('Division') not in ['CYANOBACTERIA'] else 'Bacteria',
                division=first_row.get('Division') if pd.notna(first_row.get('Division')) else None,
                class_name=first_row.get('Class') if pd.notna(first_row.get('Class')) else None,
                order_name=first_row.get('Order') if pd.notna(first_row.get('Order')) else None,
                genus=first_row.get('Genus') if pd.notna(first_row.get('Genus')) else None,
                species=first_row.get('Species') if pd.notna(first_row.get('Species')) else None,
                rank=first_row.get('WORMS Rank') if pd.notna(first_row.get('WORMS Rank')) else None
            )

            # Add geographic distribution
            if pd.notna(first_row.get('HELCOM area')):
                db.add_geographic_distribution(species_id, 'HELCOM', first_row['HELCOM area'])
            if pd.notna(first_row.get('OSPAR area')):
                db.add_geographic_distribution(species_id, 'OSPAR', first_row['OSPAR area'])

            # Process each size class
            for _, row in group.iterrows():
                size_class_no = row.get('SizeClassNo')
                size_range = row.get('SizeRange')

                # Add size class
                size_class_id = None
                if pd.notna(size_class_no):
                    size_range_min, size_range_max = parse_size_range(size_range)
                    size_class_id = db.add_size_class(
                        species_id=species_id,
                        size_class_no=int(size_class_no),
                        size_range=str(size_range) if pd.notna(size_range) else None,
                        size_range_min=size_range_min,
                        size_range_max=size_range_max
                    )

                # Add trait values for this size class

                # Trophic type
                if pd.notna(row.get('Trophy')):
                    db.add_trait_value(
                        species_id, 'trophic_type', row['Trophy'],
                        size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                    )
                    trait_value_count += 1

                # Geometric shape
                if pd.notna(row.get('Geometric_shape')):
                    db.add_trait_value(
                        species_id, 'geometric_shape', row['Geometric_shape'],
                        size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                    )
                    trait_value_count += 1

                # Size measurements (try different column name variations)
                size_columns = {
                    'length_l1': ['Length(l1)μm', 'Length(l1)µm'],
                    'length_l2': ['Length(l2)μm', 'Length(l2)µm'],
                    'width': ['Width(w)μm', 'Width(w)µm'],
                    'height': ['Height(h)μm', 'Height(h)µm'],
                    'diameter_d1': ['Diameter(d1)μm', 'Diameter(d1)µm'],
                    'diameter_d2': ['Diameter(d2)μm', 'Diameter(d2)µm'],
                    'filament_length': ['Filament_length_of_cell(μm)', 'Filament_length_of_cell(µm)']
                }

                for trait_name, possible_cols in size_columns.items():
                    for col in possible_cols:
                        # Try to find matching column (case-insensitive, handle encoding)
                        matching_cols = [c for c in row.index if col.replace('µ', '').replace('μ', '') in c]
                        if matching_cols:
                            value = row[matching_cols[0]]
                            if pd.notna(value):
                                db.add_trait_value(
                                    species_id, trait_name, float(value),
                                    size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                                )
                                trait_value_count += 1
                            break

                # Biovolume
                vol_cols = [c for c in row.index if 'volume' in c.lower() and 'counting_unit' in c and 'formula' not in c.lower()]
                if vol_cols:
                    value = row[vol_cols[0]]
                    if pd.notna(value):
                        db.add_trait_value(
                            species_id, 'biovolume', float(value),
                            size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                        )
                        trait_value_count += 1

                # Carbon content
                carbon_cols = [c for c in row.index if 'Carbon_pg/counting_unit' in c and 'formula' not in c]
                if carbon_cols:
                    value = row[carbon_cols[0]]
                    if pd.notna(value):
                        db.add_trait_value(
                            species_id, 'carbon_content', float(value),
                            size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                        )
                        trait_value_count += 1

                # Cells per counting unit
                if 'No_of_cells/counting_unit' in row.index and pd.notna(row['No_of_cells/counting_unit']):
                    db.add_trait_value(
                        species_id, 'cells_per_unit', float(row['No_of_cells/counting_unit']),
                        size_class_id=size_class_id, data_source='bvol_nomp_version_2024'
                    )
                    trait_value_count += 1

        if species_count % 100 == 0:
            logger.info(f"Imported {species_count} phytoplankton species...")

    logger.info(f"Imported {species_count} phytoplankton species with {trait_value_count} trait values")
    return species_count


def import_enriched_species_data(db, excel_path: str) -> int:
    """
    Import enriched species trait data from species_enriched.xlsx.

    Returns:
        Number of species imported
    """
    logger.info(f"Loading enriched species data from {excel_path}")
    df = pd.read_excel(excel_path)

    logger.info(f"Loaded {len(df)} enriched species records")

    species_count = 0
    trait_value_count = 0

    for _, row in df.iterrows():
        aphia_id_col = 'aphiaID' if 'aphiaID' in row.index else 'AphiaID'

        if pd.isna(row.get(aphia_id_col)):
            continue

        aphia_id = int(row[aphia_id_col])

        # Add species
        species_id = db.add_species(
            aphia_id=aphia_id,
            scientific_name=row.get('taxonomyName') if pd.notna(row.get('taxonomyName')) else None,
            common_name=row.get('synonymCommonName') if pd.notna(row.get('synonymCommonName')) else None,
            author=row.get('taxonomyAuthority') if pd.notna(row.get('taxonomyAuthority')) else None,
            data_source='species_enriched'
        )

        if species_id:
            species_count += 1

            # Add trait values
            trait_mappings = {
                # Morphological
                'male_size_range': 'biology_male_size_range',
                'female_size_range': 'biology_female_size_range',
                'male_size_at_maturity': 'biology_male_size_at_maturity',
                'female_size_at_maturity': 'biology_female_size_at_maturity',
                'growth_form': 'biology_growth_form',
                'body_flexibility': 'biology_body_flexibility',

                # Ecological
                'typical_abundance': 'biology_typical_abundance',
                'growth_rate': 'biology_growth_rate',
                'mobility': 'biology_mobility',
                'sociability': 'biology_sociability',
                'environmental_position': 'biology_environmental_position',
                'dependency': 'biology_dependency',
                'supports': 'biology_supports',

                # Trophic
                'feeding_method': 'biology_characteristic_feeding_method',
                'diet_food_source': 'biology_dietfood_source',
                'feeds_on': 'biology_typically_feeds_on',

                # Other
                'is_harmful': 'biology_is_the_species_harmful',
            }

            for trait_name, column_name in trait_mappings.items():
                if column_name in row.index and pd.notna(row[column_name]):
                    db.add_trait_value(
                        species_id, trait_name, row[column_name],
                        data_source='species_enriched'
                    )
                    trait_value_count += 1

        if species_count % 100 == 0:
            logger.info(f"Imported {species_count} enriched species...")

    logger.info(f"Imported {species_count} enriched species with {trait_value_count} trait values")
    return species_count


def main():
    """Main import function."""
    logger.info("Starting trait database import")

    # Paths
    base_path = Path(__file__).parent.parent.parent
    bvol_path = base_path / "bvol_nomp_version_2024.xlsx"
    species_path = base_path / "species_enriched.xlsx"

    # Check files exist
    if not bvol_path.exists():
        logger.error(f"Phytoplankton data file not found: {bvol_path}")
        return

    if not species_path.exists():
        logger.error(f"Enriched species data file not found: {species_path}")
        return

    # Initialize database
    db = get_trait_db()

    # Initialize categories and traits
    logger.info("Initializing trait categories and definitions")
    db.initialize_trait_categories()
    db.initialize_traits()

    # Import data
    total_species = 0

    logger.info("\n" + "=" * 70)
    logger.info("IMPORTING PHYTOPLANKTON DATA")
    logger.info("=" * 70)
    phyto_count = import_phytoplankton_data(db, str(bvol_path))
    total_species += phyto_count

    logger.info("\n" + "=" * 70)
    logger.info("IMPORTING ENRICHED SPECIES DATA")
    logger.info("=" * 70)
    enriched_count = import_enriched_species_data(db, str(species_path))
    total_species += enriched_count

    # Get statistics
    logger.info("\n" + "=" * 70)
    logger.info("DATABASE STATISTICS")
    logger.info("=" * 70)

    stats = db.get_statistics()

    logger.info(f"Total species: {stats['total_species']}")
    logger.info(f"Total traits defined: {stats['total_traits']}")
    logger.info(f"Total trait values: {stats['total_trait_values']}")
    logger.info(f"Total categories: {stats['total_categories']}")

    logger.info("\nSpecies by source:")
    for source, count in stats['species_by_source'].items():
        logger.info(f"  {source}: {count}")

    logger.info("\nTraits by category:")
    for category, count in stats['traits_by_category'].items():
        logger.info(f"  {category}: {count}")

    logger.info("\n" + "=" * 70)
    logger.info("IMPORT COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Database location: {db.db_path}")

    db.close()


if __name__ == "__main__":
    main()
