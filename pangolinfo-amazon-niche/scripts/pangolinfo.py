#!/usr/bin/env python3
"""Pangolinfo Amazon Niche Data Client

Zero-dependency Python client for Pangolinfo's Amazon 利基 (niche) data APIs.
Covers all 5 endpoints under /api/v1/amzscope/*:

    category-tree     POST /api/v1/amzscope/categories/children
    category-search   POST /api/v1/amzscope/categories/search
    category-paths    POST /api/v1/amzscope/categories/paths
    category-filter   POST /api/v1/amzscope/categories/filter
    niche-filter      POST /api/v1/amzscope/niches/filter

Environment:
    PANGOLIN_TOKEN    - Bearer token (skips login)
    PANGOLIN_EMAIL    - Account email (for login)
    PANGOLIN_PASSWORD - Account password (for login)
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://scrapeapi.pangolinfo.com"
AUTH_ENDPOINT = f"{API_BASE}/api/v1/auth"
AMZSCOPE_BASE = f"{API_BASE}/api/v1/amzscope"
TOKEN_CACHE_PATH = Path.home() / ".pangolin_token"

EXIT_SUCCESS = 0
EXIT_API_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_NETWORK_ERROR = 3
EXIT_AUTH_ERROR = 4

# API name -> (path, label)
API_ROUTES = {
    "category-tree":   ("/categories/children", "browseCategoryTreeAPI"),
    "category-search": ("/categories/search",   "searchCategoriesAPI"),
    "category-paths":  ("/categories/paths",    "batchCategoryPathsAPI"),
    "category-filter": ("/categories/filter",   "categoryFilterAPI"),
    "niche-filter":    ("/niches/filter",       "nicheFilterAPI"),
}


# ------------------------- auth -------------------------

def load_cached_token():
    if TOKEN_CACHE_PATH.exists():
        token = TOKEN_CACHE_PATH.read_text().strip()
        if token:
            return token
    return None


def save_cached_token(token):
    TOKEN_CACHE_PATH.write_text(token)
    TOKEN_CACHE_PATH.chmod(0o600)


def authenticate(email, password):
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        AUTH_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(json.dumps({"error": f"Network error during auth: {e}"}), file=sys.stderr)
        sys.exit(EXIT_NETWORK_ERROR)

    if result.get("code") != 0:
        print(
            json.dumps(
                {
                    "error": "Authentication failed",
                    "code": result.get("code"),
                    "message": result.get("message"),
                }
            ),
            file=sys.stderr,
        )
        sys.exit(EXIT_AUTH_ERROR)

    token = result["data"]
    save_cached_token(token)
    return token


def get_token():
    token = os.environ.get("PANGOLIN_TOKEN")
    if token:
        return token

    token = load_cached_token()
    if token:
        return token

    email = os.environ.get("PANGOLIN_EMAIL")
    password = os.environ.get("PANGOLIN_PASSWORD")
    if not email or not password:
        print(
            json.dumps(
                {
                    "error": "No authentication credentials. Set PANGOLIN_TOKEN, or both PANGOLIN_EMAIL and PANGOLIN_PASSWORD.",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(EXIT_AUTH_ERROR)

    return authenticate(email, password)


def refresh_token():
    email = os.environ.get("PANGOLIN_EMAIL")
    password = os.environ.get("PANGOLIN_PASSWORD")
    if not email or not password:
        print(
            json.dumps(
                {
                    "error": "Cannot refresh token: PANGOLIN_EMAIL and PANGOLIN_PASSWORD required.",
                }
            ),
            file=sys.stderr,
        )
        sys.exit(EXIT_AUTH_ERROR)
    return authenticate(email, password)


# ------------------------- request bodies -------------------------

def _parse_category_ids(raw):
    """Accept either a JSON array ('["a","b"]') or a comma-separated list."""
    raw = raw.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid --category-ids JSON: {e}"}), file=sys.stderr)
            sys.exit(EXIT_USAGE_ERROR)
        if not isinstance(parsed, list):
            print(json.dumps({"error": "--category-ids JSON must be an array"}), file=sys.stderr)
            sys.exit(EXIT_USAGE_ERROR)
        return [str(x) for x in parsed]
    return [part.strip() for part in raw.split(",") if part.strip()]


def _apply_extras(body, extras):
    """Merge --extra key=value pairs into body. Values are JSON-parsed when possible."""
    for item in extras or []:
        if "=" not in item:
            print(
                json.dumps({"error": f"--extra must be key=value, got: {item}"}),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE_ERROR)
        key, _, value = item.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            print(json.dumps({"error": f"--extra missing key: {item}"}), file=sys.stderr)
            sys.exit(EXIT_USAGE_ERROR)
        try:
            body[key] = json.loads(value)
        except json.JSONDecodeError:
            body[key] = value
    return body


def _apply_pagination(body, page, size):
    if page is not None:
        body["page"] = page
    if size is not None:
        body["size"] = size


def build_body(args):
    body = {}

    if args.api == "category-tree":
        if args.parent_path:
            body["parentBrowseNodeIdPath"] = args.parent_path
        _apply_pagination(body, args.page, args.size)

    elif args.api == "category-search":
        if not args.keyword:
            print(
                json.dumps({"error": "category-search requires --keyword"}),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE_ERROR)
        body["keyword"] = args.keyword
        _apply_pagination(body, args.page, args.size)

    elif args.api == "category-paths":
        if not args.category_ids:
            print(
                json.dumps({"error": "category-paths requires --category-ids"}),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE_ERROR)
        body["categoryIds"] = _parse_category_ids(args.category_ids)

    elif args.api == "category-filter":
        missing = [
            name
            for name, val in (
                ("--marketplace-id", args.marketplace_id),
                ("--time-range", args.time_range),
                ("--sample-scope", args.sample_scope),
            )
            if not val
        ]
        if missing:
            print(
                json.dumps(
                    {"error": f"category-filter requires: {', '.join(missing)}"}
                ),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE_ERROR)
        body["marketplaceId"] = args.marketplace_id
        body["timeRange"] = args.time_range
        body["sampleScope"] = args.sample_scope
        if args.category_id:
            body["categoryId"] = args.category_id
        _apply_pagination(body, args.page, args.size)

    elif args.api == "niche-filter":
        if not args.marketplace_id:
            print(
                json.dumps({"error": "niche-filter requires --marketplace-id"}),
                file=sys.stderr,
            )
            sys.exit(EXIT_USAGE_ERROR)
        body["marketplaceId"] = args.marketplace_id
        if args.niche_id:
            body["nicheId"] = args.niche_id
        if args.niche_title:
            body["nicheTitle"] = args.niche_title
        _apply_pagination(body, args.page, args.size)

    _apply_extras(body, args.extra)
    return body


# ------------------------- HTTP -------------------------

def call_api(token, body, endpoint, max_retries=3):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
    }
    payload = json.dumps(body).encode()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            # 4xx errors are rarely fixed by retries
            if 400 <= e.code < 500 or attempt == max_retries - 1:
                try:
                    parsed = json.loads(error_body) if error_body else {}
                    if isinstance(parsed, dict) and "code" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
                print(
                    json.dumps({"error": f"HTTP {e.code}: {error_body}"}),
                    file=sys.stderr,
                )
                sys.exit(EXIT_NETWORK_ERROR)
            time.sleep(2**attempt)
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            print(json.dumps({"error": f"Network error: {e}"}), file=sys.stderr)
            sys.exit(EXIT_NETWORK_ERROR)

    return None


def handle_response(result, body, endpoint):
    if result.get("code") == 1004:
        new_token = refresh_token()
        return call_api(new_token, body, endpoint)
    return result


# ------------------------- output shaping -------------------------

def extract_output(result, api_name):
    code = result.get("code")
    if code != 0:
        return {
            "success": False,
            "api": api_name,
            "error_code": code,
            "message": result.get("message", "Unknown error"),
        }

    data = result.get("data") or {}
    output = {"success": True, "api": api_name}

    # Upstream shapes observed:
    #   data: { items: { data: [...], total, page, size, totalPages } }   # most APIs
    #   data: { items: [...] }                                            # category-paths
    items_wrapper = data.get("items")
    if isinstance(items_wrapper, dict):
        output["items"] = items_wrapper.get("data", [])
        for key in ("total", "page", "size", "totalPages"):
            if key in items_wrapper:
                output[key] = items_wrapper[key]
    elif isinstance(items_wrapper, list):
        output["items"] = items_wrapper
    else:
        # Fallback: pass whole data through
        output["data"] = data

    if isinstance(output.get("items"), list):
        output["results_count"] = len(output["items"])

    return output


# ------------------------- CLI -------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Pangolinfo Amazon Niche Data Client",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        choices=sorted(API_ROUTES.keys()),
        help="Which niche API to call",
    )

    # pagination (shared)
    parser.add_argument("--page", type=int, help="1-based page number")
    parser.add_argument("--size", type=int, help="items per page (max 10 for filter APIs)")

    # category-tree
    parser.add_argument(
        "--parent-path",
        help="category-tree: parent browseNodeIdPath, e.g. '2619526011' or '2619526011/18116197011'",
    )

    # category-search
    parser.add_argument("--keyword", help="category-search: keyword (EN or CN)")

    # category-paths
    parser.add_argument(
        "--category-ids",
        help="category-paths: comma-separated IDs or JSON array, e.g. '2619526011,172282'",
    )

    # category-filter
    parser.add_argument("--marketplace-id", help="e.g. US, UK, DE")
    parser.add_argument("--time-range", help="e.g. l7d, l30d, l90d")
    parser.add_argument("--sample-scope", help="e.g. all_asin")
    parser.add_argument("--category-id", help="category-filter: single-category detail")

    # niche-filter
    parser.add_argument("--niche-id", help="niche-filter: specific niche ID")
    parser.add_argument("--niche-title", help="niche-filter: keyword match on title")

    # free-form extras
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        help="extra request field as key=value (JSON-parsed); repeatable",
    )

    parser.add_argument("--auth-only", action="store_true", help="authenticate and print token info")
    parser.add_argument("--raw", action="store_true", help="output raw API response")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    token = get_token()

    if args.auth_only:
        print(
            json.dumps(
                {
                    "success": True,
                    "message": "Authentication successful",
                    "token_preview": f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***",
                },
                indent=2,
            )
        )
        sys.exit(EXIT_SUCCESS)

    if not args.api:
        parser.error("--api is required (unless --auth-only)")

    path, label = API_ROUTES[args.api]
    endpoint = f"{AMZSCOPE_BASE}{path}"

    body = build_body(args)

    result = call_api(token, body, endpoint)
    if result is None:
        print(json.dumps({"error": "API call failed after retries"}), file=sys.stderr)
        sys.exit(EXIT_NETWORK_ERROR)

    result = handle_response(result, body, endpoint)

    if args.raw:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        output = extract_output(result, label)
        print(json.dumps(output, indent=2, ensure_ascii=False))

    if result.get("code") != 0:
        sys.exit(EXIT_API_ERROR)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
