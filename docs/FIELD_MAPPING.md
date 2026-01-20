# Field Mapping: Augment Analytics API → GitHub Copilot Metrics API

This document describes how Augment Analytics API fields are mapped to GitHub Copilot Metrics API format.

## Overview

The Augment Analytics API provides detailed usage metrics that we transform into the GitHub Copilot Metrics API schema. This allows Augment metrics to be consumed by tools expecting Copilot-format data.

## User-Level Metrics

### Augment Analytics API Response

From `/analytics/v0/user-activity`:

```json
{
  "users": [
    {
      "user_email": "alice@example.com",
      "active_days": 5,
      "metrics": {
        "total_modified_lines_of_code": 450,
        "total_messages": 65,
        "total_tool_calls": 120,
        "completions_count": 320,
        "completions_accepted": 280,
        "completions_lines_of_code": 350,
        "chat_messages": 25,
        "remote_agent_messages": 10,
        "remote_agent_lines_of_code": 45,
        "ide_agent_messages": 30,
        "ide_agent_lines_of_code": 40,
        "cli_agent_interactive_messages": 8,
        "cli_agent_interactive_lines_of_code": 10,
        "cli_agent_non_interactive_messages": 5,
        "cli_agent_non_interactive_lines_of_code": 5
      }
    }
  ]
}
```

### Copilot Metrics API Format

```json
{
  "date": "2025-01-15",
  "total_active_users": 1,
  "total_engaged_users": 1,
  "copilot_ide_code_completions": {
    "total_engaged_users": 1,
    "languages": [],
    "editors": []
  },
  "copilot_ide_chat": {
    "total_engaged_users": 1,
    "editors": []
  },
  "copilot_dotcom_chat": {
    "total_engaged_users": 0,
    "models": []
  },
  "copilot_dotcom_pull_requests": {
    "total_engaged_users": 0,
    "repositories": []
  },
  "breakdown": [
    {
      "user_email": "alice@example.com",
      "active_days": 5,
      "code_generation_activity_count": 320,
      "code_acceptance_activity_count": 280,
      "loc_added_sum": 450,
      "chat_panel": {
        "user_initiated_interaction_count": 25
      },
      "agent_edit": {
        "user_initiated_interaction_count": 53
      }
    }
  ]
}
```

## Field Mappings

### Complete Breakdown Field Reference

Each user in the `breakdown` array contains the following fields:

| Copilot Field | Augment Source | Type | Description |
|---------------|----------------|------|-------------|
| `user_email` | `user_email` or `service_account_name` | string | User's email address or service account name |
| `active_days` | `active_days` | integer | Number of days user was active in the period |
| `code_generation_activity_count` | `metrics.completions_count` | integer | Number of code completions generated |
| `code_acceptance_activity_count` | `metrics.completions_accepted` | integer | Number of code completions accepted |
| `loc_added_sum` | `metrics.total_modified_lines_of_code` | integer | Total lines of code modified across all features |
| `chat_panel.user_initiated_interaction_count` | `metrics.chat_messages` | integer | Number of chat panel messages |
| `agent_edit.user_initiated_interaction_count` | Sum of all agent messages | integer | Total agent interactions (see calculation below) |
| `agent_edit.loc_added_sum` | Sum of all agent LOC | integer | Total lines of code from agent edits (see calculation below) |
| `code_completions.loc_added_sum` | `metrics.completions_lines_of_code` | integer | Lines of code from code completions |

### Direct Mappings

| Augment Field | Copilot Field | Type | Notes |
|---------------|---------------|------|-------|
| `user_email` | `user_email` | string | Direct copy (or `service_account_name` if user_email is null) |
| `active_days` | `active_days` | integer | Direct copy |
| `completions_count` | `code_generation_activity_count` | integer | Code completions generated |
| `completions_accepted` | `code_acceptance_activity_count` | integer | Code completions accepted |
| `total_modified_lines_of_code` | `loc_added_sum` | integer | Total lines of code modified |

### Feature Breakdown Mappings

Augment has more granular metrics than Copilot. We aggregate them into Copilot's feature categories:

#### Chat Panel (`chat_panel`)

| Augment Field | Copilot Field | Calculation |
|---------------|---------------|-------------|
| `chat_messages` | `chat_panel.user_initiated_interaction_count` | Direct mapping |

#### Agent Edit (`agent_edit`)

**Interaction Count:**

| Augment Fields | Copilot Field | Calculation |
|----------------|---------------|-------------|
| `remote_agent_messages`<br>+ `ide_agent_messages`<br>+ `cli_agent_interactive_messages`<br>+ `cli_agent_non_interactive_messages` | `agent_edit.user_initiated_interaction_count` | Sum of all agent message types |

