#!/usr/bin/env python3
"""
Pangolinfo WIPO API Client (v3 — OSS + DuckDB backend)

Zero-dependency Python client for Pangolinfo's WIPO Global Design Database API.
The backend now reads OSS Parquet via DuckDB. Wrong params trigger full-table
scans (5–60s+) or timeouts, so this client enforces the backend's perf contract
BEFORE sending the request.

────────────────────────────────────────────────────────────────────────────
🚨 BACKEND PERF CONTRACT (read before adding new params)
────────────────────────────────────────────────────────────────────────────

1. --source IS MANDATORY.
   Different data sources have different Parquet schemas; the backend cannot
   query across sources. Skipping --source falls back to a full glob and is
   effectively unusable. Use the country code form:
     USID, CNID, DEID, JPID, KRID, EMID, FRID, INID, ITID, ESID, CHID, HAGUE
   US/us → auto-normalized to USID; CN/cn → CNID; HAGUE stays HAGUE.

2. CNID dataset rules (the largest dataset, 17M+ rows):
   - --ed is NOT supported on CNID (DETAIL_DATA absent). Use --rd instead.
   - --hol / --prod on CNID MUST also include one of: --id, --id-search,
     --rd, --status, --lcs. Otherwise the backend rejects the request.
   - --prod on CNID searches the Chinese product column (PROD_ZH); pass
     Chinese terms when targeting CNID.
   - To avoid the 5s+ full glob: pass --id "CNID.YYYY..." or --rd "YYYY".
     The backend uses these to route to a single partition.

3. Stage 2 large sources (DEID/JPID/USID/KRID/EMID):
   --hol or --prod fuzzy search on these sources can hit the 25s query
   timeout. ALWAYS pair them with --status, --lcs, or --rd "YYYY".

4. --ed is silently ignored on ALL sources (the upstream schema simply does
   not contain the expiration-date key). Don't bother sending it; use --rd
   for date filtering instead.

5. Schema gaps the backend silently skips:
     USID has no STATUS column → --status ignored
     JPID has no HOL column    → --hol ignored
     JPID has no PROD column   → --prod ignored

6. Pagination: --size (1–1000, default 10). --num is kept as an alias.

Usage examples:
    wipo.py --source USID --hol "Apple" --status ACT
    wipo.py --source CNID --rd 2024 --prod "椅子"
    wipo.py --source HAGUE --irn "DM/000298"
    wipo.py --source DEID --lcs "23-01" --status ACT
    wipo.py --auth-only

Environment:
    PANGOLINFO_API_KEY  - API key (skips login)
    PANGOLINFO_EMAIL    - Account email (for login)
    PANGOLINFO_PASSWORD - Account password (for login)
"""

import argparse
import io
import json
import os
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Fix Windows / macOS console encoding for Unicode output
# ---------------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_BASE = "https://scrapeapi.pangolinfo.com"
AUTH_ENDPOINT = f"{API_BASE}/api/v1/auth"
WIPO_ENDPOINT = f"{API_BASE}/api/v3/wipo"
API_KEY_CACHE_PATH = Path.home() / ".pangolinfo_api_key"

REFERRER_TAG = "clawhub_wipo"
PANGOLINFO_URL = f"https://pangolinfo.com/?referrer={REFERRER_TAG}"

CACHE_TO_DISK = False

EXIT_SUCCESS = 0
EXIT_API_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_NETWORK_ERROR = 3
EXIT_AUTH_ERROR = 4

# Backend perf-contract whitelists (mirror WipoParquetService.java)
KNOWN_SOURCES = {
    "USID", "CNID", "DEID", "JPID", "KRID", "EMID",
    "FRID", "INID", "ITID", "ESID", "CHID", "HAGUE",
}
STAGE2_LARGE_SOURCES = {"DEID", "JPID", "USID", "KRID", "EMID"}
SOURCES_WITHOUT_STATUS = {"USID"}
SOURCES_WITHOUT_HOL = {"JPID"}
SOURCES_WITHOUT_PROD = {"JPID"}  # CNID uses PROD_ZH; still queryable via --prod


