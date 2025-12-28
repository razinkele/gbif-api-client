import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import re
import time
import threading
import os
import sys

INPUT_EXCEL = "species.xlsx"
OUTPUT_EXCEL = "species_enriched.xlsx"
URL_COLUMN = "url"

MAX_WORKERS = 6
REQUEST_TIMEOUT = 20
DELAY_BETWEEN_TASKS = 0.2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FWE-Biology-Table-Scraper/1.2)"
}

print_lock = threading.Lock()
last_debug_lines = 0


def clear_last_lines(n):
    for _ in range(n):
        sys.stdout.write("\033[F\033[K")


def normalize_column(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name)
    return f"biology_{name}"


def extract_species_name(soup: BeautifulSoup) -> str:
    if soup.find("h1"):
        return soup.find("h1").get_text(strip=True)
    if soup.title:
        return soup.title.get_text(strip=True)
    return "Unknown species"


def find_biology_header(soup: BeautifulSoup):
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        if h.get_text(strip=True).lower() == "biology":
            return h
    return None


def extract_biology_table(biology_header):
    for sib in biology_header.find_next_siblings():
        if sib.name in ["h1", "h2", "h3", "h4"]:
            break
        if sib.name == "table":
            return sib
    return None


def parse_biology_table(table):
    data = {}
    parameters = []

    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        param = cells[0].get_text(" ", strip=True)
        value = cells[1].get_text(" ", strip=True)

        if not param or param.lower() == "parameter":
            continue

        data[normalize_column(param)] = value
        parameters.append(param)

    return data, parameters


def update_debug_display(species, parameters):
    global last_debug_lines

    with print_lock:
        clear_last_lines(last_debug_lines)

        lines = []
        lines.append("🔍 CURRENT SPECIES")
        lines.append(f"   {species}")
        lines.append("")
        lines.append(f"📋 Biology parameters found ({len(parameters)}):")

        if parameters:
            for p in parameters:
                lines.append(f"   • {p}")
        else:
            lines.append("   (none)")

        for line in lines:
            print(line)

        last_debug_lines = len(lines)


def scrape_species(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        species = extract_species_name(soup)

        biology_header = find_biology_header(soup)
        if not biology_header:
            update_debug_display(species, [])
            return {}

        table = extract_biology_table(biology_header)
        if not table:
            update_debug_display(species, [])
            return {}

        data, parameters = parse_biology_table(table)
        update_debug_display(species, parameters)

        return data

    except Exception:
        update_debug_display("ERROR", [])
        return {}


def main():
    df = pd.read_excel(INPUT_EXCEL)

    if URL_COLUMN not in df.columns:
        raise ValueError(f"Column '{URL_COLUMN}' not found")

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrape_species, url): url
            for url in df[URL_COLUMN]
        }

        with tqdm(total=len(futures), desc="Scraping species", leave=True) as pbar:
            for future in as_completed(futures):
                results.append(future.result())
                pbar.update(1)
                time.sleep(DELAY_BETWEEN_TASKS)

    biology_df = pd.DataFrame(results)
    df_out = pd.concat([df.reset_index(drop=True), biology_df], axis=1)
    df_out.to_excel(OUTPUT_EXCEL, index=False)

    print(f"\n✅ Saved enriched file: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()
