---
name: pangolinfo-amazon-niche
description: >
  Programmatic access to Pangolinfo Amazon 利基 (niche) data APIs:
  browse the Amazon category tree, search categories, batch-resolve
  category paths, and filter categories or niche markets by business
  metrics (sales, search volume, returns, trends, etc.). Use when you
  need structured niche/category intelligence (JSON) for pipelines or
  agents. Requires PANGOLIN_TOKEN or PANGOLIN_EMAIL + PANGOLIN_PASSWORD.
homepage: https://www.pangolinfo.com
metadata:
  openclaw:
    emoji: "📊"
    os: ["darwin", "linux"]
    requires:
      env: ["PANGOLIN_TOKEN"]
      notes: "Auth: set PANGOLIN_TOKEN (recommended) OR set PANGOLIN_EMAIL + PANGOLIN_PASSWORD"
---

# Pangolinfo Amazon Niche Data

Query Amazon category and niche intelligence via **Pangolinfo** APIs.
Covers 5 endpoints under `/api/v1/amzscope/*`:

| # | API | Endpoint | Credits |
|---|-----|----------|---------|
| 1 | Category Tree (browseCategoryTreeAPI) | `POST /categories/children` | 2 |
| 2 | Search Categories (searchCategoriesAPI) | `POST /categories/search` | 2 |
| 3 | Batch Category Paths (batchCategoryPathsAPI) | `POST /categories/paths` | 2 |
| 4 | Category Filter (categoryFilterAPI) | `POST /categories/filter` | 5 |
| 5 | Niche Filter (nicheFilterAPI) | `POST /niches/filter` | 10 |

All endpoints live on `https://scrapeapi.pangolinfo.com` and share the
same Bearer-token auth as the other Pangolinfo skills.

## Prerequisites

- **Python 3.6+** (standard library only)
- A **Pangolinfo account**: https://www.pangolinfo.com
- Auth env vars (choose one):
  - `PANGOLIN_TOKEN` (recommended)
  - or `PANGOLIN_EMAIL` + `PANGOLIN_PASSWORD`

```bash
export PANGOLIN_TOKEN="..."
# or
export PANGOLIN_EMAIL="..."
export PANGOLIN_PASSWORD="..."
```

## Minimal examples

Browse top-level category tree:

```bash
python3 scripts/pangolinfo.py --api category-tree
```

Browse children of a specific node:

```bash
python3 scripts/pangolinfo.py --api category-tree \
  --parent-path "2619526011"
```

Search categories by keyword (EN or CN):

```bash
python3 scripts/pangolinfo.py --api category-search \
  --keyword "headphones"
```

Batch resolve category paths by IDs:

```bash
python3 scripts/pangolinfo.py --api category-paths \
  --category-ids "2619526011,172282"
```

Filter categories by business metrics:

```bash
python3 scripts/pangolinfo.py --api category-filter \
  --marketplace-id US \
  --time-range l7d \
  --sample-scope all_asin \
  --category-id 979832011
```

Filter niches by business metrics:

```bash
python3 scripts/pangolinfo.py --api niche-filter \
  --marketplace-id US \
  --niche-title "yoga mat"
```

Pass arbitrary extra filters (any field from the API reference) via
`--extra` (repeatable, `key=value`, values are JSON-parsed):

```bash
python3 scripts/pangolinfo.py --api category-filter \
  --marketplace-id US --time-range l30d --sample-scope all_asin \
  --extra 'buyBoxPriceAvgMin=1000' \
  --extra 'buyBoxPriceTiers=["mainstream","premium"]' \
  --extra 'sortField=unitSoldSum' \
  --extra 'sortOrder=desc'
```

## Usage

```
--api API              one of: category-tree, category-search, category-paths,
                       category-filter, niche-filter (required)

# Pagination (all APIs support these; filter APIs cap size at 10)
--page N               1-based page number
--size N               items per page (max 10 for category-filter / niche-filter)

# category-tree
--parent-path PATH     e.g. "2619526011" or "2619526011/18116197011"

# category-search
--keyword WORD         required; matches EN and CN names

# category-paths
--category-ids LIST    required; comma-separated or JSON array of IDs

# category-filter
--marketplace-id CODE  required; e.g. US, UK, DE
--time-range RANGE     required; e.g. l7d, l30d, l90d
--sample-scope SCOPE   required; e.g. all_asin
--category-id ID       optional; return single-category detail

# niche-filter
--marketplace-id CODE  required
--niche-id ID          optional; detailed report for one niche
--niche-title TEXT     optional; keyword match on niche title

# Shared
--extra key=value      repeatable; any extra request field (JSON-parsed)
--auth-only            authenticate and show token info
--raw                  output raw API response instead of extracted data
```

## Output

The script prints structured JSON to stdout. For successful calls it
returns:

```json
{
  "success": true,
  "api": "category-search",
  "items": [ ... ],          // the data array
  "total": 42,               // when returned by upstream
  "page": 1,
  "size": 10,
  "totalPages": 5
}
```

Errors surface as:

```json
{
  "success": false,
  "error_code": 1002,
  "message": "Invalid Parameter: keyword is required"
}
```

Use `--raw` to inspect the full upstream envelope when debugging.

## Links

- Homepage: https://www.pangolinfo.com
- Docs index: https://docs.pangolinfo.com/cn-index

## References

- [references/amazon-niche-api.md](references/amazon-niche-api.md)
- [references/error-codes.md](references/error-codes.md)