# ---------------------------------------------------------------------------
# Error helper
# ---------------------------------------------------------------------------
def _emit_error(code, message, hint=None, api_code=None, exit_code=None):
    """Print structured error JSON to stderr and optionally exit."""
    envelope = {"success": False, "error": {"code": code, "message": message}}
    if api_code is not None:
        envelope["error"]["api_code"] = api_code
    if hint:
        envelope["error"]["hint"] = hint
    print(json.dumps(envelope, ensure_ascii=False), file=sys.stderr)
    if exit_code is not None:
        sys.exit(exit_code)


def _is_ssl_error(exc):
    msg = str(exc)
    return "CERTIFICATE_VERIFY_FAILED" in msg or "SSL" in msg


def _emit_ssl_error():
    _emit_error(
        "SSL_CERT",
        "SSL certificate verification failed.",
        hint=(
            "macOS: run '/Applications/Python 3.x/Install Certificates.command' "
            "or set SSL_CERT_FILE. See: python3 -c \"import certifi; print(certifi.where())\""
        ),
        exit_code=EXIT_NETWORK_ERROR,
    )


# ---------------------------------------------------------------------------
# Source normalization & perf-contract validation (mirror backend)
# ---------------------------------------------------------------------------
def normalize_source(raw):
    """Mirror WipoParquetService.normalizeSource — keep client errors in sync."""
    if raw is None:
        return None
    s = raw.strip().upper()
    if not s:
        return s
    if s == "HAGUE":
        return s
    if len(s) == 2:
        return s + "ID"  # US → USID, CN → CNID
    return s


def validate_perf_contract(args):
    """Pre-flight checks so the user gets a fast, clear error rather than a
    25s backend timeout. Mirrors WipoParquetService.validate() + the slow-path
    guardrails called out in comments.
    """
    source = args.source  # already normalized
    if not source:
        _emit_error(
            "MISSING_SOURCE",
            "--source is required.",
            hint=(
                "The backend cannot query across sources. Pass one of: "
                + ", ".join(sorted(KNOWN_SOURCES))
                + ". Country codes (US, CN, ...) are auto-normalized to USID/CNID."
            ),
            exit_code=EXIT_USAGE_ERROR,
        )

    if source not in KNOWN_SOURCES:
        # Don't hard-block — backend may add sources — but warn loudly.
        print(
            json.dumps({
                "warning": "UNKNOWN_SOURCE",
                "message": f"source='{source}' is not in the known list; "
                           f"if the dataset is not on OSS the backend will return 404.",
            }, ensure_ascii=False),
            file=sys.stderr,
        )

    has_fuzzy = bool(args.hol or args.prod)
    has_narrow = bool(args.record_id or args.id_search or args.rd
                      or args.status or args.lcs or args.irn)

    # Rule 1: CNID does not support ED
    if source == "CNID" and args.ed:
        _emit_error(
            "CNID_ED_UNSUPPORTED",
            "CNID dataset does not support --ed (expiration date) filtering.",
            hint='Use --rd "YYYY" instead (e.g. --rd 2024).',
            exit_code=EXIT_USAGE_ERROR,
        )

    # Rule 2: CNID + fuzzy MUST narrow
    if source == "CNID" and has_fuzzy and not has_narrow:
        _emit_error(
            "CNID_TOO_BROAD",
            "CNID dataset is too large for unconstrained --hol/--prod fuzzy search.",
            hint=(
                "Add at least one of --id, --id-search, --rd, --status, --lcs "
                "to narrow the partition scan."
            ),
            exit_code=EXIT_USAGE_ERROR,
        )

    # Rule 3: Stage 2 large source + fuzzy without narrowing → very likely timeout
    if source in STAGE2_LARGE_SOURCES and has_fuzzy and not (
        args.status or args.lcs or args.rd or args.record_id or args.id_search
    ):
        print(
            json.dumps({
                "warning": "STAGE2_FUZZY_SLOW",
                "message": (
                    f"source={source} + --hol/--prod fuzzy search WITHOUT "
                    "--status/--lcs/--rd often hits the 25s backend timeout. "
                    "Consider narrowing the query."
                ),
            }, ensure_ascii=False),
            file=sys.stderr,
        )

    # Rule 4: --ed is silently ignored on every source
    if args.ed and source != "CNID":
        print(
            json.dumps({
                "warning": "ED_IGNORED",
                "message": (
                    "The backend silently ignores --ed on ALL sources "
                    "(upstream schema lacks the expiration-date key). "
                    "Use --rd for date filtering."
                ),
            }, ensure_ascii=False),
            file=sys.stderr,
        )

    # Rule 5: Schema gaps — warn the user their filter will be dropped
    if args.status and source in SOURCES_WITHOUT_STATUS:
        print(json.dumps({"warning": "STATUS_DROPPED",
                          "message": f"source={source} has no STATUS column; --status ignored."},
                         ensure_ascii=False), file=sys.stderr)
    if args.hol and source in SOURCES_WITHOUT_HOL:
        print(json.dumps({"warning": "HOL_DROPPED",
                          "message": f"source={source} has no HOL column; --hol ignored."},
                         ensure_ascii=False), file=sys.stderr)
    if args.prod and source in SOURCES_WITHOUT_PROD:
        print(json.dumps({"warning": "PROD_DROPPED",
                          "message": f"source={source} has no PROD column; --prod ignored."},
                         ensure_ascii=False), file=sys.stderr)


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------
def load_cached_api_key():
    if API_KEY_CACHE_PATH.exists():
        api_key = API_KEY_CACHE_PATH.read_text().strip()
        if api_key and len(api_key.split(".")) == 3:
            return api_key
    return None


