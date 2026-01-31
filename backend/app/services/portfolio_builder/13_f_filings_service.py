"""
Optimized Hedge Fund Holdings Analyzer
Retrieves and analyzes 13F filings from SEC for institutional investment managers.
"""

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict
from functools import lru_cache
import shutil
import requests
from piboufilings import get_filings


class ManagerLookupService:
    """Handles SEC CIK lookups with caching and optimized search."""
    
    CIK_LOOKUP_URL = "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt"
    HEADERS = {"User-Agent": "PeakStrategy/1.0 (peakstrategy@gmail.com)"}
    
    _lookup_dict: Optional[dict[str, str]] = None  # Cache as dict for O(1) lookups

    @classmethod
    def _load_lookup_data(cls) -> dict[str, str]:
        """Downloads and caches SEC master index as a dictionary for fast lookups."""
        if cls._lookup_dict is None:
            print("Downloading SEC Master Index...")
            response = requests.get(cls.CIK_LOOKUP_URL, headers=cls.HEADERS, timeout=30)
            response.raise_for_status()
            
            # Build dict: uppercase name -> CIK
            cls._lookup_dict = {}
            for line in response.text.splitlines():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    name, cik = parts
                    cls._lookup_dict[name.upper()] = cik.zfill(10)
            
            print(f"Loaded {len(cls._lookup_dict):,} entities")
        
        return cls._lookup_dict

    @classmethod
    def find_manager_cik(cls, search_term: str) -> Optional[str]:
        """
        Searches for a manager's CIK with intelligent matching.
        Priority: exact match > partial match without slash > first match
        """
        lookup = cls._load_lookup_data()
        search_upper = search_term.upper().strip()
        
        # Fast path: exact match
        if search_upper in lookup:
            return lookup[search_upper]
        
        # Partial match: find all containing search term
        matches = {name: cik for name, cik in lookup.items() if search_upper in name}
        
        if not matches:
            return None
        
        # Prefer matches without "/" (subsidiaries like "COMPANY/DE/" are less relevant)
        clean_matches = {n: c for n, c in matches.items() if "/" not in n}
        
        if clean_matches:
            # Return shortest name (likely the parent company)
            best_match = min(clean_matches.keys(), key=len)
            return clean_matches[best_match]
        
        # Fallback to shortest match overall
        best_match = min(matches.keys(), key=len)
        return matches[best_match]


class HedgeFundLookupService:
    """Manages local hedge fund data with caching."""
    
    DATA_PATH = Path(__file__).parent / "data" / "hedge_fund_ciks.json"
    _cache: Optional[dict] = None

    @classmethod
    @lru_cache(maxsize=1)
    def load_company_data(cls) -> list[dict]:
        """Loads and caches hedge fund data from JSON."""
        if not cls.DATA_PATH.exists():
            raise FileNotFoundError(f"Data file not found: {cls.DATA_PATH}")
        
        with cls.DATA_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _get_lookup_dicts(cls) -> tuple[dict, dict]:
        """Creates optimized lookup dictionaries (computed once)."""
        if cls._cache is None:
            data = cls.load_company_data()
            company_to_cik = {hf["company"].upper(): hf["cik"] for hf in data}
            cusip_to_ticker = {hf["cusip"]: hf["ticker"] for hf in data if "cusip" in hf and "ticker" in hf}
            cls._cache = (company_to_cik, cusip_to_ticker)
        return cls._cache

    @classmethod
    def get_cik_by_company_name(cls, company_name: str) -> Optional[str]:
        """O(1) lookup of CIK by company name."""
        company_dict, _ = cls._get_lookup_dicts()
        return company_dict.get(company_name.upper())

    @classmethod
    def get_ticker_by_cusip(cls, cusip: str) -> Optional[str]:
        """O(1) lookup of ticker by CUSIP."""
        _, cusip_dict = cls._get_lookup_dicts()
        return cusip_dict.get(cusip)


