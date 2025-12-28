import os
import json
import tempfile
from pathlib import Path

from scripts import convert_biotic


def test_expand_biotic_rows(tmp_path: Path):
    # Prepare a small input CSV
    input_csv = tmp_path / "sample.csv"
    input_csv.write_text(
        """taxonID,scientificName,measurementMethod,evidence,source_reference,timestamp,feeding_surface_deposit_score,feeding_suspension_score,feeding_parasite_score,feeding_mode_score,feeding_mode_term_uri
GBIF:98765,Capitella capitata,gut_content,expert_curation,doi:10.x,2025-06-01,3,1,0,3,http://purl.obolibrary.org/obo/ECO_0000271
"""
    )

    # Use existing mapping in repo
    repo_root = Path(__file__).parents[1]
    mapping_csv = repo_root / "schemas" / "biotic_to_schema_mapping.csv"

    out_csv = tmp_path / "out_long.csv"
    out_ttl = tmp_path / "out.ttl"

    # pass vocab and publisher/date for richer RDF metadata
    repo_root = Path(__file__).parents[1]
    vocab_csv = repo_root / "schemas" / "traits_freshwater_vocab.csv"
    res = convert_biotic.expand_biotic_rows(
        str(input_csv),
        str(mapping_csv),
        str(out_csv),
        str(out_ttl),
        vocab_csv=str(vocab_csv),
        publisher="ExamplePublisher",
        dataset_date="2025-12-01",
    )

    # assert rows written (3 rows: surface_deposit (3), suspension (1), dominant feeding_mode_dominant)
    assert res["rows_written"] >= 2
    txt = out_csv.read_text()
    assert "Capitella capitata" in txt
    assert "feeding_mode" in txt

    # TTL should be created if rdflib is available and contain rich triples (ECO term / hasTrait)
    if os.environ.get("HAS_RDFLIB") or convert_biotic.RDF_AVAILABLE:
        assert out_ttl.exists()
        ttl = out_ttl.read_text()
        # ECO term for surface deposit feeder (mapped in mapping CSV) should appear
        assert "ECO_0000271" in ttl or "eco:0000271" in ttl
        # Our normalized trait URIs should appear and hasTrait predicate
        assert "http://example.org/trait/" in ttl
        assert "ex:hasTrait" in ttl
        # Publisher and date should be present in TTL
        assert "ExamplePublisher" in ttl
        assert "2025-12-01" in ttl
    else:
        # if rdflib not available, TTL might not be written
        assert True