**Lines of Code:**

| Augment Fields | Copilot Field | Calculation |
|----------------|---------------|-------------|
| `remote_agent_lines_of_code`<br>+ `ide_agent_lines_of_code`<br>+ `cli_agent_interactive_lines_of_code`<br>+ `cli_agent_non_interactive_lines_of_code` | `agent_edit.loc_added_sum` | Sum of all agent LOC types |

#### Code Completions (`code_completions`)

| Augment Field | Copilot Field | Calculation |
|---------------|---------------|-------------|
| `completions_lines_of_code` | `code_completions.loc_added_sum` | Direct mapping |

### Augment-Specific Fields (Not in Copilot Schema)

These fields are available in Augment but don't have direct Copilot equivalents. We include them in CSV exports but not in Copilot JSON:

| Augment Field | Description | Included In |
|---------------|-------------|-------------|
| `total_tool_calls` | Number of tool/function calls made | CSV only |
| `total_messages` | Total messages across all features | CSV only |
| `remote_agent_messages` | Remote agent messages (separate) | CSV only |
| `ide_agent_messages` | IDE agent messages (separate) | CSV only |
| `cli_agent_interactive_messages` | CLI interactive messages (separate) | CSV only |
| `cli_agent_non_interactive_messages` | CLI non-interactive messages (separate) | CSV only |

## Organization-Level Metrics

### Daily Usage

From `/analytics/v0/daily-usage`:

```json
{
  "date": "2025-01-15",
  "metrics": {
    "total_completions": 1250,
    "total_accepted_completions": 1050,
    "total_chat_messages": 180,
    "total_agent_messages": 95,
    "total_tool_calls": 420,
    "total_modified_lines_of_code": 2100
  }
}
```

Maps to Copilot's aggregate fields:
- `total_completions` → Used to calculate `total_engaged_users` in code completions
- `total_chat_messages` → Used to calculate `total_engaged_users` in chat
- Other fields used for validation and CSV export

### Daily Active Users

From `/analytics/v0/dau-count`:

```json
{
  "date": "2025-01-15",
  "active_user_count": 42
}
```

Maps to:
- `active_user_count` → `total_active_users`

## CSV Export Format

The CSV export includes all Augment fields plus computed Copilot fields:

```csv
User,Active Days,Completions,Accepted Completions,Chat Messages,Remote Agent Messages,IDE Agent Messages,CLI Interactive Messages,CLI Non-Interactive Messages,Total Tool Calls,Total Modified LOC,Completion LOC,Remote Agent LOC,IDE Agent LOC,CLI Agent LOC,Copilot Code Generation,Copilot Code Acceptance,Copilot Chat Interactions,Copilot Agent Interactions
alice@example.com,5,320,280,25,10,30,8,5,120,450,350,45,40,15,320,280,25,53
```

## Validation Rules

### Required Fields

All Copilot JSON exports must include:
- `date` (YYYY-MM-DD format)
- `total_active_users` (integer ≥ 0)
- `total_engaged_users` (integer ≥ 0)
- `breakdown` (array of user metrics)

### Data Integrity

- `total_active_users` ≥ `total_engaged_users`
- `code_acceptance_activity_count` ≤ `code_generation_activity_count`
- All counts must be non-negative integers
- Dates must be valid and in the past (UTC)

### Service Accounts

Service accounts are handled specially:
- `user_email` may be null for service accounts
- `service_account_name` field used instead
- Included in `total_active_users` count
- Marked with `is_service_account: true` in CSV

## Editor and Language Breakdowns

From `/analytics/v0/daily-user-activity-by-editor-language`:

```json
{
  "date": "2025-01-15",
  "users": [
    {
      "user_email": "alice@example.com",
      "editor_language_breakdown": [
        {
          "editor": "vscode",
          "language": "python",
          "completions_count": 150,
          "completions_accepted": 130,
          "chat_messages": 10
        },
        {
          "editor": "vscode",
          "language": "typescript",
          "completions_count": 170,
          "completions_accepted": 150,
          "chat_messages": 15
        }
      ]
    }
  ]
}
```

Maps to Copilot's editor/language arrays:

```json
{
  "copilot_ide_code_completions": {
    "editors": [
      {
        "name": "vscode",
        "total_engaged_users": 1,
        "models": []
      }
    ],
    "languages": [
      {
        "name": "python",
        "total_engaged_users": 1
      },
      {
        "name": "typescript",
        "total_engaged_users": 1
      }
    ]
  }
}
```

## Transformation Examples

### Example 1: Complete User Breakdown Entry

This shows all fields that appear in the `breakdown` array for each user:

