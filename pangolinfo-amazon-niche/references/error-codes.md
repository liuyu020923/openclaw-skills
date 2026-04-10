# Error Codes and Troubleshooting

Covers the error codes returned by the Amazon 利基数据 (niche data)
endpoints under `/api/v1/amzscope/*`.

## Error Code Reference

| Code | Meaning | Resolution |
|------|---------|------------|
| 0 | Success | No action needed |
| 1002 | Invalid Parameter | Check required fields for the specific API (see below) |
| 1004 | Invalid or expired token | Re-authenticate. The script does this automatically. |
| 2001 | Insufficient credits | Top up credits at pangolinfo.com |
| 2005 | No active plan | Activate a subscription at pangolinfo.com |
| 2007 | Account expired | Renew subscription at pangolinfo.com |
| 2009 | Usage limit exceeded | Wait for quota reset or upgrade plan |
| 3003 | User not logged in | Provide `Authorization: Bearer <token>` header |
| 4002 | IP denied | Request is from an IP not on the allowlist |
| 4029 | Too many requests | Back off and retry with exponential delay |
| 5000 | System error | Retry; if persistent, contact support |
| 5001 | System busy | Retry after a short delay |
| 9100 | AmzScope service disabled | Service temporarily disabled; retry later |
| 9101 | AmzScope data source unavailable | Upstream data source down; retry later |
| 9102 | AmzScope quota exceeded | Provider-level quota hit; contact support |

## Per-API required fields

| API | Required fields | On violation |
|-----|-----------------|--------------|
| `POST /categories/children` | — | none |
| `POST /categories/search` | `keyword` | `1002 keyword is required` |
| `POST /categories/paths` | `categoryIds` (non-empty array) | `1002 categoryIds is required` |
| `POST /categories/filter` | `timeRange`, `sampleScope` (also `marketplaceId` per docs) | `1002 timeRange and sampleScope are required` |
| `POST /niches/filter` | `marketplaceId` | `1002` from upstream if missing |

## Page size cap

`POST /categories/filter` and `POST /niches/filter` enforce
`pageSize <= 10`. Exceeding the cap returns:

```
1002 Invalid Parameter: pageSize must be less than 10
```

## Authentication

### Token Lifecycle

- Tokens are **permanent** -- they do not expire on their own.
- Error code `1004` indicates the token needs to be refreshed.
- The script caches tokens at `~/.pangolin_token`.

### Token Resolution Order

1. `PANGOLIN_TOKEN` environment variable
2. Cached token at `~/.pangolin_token`
3. Fresh login using `PANGOLIN_EMAIL` + `PANGOLIN_PASSWORD`

### Auth Endpoint

```
POST https://scrapeapi.pangolinfo.com/api/v1/auth
Body: {"email": "<email>", "password": "<password>"}
Response: {"code": 0, "message": "ok", "data": "<token>"}
```

## Credit Management

| API | Credits per request |
|-----|---------------------|
| Category Tree (`/categories/children`) | 2 |
| Search Categories (`/categories/search`) | 2 |
| Batch Category Paths (`/categories/paths`) | 2 |
| Category Filter (`/categories/filter`) | 5 |
| Niche Filter (`/niches/filter`) | 10 |

- Empty-result responses are **not** charged.
- Failed requests (non-zero code) are not charged.
- Check your credit balance at [pangolinfo.com](https://www.pangolinfo.com).

## Common Issues

**"No authentication credentials" error**
Set environment variables: `export PANGOLIN_EMAIL=... PANGOLIN_PASSWORD=...`
or `export PANGOLIN_TOKEN=...`.

**Empty `items` array**
Filters may be too narrow. Try loosening `*Min`/`*Max` bounds, removing
tier/level filters, or expanding `timeRange`.

**Timeout or network errors**
The script retries 3 times with exponential backoff for transient
network errors. 4xx responses are not retried.

**`9101 Data source temporarily unavailable`**
Upstream niche data provider is temporarily down. Retry later; this is
unrelated to your account state.
