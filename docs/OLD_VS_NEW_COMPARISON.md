# Old vs New: Dashboard Scraper Comparison

## Side-by-Side Comparison

| Feature | Old (dashboard-scraper) | New (augment-to-copilot-metrics) |
|---------|------------------------|----------------------------------|
| **Authentication** | Session cookies (browser) | API tokens (service account) |
| **Session Duration** | ~1 hour | Permanent (until revoked) |
| **Setup Complexity** | 7 steps, DevTools required | 3 steps, web UI only |
| **Re-auth Frequency** | Every hour | Never |
| **API Type** | Dashboard scraping | Official Analytics API v0 |
| **API Documentation** | None (reverse engineered) | Full documentation |
| **API Stability** | Fragile (UI changes break it) | Stable (versioned API) |
| **Date Format** | JSON-encoded objects | Simple YYYY-MM-DD |
| **Pagination** | None (assumes small datasets) | Cursor-based pagination |
| **Automation Ready** | ❌ Breaks on cookie expiry | ✅ Perfect for cron/CI |
| **Error Messages** | Generic HTTP errors | Structured error responses |
| **New Metrics** | None | Tool calls, editor/language |
| **Service Accounts** | Not supported | Fully supported |

## Setup Process Comparison

### Old Approach (Cookie-Based)

```bash
# Step 1: Install
pip install -e .

# Step 2: Configure
cp .env.example .env
# Edit .env with dashboard URL

# Step 3: Open browser
# Navigate to dashboard

# Step 4: Login
# Enter credentials

# Step 5: Open DevTools
# Press F12 or Cmd+Option+I

# Step 6: Find cookie
# Application → Cookies → Find _session

# Step 7: Copy cookie value
# Must be URL-decoded

# Step 8: Run auth setup
python -m dashboard_scraper --auth

# Step 9: Paste cookie
# Paste the decoded cookie value

# Step 10: Run scraper
python -m dashboard_scraper --last-28-days

# Step 11: Re-authenticate (1 hour later)
# Repeat steps 3-10 when cookie expires
```

**Total Time**: 15-20 minutes (first time), 5-10 minutes (each re-auth)
**Pain Points**: DevTools, URL decoding, hourly re-auth

---

### New Approach (API Token)

```bash
# Step 1: Install
pip install augment-to-copilot-metrics

# Step 2: Get API token (one-time)
# Visit: app.augmentcode.com/settings/service-accounts
# Click "Create Service Account"
# Click "Create Token"
# Copy token

# Step 3: Configure and run
export AUGMENT_API_TOKEN="your-token-here"
export ENTERPRISE_ID="your-enterprise-id"
augment-metrics --last-28-days
```

**Total Time**: 3-5 minutes (one-time setup)
**Pain Points**: None! 🎉

---

## API Endpoint Comparison

### Old Endpoints (Dashboard Scraping)

| Endpoint | Method | Auth | Pagination | Date Format |
|----------|--------|------|------------|-------------|
| `/api/user-feature-stats` | GET | Cookie | None | `{"year":2025,"month":1,"day":15}` |
| `/api/tenant-feature-stats` | GET | Cookie | None | `{"year":2025,"month":1,"day":15}` |
| `/api/tenant-monthly-active-users` | GET | Cookie | None | `{"year":2025,"month":1,"day":15}` |

**Issues**: Undocumented, fragile, no pagination

---

### New Endpoints (Analytics API)

| Endpoint | Method | Auth | Pagination | Date Format |
|----------|--------|------|------------|-------------|
| `/analytics/v0/user-activity` | GET | Bearer | Cursor | `2025-01-15` |
| `/analytics/v0/daily-usage` | GET | Bearer | None | `2025-01-15` |
| `/analytics/v0/dau-count` | GET | Bearer | None | `2025-01-15` |
| `/analytics/v0/daily-user-activity-by-editor-language` | GET | Bearer | Cursor | `2025-01-15` |

**Benefits**: Documented, stable, paginated, simple

---

## Summary

| Metric | Old | New | Improvement |
|--------|-----|-----|-------------|
| Setup Time | 15-20 min | 3-5 min | **75% faster** |
| Re-auth Frequency | Hourly | Never | **∞% better** |
| Steps to Run | 11 | 3 | **73% fewer** |
| API Stability | Low | High | **Much better** |
| Automation Ready | No | Yes | **Game changer** |
| New Metrics | 0 | 2+ | **More insights** |

**Bottom Line**: The new tool is simpler, more reliable, and better for automation. 🚀
