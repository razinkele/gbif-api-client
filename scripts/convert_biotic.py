"""Convert BIOTIC multi-score rows into long Darwin Core trait rows and optional RDF (Turtle).

Usage:
    python scripts/convert_biotic.py --input <input_csv> --mapping <biotic_to_schema_mapping.csv> --out-csv <out_long_csv> [--out-ttl <out_ttl>]

Features:
- Expands BIOTIC score columns (0-3) into separate Darwin Core-style trait rows.
- If available, produces a Turtle file using `rdflib` and stores per-taxon JSON in `dwc:dynamicProperties` summarizing BIOTIC scores and mapped ECO URIs.
- Keeps provenance fields (measurementMethod, evidence, source_reference, timestamp) in output rows.

The script is conservative and depends on the `biotic_to_schema_mapping.csv` to discover which input columns correspond to BIOTIC scores.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from collections import defaultdict
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

try:
    from rdflib import Graph, Literal, Namespace, URIRef, BNode, RDF, RDFS
    RDF_AVAILABLE = True
except Exception:
    RDF_AVAILABLE = False

DWC = "http://rs.tdwg.org/dwc/terms/"
EX = "http://example.org/"

LONG_HEADER = [
    "taxonID",
    "scientificName",
    "traitName",
    "traitValue",
    "traitUnit",
    "traitURI",
    "traitScope",
    "measurementMethod",
    "evidence",
    "source_reference",
    "timestamp",
]


def load_biotic_mapping(mapping_csv: str) -> List[Dict]:
    df = pd.read_csv(mapping_csv, comment="#")
    mappings = []
    for _, row in df.iterrows():
        # required columns: biotic_category, schema_field, mapped_term_uri
        mappings.append(
            {
                "biotic_category": str(row.get("biotic_category")),
                "schema_field": str(row.get("schema_field")),
                "mapped_term_uri": row.get("mapped_term_uri") if not pd.isna(row.get("mapped_term_uri")) else None,
                "default_score": int(row.get("default_score")) if not pd.isna(row.get("default_score")) else None,
            }
        )
    return mappings


def load_vocab(vocab_csv: str):
    """Load vocab CSV into mapping: field -> {label -> uri} """
    if not vocab_csv:
        return {}
    try:
        df = pd.read_csv(vocab_csv, dtype=str, keep_default_na=False)
    except Exception:
        return {}
    vocab = {}
    for _, row in df.iterrows():
        field = row.get("field")
        label = row.get("label")
        uri = row.get("uri") if not pd.isna(row.get("uri")) else None
        if not field or not label:
            continue
        vocab.setdefault(field, {})[label] = uri
    return vocab


def expand_biotic_rows(
    input_csv: str,
    mapping_csv: str,
    out_csv: str,
    out_ttl: str | None = None,
    vocab_csv: str | None = None,
    publisher: str | None = None,
    dataset_date: str | None = None,
) -> Dict:
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    mappings = load_biotic_mapping(mapping_csv)
    vocab = load_vocab(vocab_csv) if vocab_csv else {}

    out_rows = []
    per_taxon_traits = defaultdict(list)
    per_taxon_names = {}  # map taxon id/name to scientificName for TTL labels

    for _, row in df.iterrows():
        taxonID = row.get("taxonID", "")
        scientificName = row.get("scientificName", "")
        measurementMethod = row.get("measurementMethod", "")
        evidence = row.get("evidence", "")
        source_reference = row.get("source_reference", "")
        timestamp = row.get("timestamp", "")
        # remember a display name for TTL output
        per_taxon_names[taxonID or scientificName] = scientificName

        # Also support a generic dominant feeding mode column
        dominant_score = None
        dominant_term_uri = row.get("feeding_mode_term_uri") if row.get("feeding_mode_term_uri") else None
        if row.get("feeding_mode_score"):
            try:
                dominant_score = int(row.get("feeding_mode_score"))
            except Exception:
                dominant_score = None

        # For each BIOTIC mapping entry, extract the score column and produce trait rows if score > 0
        for m in mappings:
            col = m["schema_field"]
            if col not in df.columns:
                continue
            val = row.get(col, "").strip()
            if val == "":
                continue
            try:
                score = int(val)
            except Exception:
                # skip non-numeric
                continue
            if score <= 0:
                continue

            trait_row = {
                "taxonID": taxonID,
                "scientificName": scientificName,
                "traitName": "feeding_mode",
                "traitValue": score,
                "traitUnit": "",
                "traitURI": m.get("mapped_term_uri") or "",
                "traitScope": "organism_level",
                "measurementMethod": measurementMethod,
                "evidence": evidence,
                "source_reference": source_reference,
                "timestamp": timestamp,
            }
            out_rows.append(trait_row)

            # add to per-taxon traits list (rich info for RDF)
            per_taxon_traits[taxonID or scientificName].append({
                "biotic_category": m["biotic_category"],
                "score": score,
                "term": m.get("mapped_term_uri"),
                "traitName": "feeding_mode",
                "traitURI": m.get("mapped_term_uri"),
                "traitValue": score,
                "measurementMethod": measurementMethod,
                "evidence": evidence,
                "source_reference": source_reference,
                "timestamp": timestamp,
                "food_item_uri": row.get("food_item_uri", "") if "food_item_uri" in row else "",
                "relation_uri": row.get("relation_uri", "") if "relation_uri" in row else "",
            })

        # If a dominant mode is present, also create a dominant trait row
        if dominant_score and dominant_score > 0 and dominant_term_uri:
            trait_row = {
                "taxonID": taxonID,
                "scientificName": scientificName,
                "traitName": "feeding_mode_dominant",
                "traitValue": dominant_score,
                "traitUnit": "",
                "traitURI": dominant_term_uri,
                "traitScope": "organism_level",
                "measurementMethod": measurementMethod,
                "evidence": evidence,
                "source_reference": source_reference,
                "timestamp": timestamp,
            }
            out_rows.append(trait_row)

            per_taxon_traits[taxonID or scientificName].append({
                "biotic_category": "dominant",
                "score": dominant_score,
                "term": dominant_term_uri,
                "traitName": "feeding_mode_dominant",
                "traitURI": dominant_term_uri,
                "traitValue": dominant_score,
                "measurementMethod": measurementMethod,
                "evidence": evidence,
                "source_reference": source_reference,
                "timestamp": timestamp,
                "food_item_uri": row.get("food_item_uri", "") if "food_item_uri" in row else "",
                "relation_uri": row.get("relation_uri", "") if "relation_uri" in row else "",
            })

    # write out CSV
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LONG_HEADER)
        writer.writeheader()
        for r in out_rows:
            writer.writerow({k: r.get(k, "") for k in LONG_HEADER})

    # Optionally produce Turtle using rdflib (rich triples)
    if out_ttl:
        if not RDF_AVAILABLE:
            logger.warning("rdflib not installed; skipping TTL generation")
        else:
            g = Graph()
            DWCN = Namespace(DWC)
            EXN = Namespace(EX)
            RON = Namespace("http://purl.obolibrary.org/obo/RO_")
            ECON = Namespace("http://purl.obolibrary.org/obo/ECO_")
            FOODONN = Namespace("http://purl.obolibrary.org/obo/FOODON_")
            PROV = Namespace("http://www.w3.org/ns/prov#")
            DCT = Namespace("http://purl.org/dc/terms/")
            RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
            g.bind("dwc", DWCN)
            g.bind("ex", EXN)
            g.bind("ro", RON)
            g.bind("eco", ECON)
            g.bind("foodon", FOODONN)
            g.bind("prov", PROV)
            g.bind("dcterms", DCT)
            g.bind("rdfs", RDFS)

            for taxon, traits in per_taxon_traits.items():
                subj = URIRef(f"urn:taxon:{taxon}")
                # add scientific name if available
                sciname = per_taxon_names.get(taxon, "")
                if sciname:
                    g.add((subj, URIRef(DWC + "scientificName"), Literal(sciname)))
                else:
                    g.add((subj, URIRef(DWC + "scientificName"), Literal("")))

                # richer, fully normalized trait resources
                for idx, t in enumerate(traits, start=1):
                    trait_uri = URIRef(f"{EX}trait/{taxon}/{idx}")
                    g.add((subj, EXN.hasTrait, trait_uri))
                    # label and type
                    if t.get("traitName"):
                        g.add((trait_uri, RDFS.label, Literal(t.get("traitName"))))
                    if t.get("traitURI"):
                        g.add((trait_uri, RDF.type, URIRef(t.get("traitURI"))))
                    # score
                    if t.get("score") is not None:
                        g.add((trait_uri, EXN.score, Literal(int(t.get("score")))))
                    # provenance: use PROV and DCTERMS for source
                    if t.get("measurementMethod"):
                        activity = URIRef(f"{EX}activity/{taxon}/{idx}")
                        g.add((trait_uri, PROV.wasGeneratedBy, activity))
                        g.add((activity, RDFS.label, Literal(t.get("measurementMethod"))))
                        # if vocab provides a URI for the method, link activity to it using prov:used
                        method_label = t.get("measurementMethod")
                        method_uri = None
                        if vocab and "measurementMethod" in vocab:
                            method_uri = vocab.get("measurementMethod", {}).get(method_label)
                        if method_uri:
                            g.add((activity, PROV.used, URIRef(method_uri)))
                    if t.get("evidence"):
                        g.add((trait_uri, DCT.description, Literal(t.get("evidence"))))
                    if t.get("source_reference"):
                        g.add((trait_uri, DCT.source, Literal(t.get("source_reference"))))
                    # attach publisher/date metadata at trait level if provided
                    if publisher:
                        g.add((trait_uri, DCT.publisher, Literal(publisher)))
                    if dataset_date:
                        g.add((trait_uri, DCT.date, Literal(dataset_date)))
                    # optionally link to food items (trait-level and taxon-level relations)
                    food = t.get("food_item_uri")
                    rel = t.get("relation_uri")
                    if food:
                        if rel:
                            g.add((trait_uri, URIRef(rel), URIRef(food)))
                            g.add((subj, URIRef(rel), URIRef(food)))
                        else:
                            g.add((trait_uri, RON["0002470"], URIRef(food)))
                            g.add((subj, RON["0002470"], URIRef(food)))
            g.serialize(destination=out_ttl, format="turtle")

    return {"rows_written": len(out_rows), "taxa": len(per_taxon_traits)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-ttl", required=False)
    parser.add_argument("--vocab", required=False, dest="vocab_csv")
    parser.add_argument("--publisher", required=False)
    parser.add_argument("--date", required=False, dest="dataset_date")
    args = parser.parse_args()

    res = expand_biotic_rows(
        args.input,
        args.mapping,
        args.out_csv,
        args.out_ttl,
        vocab_csv=args.vocab_csv,
        publisher=args.publisher,
        dataset_date=args.dataset_date,
    )
    print(f"Wrote {res['rows_written']} trait rows for {res['taxa']} taxa to {args.out_csv}")
    if args.out_ttl:
        print(f"TTL written to {args.out_ttl} (if rdflib installed)")


if __name__ == "__main__":
    main()