def save_cached_api_key(api_key):
    if not CACHE_TO_DISK:
        return
    try:
        fd = os.open(
            str(API_KEY_CACHE_PATH) + ".tmp",
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            stat.S_IRUSR | stat.S_IWUSR,
        )
        with os.fdopen(fd, "w") as f:
            f.write(api_key)
        os.replace(str(API_KEY_CACHE_PATH) + ".tmp", str(API_KEY_CACHE_PATH))
    except OSError:
        API_KEY_CACHE_PATH.write_text(api_key)
        try:
            API_KEY_CACHE_PATH.chmod(0o600)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def _http_post(url, body_dict, headers=None, timeout=30):
    """POST JSON and return parsed response."""
    payload = json.dumps(body_dict).encode()
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=payload, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        if _is_ssl_error(e):
            _emit_ssl_error()
        raise
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        _emit_error(
            "PARSE_ERROR",
            "API returned invalid JSON.",
            hint="The API may be temporarily unavailable. Retry in a moment.",
            exit_code=EXIT_NETWORK_ERROR,
        )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def authenticate(email, password):
    try:
        result = _http_post(AUTH_ENDPOINT, {"email": email, "password": password})
    except urllib.error.URLError:
        _emit_error(
            "NETWORK", "Network error during authentication.",
            hint="Check your internet connection and try again.",
            exit_code=EXIT_NETWORK_ERROR,
        )

    if result.get("code") != 0:
        _emit_error(
            "AUTH_FAILED", "Authentication failed.",
            hint="Verify PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD are correct.",
            api_code=result.get("code"),
            exit_code=EXIT_AUTH_ERROR,
        )

    api_key = result["data"]
    save_cached_api_key(api_key)
    return api_key


