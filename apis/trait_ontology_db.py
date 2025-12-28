"""
SQLite Trait Ontology Database

A normalized, relational database for storing and querying marine species traits.
Supports complex queries, trait relationships, and ontological structure.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)


class TraitOntologyDB:
    """
    SQLite database for marine species trait ontology.

    Schema:
    - species: Core species information with AphiaID
    - trait_categories: Categories of traits (morphological, ecological, etc.)
    - traits: Individual trait definitions
    - trait_values: Trait values for each species
    - size_classes: Phytoplankton size class information
    - geographic_distribution: Geographic areas where species occur
    - taxonomic_hierarchy: Full taxonomic classification
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the trait ontology database.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "trait_ontology.db")

        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
        return self.conn

    def _init_database(self) -> None:
        """Initialize database schema with all tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create species table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS species (
                species_id INTEGER PRIMARY KEY AUTOINCREMENT,
                aphia_id INTEGER UNIQUE NOT NULL,
                scientific_name TEXT,
                genus TEXT,
                common_name TEXT,
                author TEXT,
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on aphia_id for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_species_aphia_id
            ON species(aphia_id)
        """)

        # Create trait categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trait_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                parent_category_id INTEGER,
                description TEXT,
                FOREIGN KEY (parent_category_id) REFERENCES trait_categories(category_id)
            )
        """)

        # Create traits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traits (
                trait_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait_name TEXT UNIQUE NOT NULL,
                category_id INTEGER,
                data_type TEXT CHECK(data_type IN ('numeric', 'categorical', 'text', 'boolean')),
                unit TEXT,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES trait_categories(category_id)
            )
        """)

        # Create trait values table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trait_values (
                value_id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER NOT NULL,
                trait_id INTEGER NOT NULL,
                value_numeric REAL,
                value_text TEXT,
                value_categorical TEXT,
                value_boolean INTEGER,
                size_class_id INTEGER,
                confidence REAL,
                data_source TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (species_id) REFERENCES species(species_id),
                FOREIGN KEY (trait_id) REFERENCES traits(trait_id),
                FOREIGN KEY (size_class_id) REFERENCES size_classes(size_class_id)
            )
        """)

        # Create indexes for trait values
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trait_values_species
            ON trait_values(species_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trait_values_trait
            ON trait_values(trait_id)
        """)

        # Create size classes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS size_classes (
                size_class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER NOT NULL,
                size_class_no INTEGER,
                size_range TEXT,
                size_range_min REAL,
                size_range_max REAL,
                description TEXT,
                FOREIGN KEY (species_id) REFERENCES species(species_id)
            )
        """)

        # Create geographic distribution table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geographic_distribution (
                distribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER NOT NULL,
                area_type TEXT,
                area_value TEXT,
                FOREIGN KEY (species_id) REFERENCES species(species_id)
            )
        """)

        # Create taxonomic hierarchy table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS taxonomic_hierarchy (
                taxonomy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER UNIQUE NOT NULL,
                kingdom TEXT,
                phylum TEXT,
                division TEXT,
                class TEXT,
                order_name TEXT,
                family TEXT,
                genus TEXT,
                species TEXT,
                rank TEXT,
                FOREIGN KEY (species_id) REFERENCES species(species_id)
            )
        """)

        # Create trait relationships table (for ontological structure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trait_relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait_id_1 INTEGER NOT NULL,
                trait_id_2 INTEGER NOT NULL,
                relationship_type TEXT,
                description TEXT,
                FOREIGN KEY (trait_id_1) REFERENCES traits(trait_id),
                FOREIGN KEY (trait_id_2) REFERENCES traits(trait_id)
            )
        """)

        conn.commit()
        logger.info(f"Database schema initialized at {self.db_path}")

    def initialize_trait_categories(self) -> None:
        """Initialize standard trait categories."""
        conn = self._get_connection()
        cursor = conn.cursor()

        categories = [
            # Top-level categories
            ('morphological', None, 'Physical form and structure'),
            ('ecological', None, 'Ecological characteristics and behaviors'),
            ('trophic', None, 'Feeding and nutritional characteristics'),
            ('behavioral', None, 'Behavioral traits and patterns'),
            ('geographic', None, 'Geographic distribution and habitat'),
            ('taxonomic', None, 'Taxonomic classification'),
            ('physiological', None, 'Physiological characteristics'),

            # Morphological subcategories
            ('size', 1, 'Size measurements'),
            ('shape', 1, 'Geometric shape and form'),
            ('biomass', 1, 'Biomass and carbon content'),

            # Ecological subcategories
            ('abundance', 2, 'Population abundance'),
            ('mobility', 2, 'Movement and mobility patterns'),
            ('habitat', 2, 'Habitat preferences and position'),

            # Trophic subcategories
            ('feeding_mode', 3, 'Feeding method and strategy'),
            ('diet', 3, 'Diet and food sources'),
        ]

        for name, parent_id, description in categories:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO trait_categories (category_name, parent_category_id, description)
                    VALUES (?, ?, ?)
                """, (name, parent_id, description))
            except sqlite3.IntegrityError:
                pass  # Category already exists

        conn.commit()
        logger.info("Trait categories initialized")

    def initialize_traits(self) -> None:
        """Initialize standard trait definitions."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get category IDs
        cursor.execute("SELECT category_id, category_name FROM trait_categories")
        categories = {row[1]: row[0] for row in cursor.fetchall()}

        traits = [
            # Size traits (morphological/size)
            ('length_l1', categories.get('size'), 'numeric', 'μm', 'Primary length measurement'),
            ('length_l2', categories.get('size'), 'numeric', 'μm', 'Secondary length measurement'),
            ('width', categories.get('size'), 'numeric', 'μm', 'Width measurement'),
            ('height', categories.get('size'), 'numeric', 'μm', 'Height measurement'),
            ('diameter_d1', categories.get('size'), 'numeric', 'μm', 'Primary diameter'),
            ('diameter_d2', categories.get('size'), 'numeric', 'μm', 'Secondary diameter'),
            ('filament_length', categories.get('size'), 'numeric', 'μm', 'Filament length per cell'),

            # Shape traits
            ('geometric_shape', categories.get('shape'), 'categorical', None, 'Geometric shape'),
            ('growth_form', categories.get('shape'), 'categorical', None, 'Growth form'),
            ('body_flexibility', categories.get('morphological'), 'categorical', None, 'Body flexibility'),

            # Biomass traits
            ('biovolume', categories.get('biomass'), 'numeric', 'μm³', 'Calculated biovolume'),
            ('carbon_content', categories.get('biomass'), 'numeric', 'pg', 'Carbon content'),
            ('cells_per_unit', categories.get('biomass'), 'numeric', 'count', 'Number of cells per counting unit'),

            # Trophic traits
            ('trophic_type', categories.get('trophic'), 'categorical', None, 'Trophic type (AU, HE, etc.)'),
            ('feeding_method', categories.get('feeding_mode'), 'categorical', None, 'Characteristic feeding method'),
            ('diet_food_source', categories.get('diet'), 'text', None, 'Diet and food sources'),
            ('feeds_on', categories.get('diet'), 'text', None, 'What species typically feeds on'),

            # Ecological traits
            ('typical_abundance', categories.get('abundance'), 'categorical', None, 'Typical abundance'),
            ('growth_rate', categories.get('ecological'), 'categorical', None, 'Growth rate'),
            ('mobility', categories.get('mobility'), 'categorical', None, 'Mobility level'),
            ('sociability', categories.get('behavioral'), 'categorical', None, 'Social behavior'),
            ('environmental_position', categories.get('habitat'), 'categorical', None, 'Environmental position'),
            ('dependency', categories.get('ecological'), 'categorical', None, 'Dependency on other species'),
            ('supports', categories.get('ecological'), 'text', None, 'What species supports'),

            # Size at maturity
            ('male_size_range', categories.get('size'), 'text', None, 'Male size range'),
            ('female_size_range', categories.get('size'), 'text', None, 'Female size range'),
            ('male_size_at_maturity', categories.get('size'), 'text', None, 'Male size at maturity'),
            ('female_size_at_maturity', categories.get('size'), 'text', None, 'Female size at maturity'),

            # Other
            ('is_harmful', categories.get('ecological'), 'categorical', None, 'Is species harmful'),
        ]

        for trait_name, category_id, data_type, unit, description in traits:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO traits (trait_name, category_id, data_type, unit, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (trait_name, category_id, data_type, unit, description))
            except sqlite3.IntegrityError:
                pass  # Trait already exists

        conn.commit()
        logger.info("Trait definitions initialized")

    def add_species(
        self,
        aphia_id: int,
        scientific_name: Optional[str] = None,
        genus: Optional[str] = None,
        common_name: Optional[str] = None,
        author: Optional[str] = None,
        data_source: Optional[str] = None
    ) -> int:
        """
        Add a species to the database.

        Args:
            aphia_id: WoRMS AphiaID
            scientific_name: Scientific name
            genus: Genus name
            common_name: Common name
            author: Author citation
            data_source: Source of data

        Returns:
            species_id: Database ID of the species
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO species (aphia_id, scientific_name, genus, common_name, author, data_source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (aphia_id, scientific_name, genus, common_name, author, data_source))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Species already exists, get its ID
            cursor.execute("SELECT species_id FROM species WHERE aphia_id = ?", (aphia_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def add_trait_value(
        self,
        species_id: int,
        trait_name: str,
        value: Any,
        size_class_id: Optional[int] = None,
        confidence: Optional[float] = None,
        data_source: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Add a trait value for a species.

        Args:
            species_id: Database species ID
            trait_name: Name of the trait
            value: Value of the trait (type determined automatically)
            size_class_id: Optional size class ID for phytoplankton
            confidence: Confidence level (0-1)
            data_source: Source of the data
            notes: Additional notes

        Returns:
            value_id: Database ID of the trait value
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get trait ID
        cursor.execute("SELECT trait_id, data_type FROM traits WHERE trait_name = ?", (trait_name,))
        trait_row = cursor.fetchone()

        if not trait_row:
            logger.warning(f"Trait '{trait_name}' not found in database")
            return None

        trait_id, data_type = trait_row

        # Determine which column to use based on data type
        value_numeric = None
        value_text = None
        value_categorical = None
        value_boolean = None

        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None  # Don't insert NULL values

        if data_type == 'numeric':
            value_numeric = float(value)
        elif data_type == 'boolean':
            value_boolean = int(bool(value))
        elif data_type == 'categorical':
            value_categorical = str(value)
        else:  # text
            value_text = str(value)

        cursor.execute("""
            INSERT INTO trait_values
            (species_id, trait_id, value_numeric, value_text, value_categorical, value_boolean,
             size_class_id, confidence, data_source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (species_id, trait_id, value_numeric, value_text, value_categorical, value_boolean,
              size_class_id, confidence, data_source, notes))

        conn.commit()
        return cursor.lastrowid

    def add_size_class(
        self,
        species_id: int,
        size_class_no: int,
        size_range: Optional[str] = None,
        size_range_min: Optional[float] = None,
        size_range_max: Optional[float] = None,
        description: Optional[str] = None
    ) -> int:
        """Add a size class for a species."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO size_classes
            (species_id, size_class_no, size_range, size_range_min, size_range_max, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (species_id, size_class_no, size_range, size_range_min, size_range_max, description))

        conn.commit()
        return cursor.lastrowid

    def add_taxonomy(
        self,
        species_id: int,
        kingdom: Optional[str] = None,
        phylum: Optional[str] = None,
        division: Optional[str] = None,
        class_name: Optional[str] = None,
        order_name: Optional[str] = None,
        family: Optional[str] = None,
        genus: Optional[str] = None,
        species: Optional[str] = None,
        rank: Optional[str] = None
    ) -> int:
        """Add taxonomic hierarchy for a species."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO taxonomic_hierarchy
                (species_id, kingdom, phylum, division, class, order_name, family, genus, species, rank)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (species_id, kingdom, phylum, division, class_name, order_name, family, genus, species, rank))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Taxonomy already exists, update it
            cursor.execute("""
                UPDATE taxonomic_hierarchy
                SET kingdom=?, phylum=?, division=?, class=?, order_name=?, family=?, genus=?, species=?, rank=?
                WHERE species_id=?
            """, (kingdom, phylum, division, class_name, order_name, family, genus, species, rank, species_id))
            conn.commit()
            return species_id

    def add_geographic_distribution(
        self,
        species_id: int,
        area_type: str,
        area_value: str
    ) -> int:
        """Add geographic distribution for a species."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO geographic_distribution (species_id, area_type, area_value)
            VALUES (?, ?, ?)
        """, (species_id, area_type, area_value))

        conn.commit()
        return cursor.lastrowid

    def get_species_by_aphia_id(self, aphia_id: int) -> Optional[Dict[str, Any]]:
        """Get species information by AphiaID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM species WHERE aphia_id = ?", (aphia_id,))
        row = cursor.fetchone()

        if row:
            # Convert sqlite3.Row to dictionary
            return {
                'species_id': row['species_id'],
                'aphia_id': row['aphia_id'],
                'scientific_name': row['scientific_name'],
                'genus': row['genus'],
                'common_name': row['common_name'],
                'author': row['author'],
                'data_source': row['data_source'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None

    def get_traits_for_species(
        self,
        aphia_id: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all trait values for a species.

        Args:
            aphia_id: WoRMS AphiaID
            category: Optional filter by trait category

        Returns:
            List of trait value dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if category:
            query = """
                SELECT
                    t.trait_name,
                    t.data_type,
                    t.unit,
                    tc.category_name,
                    tv.value_numeric,
                    tv.value_text,
                    tv.value_categorical,
                    tv.value_boolean,
                    tv.confidence,
                    tv.data_source,
                    sc.size_class_no,
                    sc.size_range
                FROM trait_values tv
                JOIN species s ON tv.species_id = s.species_id
                JOIN traits t ON tv.trait_id = t.trait_id
                JOIN trait_categories tc ON t.category_id = tc.category_id
                LEFT JOIN size_classes sc ON tv.size_class_id = sc.size_class_id
                WHERE s.aphia_id = ? AND tc.category_name = ?
                ORDER BY t.trait_name, sc.size_class_no
            """
            cursor.execute(query, (aphia_id, category))
        else:
            query = """
                SELECT
                    t.trait_name,
                    t.data_type,
                    t.unit,
                    tc.category_name,
                    tv.value_numeric,
                    tv.value_text,
                    tv.value_categorical,
                    tv.value_boolean,
                    tv.confidence,
                    tv.data_source,
                    sc.size_class_no,
                    sc.size_range
                FROM trait_values tv
                JOIN species s ON tv.species_id = s.species_id
                JOIN traits t ON tv.trait_id = t.trait_id
                LEFT JOIN trait_categories tc ON t.category_id = tc.category_id
                LEFT JOIN size_classes sc ON tv.size_class_id = sc.size_class_id
                WHERE s.aphia_id = ?
                ORDER BY t.trait_name, sc.size_class_no
            """
            cursor.execute(query, (aphia_id,))

        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'trait_name': row['trait_name'],
                'data_type': row['data_type'],
                'unit': row['unit'],
                'category_name': row['category_name'],
                'value_numeric': row['value_numeric'],
                'value_text': row['value_text'],
                'value_categorical': row['value_categorical'],
                'value_boolean': row['value_boolean'],
                'confidence': row['confidence'],
                'data_source': row['data_source'],
                'size_class_no': row['size_class_no'],
                'size_range': row['size_range']
            })
        return results

    def get_traits_for_species_batch(
        self,
        aphia_ids: List[int],
        category: Optional[str] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get trait values for multiple species in a single query (batch operation).

        This is significantly more efficient than calling get_traits_for_species
        repeatedly for multiple species, as it uses a single database query.

        Args:
            aphia_ids: List of WoRMS AphiaIDs
            category: Optional filter by trait category

        Returns:
            Dictionary mapping aphia_id to list of trait value dictionaries
            Species with no traits will have an empty list

        Example:
            traits = db.get_traits_for_species_batch([148984, 234567, 345678])
            # Returns: {148984: [{...}, {...}], 234567: [], 345678: [{...}]}
        """
        if not aphia_ids:
            return {}

        conn = self._get_connection()
        cursor = conn.cursor()

        # Create placeholders for SQL IN clause
        placeholders = ','.join('?' * len(aphia_ids))

        if category:
            query = f"""
                SELECT
                    s.aphia_id,
                    t.trait_name,
                    t.data_type,
                    t.unit,
                    tc.category_name,
                    tv.value_numeric,
                    tv.value_text,
                    tv.value_categorical,
                    tv.value_boolean,
                    tv.confidence,
                    tv.data_source,
                    sc.size_class_no,
                    sc.size_range
                FROM trait_values tv
                JOIN species s ON tv.species_id = s.species_id
                JOIN traits t ON tv.trait_id = t.trait_id
                JOIN trait_categories tc ON t.category_id = tc.category_id
                LEFT JOIN size_classes sc ON tv.size_class_id = sc.size_class_id
                WHERE s.aphia_id IN ({placeholders}) AND tc.category_name = ?
                ORDER BY s.aphia_id, t.trait_name, sc.size_class_no
            """
            cursor.execute(query, (*aphia_ids, category))
        else:
            query = f"""
                SELECT
                    s.aphia_id,
                    t.trait_name,
                    t.data_type,
                    t.unit,
                    tc.category_name,
                    tv.value_numeric,
                    tv.value_text,
                    tv.value_categorical,
                    tv.value_boolean,
                    tv.confidence,
                    tv.data_source,
                    sc.size_class_no,
                    sc.size_range
                FROM trait_values tv
                JOIN species s ON tv.species_id = s.species_id
                JOIN traits t ON tv.trait_id = t.trait_id
                LEFT JOIN trait_categories tc ON t.category_id = tc.category_id
                LEFT JOIN size_classes sc ON tv.size_class_id = sc.size_class_id
                WHERE s.aphia_id IN ({placeholders})
                ORDER BY s.aphia_id, t.trait_name, sc.size_class_no
            """
            cursor.execute(query, aphia_ids)

        rows = cursor.fetchall()

        # Group results by aphia_id
        results: Dict[int, List[Dict[str, Any]]] = {aphia_id: [] for aphia_id in aphia_ids}

        for row in rows:
            aphia_id = row['aphia_id']
            trait_data = {
                'trait_name': row['trait_name'],
                'data_type': row['data_type'],
                'unit': row['unit'],
                'category_name': row['category_name'],
                'value_numeric': row['value_numeric'],
                'value_text': row['value_text'],
                'value_categorical': row['value_categorical'],
                'value_boolean': row['value_boolean'],
                'confidence': row['confidence'],
                'data_source': row['data_source'],
                'size_class_no': row['size_class_no'],
                'size_range': row['size_range']
            }
            results[aphia_id].append(trait_data)

        return results

    def query_species_by_trait(
        self,
        trait_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        categorical_value: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find species matching trait criteria.

        Args:
            trait_name: Name of the trait
            min_value: Minimum value for numeric traits
            max_value: Maximum value for numeric traits
            categorical_value: Value for categorical traits

        Returns:
            List of matching species with trait values
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT
                s.aphia_id,
                s.scientific_name,
                s.genus,
                s.common_name,
                t.trait_name,
                tv.value_numeric,
                tv.value_categorical,
                tv.value_text
            FROM species s
            JOIN trait_values tv ON s.species_id = tv.species_id
            JOIN traits t ON tv.trait_id = t.trait_id
            WHERE t.trait_name = ?
        """

        params = [trait_name]

        if min_value is not None:
            base_query += " AND tv.value_numeric >= ?"
            params.append(min_value)

        if max_value is not None:
            base_query += " AND tv.value_numeric <= ?"
            params.append(max_value)

        if categorical_value is not None:
            base_query += " AND tv.value_categorical = ?"
            params.append(categorical_value)

        cursor.execute(base_query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            result = {
                'aphia_id': row['aphia_id'],
                'scientific_name': row['scientific_name'],
                'genus': row['genus'],
                'common_name': row['common_name'],
                'trait_name': row['trait_name'],
                'value_numeric': row['value_numeric'],
                'value_categorical': row['value_categorical'],
                'value_text': row['value_text']
            }
            # Add trait_value as a convenience field with the first non-null value
            result['trait_value'] = (
                row['value_numeric'] if row['value_numeric'] is not None
                else row['value_categorical'] if row['value_categorical'] is not None
                else row['value_text']
            )
            results.append(result)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Species count
        cursor.execute("SELECT COUNT(*) FROM species")
        stats['total_species'] = cursor.fetchone()[0]

        # Trait count
        cursor.execute("SELECT COUNT(*) FROM traits")
        stats['total_traits'] = cursor.fetchone()[0]

        # Trait values count
        cursor.execute("SELECT COUNT(*) FROM trait_values")
        stats['total_trait_values'] = cursor.fetchone()[0]

        # Category count
        cursor.execute("SELECT COUNT(*) FROM trait_categories")
        stats['total_categories'] = cursor.fetchone()[0]

        # Species by data source
        cursor.execute("""
            SELECT data_source, COUNT(*) as count
            FROM species
            GROUP BY data_source
        """)
        stats['species_by_source'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Traits by category
        cursor.execute("""
            SELECT tc.category_name, COUNT(t.trait_id) as count
            FROM trait_categories tc
            LEFT JOIN traits t ON tc.category_id = t.category_id
            GROUP BY tc.category_name
        """)
        stats['traits_by_category'] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton instance
_db_instance: Optional[TraitOntologyDB] = None


def get_trait_db(db_path: Optional[str] = None) -> TraitOntologyDB:
    """Get or create the global TraitOntologyDB instance."""
    global _db_instance
    if _db_instance is None or db_path is not None:
        _db_instance = TraitOntologyDB(db_path)
    return _db_instance
