Traits template & BIOTIC mapping
================================

Files added:
- `traits_freshwater_template.csv`: blank CSV template with header + BIOTIC scoring columns.
- `traits_freshwater_vocab.csv`: controlled vocabularies for dropdowns (field, label, URI, note).
- `biotic_to_schema_mapping.csv`: mapping from BIOTIC categories to schema columns and ECO URIs.

Usage
-
- Use `traits_freshwater_template.csv` as a starting point for new trait records. The template includes:
  - Darwin Core-compatible fields from `traits_freshwater.csv` plus explicit BIOTIC columns:
    - `feeding_surface_deposit_score`, `feeding_subsurface_deposit_score`, `feeding_suspension_score`, `feeding_predator_score`, `feeding_scavenger_score`, `feeding_parasite_score` (each 0–3)
  - Use `feeding_mode_score` and `feeding_mode_term_uri` when a single dominant mode is to be recorded.

Dropdowns / Controlled values
- Look up canonical terms in `traits_freshwater_vocab.csv`. Each row lists a `field`, human `label`, the canonical `uri` (when available), and a short `note`.
- For example, to set substrate, use `substrate_envo_uri` with values such as `http://purl.obolibrary.org/obo/ENVO_00002000` (mud) or `ENVO_00002001` (sand).

BIOTIC mapping
- `biotic_to_schema_mapping.csv` maps BIOTIC feeding categories to the dedicated BIOTIC score columns and ECO URIs.
- BIOTIC is multi-modal: fill the specialized score columns with 0–3 values representing relative expression.
- When a single mode dominates, set `feeding_mode_score`=3 and `feeding_mode_term_uri` to the mapped ECO term.

Next steps
- I added `scripts/convert_biotic.py` — a script that expands BIOTIC-style records into Darwin Core trait rows and optionally produces RDF/Turtle output.
- I can add an Excel template with actual dropdown validation if that helps (data validation list).
- I can add a script to convert CSV → RDF using this mapping (already included in `convert_biotic.py`).