class SecFilingsDownloader:
    """Downloads SEC 13F filings."""
    
    @staticmethod
    def download_latest_13f(cik: str, base_dir: str = "./my_sec_data") -> Path:
        """
        Downloads ONLY the latest 13F-HR filing and returns path to holdings CSV.
        Guarantees at least one filing is retrieved.
        
        Strategy:
        1. Start with current year
        2. If no filings found, expand search backwards up to 5 years
        3. Once found, download only the most recent filing
        
        Raises:
            FileNotFoundError: If no 13F filings found in the last 5 years
        """
        base_path = Path(base_dir)
        current_year = datetime.now().year
        
        # Clean up any existing data for this CIK to ensure fresh download
        if base_path.exists():
            shutil.rmtree(base_path, ignore_errors=True)
        
        # Try progressively older years until we find at least one filing
        for year_offset in range(6):  # Try current year through 5 years back
            search_year = current_year - year_offset
            
            print(f"Searching for 13F filings in {search_year}...")
            
            try:
                # Download filings for this specific year
                get_filings(
                    user_name="PeakStrategy",
                    user_agent_email="peakstrategy@gmail.com",
                    cik=cik,
                    form_type=["13F-HR"],
                    start_year=search_year,
                    end_year=search_year,
                    base_dir=str(base_path),
                    keep_raw_files=True
                )
                
                # Check if we got any CSV files
                csv_files = list(base_path.rglob("13f_holdings.csv"))
                
                if csv_files:
                    # Found filings! Return the most recent one
                    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
                    print(f"✓ Found latest filing: {latest_csv.parent.name}")
                    
                    # Clean up older filings to keep only the latest
                    for csv_file in csv_files:
                        if csv_file != latest_csv:
                            # Remove the entire filing directory
                            filing_dir = csv_file.parent
                            shutil.rmtree(filing_dir, ignore_errors=True)
                    
                    return latest_csv
                
            except Exception as e:
                print(f"  No filings found for {search_year}: {e}")
                continue
        
        # If we get here, no filings were found in the last 5 years
        raise FileNotFoundError(
            f"No 13F-HR filings found for CIK {cik} in the last 5 years. "
            f"This company may not be required to file 13F forms."
        )


class HoldingsParser:
    """Parses and processes 13F holdings data."""
    
    @staticmethod
    def parse_csv(csv_path: Path) -> list[dict]:
        """
        Parses 13F CSV into structured holdings.
        More efficient with direct type conversion and cleaner logic.
        """
        holdings = []
        
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    shares = int(float(row.get("SHARE_AMOUNT", 0) or 0))
                    value = int(float(row.get("SHARE_VALUE", 0) or 0)) * 1000
                    
                    holdings.append({
                        "issuer": row.get("NAME_OF_ISSUER", "").strip(),
                        "cusip": row.get("CUSIP", "").strip(),
                        "shares": shares,
                        "value": value,
                        "type": row.get("SH_PRN", "").strip(),
                        "ticker": None  # Will be populated later
                    })
                except (ValueError, TypeError) as e:
                    print(f"Warning: Skipping invalid row: {e}")
                    continue
        
        return holdings

    @staticmethod
    def aggregate_holdings(holdings: list[dict]) -> list[dict]:
        """
        Aggregates duplicate holdings by CUSIP (or issuer as fallback).
        More efficient with cleaner defaultdict usage.
        """
        agg = defaultdict(lambda: {
            "issuer": "",
            "cusip": "",
            "shares": 0,
            "value": 0,
            "type": "",
            "ticker": None
        })
        
        for h in holdings:
            # Use CUSIP as primary key, fallback to issuer
            key = h["cusip"] if h["cusip"] else h["issuer"]
            
            # First entry sets metadata
            if not agg[key]["issuer"]:
                agg[key]["issuer"] = h["issuer"]
                agg[key]["cusip"] = h["cusip"]
                agg[key]["type"] = h["type"]
            
            # Accumulate quantities
            agg[key]["shares"] += h["shares"]
            agg[key]["value"] += h["value"]
        
        return list(agg.values())

    @staticmethod
    def enrich_with_tickers(holdings: list[dict]) -> None:
        """Adds ticker symbols to holdings (modifies in-place for efficiency)."""
        for h in holdings:
            if h["cusip"]:
                h["ticker"] = HedgeFundLookupService.get_ticker_by_cusip(h["cusip"])

    @staticmethod
    def calculate_allocations(holdings: list[dict]) -> None:
        """Calculates portfolio allocation percentages (modifies in-place)."""
        total_value = sum(h["value"] for h in holdings if h["value"] > 0)
        
        if total_value > 0:
            for h in holdings:
                h["allocation"] = round(h["value"] / total_value, 6)
        else:
            for h in holdings:
                h["allocation"] = 0.0


