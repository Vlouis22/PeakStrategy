"""
Optimized Hedge Fund Holdings Analyzer
Retrieves and analyzes 13F filings from SEC for institutional investment managers.
Caches portfolio data in Supabase — only re-fetches if the record is older than 7 days.
"""

import csv
import random
import tempfile
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict
import time
import threading
import os

import redis as redis_lib
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from piboufilings import get_filings
from supabase import create_client, Client
from dotenv import load_dotenv

# Environment & clients
load_dotenv()

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_KEY"]
REDIS_URL: Optional[str] = os.environ.get("REDIS_URL")          # optional
PRELOAD_SEC_DATA: bool = os.environ.get("PRELOAD_SEC_DATA", "").lower() == "true"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Redis client — None when not configured (triggers local-lock fallback)
_redis: Optional[redis_lib.Redis] = None
if REDIS_URL:
    _redis = redis_lib.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL_DAYS: int = 7


"""
# SEC Rate-Limiting
#
# Production (REDIS_URL set):
#   Sliding-window counter per second.  Key = "sec_rate:{unix_second}",
#   value = number of requests made in that second across ALL containers.
#   TTL = 2 s (one extra second of headroom).  If the bucket is full we
#   sleep 1 s and retry — simple and has no external dependency beyond Redis.
#
# Local dev (no REDIS_URL):
#   Falls back to a per-process threading.Lock with a monotonic timer,
#   identical to the original behaviour.
"""
SEC_REQ_PER_SECOND: int = 8          # stay under SEC's hard 10 req/s limit
_local_rate_lock = threading.Lock()
_local_last_request_time: float = 0.0


def _rate_limit_redis() -> None:
    """Distributed sliding-window rate-limit via Redis."""
    while True:
        now_sec = int(time.time())
        key = f"sec_rate:{now_sec}"
        count = _redis.incr(key)
        if count == 1:
            _redis.expire(key, 2)         
        if count <= SEC_REQ_PER_SECOND:
            return                       
        # bucket full: wait out the current second then retry
        time.sleep(1.0)


def _rate_limit_local() -> None:
    """Single-process fallback: ~1 req/s via monotonic clock."""
    global _local_last_request_time
    with _local_rate_lock:
        elapsed = time.monotonic() - _local_last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        _local_last_request_time = time.monotonic()


def sec_get(url: str, headers: dict, timeout: int = 30) -> requests.Response:
    """Rate-limited GET that automatically picks the right strategy."""
    if _redis:
        _rate_limit_redis()
    else:
        _rate_limit_local()
    return _sec_get_with_retry(url, headers, timeout)


