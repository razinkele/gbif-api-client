"""
Tests for app_modules/trait_utils.py
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
from app_modules.trait_utils import (
    get_traits_for_aphia_id,
    format_trait_value,
    create_trait_summary_text,
    enrich_occurrences_with_traits,
    query_species_by_trait_range,
    get_trait_statistics
)


@pytest.fixture
def mock_trait_db():
    """Create a mock trait database."""
    db = Mock()
    return db


@pytest.fixture
def sample_species_info():
    """Sample species information."""
    return {
        'aphia_id': 148984,
        'scientific_name': 'Fucus vesiculosus',
        'data_source': 'bvol_nomp'
    }


@pytest.fixture
def sample_traits():
    """Sample trait data."""
    return [
        {
            'trait_name': 'biovolume',
            'category_name': 'morphology',
            'value_numeric': 125.5,
            'value_categorical': None,
            'value_text': None,
            'value_boolean': None,
            'unit': 'μm³',
            'data_type': 'numeric',
            'size_class_no': None,
            'size_range': None
        },
        {
            'trait_name': 'trophic_type',
            'category_name': 'ecology',
            'value_numeric': None,
            'value_categorical': 'phototroph',
            'value_text': None,
            'value_boolean': None,
            'unit': None,
            'data_type': 'categorical',
            'size_class_no': None,
            'size_range': None
        },
        {
            'trait_name': 'is_harmful',
            'category_name': 'ecology',
            'value_numeric': None,
            'value_categorical': None,
            'value_text': None,
            'value_boolean': False,
            'unit': None,
            'data_type': 'boolean',
            'size_class_no': None,
            'size_range': None
        }
    ]


class TestGetTraitsForAphiaId:
    """Tests for get_traits_for_aphia_id function."""

    def test_successful_retrieval(self, mock_trait_db, sample_species_info, sample_traits):
        """Test successful trait retrieval."""
        mock_trait_db.get_species_by_aphia_id.return_value = sample_species_info
        mock_trait_db.get_traits_for_species.return_value = sample_traits

        result = get_traits_for_aphia_id(mock_trait_db, 148984)

        assert result is not None
        assert result['species_info'] == sample_species_info
        assert result['total_traits'] == 3
        assert 'morphology' in result['traits_by_category']
        assert 'ecology' in result['traits_by_category']

    def test_species_not_found(self, mock_trait_db):
        """Test when species is not found."""
        mock_trait_db.get_species_by_aphia_id.return_value = None

        result = get_traits_for_aphia_id(mock_trait_db, 999999)

        assert result is None
        mock_trait_db.get_species_by_aphia_id.assert_called_once_with(999999)

    def test_organizes_traits_by_category(self, mock_trait_db, sample_species_info, sample_traits):
        """Test that traits are correctly organized by category."""
        mock_trait_db.get_species_by_aphia_id.return_value = sample_species_info
        mock_trait_db.get_traits_for_species.return_value = sample_traits

        result = get_traits_for_aphia_id(mock_trait_db, 148984)

        # Check morphology category
        assert len(result['traits_by_category']['morphology']) == 1
        assert result['traits_by_category']['morphology'][0]['name'] == 'biovolume'
        assert result['traits_by_category']['morphology'][0]['value'] == 125.5

        # Check ecology category
        assert len(result['traits_by_category']['ecology']) == 2

    def test_handles_exception(self, mock_trait_db):
        """Test exception handling."""
        # Clear cache before test to ensure exception is hit
        from app_modules.cache import trait_cache
        trait_cache.clear()

        mock_trait_db.get_species_by_aphia_id.side_effect = Exception("Database error")

        result = get_traits_for_aphia_id(mock_trait_db, 148984)

        assert result is None


class TestFormatTraitValue:
    """Tests for format_trait_value function."""

    def test_format_none_value(self):
        """Test formatting None value."""
        result = format_trait_value(None)
        assert result == "N/A"

    def test_format_numeric_float(self):
        """Test formatting numeric float value."""
        result = format_trait_value(125.456, data_type='numeric')
        assert result == "125.46"

    def test_format_numeric_with_unit(self):
        """Test formatting numeric value with unit."""
        result = format_trait_value(125.456, unit='μm³', data_type='numeric')
        assert result == "125.46 μm³"

    def test_format_numeric_integer(self):
        """Test formatting numeric integer value."""
        result = format_trait_value(100, data_type='numeric')
        assert result == "100"

    def test_format_boolean_true(self):
        """Test formatting boolean True value."""
        result = format_trait_value(True, data_type='boolean')
        assert result == "Yes"

    def test_format_boolean_false(self):
        """Test formatting boolean False value."""
        result = format_trait_value(False, data_type='boolean')
        assert result == "No"

    def test_format_text(self):
        """Test formatting text value."""
        result = format_trait_value("phototroph", data_type='text')
        assert result == "phototroph"

    def test_format_categorical(self):
        """Test formatting categorical value."""
        result = format_trait_value("heterotroph", data_type='categorical')
        assert result == "heterotroph"


class TestCreateTraitSummaryText:
    """Tests for create_trait_summary_text function."""

    def test_empty_trait_info(self):
        """Test with None trait info."""
        result = create_trait_summary_text(None)
        assert result == "No trait data available"

    def test_basic_summary(self):
        """Test basic trait summary creation."""
        trait_info = {
            'species_info': {
                'scientific_name': 'Fucus vesiculosus',
                'data_source': 'bvol_nomp'
            },
            'total_traits': 2,
            'traits_by_category': {
                'morphology': [
                    {
                        'name': 'biovolume',
                        'value': 125.5,
                        'unit': 'μm³',
                        'data_type': 'numeric',
                        'size_class': None,
                        'size_range': None
                    }
                ],
                'ecology': [
                    {
                        'name': 'trophic_type',
                        'value': 'phototroph',
                        'unit': None,
                        'data_type': 'categorical',
                        'size_class': None,
                        'size_range': None
                    }
                ]
            }
        }

        result = create_trait_summary_text(trait_info)

        assert 'Species: Fucus vesiculosus' in result
        assert 'Data source: bvol_nomp' in result
        assert 'Total traits: 2' in result
        assert 'MORPHOLOGY:' in result
        assert 'biovolume: 125.50 μm³' in result
        assert 'ECOLOGY:' in result
        assert 'trophic_type: phototroph' in result

    def test_multiple_size_classes(self):
        """Test summary with multiple size classes."""
        trait_info = {
            'species_info': {
                'scientific_name': 'Test species',
                'data_source': 'test'
            },
            'total_traits': 2,
            'traits_by_category': {
                'morphology': [
                    {
                        'name': 'biovolume',
                        'value': 100.0,
                        'unit': 'μm³',
                        'data_type': 'numeric',
                        'size_class': 1,
                        'size_range': '10-20 μm'
                    },
                    {
                        'name': 'biovolume',
                        'value': 200.0,
                        'unit': 'μm³',
                        'data_type': 'numeric',
                        'size_class': 2,
                        'size_range': '20-30 μm'
                    }
                ]
            }
        }

        result = create_trait_summary_text(trait_info)

        assert 'biovolume:' in result
        assert '100.00 μm³ (size class 1: 10-20 μm)' in result
        assert '200.00 μm³ (size class 2: 20-30 μm)' in result


class TestEnrichOccurrencesWithTraits:
    """Tests for enrich_occurrences_with_traits function."""

    def test_empty_dataframe(self, mock_trait_db):
        """Test with empty dataframe."""
        df = pd.DataFrame()
        result = enrich_occurrences_with_traits(df, mock_trait_db)
        assert result.empty

    def test_no_aphia_id_column(self, mock_trait_db):
        """Test when no AphiaID column exists."""
        df = pd.DataFrame({
            'species': ['Species A', 'Species B'],
            'count': [10, 20]
        })

        result = enrich_occurrences_with_traits(df, mock_trait_db)

        # Should return original dataframe unchanged
        assert len(result.columns) == 2
        assert 'has_trait_data' not in result.columns

    def test_enrichment_with_traits(self, mock_trait_db):
        """Test enrichment with trait data using batch queries."""
        df = pd.DataFrame({
            'species': ['Fucus vesiculosus'],
            'aphia_id': [148984]
        })

        # Mock the batch query method
        mock_trait_db.get_traits_for_species_batch.return_value = {
            148984: [
                {
                    'trait_name': 'biovolume',
                    'value_numeric': 125.5,
                    'value_categorical': None
                },
                {
                    'trait_name': 'trophic_type',
                    'value_numeric': None,
                    'value_categorical': 'phototroph'
                },
                {
                    'trait_name': 'carbon_content',
                    'value_numeric': 50.2,
                    'value_categorical': None
                }
            ]
        }

        result = enrich_occurrences_with_traits(df, mock_trait_db)

        assert 'has_trait_data' in result.columns
        assert 'trait_count' in result.columns
        assert 'trophic_type' in result.columns
        assert 'biovolume_um3' in result.columns
        assert 'carbon_pg' in result.columns

        assert result.iloc[0]['has_trait_data'] == True
        assert result.iloc[0]['trait_count'] == 3
        assert result.iloc[0]['trophic_type'] == 'phototroph'
        assert result.iloc[0]['biovolume_um3'] == 125.5
        assert result.iloc[0]['carbon_pg'] == 50.2

    def test_enrichment_with_missing_aphia_id(self, mock_trait_db):
        """Test enrichment when AphiaID is missing."""
        df = pd.DataFrame({
            'species': ['Unknown species'],
            'aphia_id': [None]
        })

        result = enrich_occurrences_with_traits(df, mock_trait_db)

        assert result.iloc[0]['has_trait_data'] == False
        assert result.iloc[0]['trait_count'] == 0
        assert pd.isna(result.iloc[0]['trophic_type'])

    def test_enrichment_with_no_traits_found(self, mock_trait_db):
        """Test enrichment when species has no traits."""
        df = pd.DataFrame({
            'species': ['Species with no traits'],
            'aphia_id': [999999]
        })

        # Mock batch query returning empty list for this species
        mock_trait_db.get_traits_for_species_batch.return_value = {999999: []}

        result = enrich_occurrences_with_traits(df, mock_trait_db)

        assert result.iloc[0]['has_trait_data'] == False
        assert result.iloc[0]['trait_count'] == 0

    def test_enrichment_handles_exception(self, mock_trait_db):
        """Test that exceptions are handled gracefully."""
        df = pd.DataFrame({
            'species': ['Error species'],
            'aphia_id': [148984]
        })

        # Mock batch query raising exception
        mock_trait_db.get_traits_for_species_batch.side_effect = Exception("Database error")

        result = enrich_occurrences_with_traits(df, mock_trait_db)

        # When batch query fails, all species get empty traits
        assert result.iloc[0]['has_trait_data'] == False
        assert result.iloc[0]['trait_count'] == 0


class TestQuerySpeciesByTraitRange:
    """Tests for query_species_by_trait_range function."""

    def test_successful_query(self, mock_trait_db):
        """Test successful trait range query."""
        mock_results = [
            {'scientific_name': 'Species A', 'biovolume': 100},
            {'scientific_name': 'Species B', 'biovolume': 150}
        ]
        mock_trait_db.query_species_by_trait.return_value = mock_results

        result = query_species_by_trait_range(
            mock_trait_db,
            trait_name='biovolume',
            min_value=50.0,
            max_value=200.0
        )

        assert len(result) == 2
        assert result[0]['scientific_name'] == 'Species A'
        mock_trait_db.query_species_by_trait.assert_called_once_with(
            trait_name='biovolume',
            min_value=50.0,
            max_value=200.0
        )

    def test_limit_results(self, mock_trait_db):
        """Test that results are limited correctly."""
        mock_results = [{'id': i} for i in range(150)]
        mock_trait_db.query_species_by_trait.return_value = mock_results

        result = query_species_by_trait_range(
            mock_trait_db,
            trait_name='biovolume',
            limit=50
        )

        assert len(result) == 50

    def test_query_with_exception(self, mock_trait_db):
        """Test exception handling."""
        mock_trait_db.query_species_by_trait.side_effect = Exception("Query error")

        result = query_species_by_trait_range(
            mock_trait_db,
            trait_name='biovolume'
        )

        assert result == []


class TestGetTraitStatistics:
    """Tests for get_trait_statistics function."""

    def test_successful_statistics(self, mock_trait_db):
        """Test successful statistics retrieval."""
        mock_stats = {
            'total_species': 2046,
            'total_traits': 21102,
            'total_categories': 5
        }
        mock_trait_db.get_statistics.return_value = mock_stats

        result = get_trait_statistics(mock_trait_db)

        assert result == mock_stats
        mock_trait_db.get_statistics.assert_called_once()

    def test_statistics_with_exception(self, mock_trait_db):
        """Test exception handling."""
        mock_trait_db.get_statistics.side_effect = Exception("Stats error")

        result = get_trait_statistics(mock_trait_db)

        assert result == {}