def get_company_holdings(company_name: str, base_dir: str = "./my_sec_data") -> list[dict]:
    """
    Main function: retrieves and processes holdings for a company.
    
    Args:
        company_name: Name of the investment manager
        base_dir: Directory to store downloaded filings
    
    Returns:
        List of holdings with ticker, allocation, value, etc.
    
    Raises:
        ValueError: If company not found
        FileNotFoundError: If no 13F filings found
    """
    # Step 1: Get CIK
    cik = HedgeFundLookupService.get_cik_by_company_name(company_name)
    if not cik:
        raise ValueError(f"Company '{company_name}' not found in database")

    # Step 2: Download latest 13F
    print(f"Downloading 13F filings for {company_name} (CIK: {cik})...")
    csv_path = SecFilingsDownloader.download_latest_13f(cik, base_dir)
    print(f"Processing {csv_path}...")

    # Step 3: Parse and aggregate
    holdings = HoldingsParser.parse_csv(csv_path)
    holdings = HoldingsParser.aggregate_holdings(holdings)

    # Step 4: Enrich with tickers and allocations
    HoldingsParser.enrich_with_tickers(holdings)
    HoldingsParser.calculate_allocations(holdings)

    # Step 5: Sort by value (largest positions first)
    holdings.sort(key=lambda x: x["value"], reverse=True)

    return holdings


def process_hedge_fund_list(csv_input_path: str, json_output_path: str) -> None:
    """
    Batch processes a CSV of hedge fund names to find their CIKs.
    
    CSV format:
        Company Name, Manager Name (optional)
    
    Output JSON format:
        [{"company": "...", "manager": "...", "cik": "..."}, ...]
    """
    input_path = Path(csv_input_path)
    output_path = Path(json_output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    print(f"Reading {input_path}...")
    
    with input_path.open(mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row_num, row in enumerate(reader, 1):
            if not row or not row[0].strip():
                continue
            
            company_name = row[0].strip()
            manager_name = row[1].strip() if len(row) > 1 and row[1].strip() else None
            
            print(f"[{row_num}] Searching CIK for: {company_name}...")
            cik = ManagerLookupService.find_manager_cik(company_name)
            
            if cik:
                print(f"    ✓ Found CIK: {cik}")
            else:
                print(f"    ✗ No CIK found")
            
            results.append({
                "company": company_name,
                "manager": manager_name,
                "cik": cik
            })

    # Save to JSON
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    success_count = sum(1 for r in results if r["cik"])
    print("-" * 50)
    print(f"✓ Saved {len(results)} managers to {output_path}")
    print(f"  ({success_count} with CIKs, {len(results) - success_count} not found)")


# Example usage
if __name__ == "__main__":
    try:
        company_name = "ARK Investment Management LLC"
        holdings = get_company_holdings(company_name)
        
        print(f"\n{'='*60}")
        print(f"Holdings for {company_name}")
        print(f"Total positions: {len(holdings):,}")
        print(f"{'='*60}\n")
        
        # Display top 10 positions
        for i, h in enumerate(holdings[:10], 1):
            ticker = h['ticker'] or 'N/A'
            value_m = h['value'] / 1_000_000
            pct = h['allocation'] * 100
            
            print(f"{i:2}. {h['issuer'][:40]:<40} ({ticker:5}) "
                  f"${value_m:>10,.1f}M  {pct:>5.2f}%")
    
    except Exception as e:
        print(f"Error: {e}")