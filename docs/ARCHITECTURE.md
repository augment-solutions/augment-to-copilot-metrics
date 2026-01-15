# Architecture Documentation

## Overview

The Augment Analytics to Copilot Metrics Converter is a Python tool that extracts usage metrics from Augment's Analytics API and converts them to GitHub Copilot Metrics API format.

## Design Principles

### 1. **Simplicity First**
- Minimal configuration required
- Clear, actionable error messages
- Sensible defaults for all settings

### 2. **Reliability**
- Stable API token authentication (no expiration)
- Retry logic with exponential backoff
- Comprehensive error handling

### 3. **Automation-Friendly**
- Perfect for cron jobs and CI/CD
- No interactive prompts during normal operation
- Exit codes for scripting

### 4. **Maintainability**
- Modular architecture
- Type hints throughout
- Comprehensive test coverage

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                      (main.py)                               │
│  - Argument parsing                                          │
│  - User interaction                                          │
│  - Orchestration                                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                       │
│                      (config.py)                             │
│  - Environment variables                                     │
│  - Settings validation                                       │
│  - Defaults management                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Authentication Layer                       │
│                   (token_auth.py)                            │
│  - API token storage                                         │
│  - Token validation                                          │
│  - Interactive setup                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Client Layer                       │
│                       (http.py)                              │
│  - Bearer token authentication                               │
│  - Retry logic with exponential backoff                      │
│  - Request/response logging                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Analytics API Client                       │
│                 (analytics_client.py)                        │
│  - /analytics/v0/user-activity                               │
│  - /analytics/v0/daily-usage                                 │
│  - /analytics/v0/dau-count                                   │
│  - /analytics/v0/daily-user-activity-by-editor-language      │
│  - Cursor-based pagination                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Transformation Layer                   │
│              (copilot_converter.py)                          │
│  - Field mapping (Augment → Copilot)                         │
│  - Schema validation                                         │
│  - Data normalization                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Export Layer                            │
│         (export.py, copilot_aggregator.py)                   │
│  - CSV export                                                │
│  - JSON export (daily)                                       │
│  - JSON aggregation (28-day)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### CLI Layer (`main.py`)

**Responsibilities:**
- Parse command-line arguments
- Validate user input
- Orchestrate the data pipeline
- Handle user-facing errors

**Key Functions:**
- `main()` - Entry point
- `parse_args()` - Argument parsing
- `run_export()` - Execute export workflow

### Configuration Layer (`config.py`)

**Responsibilities:**
- Load environment variables
- Validate configuration
- Provide defaults
- Type-safe settings access

**Key Classes:**
- `Settings` - Pydantic settings model

**Configuration Sources (priority order):**
1. Environment variables
2. `.env` file
3. Default values

### Authentication Layer (`token_auth.py`)

**Responsibilities:**
- Store API tokens securely
- Validate token format
- Interactive token setup
- Token refresh (if needed)

**Key Classes:**
- `TokenAuth` - Token management

**Security Considerations:**
- Tokens stored in `~/.augment/credentials` (user-only permissions)
- Never logged or printed
- Validated before use

### HTTP Client Layer (`http.py`)

**Responsibilities:**
- Make HTTP requests with Bearer auth
- Retry failed requests
- Log requests/responses
- Handle rate limiting

**Key Classes:**
- `HTTPClient` - HTTP client with retry logic

**Retry Strategy:**
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Max retries: 5
- Retry on: 429, 500, 502, 503, 504

### Analytics API Client (`analytics_client.py`)

**Responsibilities:**
- Call Analytics API endpoints
- Handle pagination
- Parse responses
- Validate data

**Key Classes:**
- `AnalyticsClient` - API client

**Endpoints:**
- `fetch_user_activity()` - Per-user metrics
- `fetch_daily_usage()` - Org-wide metrics
- `fetch_dau_count()` - Daily active users
- `fetch_editor_language_breakdown()` - Detailed breakdowns

**Pagination:**
- Cursor-based pagination for large datasets
- Automatic page fetching
- Configurable page size (default: 100)

### Data Transformation Layer (`copilot_converter.py`)

**Responsibilities:**
- Map Augment fields to Copilot schema
- Validate output format
- Handle missing data
- Normalize values

**Key Functions:**
- `convert_to_copilot_format()` - Main conversion
- `validate_copilot_schema()` - Schema validation