**Input (Augment Analytics API):**
```json
{
  "user_email": "benperlmutter@augmentcode.com",
  "active_days": 11,
  "metrics": {
    "completions_count": 12,
    "completions_accepted": 2,
    "completions_lines_of_code": 2,
    "chat_messages": 3,
    "remote_agent_messages": 100,
    "remote_agent_lines_of_code": 15000,
    "ide_agent_messages": 120,
    "ide_agent_lines_of_code": 12000,
    "cli_agent_interactive_messages": 20,
    "cli_agent_interactive_lines_of_code": 1500,
    "cli_agent_non_interactive_messages": 4,
    "cli_agent_non_interactive_lines_of_code": 440,
    "total_modified_lines_of_code": 28942
  }
}
```

**Output (Copilot Metrics API):**
```json
{
  "user_email": "benperlmutter@augmentcode.com",
  "active_days": 11,
  "code_generation_activity_count": 12,
  "code_acceptance_activity_count": 2,
  "loc_added_sum": 28942,
  "chat_panel": {
    "user_initiated_interaction_count": 3
  },
  "agent_edit": {
    "user_initiated_interaction_count": 244,
    "loc_added_sum": 28940
  },
  "code_completions": {
    "loc_added_sum": 2
  }
}
```

**Field Calculations:**
- `code_generation_activity_count`: `completions_count` = **12**
- `code_acceptance_activity_count`: `completions_accepted` = **2**
- `loc_added_sum`: `total_modified_lines_of_code` = **28,942**
- `chat_panel.user_initiated_interaction_count`: `chat_messages` = **3**
- `agent_edit.user_initiated_interaction_count`:
  - `remote_agent_messages` (100) + `ide_agent_messages` (120) + `cli_agent_interactive_messages` (20) + `cli_agent_non_interactive_messages` (4) = **244**
- `agent_edit.loc_added_sum`:
  - `remote_agent_lines_of_code` (15,000) + `ide_agent_lines_of_code` (12,000) + `cli_agent_interactive_lines_of_code` (1,500) + `cli_agent_non_interactive_lines_of_code` (440) = **28,940**
- `code_completions.loc_added_sum`: `completions_lines_of_code` = **2**

### Example 2: Basic User Metrics

**Input (Augment):**
```json
{
  "user_email": "bob@example.com",
  "active_days": 3,
  "metrics": {
    "completions_count": 100,
    "completions_accepted": 85,
    "chat_messages": 10,
    "total_modified_lines_of_code": 200
  }
}
```

**Output (Copilot):**
```json
{
  "user_email": "bob@example.com",
  "active_days": 3,
  "code_generation_activity_count": 100,
  "code_acceptance_activity_count": 85,
  "loc_added_sum": 200,
  "chat_panel": {
    "user_initiated_interaction_count": 10
  },
  "agent_edit": {
    "user_initiated_interaction_count": 0,
    "loc_added_sum": 0
  },
  "code_completions": {
    "loc_added_sum": 0
  }
}
```

### Example 3: Agent-Only User

**Input (Augment):**
```json
{
  "user_email": "carol@example.com",
  "active_days": 5,
  "metrics": {
    "remote_agent_messages": 5,
    "remote_agent_lines_of_code": 100,
    "ide_agent_messages": 10,
    "ide_agent_lines_of_code": 200,
    "cli_agent_interactive_messages": 3,
    "cli_agent_interactive_lines_of_code": 50,
    "cli_agent_non_interactive_messages": 2,
    "cli_agent_non_interactive_lines_of_code": 30,
    "total_modified_lines_of_code": 380
  }
}
```

**Output (Copilot):**
```json
{
  "user_email": "carol@example.com",
  "active_days": 5,
  "code_generation_activity_count": 0,
  "code_acceptance_activity_count": 0,
  "loc_added_sum": 380,
  "chat_panel": {
    "user_initiated_interaction_count": 0
  },
  "agent_edit": {
    "user_initiated_interaction_count": 20,
    "loc_added_sum": 380
  },
  "code_completions": {
    "loc_added_sum": 0
  }
}
```

**Calculation:**
- Agent interactions: 5 + 10 + 3 + 2 = **20**
- Agent LOC: 100 + 200 + 50 + 30 = **380**

## Notes

### Timezone Handling

- All dates are in UTC
- Augment API returns data up to "yesterday" (UTC) at 02:00 UTC
- Always use UTC for date parameters

### Missing Data

- If a field is missing in Augment response, default to 0
- Never omit required Copilot fields
- Log warnings for unexpected missing data

### Future Enhancements

Potential future mappings:
- Model usage (when Augment adds model tracking)
- Repository-level metrics
- Team-level aggregations
- Custom metric definitions

---

**Last Updated**: 2026-01-15
**Version**: 0.1.0 (PR #1 - Project Foundation)
