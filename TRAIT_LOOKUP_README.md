# Marine Species Trait Lookup

## Overview

The Trait Lookup module provides unified access to trait data from two complementary marine species databases:

1. **bvol_nomp_version_2024.xlsx** - Phytoplankton morphological traits
   - 3,846 records covering 1,132 unique species (primarily phytoplankton)
   - Detailed size measurements, biovolume, and carbon content
   - Multiple size classes for many species

2. **species_enriched.xlsx** - Marine species ecological and behavioral traits
   - 915 records covering 914 unique species (broader marine taxa)
   - Ecological, behavioral, and trophic characteristics
   - Size ranges, feeding methods, habitat preferences

Both datasets use **AphiaID** (WoRMS taxonomic identifier) as the primary key for species identification.

## Key Features

- **Unified API**: Single interface to query both datasets
- **Lazy Loading**: Data files loaded only when needed
- **Multiple Size Classes**: Handles phytoplankton with different size classes
- **Search Functionality**: Find species by name across both datasets
- **Comprehensive Traits**: Access morphological, ecological, and trophic information

## Installation & Setup

The trait lookup module is part of the `apis` package. Data files should be located in the parent directory of `gbif-api-client`:

```
HORIZON_EUROPE/Net/
├── bvol_nomp_version_2024.xlsx
├── species_enriched.xlsx
└── gbif-api-client/
    └── apis/
        └── trait_lookup.py
```

## Usage

### Basic Usage

```python
from apis import get_trait_lookup

# Get the singleton TraitLookup instance
lookup = get_trait_lookup()

# Get database statistics
stats = lookup.get_statistics()
print(f"Phytoplankton records: {stats['phytoplankton']['total_records']}")
print(f"Enriched species records: {stats['enriched_species']['total_records']}")
```

### Lookup by AphiaID

#### Phytoplankton Traits

```python
# Look up phytoplankton by AphiaID
phyto_traits = lookup.get_phytoplankton_traits(146564)

if phyto_traits:
    if phyto_traits['multiple_size_classes']:
        # Multiple size classes available
        print(f"Species has {len(phyto_traits['size_classes'])} size classes")

        for size_class in phyto_traits['size_classes']:
            print(f"Size class {size_class['size_class_no']}")
            print(f"  Range: {size_class['size_range']}")
            print(f"  Volume: {size_class['calculated_volume_um3']} μm³")
            print(f"  Carbon: {size_class['calculated_carbon_pg']} pg")
    else:
        # Single size class
        print(f"Species: {phyto_traits['species']}")
        print(f"Genus: {phyto_traits['genus']}")
        print(f"Shape: {phyto_traits['geometric_shape']}")
        print(f"Volume: {phyto_traits['calculated_volume_um3']} μm³")
```

#### Enriched Species Traits

```python
# Look up enriched species data
species_traits = lookup.get_species_traits(141433)

if species_traits:
    print(f"Species: {species_traits['taxonomy_name']}")
    print(f"Common name: {species_traits['common_name']}")

    # Morphological traits
    if species_traits['morphology']:
        print("\nMorphology:")
        for trait, value in species_traits['morphology'].items():
            print(f"  {trait}: {value}")

    # Ecological traits
    if species_traits['ecology']:
        print("\nEcology:")
        for trait, value in species_traits['ecology'].items():
            print(f"  {trait}: {value}")

    # Trophic traits
    if species_traits['trophic']:
        print("\nTrophic:")
        for trait, value in species_traits['trophic'].items():
            print(f"  {trait}: {value}")
```

#### Get All Available Traits

```python
# Get all available traits from both datasets
all_traits = lookup.get_all_traits(146564)

print(f"Data sources: {all_traits['data_sources']}")

if all_traits['phytoplankton_traits']:
    print("Has phytoplankton data")

if all_traits['species_traits']:
    print("Has enriched species data")
```

### Search by Species Name

```python
# Search for species by name (partial match supported)
results = lookup.search_by_species_name('Coscinodiscus')

print(f"Found {len(results)} matches")

for result in results[:5]:
    print(f"AphiaID {result['aphia_id']}: {result['species']}")
    print(f"  Source: {result['source']}")
    if 'genus' in result:
        print(f"  Genus: {result['genus']}")
```

## Data Structure

### Phytoplankton Traits (Single Size Class)

```python
{
    'aphia_id': 162699,
    'source': 'bvol_nomp_version_2024',
    'multiple_size_classes': False,
    'species': 'Chroococcus cumulatus',
    'genus': 'Chroococcus',
    'division': 'CYANOBACTERIA',
    'class': 'Cyanophyceae',
    'order': 'CHROOCOCCALES',
    'author': 'Geitler 1932',
    'trophic_type': 'AU',
    'geometric_shape': 'sphere',
    'formula': '4/3*π*(d1/2)^3',
    'size_class_no': 1,
    'size_range': '2-5',
    'measurements_um': {
        'Diameter_d1_um': 3.5
    },
    'calculated_volume_um3': 22.45,
    'calculated_carbon_pg': 5.39,
    'cells_per_counting_unit': 1.0,
    'geographic_areas': {
        'helcom': 'x',
        'ospar': None
    }
}
```

### Phytoplankton Traits (Multiple Size Classes)

