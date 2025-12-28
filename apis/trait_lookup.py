"""
Trait Lookup Module for Marine Species

This module provides access to trait data from two complementary datasets:
1. bvol_nomp_version_2024.xlsx - Phytoplankton morphological traits
2. species_enriched.xlsx - Broader marine species ecological/behavioral traits

Both datasets use AphiaID (WoRMS taxonomic identifier) as the primary key.
"""

import functools
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


class TraitLookup:
    """
    Unified trait lookup service for marine species traits.

    Provides access to:
    - Phytoplankton morphological traits (size, volume, carbon content)
    - Marine species ecological and behavioral traits
    """

    def __init__(
        self,
        bvol_path: Optional[str] = None,
        species_enriched_path: Optional[str] = None
    ):
        """
        Initialize trait lookup with paths to data files.

        Args:
            bvol_path: Path to bvol_nomp_version_2024.xlsx
            species_enriched_path: Path to species_enriched.xlsx
        """
        # Default paths (assume files are in parent directory of gbif-api-client)
        base_path = Path(__file__).parent.parent.parent

        self.bvol_path = bvol_path or str(base_path / "bvol_nomp_version_2024.xlsx")
        self.species_enriched_path = species_enriched_path or str(
            base_path / "species_enriched.xlsx"
        )

        # Lazy loading - data loaded on first access
        self._bvol_data: Optional[pd.DataFrame] = None
        self._species_data: Optional[pd.DataFrame] = None
        self._bvol_loaded = False
        self._species_loaded = False

    @property
    def bvol_data(self) -> pd.DataFrame:
        """Lazy load phytoplankton trait data."""
        if not self._bvol_loaded:
            self._load_bvol_data()
        return self._bvol_data

    @property
    def species_data(self) -> pd.DataFrame:
        """Lazy load enriched species trait data."""
        if not self._species_loaded:
            self._load_species_data()
        return self._species_data

    def _load_bvol_data(self) -> None:
        """Load phytoplankton biovolume and trait data."""
        try:
            if not os.path.exists(self.bvol_path):
                logger.warning(f"Biovolume data file not found: {self.bvol_path}")
                self._bvol_data = pd.DataFrame()
            else:
                logger.info(f"Loading biovolume data from {self.bvol_path}")
                df = pd.read_excel(self.bvol_path)

                # Standardize AphiaID column
                if 'AphiaID' in df.columns:
                    df['AphiaID'] = df['AphiaID'].astype('Int64')

                self._bvol_data = df
                logger.info(
                    f"Loaded {len(df)} phytoplankton records "
                    f"with {df['AphiaID'].nunique()} unique AphiaIDs"
                )
        except Exception as e:
            logger.error(f"Error loading biovolume data: {e}")
            self._bvol_data = pd.DataFrame()
        finally:
            self._bvol_loaded = True

    def _load_species_data(self) -> None:
        """Load enriched species trait data."""
        try:
            if not os.path.exists(self.species_enriched_path):
                logger.warning(
                    f"Species enriched data file not found: {self.species_enriched_path}"
                )
                self._species_data = pd.DataFrame()
            else:
                logger.info(f"Loading species data from {self.species_enriched_path}")
                df = pd.read_excel(self.species_enriched_path)

                # Standardize AphiaID column (it's lowercase 'aphiaID' in this file)
                if 'aphiaID' in df.columns:
                    df['AphiaID'] = df['aphiaID'].astype('Int64')
                elif 'AphiaID' in df.columns:
                    df['AphiaID'] = df['AphiaID'].astype('Int64')

                self._species_data = df
                logger.info(
                    f"Loaded {len(df)} enriched species records "
                    f"with {df['AphiaID'].nunique()} unique AphiaIDs"
                )
        except Exception as e:
            logger.error(f"Error loading species enriched data: {e}")
            self._species_data = pd.DataFrame()
        finally:
            self._species_loaded = True

    def get_phytoplankton_traits(self, aphia_id: int) -> Optional[Dict[str, Any]]:
        """
        Get phytoplankton morphological traits by AphiaID.

        Args:
            aphia_id: WoRMS AphiaID

        Returns:
            Dictionary with trait data or None if not found
        """
        if self.bvol_data.empty:
            return None

        matches = self.bvol_data[self.bvol_data['AphiaID'] == aphia_id]

        if matches.empty:
            return None

        # If multiple size classes, return all as a list
        if len(matches) > 1:
            traits_list = []
            for _, row in matches.iterrows():
                traits_list.append(self._extract_bvol_traits(row))
            return {
                'aphia_id': aphia_id,
                'source': 'bvol_nomp_version_2024',
                'multiple_size_classes': True,
                'size_classes': traits_list
            }
        else:
            row = matches.iloc[0]
            result = self._extract_bvol_traits(row)
            result['source'] = 'bvol_nomp_version_2024'
            result['multiple_size_classes'] = False
            return result

    def _extract_bvol_traits(self, row: pd.Series) -> Dict[str, Any]:
        """Extract relevant traits from a bvol data row."""
        # Helper function to safely get values
        def safe_get(col_name):
            if col_name in row.index:
                val = row[col_name]
                return val if pd.notna(val) else None
            return None

        # Clean up column names for dictionary keys
        traits = {
            'aphia_id': int(row['AphiaID']) if pd.notna(row['AphiaID']) else None,
            'species': safe_get('Species'),
            'genus': safe_get('Genus'),
            'division': safe_get('Division'),
            'class': safe_get('Class'),
            'order': safe_get('Order'),
            'author': safe_get('Author'),
            'trophic_type': safe_get('Trophy'),
            'geometric_shape': safe_get('Geometric_shape'),
            'formula': safe_get('FORMULA'),
            'size_class_no': safe_get('SizeClassNo'),
            'size_range': safe_get('SizeRange'),
        }

        # Size measurements (micrometers)
        size_cols = [
            'Length(l1)µm', 'Length(l2)µm', 'Width(w)µm',
            'Height(h)µm', 'Diameter(d1)µm', 'Diameter(d2)µm',
            'Filament_length_of_cell(µm)'
        ]

        traits['measurements_um'] = {}
        for col in size_cols:
            # Handle different possible column name encodings
            matching_cols = [c for c in row.index if col.replace('µ', '').replace('m', '') in c]
            if matching_cols:
                val = row[matching_cols[0]]
                if pd.notna(val):
                    key = col.replace('(', '_').replace(')', '').replace('µm', 'um')
                    traits['measurements_um'][key] = float(val)

        # Volume and carbon
        vol_col = 'Calculated_volume_µm3/counting_unit'
        carbon_col = 'Calculated_Carbon_pg/counting_unit'

        # Find matching columns (handle encoding issues)
        vol_matches = [c for c in row.index if 'volume' in c.lower() and 'counting_unit' in c]
        carbon_matches = [c for c in row.index if 'Carbon_pg/counting_unit' in c and 'formula' not in c]

        if vol_matches:
            val = row[vol_matches[0]]
            traits['calculated_volume_um3'] = float(val) if pd.notna(val) else None

        if carbon_matches:
            val = row[carbon_matches[0]]
            traits['calculated_carbon_pg'] = float(val) if pd.notna(val) else None

        # Cell count
        if 'No_of_cells/counting_unit' in row.index:
            val = row['No_of_cells/counting_unit']
            traits['cells_per_counting_unit'] = float(val) if pd.notna(val) else None

        # Geographic distribution
        traits['geographic_areas'] = {
            'helcom': safe_get('HELCOM area'),
            'ospar': safe_get('OSPAR area')
        }

        # Comments
        comment = safe_get('Comment')
        if comment:
            traits['comment'] = comment

        return traits

    def get_species_traits(self, aphia_id: int) -> Optional[Dict[str, Any]]:
        """
        Get enriched species ecological/behavioral traits by AphiaID.

        Args:
            aphia_id: WoRMS AphiaID

        Returns:
            Dictionary with trait data or None if not found
        """
        if self.species_data.empty:
            return None

        matches = self.species_data[self.species_data['AphiaID'] == aphia_id]

        if matches.empty:
            return None

        row = matches.iloc[0]

        # Helper function to safely get values
        def safe_get(col_name):
            if col_name in row.index:
                val = row[col_name]
                return val if pd.notna(val) else None
            return None

        traits = {
            'aphia_id': aphia_id,
            'source': 'species_enriched',
            'species_id': safe_get('speciesID'),
            'taxonomy_name': safe_get('taxonomyName'),
            'common_name': safe_get('synonymCommonName'),
            'taxonomy_authority': safe_get('taxonomyAuthority'),
            'url': safe_get('url'),
        }

        # Morphological traits
        traits['morphology'] = {
            'male_size_range': safe_get('biology_male_size_range'),
            'male_size_at_maturity': safe_get('biology_male_size_at_maturity'),
            'female_size_range': safe_get('biology_female_size_range'),
            'female_size_at_maturity': safe_get('biology_female_size_at_maturity'),
            'growth_form': safe_get('biology_growth_form'),
            'body_flexibility': safe_get('biology_body_flexibility'),
        }

        # Ecological traits
        traits['ecology'] = {
            'typical_abundance': safe_get('biology_typical_abundance'),
            'growth_rate': safe_get('biology_growth_rate'),
            'mobility': safe_get('biology_mobility'),
            'sociability': safe_get('biology_sociability'),
            'environmental_position': safe_get('biology_environmental_position'),
            'dependency': safe_get('biology_dependency'),
            'supports': safe_get('biology_supports'),
        }

        # Trophic traits
        traits['trophic'] = {
            'feeding_method': safe_get('biology_characteristic_feeding_method'),
            'diet_food_source': safe_get('biology_dietfood_source'),
            'typically_feeds_on': safe_get('biology_typically_feeds_on'),
        }

        # Other
        traits['is_harmful'] = safe_get('biology_is_the_species_harmful')

        # Remove None values from nested dicts
        for key in ['morphology', 'ecology', 'trophic']:
            traits[key] = {k: v for k, v in traits[key].items() if pd.notna(v)}

        return traits

    def get_all_traits(self, aphia_id: int) -> Dict[str, Any]:
        """
        Get all available traits for a species from both datasets.

        Args:
            aphia_id: WoRMS AphiaID

        Returns:
            Combined dictionary with all available trait data
        """
        result = {
            'aphia_id': aphia_id,
            'phytoplankton_traits': None,
            'species_traits': None,
            'data_sources': []
        }

        # Get phytoplankton traits
        phyto_traits = self.get_phytoplankton_traits(aphia_id)
        if phyto_traits:
            result['phytoplankton_traits'] = phyto_traits
            result['data_sources'].append('bvol_nomp_version_2024')

        # Get enriched species traits
        species_traits = self.get_species_traits(aphia_id)
        if species_traits:
            result['species_traits'] = species_traits
            result['data_sources'].append('species_enriched')

        if not result['data_sources']:
            logger.info(f"No trait data found for AphiaID {aphia_id}")

        return result

    def search_by_species_name(self, species_name: str) -> List[Dict[str, Any]]:
        """
        Search for species by name across both datasets.

        Args:
            species_name: Species name (partial match supported)

        Returns:
            List of matching species with their AphiaIDs
        """
        results = []
        species_name_lower = species_name.lower()

        # Search in bvol data
        if not self.bvol_data.empty and 'Species' in self.bvol_data.columns:
            matches = self.bvol_data[
                self.bvol_data['Species'].str.lower().str.contains(
                    species_name_lower, na=False
                )
            ]
            for _, row in matches.iterrows():
                if pd.notna(row['AphiaID']):
                    results.append({
                        'aphia_id': int(row['AphiaID']),
                        'species': row['Species'],
                        'genus': row.get('Genus'),
                        'source': 'bvol_nomp_version_2024'
                    })

        # Search in species enriched data
        if not self.species_data.empty and 'taxonomyName' in self.species_data.columns:
            matches = self.species_data[
                self.species_data['taxonomyName'].str.lower().str.contains(
                    species_name_lower, na=False
                )
            ]
            for _, row in matches.iterrows():
                if pd.notna(row['AphiaID']):
                    results.append({
                        'aphia_id': int(row['AphiaID']),
                        'species': row['taxonomyName'],
                        'common_name': row.get('synonymCommonName'),
                        'source': 'species_enriched'
                    })

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the trait databases."""
        return {
            'phytoplankton': {
                'total_records': len(self.bvol_data) if not self.bvol_data.empty else 0,
                'unique_aphia_ids': (
                    self.bvol_data['AphiaID'].nunique()
                    if not self.bvol_data.empty else 0
                ),
                'file_loaded': self._bvol_loaded,
                'file_path': self.bvol_path
            },
            'enriched_species': {
                'total_records': len(self.species_data) if not self.species_data.empty else 0,
                'unique_aphia_ids': (
                    self.species_data['AphiaID'].nunique()
                    if not self.species_data.empty else 0
                ),
                'file_loaded': self._species_loaded,
                'file_path': self.species_enriched_path
            }
        }


# Global singleton instance (lazy loaded)
_trait_lookup_instance: Optional[TraitLookup] = None


def get_trait_lookup() -> TraitLookup:
    """Get or create the global TraitLookup instance."""
    global _trait_lookup_instance
    if _trait_lookup_instance is None:
        _trait_lookup_instance = TraitLookup()
    return _trait_lookup_instance