@retry(
    retry=retry_if_exception_type((requests.exceptions.ConnectionError,
                                   requests.exceptions.Timeout,
                                   requests.exceptions.HTTPError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True
)
def _sec_get_with_retry(url: str, headers: dict, timeout: int) -> requests.Response:
    """HTTP GET with automatic retry + exponential backoff."""
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


# ---------------------------------------------------------------------------
# Supabase caching layer — holdings (existing)
# ---------------------------------------------------------------------------

def _get_cached_holdings(company_name: str) -> Optional[list[dict]]:
    """
    Returns cached [{issuer, ticker, allocation}] if the row exists and is
    fresh (≤ 7 days old).  Returns None otherwise.
    """
    response = (
        supabase.table("hedgefund")
        .select("name, data, last_updated")
        .eq("name", company_name)
        .execute()
    )

    if not response.data:
        print(f"  [DB] No cached data found for '{company_name}'.")
        return None

    row = response.data[0]
    last_updated = datetime.fromisoformat(row["last_updated"])
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)

    age = datetime.now(timezone.utc) - last_updated
    if age > timedelta(days=CACHE_TTL_DAYS):
        print(f"  [DB] Cached data for '{company_name}' is {age.days} days old — refreshing.")
        return None

    print(f"  [DB] Using cached data for '{company_name}' (updated {age.days} days ago).")
    return row["data"]


def _save_holdings_to_db(company_name: str, holdings: list[dict]) -> None:
    """
    Upserts [{issuer, ticker, allocation}] into Supabase.
    `holdings` is expected to already be in the three-key shape — no
    extra stripping is done here.
    """
    supabase.table("hedgefund").upsert(
        {
            "name":         company_name,
            "data":         holdings,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="name",
    ).execute()

    print(f"  [DB] Saved {len(holdings)} holdings for '{company_name}'.")


# ---------------------------------------------------------------------------
# Supabase layer — hedge_funds (new, read-heavy registry)
#
# Table schema (create once in your Supabase dashboard or via migration):
#
#   CREATE TABLE hedge_funds (
#       id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
#       company     text   NOT NULL UNIQUE,
#       manager     text,                          -- nullable
#       cik         text,                          -- nullable; NULL = lookup failed
#       created_at  timestamptz DEFAULT now(),
#       updated_at  timestamptz DEFAULT now()
#   );
#
# ---------------------------------------------------------------------------

def _save_hedge_fund(company: str, manager: Optional[str], cik: str) -> None:
    """
    Upserts a single hedge fund row.  Only called after a *successful* CIK
    resolution so the table never contains rows where the fund couldn't be
    confirmed on SEC EDGAR.

    Conflict strategy: if `company` already exists the row is updated in place
    (manager and cik may have changed; timestamps are refreshed).
    """
    now = datetime.now(timezone.utc).isoformat()

    supabase.table("hedge_funds").upsert(
        {
            "company":    company,
            "manager":    manager,
            "cik":        cik,
            "created_at": now,   # ignored on conflict due to the update below
            "updated_at": now,
        },
        on_conflict="company",
    ).execute()

    print(f"  [DB] Saved hedge fund: {company} (CIK: {cik})")


def get_all_hedge_funds() -> list[dict]:
    """
    Returns every fund in the registry as [{company, manager}].

    This is the endpoint payload — CIK and timestamps are intentionally
    excluded so the frontend only sees what it needs.

    Ordered alphabetically by company name for consistent UI rendering.
    """
    response = (
        supabase.table("hedge_funds")
        .select("company, manager")
        .order("company")
        .execute()
    )
    return response.data


# SEC index services
class ManagerLookupService:
    """Handles SEC CIK lookups with caching and optimized search."""

    CIK_LOOKUP_URL = "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt"
    HEADERS = {"User-Agent": "PeakStrategy/1.0 (peakstrategy@gmail.com)"}

    _lookup_dict: Optional[dict[str, str]] = None
    _load_lock = threading.Lock()

    @classmethod
    def _load_lookup_data(cls) -> dict[str, str]:
        """Downloads and caches SEC master index as a dict for fast lookups."""
        if cls._lookup_dict is not None:
            return cls._lookup_dict

        with cls._load_lock:
            if cls._lookup_dict is not None:
                return cls._lookup_dict

            print("Downloading SEC Master Index...")
            response = sec_get(cls.CIK_LOOKUP_URL, cls.HEADERS)

            lookup: dict[str, str] = {}
            for line in response.text.splitlines():
                parts = line.split(":")
                if len(parts) >= 2 and parts[1].strip().isdigit():
                    lookup[parts[0].upper()] = parts[1].strip().zfill(10)

            cls._lookup_dict = lookup
            print(f"Loaded {len(cls._lookup_dict):,} entities")

        return cls._lookup_dict

    @classmethod
    def find_manager_cik(cls, search_term: str) -> Optional[str]:
        """
        Priority: exact match > shortest partial match without slash > shortest partial match.
        """
        lookup = cls._load_lookup_data()
        search_upper = search_term.upper().strip()

        if search_upper in lookup:
            return lookup[search_upper]

        matches = {name: cik for name, cik in lookup.items() if search_upper in name}
        if not matches:
            return None

        clean_matches = {n: c for n, c in matches.items() if "/" not in n}
        if clean_matches:
            return clean_matches[min(clean_matches, key=len)]

        return matches[min(matches, key=len)]


class TickerResolutionService:
    """
    Resolves tickers from holdings issuer names using live SEC data.

    Strategy:
        SEC's company_tickers.json (updated daily) maps CIK <-> ticker <-> title.
        Two indexes are built:
            1. Normalized title  -> ticker   (exact match)
            2. Sorted list of (normalized_title, ticker) for binary-search prefix matching
    """

    TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    HEADERS = {"User-Agent": "PeakStrategy/1.0 (peakstrategy@gmail.com)"}

    _exact_map: Optional[dict[str, str]] = None
    _prefix_sorted: Optional[list[tuple[str, str]]] = None
    _load_lock = threading.Lock()

    @classmethod
    def _normalize(cls, name: str) -> str:
        """
        Strips legal suffixes and punctuation so that "Apple Inc.", "APPLE INC",
        and "Apple Incorporated" all collapse to the same key.
        """
        suffixes_to_strip = (
            " INCORPORATED", " INC.", " INC", " CORP.", " CORP",
            " CO.", " CO", " LTD.", " LTD", " LLC", " LP", " L.P.",
            " PLC", " SE", " AG", " NV", " SA", " GROUP",
        )
        n = name.upper().strip()
        # Single trailing-period removal.  Do NOT use rstrip(".") — it is
        # character-based and would eat interior dots (e.g. "U.S. BANCORP").
        if n.endswith("."):
            n = n[:-1].strip()

        changed = True
        while changed:
            changed = False
            for suffix in suffixes_to_strip:
                if n.endswith(suffix):
                    n = n[: -len(suffix)].strip()
                    changed = True
            if n.endswith("."):
                n = n[:-1].strip()
                changed = True

        # Drop trailing punctuation left over after suffix removal
        # (e.g. "&" from "WELLS FARGO & CO.")
        n = n.rstrip(" &")
        return n

    @classmethod
    def _load_indexes(cls) -> None:
        """Downloads company_tickers.json and builds lookup indexes."""
        if cls._exact_map is not None:
            return

        with cls._load_lock:
            if cls._exact_map is not None:
                return

            print("Downloading SEC company tickers index...")
            response = sec_get(cls.TICKERS_URL, cls.HEADERS)
            data = response.json()

            exact: dict[str, str] = {}
            for entry in data.values():
                ticker = entry.get("ticker", "").strip().upper()
                title = entry.get("title", "").strip()
                if not ticker or not title:
                    continue
                normalized = cls._normalize(title)
                if normalized and normalized not in exact:
                    exact[normalized] = ticker

            cls._prefix_sorted = sorted(exact.items(), key=lambda item: item[0])
            cls._exact_map = exact
            print(f"Loaded {len(cls._exact_map):,} ticker entries")

    @classmethod
    def _prefix_search(cls, normalized: str) -> Optional[str]:
        """
        Binary-search prefix match: O(log n).
        Finds the longest key in _prefix_sorted that `normalized` starts with.
        """
        import bisect

        candidates = cls._prefix_sorted
        idx = bisect.bisect_right(candidates, (normalized,))

        best_ticker: Optional[str] = None
        best_len = 0

        for i in range(idx - 1, -1, -1):
            key, ticker = candidates[i]
            if normalized.startswith(key):
                if len(key) > best_len:
                    best_ticker = ticker
                    best_len = len(key)
                break
            if key[0] != normalized[0]:
                break

        # Minimum 4-char prefix to avoid false positives
        if best_ticker and best_len >= 4:
            return best_ticker
        return None

    @classmethod
    def resolve(cls, issuer_name: str) -> Optional[str]:
        """
        Resolves issuer name → ticker.
        Match order: exact → prefix.  Returns None if no match.
        """
        cls._load_indexes()

        if not issuer_name or not issuer_name.strip():
            return None

        normalized = cls._normalize(issuer_name)
        if not normalized:
            return None

        return cls._exact_map.get(normalized) or cls._prefix_search(normalized)


# ---------------------------------------------------------------------------
# SEC filing download  (ephemeral filesystem)
# ---------------------------------------------------------------------------

class SecFilingsDownloader:
    """Downloads SEC 13F filings into a caller-supplied directory."""

    @staticmethod
    def download_latest_13f(cik: str, base_dir: str) -> Path:
        """
        Downloads the latest 13F-HR filing into *base_dir* and returns the
        path to the holdings CSV.

        The caller is responsible for the lifetime of base_dir.  In
        production this is a TemporaryDirectory managed by _fetch_holdings_from_sec.

        Raises:
            FileNotFoundError: If no 13F filings are found in the last 6 years.
        """
        cik_dir = Path(base_dir) / cik
        current_year = datetime.now().year

        for year_offset in range(6):
            search_year = current_year - year_offset
            print(f"Searching for 13F filings in {search_year}...")

            try:
                get_filings(
                    user_name="PeakStrategy",
                    user_agent_email="peakstrategy@gmail.com",
                    cik=cik,
                    form_type=["13F-HR"],
                    start_year=search_year,
                    end_year=search_year,
                    base_dir=str(cik_dir),
                    keep_raw_files=True
                )

                csv_files = list(cik_dir.rglob("13f_holdings.csv"))
                if csv_files:
                    latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
                    print(f"✓ Found latest filing: {latest_csv.parent.name}")
                    return latest_csv

            except Exception as e:
                print(f"  No filings found for {search_year}: {e}")
                continue

        raise FileNotFoundError(
            f"No 13F-HR filings found for CIK {cik} in the last 6 years. "
            f"This company may not be required to file 13F forms."
        )


# ---------------------------------------------------------------------------
# Holdings parsing
# ---------------------------------------------------------------------------

class HoldingsParser:
    """Parses and processes 13F holdings data."""

    @staticmethod
    def parse_csv(csv_path: Path) -> list[dict]:
        """
        Parses 13F CSV into structured holdings.
        Warns and raises if the drop rate exceeds 5%.
        """
        holdings = []
        total_rows = 0
        skipped_rows = 0
        MAX_DROP_RATE = 0.05

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                try:
                    shares = int(float(row.get("SHARE_AMOUNT", 0) or 0))
                    value = int(float(row.get("SHARE_VALUE", 0) or 0)) * 1000

                    holdings.append({
                        "issuer":     row.get("NAME_OF_ISSUER", "").strip(),
                        "cusip":      row.get("CUSIP", "").strip(),
                        "shares":     shares,
                        "value":      value,
                        "type":       row.get("SH_PRN", "").strip(),
                        "ticker":     None,
                        "allocation": 0.0,
                    })
                except (ValueError, TypeError) as e:
                    skipped_rows += 1
                    print(f"Warning: Skipping invalid row #{total_rows}: {e}")

        if total_rows > 0:
            drop_rate = skipped_rows / total_rows
            if skipped_rows > 0:
                print(f"Warning: Skipped {skipped_rows}/{total_rows} rows "
                      f"({drop_rate:.1%} drop rate)")
            if drop_rate > MAX_DROP_RATE:
                raise ValueError(
                    f"Parse failure rate {drop_rate:.1%} exceeds the {MAX_DROP_RATE:.0%} "
                    f"threshold ({skipped_rows}/{total_rows} rows skipped). "
                    f"The CSV may be malformed or in an unexpected format."
                )

        return holdings

    @staticmethod
    def aggregate_holdings(holdings: list[dict]) -> list[dict]:
        """Aggregates duplicate holdings by CUSIP (or issuer as fallback)."""
        agg = defaultdict(lambda: {
            "issuer": "", "cusip": "", "shares": 0,
            "value": 0, "type": "", "ticker": None, "allocation": 0.0,
        })

        for h in holdings:
            key = h["cusip"] if h["cusip"] else h["issuer"]
            if not agg[key]["issuer"]:
                agg[key]["issuer"] = h["issuer"]
                agg[key]["cusip"]  = h["cusip"]
                agg[key]["type"]   = h["type"]
            agg[key]["shares"] += h["shares"]
            agg[key]["value"]  += h["value"]

        return list(agg.values())

    @staticmethod
    def enrich_with_tickers(holdings: list[dict]) -> None:
        """Resolves ticker symbols in-place."""
        for h in holdings:
            if h["issuer"]:
                h["ticker"] = TickerResolutionService.resolve(h["issuer"])

    @staticmethod
    def calculate_allocations(holdings: list[dict]) -> None:
        """Calculates portfolio allocation percentages in-place."""
        total_value = sum(h["value"] for h in holdings if h["value"] > 0)
        if total_value > 0:
            for h in holdings:
                h["allocation"] = round(h["value"] / total_value, 6)


# ---------------------------------------------------------------------------
# Core fetch  (ephemeral temp dir wraps the entire download+parse lifecycle)
# ---------------------------------------------------------------------------

def _fetch_holdings_from_sec(company_name: str) -> list[dict]:
    """
    Full SEC pipeline: CIK lookup → download → parse → enrich → allocations.

    Downloads land in a TemporaryDirectory that is automatically deleted once
    parsing is complete — nothing is written to the persistent filesystem.

    Returns [{issuer, ticker, allocation}] — the same shape the DB stores.
    """
    cik = ManagerLookupService.find_manager_cik(company_name)
    if not cik:
        raise ValueError(
            f"Company '{company_name}' not found in SEC EDGAR. "
            f"Try variations of the name (e.g. include/exclude 'LLC', 'LP')."
        )

    print(f"Downloading 13F filings for {company_name} (CIK: {cik})...")

    # TemporaryDirectory is the ONLY place files touch disk.
    # It is automatically removed when the `with` block exits —
    # even if an exception is raised.
    with tempfile.TemporaryDirectory(prefix=f"sec_{cik}_") as tmp_dir:
        csv_path = SecFilingsDownloader.download_latest_13f(cik, tmp_dir)
        print(f"Processing {csv_path}...")

        holdings = HoldingsParser.parse_csv(csv_path)
        # csv_path is no longer needed after this point; the rest of the
        # pipeline operates purely on in-memory lists.

    # tmp_dir is now deleted.  Continue with in-memory data only.
    holdings = HoldingsParser.aggregate_holdings(holdings)
    HoldingsParser.enrich_with_tickers(holdings)
    HoldingsParser.calculate_allocations(holdings)

    # Sort by allocation descending before projecting down to the final shape.
    holdings.sort(key=lambda x: x["allocation"], reverse=True)

    # Project to the DB shape.  Every caller (cache and fresh) now sees
    # exactly the same three keys.
    return [
        {
            "issuer":     h["issuer"],
            "ticker":     h["ticker"],
            "allocation": h["allocation"],
        }
        for h in holdings
    ]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_company_holdings(company_names: list[str]) -> list[dict]:
    """
    Returns holdings for each company as separate lists.
    Each company result is a dict: {"company": company_name, "holdings": [...]}

    Cache logic for each company:
        1. Query Supabase.
        2. If fresh (≤ 7 days) → use cached data.
        3. Otherwise fetch from SEC, persist, then use.

    Raises:
        ValueError:        Any company not found in SEC EDGAR.
        FileNotFoundError: No 13F filings available for any company.
    """
    result = []

    for company_name in company_names:
        cached = _get_cached_holdings(company_name)
        if cached is not None:
            result.append({"company": company_name, "holdings": cached})
            continue

        holdings = _fetch_holdings_from_sec(company_name)
        _save_holdings_to_db(company_name, holdings)
        result.append({"company": company_name, "holdings": holdings})

    return result


def process_hedge_fund_list(csv_input_path: str, json_output_path: str) -> None:
    """
    Batch processes a CSV of hedge fund names to find their CIKs.
    Each fund with a successful CIK resolution is persisted to the
    hedge_funds table so the frontend can discover available funds.

    CSV format:   Company Name, Manager Name (optional)
    Output JSON:  [{"company": "...", "manager": "...", "cik": "..."}, ...]
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
                # Write-on-success: persist only confirmed funds
                _save_hedge_fund(company_name, manager_name, cik)
            else:
                print(f"    ✗ No CIK found")

            results.append({"company": company_name, "manager": manager_name, "cik": cik})

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    success_count = sum(1 for r in results if r["cik"])
    print("-" * 50)
    print(f"✓ Saved {len(results)} managers to {output_path}")
    print(f"  ({success_count} with CIKs, {len(results) - success_count} not found)")


def load_hedge_funds_from_json(json_file_path: str) -> None:
    """
    Loads hedge fund data from a JSON file and uploads to the hedge_funds table.
    
    Expected JSON format:
    [
        {"company": "...", "manager": "...", "cik": "..."},
        ...
    ]
    
    Only entries with a valid CIK (not null) are uploaded.
    """
    json_path = Path(json_file_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    print(f"Reading hedge fund data from {json_path}...")
    
    with json_path.open('r', encoding='utf-8') as f:
        hedge_funds = json.load(f)
    
    if not isinstance(hedge_funds, list):
        raise ValueError("JSON file must contain an array of hedge fund objects")
    
    uploaded_count = 0
    skipped_count = 0
    
    for fund in hedge_funds:
        company = fund.get("company")
        manager = fund.get("manager")
        cik = fund.get("cik")
        
        # Skip entries without a valid CIK
        if not cik or not company:
            skipped_count += 1
            print(f"  ✗ Skipping {company or 'Unknown'} (missing company name or CIK)")
            continue
        
        try:
            _save_hedge_fund(company, manager, cik)
            uploaded_count += 1
        except Exception as e:
            print(f"  ✗ Failed to save {company}: {e}")
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print(f"Upload complete!")
    print(f"  ✓ Successfully uploaded: {uploaded_count}")
    print(f"  ✗ Skipped/Failed: {skipped_count}")
    print(f"  Total processed: {len(hedge_funds)}")
    print("=" * 60)


"""
# Startup preload  (production only)
#
# Set PRELOAD_SEC_DATA=true in your container env.  On import the two heavy
# SEC indexes are fetched with a random 0–3 s jitter so that simultaneous
# container scale-outs don't all hit SEC at the exact same instant.
"""
def _preload_sec_indexes() -> None:
    """Eagerly loads both SEC indexes with startup jitter."""
    jitter = random.uniform(0, 3)
    print(f"[PRELOAD] Waiting {jitter:.1f}s jitter before fetching SEC indexes...")
    time.sleep(jitter)

    ManagerLookupService._load_lookup_data()
    TickerResolutionService._load_indexes()
    print("[PRELOAD] SEC indexes ready.")


if PRELOAD_SEC_DATA:
    _preload_sec_indexes()



if __name__ == "__main__":
    try:
        # Example 1: Load hedge funds from JSON file
        BASE_DIR = Path(__file__).resolve().parent
        json_file = BASE_DIR / "hedge_fund_ciks.json"
        
        #Example 2: Get holdings for a specific company
        company_name = "Berkshire Hathaway Inc"
        holdings = get_company_holdings(company_name)
        
        print(f"\n{'=' * 60}")
        print(f"Holdings for {company_name}")
        print(f"Total positions: {len(holdings):,}")
        print(f"{'=' * 60}\n")
        
        for i, h in enumerate(holdings[:10], 1):
            ticker = h.get("ticker") or "N/A"
            pct = h.get("allocation", 0.0) * 100
            print(f"{i:2}. {h.get('issuer', 'N/A')[:40]:<40} "
                  f"({ticker:5})  {pct:>6.2f}%")

    except Exception as e:
        print(f"Error: {e}")