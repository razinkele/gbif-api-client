# Marine & Biodiversity Data Explorer

**Version 2.0.0** | Comprehensive marine biodiversity data integration platform

A powerful Python-based web application for accessing, analyzing, and visualizing marine biodiversity data from multiple international databases with integrated trait ontology capabilities.

---

## Overview

The Marine & Biodiversity Data Explorer is a professional-grade application that integrates data from 10+ marine biodiversity databases into a single, intuitive interface. Built with Python Shiny, it provides researchers, scientists, and biodiversity analysts with comprehensive access to:

- **Species occurrence data** from GBIF, SHARK, OBIS
- **Taxonomic information** from WoRMS, Dyntaxa (SLU Artdatabanken)
- **Phytoplankton data** from Nordic Microalgae, AlgaeBase
- **Trait data** from specialized trait databases (2,046 species, 21,102 trait values)
- **Harmful algae information** from IOC-UNESCO HAB database
- **Freshwater ecology** data integration

## Key Features

### Multi-Database Integration
- **GBIF (Global Biodiversity Information Facility)**: 2+ billion occurrence records
- **SHARK (Swedish oceanographic data)**: Swedish marine monitoring data
- **OBIS (Ocean Biodiversity Information System)**: Marine species occurrences
- **WoRMS (World Register of Marine Species)**: Taxonomic authority
- **Dyntaxa (SLU Artdatabanken)**: Swedish taxonomic database
- **Nordic Microalgae**: Nordic microalgae & cyanobacteria
- **AlgaeBase**: Global algal database
- **IOC-UNESCO HAB**: Harmful algal blooms database
- **Freshwater Ecology**: Freshwater species data
- **Plankton Toolbox**: Baltic plankton monitoring data

### Trait Ontology Database
- **2,046 species** with comprehensive trait data
- **21,102 trait values** across 29 trait types
- **15 trait categories**: morphological, ecological, trophic, behavioral
- **Query by traits**: Find species by biovolume, trophic type, shape, mobility, etc.
- **Multiple size classes**: Phytoplankton trait variations by size
- **Geographic distribution**: HELCOM/OSPAR area data

### Advanced Analysis Features
- **Bulk species analysis**: Process hundreds of species from Excel files
- **Size data detection**: Comprehensive morphological measurements
- **Real-time progress tracking**: Monitor long-running analyses
- **Interactive visualizations**: Maps, charts, and data tables
- **Export capabilities**: Download results in multiple formats

### Professional UI/UX
- **Modern dashboard design**: Card-based layout with intuitive navigation
- **Responsive components**: Optimized for various screen sizes
- **Real-time updates**: Reactive data binding for instant feedback
- **Custom styling**: Professional CSS with design tokens
- **10 specialized tabs**: Organized by data source and function

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gbif-api-client.git
   cd gbif-api-client
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize trait database** (optional, for trait features)
   ```bash
   python scripts/import_traits_to_db.py
   ```

4. **Run the application**
   ```bash
   shiny run app.py
   ```

5. **Access the dashboard**
   - Open your browser to `http://localhost:8000`
   - Start exploring marine biodiversity data!

### Development Installation

For development with testing and linting tools:

```bash
pip install -r requirements-dev.txt
```

## Usage Guide

### Dashboard Navigation

The application is organized into 10 main tabs:

1. **Dashboard**: Overview and bulk analysis summary
2. **Species**: Species search results and detailed information
3. **Occurrences**: Occurrence records with statistics
4. **Map**: Interactive geographic distribution maps
5. **Bulk Analysis**: Results from batch species processing
6. **SHARK Marine Data**: Swedish oceanographic database
7. **SLU Artdatabanken (Dyntaxa)**: Swedish taxonomy
8. **WoRMS**: World Register of Marine Species
9. **Database Overview**: Integration status and capabilities
10. **Trait Database**: Trait-based species queries

### Searching for Species

**Basic Search:**
1. Enter species name in the search box (e.g., "Fucus vesiculosus")
2. Optional: Select country filter
3. Optional: Enable "Only show records with size data"
4. Click "Search"

**Trait-Based Search:**
1. Navigate to "Trait Database" tab
2. Select trait from dropdown (biovolume, trophic type, etc.)
3. Set query parameters:
   - Numeric traits: Enter min/max range
   - Categorical traits: Select value
4. Click "Search by Trait"
5. View matching species and detailed trait information

### Bulk Species Analysis

Process multiple species from Excel files:

1. **Prepare Excel file**
   - Species names in first column
   - No headers required
   - .xlsx format

