"""Enrich bvol spreadsheet using FreshwaterEcology API

Usage:
  python scripts/enrich_bvol_with_fwe.py --input ../bvol_nomp_version_2024.xlsx --sheet "Biovolume file" --out schemas/bvol_with_fwe.xlsx --max-rows 200

Notes:
- The script will look up taxa via FWE (organismgroup='al') using taxonname, genus, and q searches.
- On match, it will try to extract biovolume/carbon/trophic-related parameters and add them as new columns.
- Safe: writes incremental backups and a resumable output file.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from apis import FreshwaterEcologyAPI


def extract_traits_from_response(data) -> Dict[str, Any]:
    """Given parsed response (DataFrame or list), extract biovolume/carbon/trophic info."""
    result = {
        "fwe_found": False,
        "fwe_biovolume": None,
        "fwe_carbon_pg_per_unit": None,
        "fwe_trophic": None,
        "fwe_raw_sample": None,
    }
    rows = []
    if isinstance(data, list):
        rows = data
    else:
        try:
            if not data.empty:
                rows = data.to_dict(orient="records")
        except Exception:
            rows = []

    if not rows:
        return result

    result["fwe_found"] = True
    result["fwe_raw_sample"] = rows[:3]

    for r in rows:
        # try to fetch trait-like fields
        # keys may be 'trait', 'parameter', 'ecoparam', 'parameterName', 'value'
        keys = {k.lower(): v for k, v in (r.items() if isinstance(r, dict) else [])}
        # join possible name fields
        name = (
            str(keys.get("trait") or keys.get("parameter") or keys.get("ecoparam") or keys.get("param") or "")).lower()
        value = keys.get("value") or keys.get("val") or keys.get("measurement") or None
        if value is None:
            # try typical numeric keys
            for candidate in ("value","val","V","measurement"):
                if candidate in keys:
                    value = keys[candidate]
                    break
        if not name:
            continue
        if "carbon" in name or "carb" in name:
            try:
                result["fwe_carbon_pg_per_unit"] = float(value)
            except Exception:
                result["fwe_carbon_pg_per_unit"] = value
        if "biovol" in name or "volume" in name:
            try:
                result["fwe_biovolume"] = float(value)
            except Exception:
                result["fwe_biovolume"] = value
        if "troph" in name or "trophy" in name or "feeding" in name:
            result["fwe_trophic"] = value

    return result


def enrich(input_path: Path, sheet: str, out_path: Path, max_rows: int = 200, api_key: str | None = None):
    df = pd.read_excel(input_path, sheet_name=sheet)
    # add columns if missing
    for col in ["fwe_found", "fwe_biovolume", "fwe_carbon_pg_per_unit", "fwe_trophic", "fwe_raw_sample"]:
        if col not in df.columns:
            df[col] = None

    api = FreshwaterEcologyAPI(api_key=api_key) if api_key else FreshwaterEcologyAPI()

    processed = 0
    for idx, row in df.iterrows():
        if processed >= max_rows:
            break
        # skip already enriched rows
        if pd.notna(row.get("fwe_found")) and row.get("fwe_found"):
            processed += 1
            continue

        genus = str(row.get("Genus", "")).strip()
        species = str(row.get("Species", "")).strip()
        taxonname = f"{genus} {species}".strip() if genus and species else None

        success_data = None
        for attempt_method in ("taxonname", "genus", "q"):
            try:
                if attempt_method == "taxonname" and taxonname:
                    res = api.query(organismgroup="al", taxonname=taxonname, limit=10)
                elif attempt_method == "genus" and genus:
                    res = api.query(organismgroup="al", genus=genus, limit=10)
                elif attempt_method == "q" and taxonname:
                    res = api.query(organismgroup="al", q=taxonname, limit=10)
                else:
                    continue

                extracted = extract_traits_from_response(res)
                if extracted["fwe_found"]:
                    success_data = extracted
                    break
            except Exception as e:
                # log and continue
                print(f"API error for row {idx} ({taxonname}) with method {attempt_method}: {e}")
            time.sleep(1.0)  # rate limit

        if success_data:
            df.at[idx, "fwe_found"] = True
            df.at[idx, "fwe_biovolume"] = success_data.get("fwe_biovolume")
            df.at[idx, "fwe_carbon_pg_per_unit"] = success_data.get("fwe_carbon_pg_per_unit")
            df.at[idx, "fwe_trophic"] = success_data.get("fwe_trophic")
            df.at[idx, "fwe_raw_sample"] = json.dumps(success_data.get("fwe_raw_sample"))
        else:
            df.at[idx, "fwe_found"] = False

        processed += 1
        if processed % 20 == 0:
            # write intermediate output
            temp_out = out_path.with_suffix(".partial.xlsx")
            df.to_excel(temp_out, index=False)
            print(f"Wrote interim results to {temp_out} (processed {processed})")

    # final write
    df.to_excel(out_path, index=False)
    print(f"Enrichment complete. Wrote {out_path}. Processed {processed} rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--api-key", required=False)
    args = parser.parse_args()

    enrich(Path(args.input), args.sheet, Path(args.out), max_rows=args.max_rows, api_key=args.api_key)
