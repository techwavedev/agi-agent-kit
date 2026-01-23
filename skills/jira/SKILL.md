---
name: jira
description: "Jira ticket management skill for creating, updating, and managing issues. Use for: (1) Creating new tickets/issues with custom fields, (2) Updating existing tickets (status, assignee, priority, labels), (3) Adding and updating comments, (4) Logging work time and time tracking, (5) Searching issues with JQL, (6) Managing transitions and workflows, (7) Bulk operations on multiple tickets, (8) Sprint and board management. Supports both MCP server integration and direct REST API calls. Requires JIRA_API_TOKEN and JIRA_URL environment variables."
---

# Jira Skill

Comprehensive Jira ticket management for creating, updating, and managing issues with support for MCP server integration and direct REST API access.

> **Last Updated:** 2026-01-23

---

## Quick Start

```bash
# Create a new ticket
python skills/jira/scripts/create_ticket.py \
  --project "PROJ" \
  --summary "Fix login bug" \
  --type "Bug" \
  --priority "High"

# Update an existing ticket
python skills/jira/scripts/update_ticket.py \
  --ticket "PROJ-123" \
  --status "In Progress" \
  --assignee "john.doe"

# Add a comment
python skills/jira/scripts/add_comment.py \
  --ticket "PROJ-123" \
  --comment "Started working on this issue."

# Log work time
python skills/jira/scripts/log_work.py \
  --ticket "PROJ-123" \
  --time "2h 30m" \
  --comment "Debugging session"

# Search tickets
python skills/jira/scripts/search_tickets.py \
  --jql "project = PROJ AND status = 'In Progress'"
```

---

## Prerequisites

### Environment Variables

Configure these in your `.env` file (never commit credentials):

```bash
# Required
JIRA_URL=https://your-domain.atlassian.net
JIRA_API_TOKEN=your-api-token-here
JIRA_EMAIL=your-email@example.com

# Optional
JIRA_DEFAULT_PROJECT=PROJ
JIRA_DEFAULT_ASSIGNEE=me
```

### API Token Generation

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "Agent Automation")
4. Copy the token to your `.env` file

---

## Core Workflow

1. **Authenticate** — Load credentials from environment
2. **Execute Operation** — Create, update, comment, or search
3. **Handle Response** — Parse results and handle errors
4. **Return Structured Output** — JSON for automation, readable for display

---

## Scripts

### `create_ticket.py` — Create New Issues

Create Jira tickets with full field support.

```bash
python skills/jira/scripts/create_ticket.py \
  --project <key>           # Project key (required)
  --summary <text>          # Issue summary (required)
  --type <type>             # Issue type: Bug, Task, Story, Epic (default: Task)
  --priority <level>        # Priority: Highest, High, Medium, Low, Lowest
  --description <text>      # Description (supports markdown)
  --assignee <user>         # Assignee username or email
  --labels <labels>         # Comma-separated labels
  --components <comps>      # Comma-separated components
  --epic <key>              # Epic link (e.g., PROJ-100)
  --sprint <id>             # Sprint ID to add to
  --custom-fields <json>    # Custom fields as JSON
  --output <format>         # Output: json, key, url (default: json)
```

**Examples:**

```bash
# Simple bug report
python skills/jira/scripts/create_ticket.py \
  --project PROJ \
  --summary "Login page returns 500 error" \
  --type Bug \
  --priority High \
  --labels "production,urgent"

# Story with description
python skills/jira/scripts/create_ticket.py \
  --project PROJ \
  --summary "Implement user dashboard" \
  --type Story \
  --description "As a user, I want to see my activity dashboard..." \
  --assignee john.doe

# Task with custom fields
python skills/jira/scripts/create_ticket.py \
  --project PROJ \
  --summary "Database migration" \
  --type Task \
  --custom-fields '{"customfield_10001": "value"}'
```

### `update_ticket.py` — Update Existing Issues

Update any field on existing tickets.

```bash
python skills/jira/scripts/update_ticket.py \
  --ticket <key>            # Ticket key (required, e.g., PROJ-123)
  --status <status>         # Transition to status
  --assignee <user>         # New assignee
  --priority <level>        # New priority
  --summary <text>          # Updated summary
  --description <text>      # Updated description
  --labels <labels>         # Replace labels (comma-separated)
  --add-labels <labels>     # Add labels
  --remove-labels <labels>  # Remove labels
  --components <comps>      # Replace components
  --custom-fields <json>    # Custom fields as JSON
```

