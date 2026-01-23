import requests
import json
import csv
from pathlib import Path
import json
from pathlib import Path
from piboufilings import get_filings
import csv
from glob import glob
import os
from collections import defaultdict


class ManagerLookupService:
    # This is a public, official SEC mapping of ALL entity names to CIKs
    CIK_LOOKUP_URL = "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt"
    HEADERS = {"User-Agent": "PeakStrategy/1.0 (peakstrategy@gmail.com)"}
    
    _cached_lookup_data = None

    @classmethod
    def _load_lookup_data(cls):
        """Downloads the master list once and caches it."""
        if cls._cached_lookup_data is None:
            print("Downloading SEC Master Index (this may take 10-20 seconds)...")
            response = requests.get(cls.CIK_LOOKUP_URL, headers=cls.HEADERS)
            response.raise_for_status()
            cls._cached_lookup_data = response.text.splitlines()
        return cls._cached_lookup_data

    @staticmethod
    def find_manager_cik(search_term: str):
        """
        Searches the SEC master CIK list for a manager name.
        """
        lookup_data = ManagerLookupService._load_lookup_data()
        results = []
        search_term_upper = search_term.upper().strip()
        
        for line in lookup_data:
            if search_term_upper in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    name = parts[0]
                    cik = parts[1].zfill(10)
                    results.append({"name": name, "cik": cik})
        
        return ManagerLookupService.get_best_cik(results, search_term_upper)
    
    @staticmethod
    def get_best_cik(matches, original_query):
        """
        Picks the best CIK from a list of potential matches.
        """
        if not matches:
            return None
        
        # 1. Look for Exact Name Match
        for m in matches:
            if m['name'].upper() == original_query:
                return m['cik']

        # 2. Look for matches without slashes (avoids subsidiaries /DE/, /NY/)
        clean_matches = [m for m in matches if "/" not in m['name']]
        if clean_matches:
            return clean_matches[0]['cik']
            
        # 3. Fallback to the first result
        return matches[0]['cik']


def process_hedge_fund_list(csv_input_path, json_output_path):
    input_path = Path(csv_input_path)
    output_path = Path(json_output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = []

    print(f"Reading {input_path}...")
    
    with open(input_path, mode='r', encoding='utf-8') as f:
        # csv.reader handles quoted strings like "Scion Asset Management, LLC" correctly
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            
            company_name = row[0].strip()
            # If manager name exists in column 2, use it; otherwise None
            manager_human_name = row[1].strip() if len(row) > 1 and row[1].strip() else None
            
            print(f"Searching CIK for: {company_name}...")
            cik = ManagerLookupService.find_manager_cik(company_name)
            
            results.append({
                "company": company_name,
                "manager": manager_human_name,
                "cik": cik
            })

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("-" * 30)
    print(f"Success! Saved {len(results)} managers to {output_path}")


# ===============================
# Step 1: Lookup CIK and ticker mapping
# ===============================
class HedgeFundLookupService:
    DATA_PATH = Path("/Users/valerylouis/Documents/PeakStrategy/backend/app/data/hedge_fund_ciks.json")

    @staticmethod
    def load_company_data() -> list:
        with HedgeFundLookupService.DATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_cik_by_company_name(company_name: str) -> str | None:
        hedge_funds = HedgeFundLookupService.load_company_data()
        for hf in hedge_funds:
            if hf["company"].upper() == company_name.upper():
                return hf["cik"]
        return None

    @staticmethod
    def get_ticker_by_cusip(cusip: str) -> str | None:
        hedge_funds = HedgeFundLookupService.load_company_data()
        for hf in hedge_funds:
            if hf.get("cusip") == cusip:
                return hf.get("ticker")
        return None

# ===============================
# Step 2: Download 13F filing using piboufilings
# ===============================
class SecFilingsDownloader:
    @staticmethod
    def download_latest_13f(cik: str, base_dir: str = "./my_sec_data"):
        """
        Downloads 13F-HR filings for the current year using piboufilings.
        Returns path to the latest CSV file.
        """
        get_filings(
            user_name="PeakStrategy",
            user_agent_email="peakstrategy@gmail.com",
            cik=cik,
            form_type=["13F-HR"],
            start_year=2020,
            end_year=2025,
            base_dir=base_dir,
            keep_raw_files=True
        )

        csv_files = [f for f in glob(f"{base_dir}/**/*.csv", recursive=True) if os.path.basename(f) == "13f_holdings.csv"]
        if not csv_files:
            raise FileNotFoundError(f"No holdings CSV found in {base_dir}")
        latest_csv = csv_files[0]  # only one file matches

        return latest_csv


# ===============================
# Step 3: Parse CSV into holdings
# ===============================
class HoldingsParser:
    @staticmethod
    def parse_csv(csv_path: str) -> list[dict]:
        holdings = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                holdings.append({
                    "issuer": row.get("NAME_OF_ISSUER", ""),
                    "cusip": row.get("CUSIP", ""),
                    "shares": int(float(row.get("SHARE_AMOUNT", 0))),
                    "value": int(float(row.get("SHARE_VALUE", 0))) * 1000,  # convert to USD
                    "type": row.get("SH_PRN", "")
                })
        return holdings

# ===============================
# Step 4: End-to-end function
# ===============================
def get_company_holdings_user_friendly(company_name: str) -> list[dict]:
    cik = HedgeFundLookupService.get_cik_by_company_name(company_name)
    if not cik:
        raise ValueError(f"Company '{company_name}' not found in JSON mapping")

    # Download latest 13F CSV using piboufilings
    csv_path = SecFilingsDownloader.download_latest_13f(cik)

    # Parse CSV into holdings
    holdings = HoldingsParser.parse_csv(csv_path)
    holdings = aggregate_holdings(holdings)

    # Map CUSIP -> ticker
    for h in holdings:
        ticker = HedgeFundLookupService.get_ticker_by_cusip(h["cusip"])
        h["ticker"] = ticker if ticker else None

    # Calculate total portfolio value
    total_value = sum(h["value"] for h in holdings if h["value"] is not None and h["value"] > 0)
    if total_value > 0:
        for h in holdings:
            h["allocation"] = round(h["value"] / total_value, 6)  # decimal fraction
    else:
        for h in holdings:
            h["allocation"] = 0.0

    return holdings

def aggregate_holdings(holdings: list[dict]) -> list[dict]:
    agg = defaultdict(lambda: {"issuer": "", "cusip": "", "shares": 0, "value": 0, "type": "", "ticker": None})
    
    for h in holdings:
        key = h["cusip"] or h["issuer"]
        agg[key]["issuer"] = h["issuer"]
        agg[key]["cusip"] = h["cusip"]
        agg[key]["type"] = h["type"]
        agg[key]["shares"] += h["shares"]
        agg[key]["value"] += h["value"]
        agg[key]["ticker"] = h.get("ticker")
    
    return list(agg.values())


# ===============================
# Example usage
# ===============================
if __name__ == "__main__":
    company_name = "BlackRock Inc."
    holdings = get_company_holdings_user_friendly(company_name)
    print(f"User-friendly holdings for {company_name} ({len(holdings)} securities):\n")
    for h in holdings[:]:  # print first 10 as sample
        print(h)




    # CSV_FILE = "/Users/valerylouis/Documents/PeakStrategy/backend/app/data/hedge_funds.csv"
    # JSON_FILE = "/Users/valerylouis/Documents/PeakStrategy/backend/app/data/hedge_fund_ciks.json"
    
    # process_hedge_fund_list(CSV_FILE, JSON_FILE)