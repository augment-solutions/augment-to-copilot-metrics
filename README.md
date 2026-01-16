# Augment Analytics to Copilot Metrics Converter

Convert [Augment](https://www.augmentcode.com/) Analytics API metrics to [GitHub Copilot Metrics API](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage) format.

Perfect for organizations integrating Augment usage data into Copilot-compatible analytics tools.

## ✨ Key Benefits

### 🔐 **Simple, Reliable Authentication**
- ✅ **API tokens** from Augment service accounts (no expiration!)
- ✅ Secure Bearer token authentication
- ✅ No manual cookie extraction needed

### 🚀 **Automation-Ready**
- Perfect for **cron jobs** and **CI/CD pipelines**
- No re-authentication needed
- Stable, versioned API endpoints

### 📊 **Enhanced Metrics**
- All standard Augment metrics (completions, chat, agent usage)
- Tool usage tracking
- Editor and language breakdowns
- Service account metrics

### ⚡ **Easy Setup**
- **3 simple steps** to get running
- **3-5 minutes** setup time
- Clear error messages and helpful documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Augment Enterprise account
- Service account with API token

### Installation

```bash
pip install augment-to-copilot-metrics
```

### Setup (One-Time)

1. **Create a service account** in Augment:
   - Visit: https://app.augmentcode.com/settings/service-accounts
   - Click "Service Accounts" on the left sidebar
   - Select "Add Service Account"
   - Give it a name (e.g., "Metrics Export") and description and click "Add"

2. **Generate an API token**:
   - Click "Create Token" for your service account
   - Copy the token (you'll only see it once!)

3. **Configure environment**:
   ```bash
   export AUGMENT_API_TOKEN="your-token-here"
   export ENTERPRISE_ID="your-enterprise-id"
   ```

### Usage

**Export last 28 days of metrics:**
```bash
augment-metrics --last-28-days
```

**Export specific date range:**
```bash
augment-metrics --start-date 2025-01-01 --end-date 2025-01-31
```

**Export with aggregation:**
```bash
augment-metrics --last-28-days --aggregate
```

### Output

The tool generates:
- **Daily JSON files** in Copilot Metrics API format
- **CSV export** with all metrics
- **Aggregated JSON** (optional) combining all days

Output location: `./data/` (configurable via `OUTPUT_DIR`)

## 📖 Documentation

- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [Architecture](docs/ARCHITECTURE.md) - System design and decisions
- [Field Mapping](docs/FIELD_MAPPING.md) - Augment → Copilot field mappings

## 🏗️ Architecture

```
augment-to-copilot-metrics/
├── src/augment_metrics/
│   ├── token_auth.py          # API token authentication
│   ├── http.py                # HTTP client with Bearer auth
│   ├── analytics_client.py    # Analytics API client
│   ├── config.py              # Configuration management
│   ├── copilot_converter.py   # Augment → Copilot conversion
│   ├── copilot_aggregator.py  # 28-day aggregation
│   ├── daily_metrics.py       # Daily processing
│   └── main.py                # CLI entrypoint
├── tests/                     # Test suite
├── docs/                      # Documentation
└── scripts/                   # Utility scripts
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/augment-solutions/augment-to-copilot-metrics.git
cd augment-to-copilot-metrics

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## 📊 Metrics Mapping

### Augment Analytics API → Copilot JSON

| Augment Field | Copilot Field | Notes |
|---------------|---------------|-------|
| `completions_count` | `code_generation_activity_count` | Direct mapping |
| `completions_accepted` | `code_acceptance_activity_count` | Direct mapping |
| `chat_messages` | `chat_panel.user_initiated_interaction_count` | Feature breakdown |
| `remote_agent_messages` | `agent_edit.user_initiated_interaction_count` | Feature breakdown |
| `total_modified_lines_of_code` | `loc_added_sum` | Direct mapping |
| `total_tool_calls` | N/A | New metric (not in Copilot schema) |

See [FIELD_MAPPING.md](docs/FIELD_MAPPING.md) for complete mappings.

## 🔗 API Reference

This tool uses the [Augment Analytics API v0](https://www.notion.so/Runbook-Enterprise-Analytics-API-2c4bba10175a808da26cc956c34a7645):

- `/analytics/v0/user-activity` - Per-user metrics
- `/analytics/v0/daily-usage` - Organization-wide daily metrics
- `/analytics/v0/dau-count` - Daily active users
- `/analytics/v0/daily-user-activity-by-editor-language` - Detailed breakdowns

## 🤝 Contributing

Contributions are welcome! Please see our [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) for the development roadmap.

### PR Workflow

1. Create a feature branch: `feature/your-feature-name`
2. Make your changes
3. Add tests
4. Update documentation
5. Submit a PR using our [PR template](.github/PULL_REQUEST_TEMPLATE.md)

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **Issues**: https://github.com/augment-solutions/augment-to-copilot-metrics/issues
- **Documentation**: https://github.com/augment-solutions/augment-to-copilot-metrics#readme
- **Augment Support**: support@augmentcode.com

## 🎯 Roadmap

See [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for the complete development roadmap.

**Current Status**: 🚧 PR #1 - Project Foundation (In Progress)

### Upcoming Features

- [ ] API token authentication (PR #2)
- [ ] Core Analytics API client (PR #3)
- [ ] Enhanced metrics (editor/language breakdowns) (PR #4)
- [ ] Data transformation layer (PR #5)
- [ ] CLI and configuration (PR #6)
- [ ] Comprehensive testing (PR #7)
- [ ] Complete documentation (PR #8)

## 🙏 Acknowledgments

- Built on the [Augment Analytics API](https://www.augmentcode.com/)
- Compatible with [GitHub Copilot Metrics API](https://docs.github.com/en/enterprise-cloud@latest/rest/copilot/copilot-usage)

---

**Made with ❤️ by Augment Solutions**