2. **Upload and analyze**
   - Click "Browse" to select file
   - Click "Analyze Species for Size Data"
   - Monitor progress in Progress tab

3. **View results**
   - Switch to "Bulk Analysis" tab
   - See which species have size data available
   - Export results if needed

### Size Data Detection

The application comprehensively checks for organism size data:

**Data Sources:**
- MeasurementOrFact extension (detailed measurements)
- Dynamic properties (morphological data)
- Sampling protocols (size fractions)
- Traditional fields (organismQuantity, individualCount)

**Measurement Types:**
- Cell dimensions (length, width, diameter, height)
- Volume measurements (biovolume, biomass)
- Carbon content
- Size fractions from sampling protocols

**Recommended Datasets:**
- KPLANK (Finnish Baltic monitoring): 240,000+ records with size classes
- San Francisco Bay Phytoplankton: Microscopic cell size analyses
- Tara Oceans: Size fraction data (20-200 μm)
- Inner Oslofjorden Phytoplankton: Quantitative cell measurements

## Project Structure

```
gbif-api-client/
├── apis/                          # API client modules
│   ├── __init__.py
│   ├── algaebase_api.py          # AlgaeBase integration
│   ├── dyntaxa_api.py            # Dyntaxa/SLU integration
│   ├── freshwater_ecology_api.py # Freshwater data
│   ├── ioc_hab_api.py            # IOC harmful algae
│   ├── nordic_microalgae_api.py  # Nordic microalgae
│   ├── obis_api.py               # OBIS integration
│   ├── shark_api.py              # SHARK integration
│   ├── trait_lookup.py           # Pandas-based trait lookup
│   ├── trait_ontology_db.py      # SQLite trait database
│   └── worms_api.py              # WoRMS integration
│
├── app_modules/                   # Application modules
│   ├── constants.py              # Configuration constants
│   ├── utils.py                  # Utility functions
│   ├── trait_utils.py            # Trait data utilities
│   └── ui/
│       ├── __init__.py
│       └── components.py         # Reusable UI components
│
├── data/                          # Data files
│   └── trait_ontology.db         # Trait database (SQLite)
│
├── examples/                      # Usage examples
│   └── trait_lookup_example.py   # Trait database examples
│
├── scripts/                       # Utility scripts
│   ├── import_traits_to_db.py    # Trait data import
│   ├── test_trait_db.py          # Database tests
│   └── test_trait_integration.py # Integration tests
│
├── tests/                         # Test suite
│   ├── test_gbif_client.py
│   ├── test_shark_api.py
│   ├── test_worms_api.py
│   └── ...
│
├── www/                           # Static web assets
│   └── custom.css                # Custom styling
│
├── app.py                         # Main Shiny application
├── gbif_client.py                # GBIF API client
├── shark_client.py               # SHARK client
├── requirements.txt              # Dependencies
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

## Architecture

### Modular Design

The application follows a clean, modular architecture:

- **API Layer** (`apis/`): Independent API clients for each data source
- **Application Logic** (`app_modules/`): Business logic and utilities
- **UI Layer** (`app.py` + `app_modules/ui/`): Presentation and user interaction
- **Data Layer** (`data/`): Local databases and cached data

### Key Design Patterns

- **Singleton Pattern**: Database connections (trait_ontology_db)
- **Factory Pattern**: API client creation
- **Observer Pattern**: Reactive programming (Shiny)
- **Strategy Pattern**: Different size data detection strategies

### Database Schema

The trait ontology database uses 8 normalized tables:

```sql
species                      -- Core species information
trait_categories            -- Hierarchical trait categories
traits                      -- Trait definitions with data types
trait_values                -- Actual measurements and values
size_classes                -- Phytoplankton size class data
geographic_distribution     -- Species distribution data
taxonomic_hierarchy         -- Complete taxonomic classification
trait_relationships         -- Ontological relationships
```

## API Documentation

### GBIF Client

```python
from gbif_client import GBIFClient

client = GBIFClient()

# Search for species
species = client.search_species("Fucus vesiculosus")

# Get occurrences
occurrences = client.get_occurrences(species_key, limit=1000)

# Check for size data
has_size = client.has_size_data(occurrence)
```

### Trait Database

```python
from apis.trait_ontology_db import get_trait_db

# Get database instance
trait_db = get_trait_db()

# Query by AphiaID
species = trait_db.get_species_by_aphia_id(146564)
traits = trait_db.get_traits_for_species(146564)

# Query by trait value
results = trait_db.query_species_by_trait(
    trait_name='biovolume',
    min_value=1.0,
    max_value=10.0
)

