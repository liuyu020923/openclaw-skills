---
name: pangolinfo-ai-serp
description: >
  Programmatic Google SERP + AI Overview extraction (including citations/sources).
metadata:
  openclaw:
    requires:
      env:
        - PANGOLINFO_API_KEY
        - PANGOLINFO_EMAIL
        - PANGOLINFO_PASSWORD
      notes: "Auth: set PANGOLINFO_API_KEY (recommended) OR PANGOLINFO_EMAIL + PANGOLINFO_PASSWORD."
---

# Pangolinfo AI SERP Skill

Google AI Mode search and standard SERP extraction with AI Overview and citations via Pangolinfo APIs.

## When to Use This Skill

Triggers: Google SERP scraping, AI Overview extraction, AI Mode search, Google citation extraction, 抓Google SERP, 谷歌AI概览, 引用来源提取

Do **not** use this skill for: Amazon product searches, Google Trends, Google Maps, or non-Google search engines.

## Prerequisites

- **Python 3.8+** (standard library only -- no `pip install` needed)
- **Pangolinfo account** at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_serp)

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
python3 scripts/pangolinfo.py --q "your query"
```

## Intent-to-Command Mapping

### AI Mode Search (default)

AI-generated answers with references. Default mode, costs **2 credits**.

```bash
python3 scripts/pangolinfo.py --q "what is quantum computing"
```

### Standard SERP

Traditional Google search results + optional AI Overview. Costs **2 credits**.

```bash
python3 scripts/pangolinfo.py --q "best databases 2025" --mode serp
```

### SERP Plus (cheaper)

Same as SERP but costs only **1 credit**. Uses the `googleSearchPlus` parser.

```bash
python3 scripts/pangolinfo.py --q "best databases 2025" --mode serp-plus
```

### SERP with Screenshot

```bash
python3 scripts/pangolinfo.py --q "best databases 2025" --mode serp --screenshot
```

### SERP with Region

```bash
python3 scripts/pangolinfo.py --q "best databases 2025" --mode serp --region us
```

### Multi-Turn Dialogue (AI Mode only)

```bash
python3 scripts/pangolinfo.py --q "kubernetes" --follow-up "how to deploy" --follow-up "monitoring tools"
```

### Auth Check (no credits consumed)

```bash
python3 scripts/pangolinfo.py --auth-only
```

## All CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--q` | string | *required* | Search query |
| `--mode` | `ai-mode` \| `serp` \| `serp-plus` | `ai-mode` | API mode |
| `--screenshot` | flag | off | Capture page screenshot |
| `--follow-up` | string (repeatable) | none | Follow-up question (ai-mode only) |
| `--num` | int (1-100) | `10` | Number of results |
| `--region` | string | none | Geographic region (SERP/SERP-Plus only). See supported regions below. |
| `--auth-only` | flag | off | Auth check only (no query, no credits) |
| `--raw` | flag | off | Output raw API response |
| `--timeout` | int | `120` | Request timeout in seconds |
| `--cache-key` | flag | off | Persist API key to `~/.pangolinfo_api_key`. Also settable via `PANGOLINFO_CACHE=1`. |

## Supported Regions

| Code | Language | Code | Language |
|------|----------|------|----------|
| `us` | English | `cn` | Chinese |
| `uk` | English | `dk` | Danish |
| `au` | English | `no` | Norwegian |
| `ca` | English | `se` | Swedish |
| `nz` | English | `nl` | Dutch |
| `de` | German | `pt` | Portuguese |
| `fr` | French | `es` | Spanish |
| `it` | Italian | `jp` | Japanese |

## Cost

| Mode | Credits | Parser |
|------|---------|--------|
| AI Mode | 2 | `googleAiSearch` |
| SERP | 2 | `googleSearch` |
| SERP Plus | 1 | `googleSearchPlus` |

Credits are only consumed on successful requests (API code 0). Auth checks do not consume credits.

## Output Format

JSON to **stdout** on success, structured error JSON to **stderr** on failure.

### Success Example (AI Mode)

```json
{
  "success": true,
  "task_id": "1768988520324-766a695d93b57aad",
  "results_num": 1,
  "ai_overview_count": 1,
  "ai_overview": [
    {
      "content": ["Quantum computing uses quantum bits (qubits)..."],
      "references": [
        {
          "title": "Quantum Computing - Wikipedia",
          "url": "https://en.wikipedia.org/wiki/Quantum_computing",
          "domain": "Wikipedia"
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
    "message": "The search API returned an error.",
    "api_code": 2001,
    "hint": "Insufficient credits. Top up at https://pangolinfo.com/?referrer=clawhub_serp"
  }
}
```

## Response Presentation

1. **Use natural language** -- never dump raw JSON.
2. **Match the user's language.**
3. **Summarize AI overview first**, then list organic results with URLs.
4. **On error**, explain the issue using the `hint` field.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API error (non-zero code from Pangolinfo) |
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
| `API_ERROR` | Pangolinfo API error | Check `api_code` and `hint` |
| `PARSE_ERROR` | Invalid API response | Retry; may be transient |

### Pangolinfo API Error Codes

| API Code | Meaning | Resolution |
|----------|---------|------------|
| 1004 | Invalid token | Auto-retried by script. If persistent, re-auth. |
| 1009 | Invalid parser name | Check `--mode` value. |
| 2001 | Insufficient credits | Top up at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_serp) |
| 2005 | No active plan | Subscribe at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_serp) |
| 2007 | Account expired | Renew at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_serp) |
| 2009 | Usage limit reached | Wait for next billing cycle or contact support |
| 2010 | Bill day not configured | Contact support |
| 4029 | Rate limited (server) | Reduce request frequency |
| 10000 | Task execution failed | Retry. Check query format. |
| 10001 | Task execution failed | Retry. Likely transient. |

## First-Time Setup

See [references/setup-guide.md](references/setup-guide.md) for detailed first-time setup instructions.

Quick start:
```bash
export PANGOLINFO_API_KEY="your-api-key"
python3 scripts/pangolinfo.py --auth-only
```

## Important Notes for AI Agents

1. **Run `--auth-only` first** if unsure about credentials.
2. **Default to `ai-mode`** unless user explicitly asks for standard search.
3. **Use `serp-plus`** when user wants cheaper SERP results and doesn't need the premium parser.
4. **Never expose raw JSON** to the user.
5. **Respond in the user's language.**
6. **Keep follow-ups to 5 or fewer.**
7. **Do not log API keys, passwords, or cookies.**
8. **Mention credit cost** when running multiple searches.
9. **`--screenshot` is optional** -- only when user wants visual results.
10. **`--follow-up` is ai-mode only.**
11. **`--region` is SERP/SERP-Plus only.**

## Output Schema

See [references/output-schema.md](references/output-schema.md) for the complete JSON output schema.