**Examples:**

```bash
# Change status
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-123 \
  --status "In Progress"

# Reassign and change priority
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-123 \
  --assignee jane.doe \
  --priority Critical

# Add labels
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-123 \
  --add-labels "reviewed,tested"
```

### `add_comment.py` — Add Comments

Add comments to existing tickets.

```bash
python skills/jira/scripts/add_comment.py \
  --ticket <key>            # Ticket key (required)
  --comment <text>          # Comment text (required)
  --visibility <group>      # Restrict to group (optional)
  --mention <users>         # Mention users (comma-separated)
```

**Examples:**

```bash
# Simple comment
python skills/jira/scripts/add_comment.py \
  --ticket PROJ-123 \
  --comment "Investigation complete. Root cause identified."

# Comment with mentions
python skills/jira/scripts/add_comment.py \
  --ticket PROJ-123 \
  --comment "Ready for review" \
  --mention "john.doe,jane.doe"

# Restricted comment
python skills/jira/scripts/add_comment.py \
  --ticket PROJ-123 \
  --comment "Internal note: security issue" \
  --visibility "jira-developers"
```

### `update_comment.py` — Update Existing Comments

Edit previously added comments.

```bash
python skills/jira/scripts/update_comment.py \
  --ticket <key>            # Ticket key (required)
  --comment-id <id>         # Comment ID (required)
  --text <text>             # New comment text (required)
```

### `log_work.py` — Time Tracking

Log work time against tickets.

```bash
python skills/jira/scripts/log_work.py \
  --ticket <key>            # Ticket key (required)
  --time <duration>         # Time spent: "2h", "30m", "1d", "2h 30m"
  --comment <text>          # Work description (optional)
  --started <datetime>      # Start time ISO format (optional)
  --remaining <duration>    # Remaining estimate (optional)
```

### `bulk_log_work.py` — Automated Bulk Logging

Log work across a date range. Automatically skips weekends and European Commission holidays.

```bash
python skills/jira/scripts/bulk_log_work.py \
  --ticket <key>            # Ticket key (required)
  --start <YYYY-MM-DD>      # Start date (required)
  --end <YYYY-MM-DD>        # End date (default: today)
  --time <duration>         # Time per day (e.g., "3h")
  --comment <text>          # Comment (use | to rotate multiple comments)
```

**Example:**

```bash
# Log 2h for every working day of the month with rotating comments
python skills/jira/scripts/bulk_log_work.py \
  --ticket KASP-1241 \
  --start 2026-01-01 \
  --time 2h \
  --comment "Infra check|Alerts check|Maintenance check"
```

**Examples:**

```bash
# Log 2 hours of work
python skills/jira/scripts/log_work.py \
  --ticket PROJ-123 \
  --time "2h" \
  --comment "Implemented authentication module"

# Log with specific start time
python skills/jira/scripts/log_work.py \
  --ticket PROJ-123 \
  --time "4h" \
  --started "2026-01-23T09:00:00" \
  --comment "Morning coding session"

# Log and update remaining estimate
python skills/jira/scripts/log_work.py \
  --ticket PROJ-123 \
  --time "1d" \
  --remaining "2d" \
  --comment "Major refactoring complete"
```

### `search_tickets.py` — Search with JQL

Search and filter tickets using JQL.

```bash
python skills/jira/scripts/search_tickets.py \
  --jql <query>             # JQL query (required)
  --fields <fields>         # Comma-separated fields to return
  --max-results <n>         # Maximum results (default: 50)
  --output <format>         # Output: json, table, keys (default: table)
```

**Common JQL Examples:**

```bash
# All open bugs in project
python skills/jira/scripts/search_tickets.py \
  --jql "project = PROJ AND type = Bug AND status != Done"

# My assigned tickets
python skills/jira/scripts/search_tickets.py \
  --jql "assignee = currentUser() AND status != Done"

# Recently updated
python skills/jira/scripts/search_tickets.py \
  --jql "project = PROJ AND updated >= -7d ORDER BY updated DESC"

# High priority in current sprint
python skills/jira/scripts/search_tickets.py \
  --jql "project = PROJ AND sprint in openSprints() AND priority = High"
```