# Get statistics
stats = trait_db.get_statistics()
```

### SHARK Client

```python
from shark_client import SHARKClient

client = SHARKClient()

# Search SHARK database
results = client.search_species("Fucus vesiculosus")

# Get detailed data
data = client.get_species_data(species_name)
```

See individual API module documentation in `apis/` for detailed usage.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_gbif_client.py

# Run with coverage
pytest --cov=apis --cov=app_modules

# Run trait database tests
python scripts/test_trait_db.py
python scripts/test_trait_integration.py
```

### Test Coverage

- **Unit tests**: Individual API clients and utilities
- **Integration tests**: Multi-component workflows
- **Database tests**: Trait database functionality
- **UI tests**: Component rendering and interactions

## Configuration

### Environment Variables

Create a `.env` file for optional configuration:

```env
# Database paths
TRAIT_DB_PATH=data/trait_ontology.db

# API rate limiting
GBIF_RATE_LIMIT=100
SHARK_RATE_LIMIT=50

# Logging
LOG_LEVEL=INFO
```

### Application Settings

Modify `app_modules/constants.py` for application-wide settings:

```python
DEFAULT_OCCURRENCE_LIMIT = 1000
BULK_ANALYSIS_SAMPLE_SIZE = 100
MAX_SIZE_MEASUREMENTS_DISPLAY = 50
```

## Data Sources & Attribution

### Primary Data Sources

- **GBIF.org**: GBIF Occurrence Download https://doi.org/10.15468/dl.xxxxx
- **SHARK**: Swedish Oceanographic Data Centre, SMHI
- **OBIS**: Ocean Biodiversity Information System
- **WoRMS**: World Register of Marine Species (www.marinespecies.org)
- **Nordic Microalgae**: Nordic Microalgae and Aquatic Protozoa (nordicmicroalgae.org)
- **AlgaeBase**: AlgaeBase (www.algaebase.org)
- **IOC-UNESCO**: Intergovernmental Oceanographic Commission HAB Programme

### Trait Data Sources

- **bvol_nomp_version_2024.xlsx**: HELCOM/OSPAR phytoplankton biovolume reference list
- **species_enriched.xlsx**: Marine species biological traits from MARLIN (Marine Life Information Network)

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use type hints where applicable
- Run linters before committing:
  ```bash
  black .
  ruff check .
  mypy .
  ```

## Documentation

### Available Documentation

- **README.md** (this file): Main project documentation
- **REFACTORING_SUMMARY.md**: Architecture refactoring details
- **TRAIT_LOOKUP_README.md**: Trait lookup system documentation
- **TRAIT_DATABASE_TEST_RESULTS.md**: Database testing results
- **TRAIT_INTEGRATION_SUMMARY.md**: Trait integration guide
- **CHANGELOG.md**: Version history and changes

### API Documentation

Each API module includes detailed docstrings. Generate API docs:

```bash
# Install documentation tools
pip install sphinx sphinx-rtd-theme

# Generate docs
cd docs
make html
```

## Troubleshooting

### Common Issues

**Database not found:**
```bash
# Initialize trait database
python scripts/import_traits_to_db.py
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

**Port already in use:**
```bash
# Run on different port
shiny run app.py --port 8080
```

### Getting Help

- Check existing [Issues](https://github.com/yourusername/gbif-api-client/issues)
- Review [Documentation](./docs/)
- Contact maintainers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{marine_biodiversity_explorer_2025,
  title = {Marine & Biodiversity Data Explorer},
  author = {Your Team},
  year = {2025},
  version = {2.0.0},
  url = {https://github.com/yourusername/gbif-api-client}
}
```

## Acknowledgments

- GBIF.org for providing global biodiversity data
- Swedish Meteorological and Hydrological Institute (SMHI) for SHARK data
- WoRMS Editorial Board for taxonomic authority
- Nordic Microalgae project contributors
- All database providers and contributors

## Roadmap

### Version 2.1 (Planned)
- [ ] Advanced trait-based filtering in bulk analysis
- [ ] Export trait data to various formats
- [ ] Trait value distribution visualizations
- [ ] User-contributed trait values

### Version 3.0 (Future)
- [ ] Machine learning for trait prediction
- [ ] REST API for programmatic access
- [ ] Docker containerization
- [ ] Cloud deployment support
- [ ] Real-time data streaming

## Contact

- **Project Lead**: [Your Name]
- **Email**: your.email@example.com
- **GitHub**: https://github.com/yourusername/gbif-api-client
- **Issues**: https://github.com/yourusername/gbif-api-client/issues

---

**Built with ❤️ for marine biodiversity research**

*Last updated: December 26, 2025*
