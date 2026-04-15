---
name: pangolinfo-wipo
description: >
  WIPO Global Design Database search via Pangolinfo API (industrial design IP lookup).
unlisted: true
metadata:
  openclaw:
    requires:
      env:
        - PANGOLINFO_API_KEY
      notes: "Set PANGOLINFO_API_KEY (recommended). Alternative: set PANGOLINFO_EMAIL + PANGOLINFO_PASSWORD instead (optional, for email/password login). Credentials are NOT cached to disk by default; disk persistence only activates with explicit --cache-key flag or PANGOLINFO_CACHE=1."
---

# Pangolinfo WIPO Skill

Search the WIPO Global Design Database for industrial design registrations via Pangolinfo's WIPO API. Look up designs by international registration number (IRN), holder, product name, Locarno classification, designated state, and more.

## When to Use This Skill

Triggers: WIPO search, industrial design lookup, design patent, international registration, Hague system, Locarno classification, 外观设计, 工业设计, 国际注册, WIPO 查询

Do **not** use this skill for: Amazon product searches, Google SERP, trademark search, utility patent search, or non-WIPO IP databases.

## Prerequisites

- **Python 3.8+** (standard library only -- no `pip install` needed)
- **Pangolinfo account** at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_wipo)

### Environment Variables

Set **one** of:

| Variable | Option | Description |
|----------|--------|-------------|
| `PANGOLINFO_API_KEY` | A (recommended) | API Key -- skips login |
| `PANGOLINFO_EMAIL` + `PANGOLINFO_PASSWORD` | B | Account credentials |

API key resolution order: `PANGOLINFO_API_KEY` env var > cached `~/.pangolinfo_api_key` (if previously cached) > fresh login.

### macOS SSL Fix

If you see error code `SSL_CERT`, run:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```
Or: `pip3 install certifi && export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")`

## Script Execution

The main script is `scripts/pangolinfo.py` relative to this skill directory.

```bash
python3 scripts/pangolinfo.py --irn "000298" --ds AL
```

## Intent-to-Command Mapping

### Search by International Registration Number (IRN)

```bash
python3 scripts/pangolinfo.py --irn "000298" --ds AL
```

### Search by Holder (Rights Owner)

```bash
python3 scripts/pangolinfo.py --hol "Apple" --ds US
```

### Search by Product Name

```bash
python3 scripts/pangolinfo.py --prod "chair" --ds US
```

### Search by Locarno Classification

```bash
python3 scripts/pangolinfo.py --lcs "23-01" --ds AL
```

### Filter by Status (Active Only)

```bash
python3 scripts/pangolinfo.py --irn "000298" --ds AL --status ACT
```

### Paginated Results

```bash
python3 scripts/pangolinfo.py --prod "bottle" --ds US --from 0 --num 20
```

### Combined Search

```bash
python3 scripts/pangolinfo.py --hol "Samsung" --lcs "14-03" --ds US --status ACT
```

### Auth Check (no credits consumed)

```bash
python3 scripts/pangolinfo.py --auth-only
```

## All CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--irn` | string | none | International registration number |
| `--ds` | string | none | Designated state (country code, e.g. `US`, `AL`, `CN`) |
| `--hol` | string | none | Holder / rights owner name |
| `--prod` | string | none | Product name |
| `--lcs` | string | none | Locarno classification code (e.g. `23-01`) |
| `--status` | string | none | Legal status filter (e.g. `ACT` for active) |
| `--id` | string | none | Unique record identifier |
| `--id-search` | string | none | ID variant search |
| `--source` | string | none | Data source filter |
| `--rd` | string | none | Registration date (e.g. `2022-01-01`) |
| `--ed` | string | none | Expiry date filter |
| `--from` | int | `0` | Pagination offset (0-based) |
| `--num` | int | `10` | Results per page |
| `--auth-only` | flag | off | Auth check only (no query, no credits) |
| `--raw` | flag | off | Output raw API response |
| `--timeout` | int | `120` | Request timeout in seconds |
| `--cache-key` | flag | off | Persist API key to `~/.pangolinfo_api_key`. Also: `PANGOLINFO_CACHE=1`. |

## Cost

| Operation | Credits |
|-----------|---------|
| WIPO search request | 2 |

Credits are only consumed on successful requests. Auth checks do not consume credits.

## Output Format

JSON to **stdout** on success, structured error JSON to **stderr** on failure.

### Success Example

```json
{
  "success": true,
  "total": 1,
  "results_count": 1,
  "results": [
    {
      "irn": "000298",
      "status": "ACT",
      "registration_date": "2022-01-24T23:59:59Z",
      "expiry_date": "2026-01-11",
      "holder": ["W-A PROGETTAZIONI S.R.L."],
      "product": ["液体分配设备"],
      "locarno_class": ["23-01"],
      "designated_states": ["AL"],
      "source": "ALID",
      "id": "ALID.AL/I/2021/000001",
      "images": [
        {
          "url": "https://scrapeapi.pangolinfo.com/.../ALI2021000001-0001.1-th.jpg",
          "filename": "ALI2021000001-0001.1-th.jpg"
        }
      ]
    }
  ]
}
```

### Error Example (stderr)

```json
{
  "success": false,
  "error": {
    "code": "API_ERROR",
    "message": "The WIPO API returned an error.",
    "hint": "Check your search parameters and try again."
  }
}
```

## Response Presentation

1. **Use natural language** -- never dump raw JSON.
2. **Match the user's language.**
3. **Present results as structured cards**: IRN, holder, product, status, registration/expiry dates, Locarno class, designated states.
4. **Show design images** when available (provide image URLs).
5. **On error**, explain the issue using the `hint` field.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API error |
| 2 | Usage error (bad arguments) |
| 3 | Network error |
| 4 | Authentication error |

## Error Reference

### Script Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `MISSING_ENV` | No credentials | Set `PANGOLINFO_API_KEY`, or `PANGOLINFO_EMAIL` + `PANGOLINFO_PASSWORD` |
| `AUTH_FAILED` | Wrong credentials | Verify email and password |
| `RATE_LIMIT` | Too many requests | Wait and retry |
| `NETWORK` | Connection issue | Check internet / firewall |
| `SSL_CERT` | Certificate error | See macOS SSL Fix above |
| `API_ERROR` | Pangolinfo API error | Check parameters and `hint` |
| `PARSE_ERROR` | Invalid API response | Retry; may be transient |

## First-Time Setup

See [references/setup-guide.md](references/setup-guide.md) for detailed first-time setup instructions.

Quick start:
```bash
export PANGOLINFO_API_KEY="your-api-key"
python3 scripts/pangolinfo.py --auth-only
```

## Important Notes for AI Agents

1. **Run `--auth-only` first** if unsure about credentials.
2. **At least one search parameter is required** (`--irn`, `--hol`, `--prod`, `--lcs`, or `--id`).
3. **`--ds` (designated state) is required** for all searches.
4. **Never expose raw JSON** to the user.
5. **Respond in the user's language.**
6. **Mention credit cost** (2 credits/request) when running multiple searches.
7. **Do not log API keys, passwords, or cookies.**
8. **Show design images** when the user is looking for visual references.
9. **Use `--status ACT`** to filter for active/valid designs only when the user wants current registrations.
10. **Paginate large results** -- default is 10 per page; use `--from` and `--num` to navigate.