**Field Mapping Strategy:**
- Direct mapping where possible
- Feature breakdown for complex metrics
- Preserve all data (no loss)

### Export Layer (`export.py`, `copilot_aggregator.py`)

**Responsibilities:**
- Write CSV files
- Write JSON files
- Aggregate daily metrics
- Organize output files

**Key Functions:**
- `export_to_csv()` - CSV export
- `export_to_json()` - JSON export
- `aggregate_metrics()` - 28-day aggregation

**Output Structure:**
```
data/
├── daily_exports_YYYY-MM-DD_to_YYYY-MM-DD/
│   ├── metrics_YYYY-MM-DD.json
│   ├── metrics_YYYY-MM-DD.json
│   └── ...
├── metrics_YYYYMMDD_to_YYYYMMDD.csv
└── aggregated_metrics_YYYYMMDD_to_YYYYMMDD.json
```

## Data Flow

### Normal Export Flow

```
1. User runs: augment-metrics --last-28-days
2. CLI parses arguments
3. Config loads settings (API token, enterprise ID)
4. TokenAuth validates token
5. AnalyticsClient fetches data for each day:
   a. Call /analytics/v0/user-activity (with pagination)
   b. Call /analytics/v0/daily-usage
   c. Call /analytics/v0/dau-count
6. CopilotConverter transforms each day's data
7. Export layer writes:
   a. Daily JSON files
   b. CSV file (all days)
   c. Aggregated JSON (optional)
8. Success message with output location
```

### Error Handling Flow

```
1. Error occurs (e.g., invalid token)
2. HTTPClient retries (if retryable)
3. If still fails, exception raised
4. CLI catches exception
5. User-friendly error message displayed
6. Exit with non-zero code
```

## Design Decisions

### Why Pydantic for Configuration?

- **Type safety**: Catch config errors early
- **Validation**: Automatic validation of settings
- **Documentation**: Self-documenting settings
- **Environment variables**: Built-in support

### Why Cursor-Based Pagination?

- **Scalability**: Handles large datasets
- **Consistency**: No missed/duplicate records
- **API standard**: Matches Analytics API design

### Why Separate CSV and JSON?

- **CSV**: Human-readable, Excel-compatible
- **JSON**: Machine-readable, Copilot-compatible
- **Both**: Different use cases, both valuable

### Why 28-Day Aggregation?

- **Copilot standard**: Matches Copilot's reporting period
- **Trend analysis**: Good for monthly comparisons
- **Manageable size**: Not too large, not too granular

## Testing Strategy

### Unit Tests
- Each module tested independently
- Mock external dependencies
- Test edge cases and error conditions

### Integration Tests
- Test full data pipeline
- Use test API credentials
- Validate output format

### End-to-End Tests
- Test CLI commands
- Verify file outputs
- Check error messages

## Performance Considerations

### API Rate Limiting
- Respect API rate limits
- Exponential backoff on 429
- Configurable request delays

### Memory Usage
- Stream large responses
- Process data in chunks
- Don't load all days in memory

### Disk Usage
- Compress old exports (optional)
- Configurable retention policy
- Clean up temp files

## Security Considerations

### Token Storage
- User-only file permissions (0600)
- Never in version control
- Never in logs

### API Communication
- HTTPS only
- Validate SSL certificates
- No sensitive data in URLs

### Input Validation
- Validate all user input
- Sanitize file paths
- Prevent injection attacks

## Future Enhancements

### Planned Features
- [ ] Incremental exports (only new data)
- [ ] Multiple output formats (Parquet, etc.)
- [ ] Data visualization
- [ ] Webhook notifications
- [ ] Cloud storage integration (S3, GCS)

### Performance Improvements
- [ ] Parallel API requests
- [ ] Caching layer
- [ ] Compression

### Monitoring
- [ ] Metrics collection
- [ ] Health checks
- [ ] Alerting

## Maintenance

### Versioning
- Semantic versioning (MAJOR.MINOR.PATCH)
- CHANGELOG.md for all changes
- Git tags for releases

### Dependencies
- Regular security updates
- Pin major versions
- Test before upgrading

### Documentation
- Keep docs in sync with code
- Update examples
- Document breaking changes

---

**Last Updated**: 2026-01-15
**Version**: 0.1.0 (PR #1 - Project Foundation)