```python
{
    'aphia_id': 146564,
    'source': 'bvol_nomp_version_2024',
    'multiple_size_classes': True,
    'size_classes': [
        {
            'aphia_id': 146564,
            'species': 'Aphanocapsa elachista',
            'genus': 'Aphanocapsa',
            'size_class_no': 1,
            'size_range': '1.3-2',
            'calculated_volume_um3': 2.14,
            'calculated_carbon_pg': 0.93,
            # ... other traits
        },
        {
            'size_class_no': 2,
            'size_range': '2-3',
            # ... traits for size class 2
        },
        # ... more size classes
    ]
}
```

### Enriched Species Traits

```python
{
    'aphia_id': 141433,
    'source': 'species_enriched',
    'species_id': 'NBNSYS0000002076',
    'taxonomy_name': 'Abra alba',
    'common_name': 'White furrow shell',
    'taxonomy_authority': '(W. Wood, 1802)',
    'url': 'https://www.marlin.ac.uk/species/detail/2076',
    'morphology': {
        'female_size_range': '10-25mm',
        'growth_form': 'Vermiform',
        'body_flexibility': 'Flexible'
    },
    'ecology': {
        'typical_abundance': 'Common',
        'growth_rate': 'Fast',
        'mobility': 'Slow',
        'environmental_position': 'Infaunal',
        'dependency': 'Independent'
    },
    'trophic': {
        'feeding_method': 'Deposit feeder',
        'diet_food_source': 'Detritus',
        'typically_feeds_on': 'Organic particles'
    },
    'is_harmful': 'Not harmful'
}
```

## Available Trait Categories

### Phytoplankton (bvol_nomp_version_2024)

#### Taxonomic
- Division, Class, Order, Genus, Species, Author
- WoRMS Rank

#### Morphological
- Geometric shape (sphere, ellipsoid, cylinder, etc.)
- Formula for volume calculation
- Size measurements (μm):
  - Length (l1, l2)
  - Width (w)
  - Height (h)
  - Diameter (d1, d2)
  - Filament length

#### Calculated Values
- Biovolume (μm³)
- Carbon content (pg)
- Number of cells per counting unit

#### Ecological
- Trophic type (AU = autotroph, etc.)
- Size class and range

#### Geographic
- HELCOM area
- OSPAR area

### Enriched Species (species_enriched)

#### Taxonomic
- Taxonomy name
- Common name
- Authority
- Species ID
- NBN Version Key

#### Morphological
- Male/female size range
- Male/female size at maturity
- Growth form
- Body flexibility

#### Ecological/Behavioral
- Typical abundance
- Growth rate
- Mobility
- Sociability
- Environmental position
- Dependency
- Species supports

#### Trophic
- Characteristic feeding method
- Diet/food source
- Typically feeds on

#### Other
- Is the species harmful?

## Integration with GBIF Client

The trait lookup can be integrated with GBIF occurrence data to enrich species records:

```python
from gbif_client import GBIFClient
from apis import get_trait_lookup

gbif = GBIFClient()
lookup = get_trait_lookup()

# Search for a species
species = gbif.search_species("Coscinodiscus asteromphalus", limit=1)
if species:
    taxon_key = species[0]['key']

    # Get AphiaID from GBIF (if available in occurrence data)
    # Or use a taxonomic matching service

    # Look up traits
    traits = lookup.get_all_traits(aphia_id)

    # Combine GBIF occurrence data with trait data
    enriched_data = {
        'gbif_taxon_key': taxon_key,
        'species_name': species[0]['species'],
        'traits': traits
    }
```

## Performance Considerations

- **Lazy Loading**: Excel files are only loaded when first accessed
- **Singleton Pattern**: TraitLookup instance is reused across the application
- **In-Memory Storage**: Once loaded, data is kept in memory for fast access
- **Pandas DataFrames**: Efficient filtering and querying

## Error Handling

```python
# Handle missing data gracefully
traits = lookup.get_phytoplankton_traits(999999)
if traits is None:
    print("No traits found for this AphiaID")

# Check data availability
stats = lookup.get_statistics()
if stats['phytoplankton']['total_records'] == 0:
    print("Phytoplankton data file not loaded")
```

## Limitations

1. **No Overlap**: The two datasets contain different species (no common AphiaIDs)
   - bvol_nomp_version_2024: Primarily phytoplankton
   - species_enriched: Broader marine taxa

2. **Static Data**: Data is loaded from Excel files and not updated automatically

3. **File Dependencies**: Requires Excel files to be in the correct location

## Future Enhancements

Potential improvements for the trait lookup system:

1. **Database Backend**: Move from Excel to SQLite or PostgreSQL for better performance
2. **API Integration**: Connect to WoRMS API for real-time taxonomic validation
3. **Trait Standardization**: Normalize trait values across datasets
4. **Caching**: Add caching layer for frequently accessed traits
5. **Bulk Lookup**: Optimize for bulk AphiaID queries
6. **Export Functions**: Export trait data to various formats (CSV, JSON, etc.)

## Contact & Support

For issues or questions about the trait lookup module, please refer to the main project documentation or contact the development team.

## Data Sources

- **bvol_nomp_version_2024.xlsx**: HELCOM/OSPAR phytoplankton biovolume reference list
- **species_enriched.xlsx**: Marine species biological traits from MARLIN (Marine Life Information Network)

Both datasets use WoRMS (World Register of Marine Species) AphiaID as the taxonomic identifier.