def get_api_key():
    api_key = os.environ.get("PANGOLINFO_API_KEY")
    if api_key:
        save_cached_api_key(api_key)
        return api_key

    api_key = load_cached_api_key()
    if api_key:
        return api_key

    email = os.environ.get("PANGOLINFO_EMAIL")
    password = os.environ.get("PANGOLINFO_PASSWORD")
    if not email or not password:
        _emit_error(
            "MISSING_ENV", "No authentication credentials found.",
            hint="Set PANGOLINFO_API_KEY, or both PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD.",
            exit_code=EXIT_AUTH_ERROR,
        )
    return authenticate(email, password)


def refresh_api_key():
    email = os.environ.get("PANGOLINFO_EMAIL")
    password = os.environ.get("PANGOLINFO_PASSWORD")
    if not email or not password:
        _emit_error(
            "MISSING_ENV", "Cannot refresh API key without credentials.",
            hint="Set PANGOLINFO_EMAIL and PANGOLINFO_PASSWORD environment variables.",
            exit_code=EXIT_AUTH_ERROR,
        )
    return authenticate(email, password)


# ---------------------------------------------------------------------------
# WIPO request builder
# ---------------------------------------------------------------------------
def build_wipo_body(args):
    """Build the WIPO API request body. Uses backend's UPPERCASE JSON keys.

    The backend's SearchWipoRequest accepts both lowercase aliases and the
    canonical UPPERCASE form via @JsonAlias. We send UPPERCASE to be explicit
    and to match server-side logging.
    """
    body = {}

    if args.source:
        body["SOURCE"] = args.source  # already normalized
    if args.irn:
        body["IRN"] = args.irn
    if args.ds:
        body["DS"] = args.ds
    if args.hol:
        body["HOL"] = args.hol
    if args.prod:
        body["PROD"] = args.prod
    if args.lcs:
        body["LCS"] = args.lcs
    if args.status:
        body["STATUS"] = args.status
    if args.record_id:
        body["ID"] = args.record_id
    if args.id_search:
        body["ID_search"] = args.id_search
    if args.rd:
        body["RD"] = args.rd
    if args.ed:
        body["ED"] = args.ed  # silently dropped by backend, kept for forward compat

    body["from"] = args.offset
    body["size"] = args.size

    return body


# ---------------------------------------------------------------------------
# API call with retry
# ---------------------------------------------------------------------------
def call_api(api_key, body, max_retries=3, timeout=120):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Pangolinfo-CLI/3.0",
    }

    for attempt in range(max_retries):
        try:
            result = _http_post(WIPO_ENDPOINT, body, headers=headers, timeout=timeout)
            return result
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode() if e.fp else ""
            except Exception:
                pass

            if e.code == 429:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                _emit_error(
                    "RATE_LIMIT", "Rate limited by API server.",
                    hint="Wait a moment and retry, or reduce request frequency.",
                    exit_code=EXIT_NETWORK_ERROR,
                )

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue

            detail = ""
            if error_body:
                try:
                    err_json = json.loads(error_body)
                    detail = f" Server: {err_json.get('message', error_body[:200])}"
                except (json.JSONDecodeError, ValueError):
                    detail = f" Server: {error_body[:200]}"

            # Map common backend errors to actionable hints
            hint = "Check your request parameters and try again."
            lower_detail = detail.lower()
            if "查询超时" in detail or "timed out" in lower_detail or "timeout" in lower_detail:
                hint = ("Backend hit the 25s query timeout. Add --status, --lcs, "
                        "or --rd \"YYYY\" to narrow the search.")
            elif "source 必填" in detail.lower() or "source 数据集不存在" in detail.lower():
                hint = ("Verify --source is correct. Country codes are auto-normalized "
                        "(US→USID, CN→CNID); HAGUE stays HAGUE.")
            elif "cnid 数据集" in detail.lower():
                hint = ("CNID + fuzzy search requires narrowing. Add --rd \"YYYY\", "
                        "--id, --id-search, --status, or --lcs.")

            _emit_error(
                "API_ERROR", f"HTTP {e.code} from API.{detail}",
                hint=hint,
                exit_code=EXIT_NETWORK_ERROR,
            )
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            _emit_error(
                "NETWORK", "Network error communicating with API.",
                hint="Check your internet connection and try again.",
                exit_code=EXIT_NETWORK_ERROR,
            )

    _emit_error(
        "NETWORK", "API call failed after retries.",
        hint="Check your internet connection and try again.",
        exit_code=EXIT_NETWORK_ERROR,
    )


