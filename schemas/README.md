schemas/
=======

This folder contains schema templates and examples for trait data focused on freshwater/brackish benthic research.

Files
- `traits_freshwater.csv` — CSV schema (Darwin Core-compatible fields) with two example rows. Header columns:
  - `taxonID, scientificName, traitName, traitValue, traitUnit, traitURI, traitScope, feeding_mode_score, feeding_mode_term_uri, food_item_uri, relation_uri, habitat_envo_uri, substrate_envo_uri, measurementMethod, evidence, source_reference, timestamp`
  - Use `traitURI` to store an ontology term (ECO/PCO/TO). Use `food_item_uri` for FOODON URIs and `habitat_envo_uri`/`substrate_envo_uri` for ENVO terms.

- `traits_freshwater.ttl` — small Turtle/RDF examples demonstrating how you might serialize the same data as RDF (e.g., using `dwc:dynamicProperties` for structured values).

Notes and guidance
- Use BIOTIC fuzzy coding (0–3) in `feeding_mode_score` for functional diversity analyses.
- Keep `measurementMethod`, `evidence`, and `source_reference` populated for reproducibility.
- When publishing or integrating, map to the Darwin Core trait extension or use `dwc:dynamicProperties` for flexible representations.

If you want, I can:
- Add a script to convert CSV → RDF using this mapping.
- Add more comprehensive RDF predicates (using RO, ECO with precise predicates).
- Validate URIs against OLS and replace example CURIEs with canonical OBO URIs.

New files added for templates and BIOTIC mapping:
- `traits_freshwater_template.csv` — blank template with BIOTIC scoring columns.
- `traits_freshwater_vocab.csv` — dropdown vocabularies (labels + canonical URIs).
- `biotic_to_schema_mapping.csv` — BIOTIC → schema mapping (BIOTIC categories → ECO terms & score columns).
- `README_traits_template.md` — usage notes and guidance.

Tell me which of the follow-up actions you want next (or choose a new one): convert CSV→RDF, make an Excel template with dropdown validation, or open a PR with these changes.

Validation scripts
- `scripts/validate_uris.py` — quick OLS validator/canonicalizer. Usage:

```bash
python scripts/validate_uris.py --csv schemas/traits_freshwater.csv --ttl schemas/traits_freshwater.ttl
```

The script backs up originals (`.bak`) and replaces CSV and TTL values when a canonical match is found in the expected ontology for each column.