"""Run a quick live check against FreshwaterEcology API using a provided API key.

Usage:
  python scripts/run_fwe_live_check.py --api-key <KEY> [--limit N]

The script will not store the key; it only uses it for this run and prints brief summaries.
"""
import argparse
import json
from apis import FreshwaterEcologyAPI

parser = argparse.ArgumentParser()
parser.add_argument("--api-key", required=True)
parser.add_argument("--limit", type=int, default=5)
args = parser.parse_args()

api = FreshwaterEcologyAPI(api_key=args.api_key)
print("Checking status...")
status = api.get_status()
print("Status:", status)
print("Authenticating...")
token = api.authenticate()
print("Token obtained?", bool(token))
print("Running sample query (organismgroup=fi, genus=Salmo)...")
df = api.query(organismgroup="fi", genus="Salmo", limit=args.limit)
print("Rows returned:", len(df))
if not df.empty:
    print(json.dumps(df.head().to_dict(orient="records"), indent=2))
else:
    print("No rows returned")
