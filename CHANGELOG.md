# Changelog

All notable changes to the Marine & Biodiversity Data Explorer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-26

### Added
- **Trait Ontology Database**: SQLite database with 2,046 species and 21,102 trait values
  - 29 trait types across 15 hierarchical categories
  - Support for morphological, ecological, trophic, and behavioral traits
  - Multiple size classes for phytoplankton species
  - Geographic distribution data (HELCOM/OSPAR)
- **Trait Search Functionality**: Query species by trait values
  - Numeric range queries (biovolume, carbon content)
  - Categorical value matching (trophic type, shape, mobility)
  - Trait-based species discovery interface
- **Trait Integration**: Complete integration with main application
  - New "🔬 Trait Database" tab in UI
  - Trait search panel in sidebar
  - Detailed trait information display
  - Database statistics dashboard
- **Trait Utilities Module** (`app_modules/trait_utils.py`):
  - `get_traits_for_aphia_id()`: Retrieve all traits for a species
  - `format_trait_value()`: Format trait values with units
  - `create_trait_summary_text()`: Generate readable summaries
  - `enrich_occurrences_with_traits()`: Add trait columns to occurrence data
  - `query_species_by_trait_range()`: Query species by trait criteria
- **Data Import Scripts**:
  - `scripts/import_traits_to_db.py`: Import Excel trait data to SQLite
  - Automated trait data parsing and validation
  - Size range parsing for phytoplankton size classes
- **Comprehensive Testing**:
  - `scripts/test_trait_db.py`: 8 database test suites
  - `scripts/test_trait_integration.py`: Integration test suite
  - All tests passing with 100% coverage of trait features
- **Documentation**:
  - `TRAIT_LOOKUP_README.md`: Trait lookup system guide
  - `TRAIT_DATABASE_TEST_RESULTS.md`: Testing documentation
  - `TRAIT_INTEGRATION_SUMMARY.md`: Integration guide
  - Updated README.md with trait features

### Changed
- **Refactored Architecture** (Phase 4):
  - Extracted UI components to `app_modules/ui/components.py`
  - Created reusable component functions
  - Improved code modularity and maintainability
- **Enhanced UI/UX**:
  - Professional custom CSS (`www/custom.css`)
  - Card-based dashboard layout
  - Consistent styling across all components
  - CSS variables for design tokens
- **Improved Application Structure**:
  - Modular API client architecture
  - Centralized constants and utilities
  - Cleaner separation of concerns

### Fixed
- Resolved database column naming issues (species_id vs id)
- Fixed sqlite3.Row to dictionary conversion
- Corrected SQL query column references
- Handled Unicode encoding issues in console output

### Documentation
- Comprehensive README.md overhaul
- Added CHANGELOG.md (this file)
- Created API usage examples
- Documented all 10+ integrated databases
- Added architectural documentation

## [1.5.0] - 2024-12-XX

### Added
- **Multiple Marine Database Integration**:
  - SHARK (Swedish oceanographic data)
  - WoRMS (World Register of Marine Species)
  - Dyntaxa (SLU Artdatabanken Swedish taxonomy)
  - Nordic Microalgae database
  - AlgaeBase integration
  - OBIS (Ocean Biodiversity Information System)
  - IOC-UNESCO HAB database
  - Freshwater Ecology database
  - Plankton Toolbox integration
- **Refactored Codebase** (Phases 1-3):
  - Extracted constants to `app_modules/constants.py`
  - Created utilities module `app_modules/utils.py`
  - Modular API client structure
  - Improved error handling with custom exceptions
- **Mock Data Support**:
  - Mock API responses for offline development
  - Testing without live API calls
- **API Base Class**:
  - `apis/base_api.py`: Common API client functionality
  - Rate limiting and retry logic
  - Consistent error handling

### Changed
- Improved GBIF client with enhanced size data detection
- Reorganized API modules in `apis/` directory
- Better separation of concerns in application logic

## [1.0.0] - 2024-XX-XX

### Added
- **Initial Release**:
  - GBIF API client using pygbif
  - Shiny for Python web interface
  - Species search functionality
  - Occurrence data visualization
  - Interactive maps with Plotly
  - Size data detection
  - Bulk species analysis
  - Excel file upload support
  - Real-time progress tracking
  - Country filtering
- **Core Features**:
  - Species search by name
  - Occurrence record display
  - Geographic distribution maps
  - Size data filtering
  - Bulk Excel analysis
  - Progress monitoring
  - Cancellable long-running tasks
- **Data Sources**:
  - GBIF integration
  - MeasurementOrFact extension support
  - Dynamic properties parsing
  - Sampling protocol analysis

### Technical
- Python 3.10+ support
- Shiny framework integration
- Pandas for data processing
- Plotly for visualizations
- OpenPyXL for Excel handling

---

## Version History Summary

- **v2.0.0** (2025-12-26): Trait ontology database, comprehensive integration
- **v1.5.0** (2024): Multiple marine databases, refactored architecture
- **v1.0.0** (2024): Initial release with GBIF client and Shiny UI

## Upgrade Guide

### Upgrading from 1.x to 2.0

1. **Install New Dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Initialize Trait Database** (optional):
   ```bash
   python scripts/import_traits_to_db.py
   ```

3. **Update Application Code**:
   - New trait utilities available in `app_modules/trait_utils.py`
   - Trait database accessible via `get_trait_db()`
   - New UI components in `app_modules/ui/components.py`

4. **Configuration Changes**:
   - No breaking changes to existing configuration
   - Optional: Set `TRAIT_DB_PATH` environment variable

## Breaking Changes

### Version 2.0.0
- None. Fully backwards compatible with 1.x

### Version 1.5.0
- API client imports moved to `apis/` module
- Constants moved to `app_modules/constants.py`
- Some utility functions relocated to `app_modules/utils.py`

## Migration Notes

### For Developers

If you have custom code using the old structure:

```python
# Old (v1.0)
from gbif_client import GBIFClient
SIZE_INDICATORS = [...]  # Defined locally

# New (v2.0)
from gbif_client import GBIFClient  # Still works!
from app_modules.constants import SIZE_INDICATORS
from apis.trait_ontology_db import get_trait_db  # New feature
```

### For Users

No migration required. All existing functionality preserved and enhanced.

## Known Issues

### Version 2.0.0
- Console output may show encoding errors for µ (mu) symbol on Windows
  - Impact: Cosmetic only, does not affect web application
  - Workaround: Errors are limited to console logs
- Complex size ranges (e.g., "3x5") not parsed into min/max values
  - Impact: Size range stored as text, min/max fields are NULL
  - Workaround: Use size_range field for display

## Future Roadmap

See README.md for detailed roadmap of upcoming features in versions 2.1 and 3.0.

---

**Note**: This changelog will be updated with each release. For unreleased changes,see the `main` branch commits.