### `get_ticket.py` — Get Ticket Details

Retrieve full details for a specific ticket.

```bash
python skills/jira/scripts/get_ticket.py \
  --ticket <key>            # Ticket key (required)
  --include-comments        # Include comments (default: false)
  --include-worklog         # Include work logs (default: false)
  --include-transitions     # Show available transitions
  --output <format>         # Output: json, summary (default: summary)
```

---

## MCP Integration

The skill supports the Jira MCP server for enhanced integration.

### MCP Server Configuration

Add to your MCP settings (`~/.config/mcp/settings.json`):

```json
{
  "mcpServers": {
    "jira": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-jira"],
      "env": {
        "JIRA_URL": "${JIRA_URL}",
        "JIRA_EMAIL": "${JIRA_EMAIL}",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
      }
    }
  }
}
```

### MCP vs Direct API

| Feature     | MCP Server          | Direct API       |
| ----------- | ------------------- | ---------------- |
| Setup       | Requires MCP        | Only env vars    |
| Speed       | Faster (persistent) | Per-request auth |
| Flexibility | Limited tools       | Full API access  |
| Best for    | Common operations   | Custom/bulk ops  |

---

## Configuration

### Default Settings

Create `~/.config/jira/defaults.json`:

```json
{
  "project": "PROJ",
  "type": "Task",
  "priority": "Medium",
  "labels": ["automation"],
  "assignee": "me"
}
```

### Field Mappings

Common custom field IDs (check your Jira instance):

| Field        | Common ID           |
| ------------ | ------------------- |
| Sprint       | `customfield_10020` |
| Story Points | `customfield_10021` |
| Epic Link    | `customfield_10014` |
| Team         | `customfield_10001` |

---

## Common Workflows

### 1. Bug Triage Workflow

```bash
# Create bug
python skills/jira/scripts/create_ticket.py \
  --project PROJ \
  --type Bug \
  --summary "Error in payment processing" \
  --priority High \
  --labels "triage"

# After investigation, update with findings
python skills/jira/scripts/add_comment.py \
  --ticket PROJ-123 \
  --comment "Root cause: null pointer in PaymentService.process()"

# Start work
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-123 \
  --status "In Progress" \
  --assignee me

# Log work
python skills/jira/scripts/log_work.py \
  --ticket PROJ-123 \
  --time "3h" \
  --comment "Fixed null check, added unit tests"

# Complete
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-123 \
  --status "Done" \
  --add-labels "fixed"
```

### 2. Sprint Planning

```bash
# Find unestimated stories
python skills/jira/scripts/search_tickets.py \
  --jql "project = PROJ AND type = Story AND 'Story Points' is EMPTY AND sprint is EMPTY"

# Add story to sprint
python skills/jira/scripts/update_ticket.py \
  --ticket PROJ-456 \
  --custom-fields '{"customfield_10020": 15}'  # Sprint ID
```

### 3. Daily Standup Report

```bash
# What I worked on yesterday
python skills/jira/scripts/search_tickets.py \
  --jql "assignee = currentUser() AND worklogDate >= -1d" \
  --output table

# What I'm working on today
python skills/jira/scripts/search_tickets.py \
  --jql "assignee = currentUser() AND status = 'In Progress'" \
  --output table
```

---

## Troubleshooting

| Issue                  | Cause               | Solution                                     |
| ---------------------- | ------------------- | -------------------------------------------- |
| **401 Unauthorized**   | Invalid credentials | Check JIRA_API_TOKEN and JIRA_EMAIL          |
| **403 Forbidden**      | No permission       | Verify account has project access            |
| **404 Not Found**      | Wrong ticket key    | Verify ticket exists and key is correct      |
| **Transition failed**  | Invalid workflow    | Use `--include-transitions` to see available |
| **Custom field error** | Wrong field ID      | Check field IDs in Jira admin                |

---

## Dependencies

```bash
pip install requests python-dotenv
```

---

## Related Skills

- **[gitlab](../gitlab/SKILL.md)** — Link Jira tickets to GitLab branches
- **[documentation](../documentation/SKILL.md)** — Generate ticket documentation

---

## External Resources

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [JQL Reference](https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jql/)
- [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
