# Documentation Index

Welcome to the Marine & Biodiversity Data Explorer documentation! This index provides an overview of all available documentation resources.

**Version 2.0.0** | Last updated: December 26, 2025

---

## Quick Start

New to the project? Start here:

1. **[README.md](README.md)** - Main project documentation
2. **[Installation Guide](#installation)** - Get up and running
3. **[Usage Examples](#usage-examples)** - Common workflows
4. **[API Documentation](#api-documentation)** - Code references

---

## Core Documentation

### Project Overview

| Document | Description | Status |
|----------|-------------|--------|
| **[README.md](README.md)** | Main project documentation with features, installation, and usage | ✅ Current |
| **[CHANGELOG.md](CHANGELOG.md)** | Version history and changes | ✅ Current |
| **[__version__.py](__version__.py)** | Version information and feature flags | ✅ Current |

### Architecture & Design

| Document | Description | Status |
|----------|-------------|--------|
| **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** | Detailed refactoring phases and architectural changes | ✅ Current |

### Trait Database Documentation

| Document | Description | Status |
|----------|-------------|--------|
| **[TRAIT_LOOKUP_README.md](TRAIT_LOOKUP_README.md)** | Comprehensive trait lookup system guide | ✅ Current |
| **[TRAIT_DATABASE_TEST_RESULTS.md](TRAIT_DATABASE_TEST_RESULTS.md)** | Database testing documentation and results | ✅ Current |
| **[TRAIT_INTEGRATION_SUMMARY.md](TRAIT_INTEGRATION_SUMMARY.md)** | Integration guide for trait functionality | ✅ Current |

---

## Installation

### Quick Installation

```bash
# Clone repository
git clone https://github.com/yourusername/gbif-api-client.git
cd gbif-api-client

# Install dependencies
pip install -r requirements.txt

# Run application
shiny run app.py
```

### Detailed Installation

See **[README.md - Installation](README.md#installation)** for:
- Prerequisites
- Development installation
- Optional dependencies
- Trait database initialization

---

## Usage Examples

### Basic Usage

Find detailed examples in:
- **[README.md - Usage Guide](README.md#usage-guide)**
- **[examples/trait_lookup_example.py](examples/trait_lookup_example.py)**

### Common Workflows

#### 1. Search for Species
```python
from gbif_client import GBIFClient

client = GBIFClient()
species = client.search_species("Fucus vesiculosus")
```

See: **[README.md - Searching for Species](README.md#searching-for-species)**

#### 2. Query Trait Database
```python
from apis.trait_ontology_db import get_trait_db

trait_db = get_trait_db()
results = trait_db.query_species_by_trait(
    trait_name='biovolume',
    min_value=1.0,
    max_value=10.0
)
```

See: **[TRAIT_LOOKUP_README.md - Usage](TRAIT_LOOKUP_README.md#usage)**

#### 3. Bulk Species Analysis

See: **[README.md - Bulk Species Analysis](README.md#bulk-species-analysis)**

---

## API Documentation

### Core API Clients

| Module | Description | Documentation |
|--------|-------------|---------------|
| `gbif_client.py` | GBIF API client | Inline docstrings + README |
| `shark_client.py` | SHARK database client | Inline docstrings |
| `apis/trait_ontology_db.py` | Trait database | [TRAIT_LOOKUP_README.md](TRAIT_LOOKUP_README.md) |

### API Modules (`apis/`)

| Module | Database | Status |
|--------|----------|--------|
| `algaebase_api.py` | AlgaeBase | ✅ Active |
| `dyntaxa_api.py` | Dyntaxa (SLU) | ✅ Active |
| `freshwater_ecology_api.py` | Freshwater Ecology | ✅ Active |
| `ioc_hab_api.py` | IOC-UNESCO HAB | ✅ Active |
| `nordic_microalgae_api.py` | Nordic Microalgae | ✅ Active |
| `obis_api.py` | OBIS | ✅ Active |
| `shark_api.py` | SHARK | ✅ Active |
| `worms_api.py` | WoRMS | ✅ Active |
| `trait_lookup.py` | Trait Lookup (Pandas) | ✅ Active |
| `trait_ontology_db.py` | Trait Database (SQLite) | ✅ Active |

### Utility Modules (`app_modules/`)

| Module | Purpose | Documentation |
|--------|---------|---------------|
| `constants.py` | Configuration constants | Inline docstrings |
| `utils.py` | General utilities | Inline docstrings |
| `trait_utils.py` | Trait data utilities | Inline docstrings |
| `ui/components.py` | UI components | Inline docstrings |

---

## Testing Documentation

### Test Suites

| Test Suite | Coverage | Documentation |
|------------|----------|---------------|
| Unit Tests (`tests/`) | API clients & utilities | Inline docstrings |
| Trait Database Tests | Database functionality | [TRAIT_DATABASE_TEST_RESULTS.md](TRAIT_DATABASE_TEST_RESULTS.md) |
| Integration Tests | Multi-component workflows | [TRAIT_INTEGRATION_SUMMARY.md](TRAIT_INTEGRATION_SUMMARY.md) |

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_gbif_client.py

# With coverage
pytest --cov=apis --cov=app_modules

# Trait database tests
python scripts/test_trait_db.py
python scripts/test_trait_integration.py
```

See: **[README.md - Testing](README.md#testing)**

---

## Configuration

### Environment Variables

Create a `.env` file:

```env
TRAIT_DB_PATH=data/trait_ontology.db
GBIF_RATE_LIMIT=100
SHARK_RATE_LIMIT=50
LOG_LEVEL=INFO
```

See: **[README.md - Configuration](README.md#configuration)**

### Application Settings

Modify `app_modules/constants.py` for:
- Default limits
- Size indicators
- Sampling protocol keywords
- Display settings

---

## Database Documentation

### Trait Ontology Database

**Schema**: 8 normalized tables
- `species` - Core species information
- `trait_categories` - Hierarchical categories
- `traits` - Trait definitions
- `trait_values` - Measurements and values
- `size_classes` - Phytoplankton size classes
- `geographic_distribution` - Species distribution
- `taxonomic_hierarchy` - Taxonomic classification
- `trait_relationships` - Ontological relationships

**Documentation**:
- **[TRAIT_LOOKUP_README.md](TRAIT_LOOKUP_README.md)** - Complete system guide
- **[TRAIT_DATABASE_TEST_RESULTS.md](TRAIT_DATABASE_TEST_RESULTS.md)** - Testing & validation
- **[TRAIT_INTEGRATION_SUMMARY.md](TRAIT_INTEGRATION_SUMMARY.md)** - Integration details

### Data Import

**Import Scripts**:
- `scripts/import_traits_to_db.py` - Excel to SQLite import
- `scripts/enrich_bvol_with_fwe.py` - Data enrichment

**Data Sources**:
- `bvol_nomp_version_2024.xlsx` - Phytoplankton traits (1,132 species)
- `species_enriched.xlsx` - Marine species traits (914 species)

---

## Troubleshooting

### Common Issues

| Issue | Solution | Documentation |
|-------|----------|---------------|
| Database not found | Run `python scripts/import_traits_to_db.py` | [README.md - Troubleshooting](README.md#troubleshooting) |
| Import errors | Run `pip install -r requirements.txt --upgrade` | [README.md](README.md) |
| Port in use | Run with `--port 8080` | [README.md](README.md) |
| Unicode errors | Windows console only, web app unaffected | [CHANGELOG.md - Known Issues](CHANGELOG.md#known-issues) |

---

## Development

### Contributing

See **[README.md - Contributing](README.md#contributing)** for:
- Development guidelines
- Code style (PEP 8)
- Testing requirements
- Pull request process

### Code Quality Tools

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

Configuration in `pyproject.toml`.

---

## Version History

| Version | Date | Major Changes | Documentation |
|---------|------|---------------|---------------|
| **2.0.0** | 2025-12-26 | Trait database integration | [CHANGELOG.md](CHANGELOG.md#200---2025-12-26) |
| **1.5.0** | 2024 | Multi-database integration, refactoring | [CHANGELOG.md](CHANGELOG.md#150---2024-12-xx) |
| **1.0.0** | 2024 | Initial release | [CHANGELOG.md](CHANGELOG.md#100---2024-xx-xx) |

---

## Data Sources & Attribution

### Primary Databases

| Database | Provider | Documentation |
|----------|----------|---------------|
| GBIF | Global Biodiversity Information Facility | [gbif.org](https://www.gbif.org) |
| SHARK | Swedish Oceanographic Data Centre, SMHI | [sharkdata.se](https://sharkdata.se) |
| WoRMS | World Register of Marine Species | [marinespecies.org](http://www.marinespecies.org) |
| OBIS | Ocean Biodiversity Information System | [obis.org](https://obis.org) |
| Nordic Microalgae | Nordic Microalgae Project | [nordicmicroalgae.org](http://nordicmicroalgae.org) |
| AlgaeBase | AlgaeBase | [algaebase.org](http://www.algaebase.org) |

See: **[README.md - Data Sources & Attribution](README.md#data-sources--attribution)**

---

## Support & Contact

### Getting Help

1. **Documentation**: Check this index and linked docs
2. **Issues**: [GitHub Issues](https://github.com/yourusername/gbif-api-client/issues)
3. **Examples**: See `examples/` directory
4. **Tests**: Review test files for usage patterns

### Contact

- **GitHub**: https://github.com/yourusername/gbif-api-client
- **Issues**: https://github.com/yourusername/gbif-api-client/issues

---

## License

MIT License - See [README.md - License](README.md#license)

---

## Citation

```bibtex
@software{marine_biodiversity_explorer_2025,
  title = {Marine & Biodiversity Data Explorer},
  author = {Marine Biodiversity Team},
  year = {2025},
  version = {2.0.0},
  url = {https://github.com/yourusername/gbif-api-client}
}
```

---

## Documentation Maintenance

### Last Updated
- **Date**: December 26, 2025
- **Version**: 2.0.0
- **Maintainer**: Marine Biodiversity Team

### Update Schedule
- Documentation reviewed with each release
- CHANGELOG updated per release
- API docs updated with code changes
- Examples tested before release

---

**Questions about documentation?** [Open an issue](https://github.com/yourusername/gbif-api-client/issues/new) with the `documentation` label.
