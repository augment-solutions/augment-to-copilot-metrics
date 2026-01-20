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

**Option 1: Install from GitHub (Recommended)**
```bash
pip install git+https://github.com/augment-solutions/augment-to-copilot-metrics.git
```

**Option 2: Clone and Install Locally**
```bash
# Clone the repository
git clone https://github.com/augment-solutions/augment-to-copilot-metrics.git
cd augment-to-copilot-metrics

# Install the package
pip install .
```

**Option 3: Development Installation**
```bash
# Clone the repository
git clone https://github.com/augment-solutions/augment-to-copilot-metrics.git
cd augment-to-copilot-metrics

# Install in editable mode (for development)
pip install -e .
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

Each user in the `breakdown` array contains these fields:

| Copilot Field | Augment Source | Description |
|---------------|----------------|-------------|
| `user_email` | `user_email` | User's email address |
| `active_days` | `active_days` | Number of active days in period |
| `code_generation_activity_count` | `completions_count` | Code completions generated |
| `code_acceptance_activity_count` | `completions_accepted` | Code completions accepted |
| `loc_added_sum` | `total_modified_lines_of_code` | Total lines of code modified |
| `chat_panel.user_initiated_interaction_count` | `chat_messages` | Chat panel messages |
| `agent_edit.user_initiated_interaction_count` | Sum of all agent messages* | Total agent interactions |
| `agent_edit.loc_added_sum` | Sum of all agent LOC* | Lines from agent edits |
| `code_completions.loc_added_sum` | `completions_lines_of_code` | Lines from completions |

**Agent aggregations:**
- `agent_edit.user_initiated_interaction_count` = `remote_agent_messages` + `ide_agent_messages` + `cli_agent_interactive_messages` + `cli_agent_non_interactive_messages`
- `agent_edit.loc_added_sum` = `remote_agent_lines_of_code` + `ide_agent_lines_of_code` + `cli_agent_interactive_lines_of_code` + `cli_agent_non_interactive_lines_of_code`

See [FIELD_MAPPING.md](docs/FIELD_MAPPING.md) for complete mappings and examples.

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