# ---------------------------------------------------------------------------
# Output extraction
# ---------------------------------------------------------------------------
def extract_wipo_output(result):
    """Transform raw WIPO API response into clean output."""
    data = result.get("data")
    if data is None:
        code = result.get("code")
        if code is not None and code != 0:
            return {
                "success": False,
                "error": {
                    "code": "API_ERROR",
                    "api_code": code,
                    "message": result.get("message", "Unknown API error"),
                    "hint": f"Pangolinfo API error code {code}. Retry or check request.",
                },
            }
        return {
            "success": False,
            "error": {
                "code": "API_ERROR",
                "message": "No data returned from WIPO API.",
                "hint": "Check your search parameters and try again.",
            },
        }

    total = data.get("total", 0)
    hits = data.get("hits", [])

    results = []
    for hit in hits:
        record = {
            "irn": hit.get("IRN", ""),
            "status": hit.get("STATUS", ""),
            "registration_date": hit.get("RD", ""),
            "expiry_date": hit.get("ED", ""),
            "holder": hit.get("HOL", []),
            "product": hit.get("PROD", []) or hit.get("PROD_ZH", []),
            "locarno_class": hit.get("LCS", []),
            "designated_states": hit.get("DS", []),
            "source": hit.get("SOURCE", ""),
            "id": hit.get("ID", ""),
            "doc": hit.get("DOC", ""),
            "dc": hit.get("DC", ""),
        }
        img_data = hit.get("IMG_DATA", [])
        if img_data:
            record["images"] = img_data
        detail_url = hit.get("DETAIL_URL")
        if detail_url:
            record["detail_url"] = detail_url
        detail_data = hit.get("DETAIL_DATA")
        if detail_data:
            record["detail_data"] = detail_data
        results.append(record)

    out = {
        "success": True,
        "total": total,
        "results_count": len(results),
        "results": results,
    }
    # Backend uses total=-1 to mean "not precisely counted" (CNID full glob).
    if total == -1:
        out["total_note"] = "Total not precisely counted (CNID full-glob query)."
    return out


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Pangolinfo WIPO Global Design Database API Client (v3 / OSS+DuckDB)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  wipo.py --source USID --hol "Apple" --status ACT\n'
            '  wipo.py --source CNID --rd 2024 --prod "椅子"\n'
            '  wipo.py --source HAGUE --irn "DM/000298"\n'
            '  wipo.py --source DEID --lcs "23-01" --status ACT\n'
            "  wipo.py --auth-only\n\n"
            "Perf contract:\n"
            "  --source is REQUIRED.\n"
            "  CNID + --hol/--prod also requires --rd or --id/--id-search/--status/--lcs.\n"
            "  Stage 2 large sources (DEID/JPID/USID/KRID/EMID) + fuzzy without narrowing\n"
            "  often hits the 25s backend timeout — add --status/--lcs/--rd.\n"
            "  --ed is silently ignored on all sources; use --rd for date filters.\n"
        ),
    )
    parser.add_argument(
        "--source", required=False,
        help="REQUIRED. Data source: USID, CNID, DEID, JPID, KRID, EMID, "
             "FRID, INID, ITID, ESID, CHID, HAGUE. US→USID, CN→CNID auto-normalized.",
    )
    parser.add_argument("--irn", help="International registration number")
    parser.add_argument("--ds", help="Designated state filter (country code, e.g. US, AL, CN)")
    parser.add_argument("--hol", help="Holder / rights owner name (fuzzy ILIKE %%name%%)")
    parser.add_argument("--prod",
                        help="Product name (fuzzy ILIKE). CNID searches Chinese PROD_ZH.")
    parser.add_argument("--lcs", help="Locarno classification code (e.g. 23-01)")
    parser.add_argument("--status", help="Legal status filter (e.g. ACT for active)")
    parser.add_argument("--id", dest="record_id", help="Exact record ID (e.g. CNID.2024.XXXXX)")
    parser.add_argument("--id-search", dest="id_search",
                        help="ID prefix search (e.g. CNID.2024 — also routes CNID to single partition)")
    parser.add_argument("--rd", help="Registration date filter (YYYY or YYYY-MM-DD)")
    parser.add_argument("--ed", help="Expiration date filter (CURRENTLY IGNORED BY BACKEND)")
    parser.add_argument(
        "--from", dest="offset", type=int, default=0,
        help="Pagination offset, 0-based (default: 0)",
    )
    parser.add_argument(
        "--size", "--num", dest="size", type=int, default=10,
        help="Results per page, 1-1000 (default: 10). --num kept as alias.",
    )
    parser.add_argument("--auth-only", action="store_true", help="Auth check only")
    parser.add_argument("--raw", action="store_true", help="Output raw API response")
    parser.add_argument("--timeout", type=int, default=120,
                        help="HTTP timeout in seconds (default: 120). Backend SQL timeout is 25s.")
    parser.add_argument(
        "--cache-key", action="store_true",
        help="Persist API key to ~/.pangolinfo_api_key. Also: PANGOLINFO_CACHE=1.",
    )

    args = parser.parse_args()

    # Configure caching
    global CACHE_TO_DISK
    CACHE_TO_DISK = bool(args.cache_key) or os.environ.get("PANGOLINFO_CACHE", "").strip().lower() in (
        "1", "true", "yes", "on",
    )

    # Normalize source up front so all downstream checks see USID/CNID/HAGUE/...
    args.source = normalize_source(args.source)

    # Auth-only short-circuit
    if args.auth_only:
        api_key = get_api_key()
        preview = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(json.dumps({
            "success": True,
            "message": "Authentication successful",
            "api_key_preview": preview,
        }, indent=2))
        sys.exit(EXIT_SUCCESS)

    # Validate: at least one search parameter
    has_search_param = any([
        args.irn, args.ds, args.hol, args.prod, args.lcs,
        args.status, args.record_id, args.id_search, args.rd, args.ed,
    ])
    if not has_search_param:
        parser.error(
            "At least one search parameter is required (e.g. --irn, --hol, --prod, "
            "--lcs, --id, --id-search, --rd, --status). --source alone is not enough."
        )

    # Pre-flight perf-contract validation (mirrors backend rules — fails fast)
    validate_perf_contract(args)

    # Authenticate
    api_key = get_api_key()

    # Build request body
    body = build_wipo_body(args)

    # Call API
    result = call_api(api_key, body, timeout=args.timeout)

    if result is None:
        _emit_error(
            "NETWORK", "API call failed after retries.",
            hint="Check your internet connection and try again.",
            exit_code=EXIT_NETWORK_ERROR,
        )

    # Handle token refresh on 1004
    if isinstance(result, dict) and result.get("code") == 1004:
        new_api_key = refresh_api_key()
        result = call_api(new_api_key, body, timeout=args.timeout)
        if result is None:
            _emit_error(
                "NETWORK", "API call failed after token refresh.",
                hint="Check your internet connection and try again.",
                exit_code=EXIT_NETWORK_ERROR,
            )

    # Output
    if args.raw:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        output = extract_wipo_output(result)
        if output.get("success"):
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False), file=sys.stderr)

    # Exit code based on success
    if isinstance(result, dict):
        code = result.get("code")
        if code is not None and code != 0:
            sys.exit(EXIT_API_ERROR)
        if result.get("data") is None:
            sys.exit(EXIT_API_ERROR)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
