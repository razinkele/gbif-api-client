"""Quick OLS URI validator and canonicalizer

Usage:
    python scripts/validate_uris.py --csv schemas/traits_freshwater.csv --ttl schemas/traits_freshwater.ttl

- Checks URI-like values in selected CSV columns against the EBI OLS API
- Replaces matched values with the canonical OLS iri
- Writes a backed-up copy of original file and replaces original in-place
- Produces a small report of replacements and not-found entries
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
from urllib.parse import quote_plus

import requests

OLS_BASE = "https://www.ebi.ac.uk/ols/api"

# Columns in the CSV we will validate (comma-separated URIs may appear)
URI_COLUMNS = [
    "traitURI",
    "feeding_mode_term_uri",
    "food_item_uri",
    "relation_uri",
    "habitat_envo_uri",
    "substrate_envo_uri",
]

CURIE_PREFIXES = {
    "ENVO": "http://purl.obolibrary.org/obo/ENVO_",
    "ECO": "http://purl.obolibrary.org/obo/ECO_",
    "FOODON": "http://purl.obolibrary.org/obo/FOODON_",
    "RO": "http://purl.obolibrary.org/obo/RO_",
}


def query_ols_by_iri(iri):
    """Query OLS terms endpoint by IRI. Return tuple (canonical_iri, ontology_name) or (None, None)."""
    url = f"{OLS_BASE}/terms?iri={quote_plus(iri)}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        j = r.json()
        terms = j.get("_embedded", {}).get("terms", [])
        if terms:
            t = terms[0]
            return t.get("iri"), t.get("ontology_name") or t.get("ontology")
    except Exception as e:
        print(f"OLS query error for {iri}: {e}")
    return None, None


def search_ols_by_label(label, ontology_filter=None):
    """Fallback: search for a label (q) and optionally filter by ontology; return (iri, ontology_name) or (None, None)."""
    q = quote_plus(label)
    url = f"{OLS_BASE}/search?q={q}&rows=20"
    if ontology_filter:
        url += f"&ontology={ontology_filter}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        j = r.json()
        docs = j.get("response", {}).get("docs", [])
        if docs:
            d = docs[0]
            return d.get("iri"), d.get("ontology") or d.get("ontology_name")
    except Exception as e:
        print(f"OLS search error for {label}: {e}")
    return None, None


def canonicalize_value(value, expected_ontologies=None):
    """Given a string value (uri, semicolon-list, or CURIE), try to canonicalize each URI inside and return new string and mapping.

    expected_ontologies: set/list of ontology short names (e.g., {'envo','eco','foodon','ro'}) to restrict matches.
    """
    if not value or not value.strip():
        return value, {}

    expected_ontologies = {e.lower() for e in (expected_ontologies or [])}

    parts = [p.strip() for p in value.split(";") if p.strip()]
    new_parts = []
    mapping = {}
    for p in parts:
        original = p
        canon = None
        canon_ont = None
        # If looks like a URI, query OLS directly
        if p.startswith("http://") or p.startswith("https://"):
            canon, canon_ont = query_ols_by_iri(p)
            if not canon:
                # try to search by last path segment or short form
                short = p.split("/")[-1]
                short = short.replace("_", ":") if "_" in short else short
                canon, canon_ont = search_ols_by_label(short)
        else:
            # Try CURIE like ECO:0000213 or ECO:DepositFeeding
            if ":" in p:
                pre, rest = p.split(":", 1)
                pre = pre.upper()
                if pre in CURIE_PREFIXES and re.match(r"^\d+$|^0+\d+|^[A-Za-z0-9_]+$", rest):
                    # if numeric id (or mixed), expand
                    if re.match(r"^\d+$", rest) or re.match(r"^0+\d+", rest) or rest.isupper():
                        # numeric form possibly like 0000213 or 213
                        # form to canonical OBO: ECO_0000213
                        # ensure underscore
                        rest_norm = rest.zfill(7) if rest.isdigit() else rest
                        candidate = CURIE_PREFIXES[pre] + rest_norm
                        canon, canon_ont = query_ols_by_iri(candidate)
                if not canon:
                    # Try to search by label
                    canon, canon_ont = search_ols_by_label(rest, ontology_filter=pre.lower())
        # Accept replacement only if ontology matches expected_ontologies when provided
        if canon and (not expected_ontologies or (canon_ont and canon_ont.lower() in expected_ontologies)):
            new_parts.append(canon)
            mapping[original] = canon
        else:
            new_parts.append(original)
            mapping[original] = None
    return ";".join(new_parts), mapping


def process_csv(path):
    bak = path + ".bak"
    shutil.copy(path, bak)
    print(f"Backup written to {bak}")
    replaced = {}
    checked = 0

    # Column -> allowed ontology prefixes mapping
    COLUMN_ONTOLOGY = {
        "traitURI": {"eco", "pco", "to"},
        "feeding_mode_term_uri": {"eco", "pco"},
        "food_item_uri": {"foodon"},
        "relation_uri": {"ro"},
        "habitat_envo_uri": {"envo"},
        "substrate_envo_uri": {"envo"},
    }

    with open(path, newline="", encoding="utf-8") as fh:
        reader = list(csv.DictReader(fh))
        fieldnames = reader[0].keys() if reader else []

    for row in reader:
        for col in URI_COLUMNS:
            if col in row:
                val = row[col]
                if val and val.strip():
                    checked += 1
                    expected = COLUMN_ONTOLOGY.get(col, None)
                    newval, mapping = canonicalize_value(val, expected_ontologies=expected)
                    # Only commit replacements where at least one part matched allowed ontology
                    if any(v for v in mapping.values() if v is not None):
                        row[col] = newval
                        for k, v in mapping.items():
                            if v and k != v:
                                replaced[k] = v

    # write back
    out_path = path
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in reader:
            writer.writerow(row)

    print(f"Checked {checked} URI-containing cells; replacements made: {len(replaced)}")
    for k, v in replaced.items():
        print(f"  {k} -> {v}")
    return replaced


def process_ttl(path, replacements):
    """Replace exact occurrences of replaced URIs in the TTL file (in-place after backup)"""
    bak = path + ".bak"
    shutil.copy(path, bak)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    count = 0
    for old, new in replacements.items():
        if new and old in text:
            text = text.replace(old, new)
            count += 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"Updated {count} TTL occurrences in {path} (backup: {bak})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--ttl", required=False)
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print("CSV not found", args.csv)
        sys.exit(1)

    replacements = process_csv(args.csv)

    if args.ttl and os.path.exists(args.ttl):
        process_ttl(args.ttl, replacements)


if __name__ == "__main__":
    main()
