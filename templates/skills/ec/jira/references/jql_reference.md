# Jira REST API Reference

Quick reference for common Jira REST API operations.

---

## JQL Query Examples

### By Status

```jql
# Open issues
status != Done AND status != Closed

# In Progress
status = "In Progress"

# Recently resolved
status changed to Done during (-7d, now())
```

### By Assignee

```jql
# My issues
assignee = currentUser()

# Unassigned
assignee is EMPTY

# Specific user
assignee = "john.doe"
```

### By Project and Type

```jql
# All bugs in project
project = PROJ AND type = Bug

# Stories in sprint
project = PROJ AND type = Story AND sprint in openSprints()

# Epic and its children
"Epic Link" = PROJ-100
```

### By Date

```jql
# Created this week
created >= startOfWeek()

# Updated in last 7 days
updated >= -7d

# Due soon
duedate <= 7d AND duedate >= now()
```

### Combined Queries

```jql
# My high-priority bugs
project = PROJ AND type = Bug AND assignee = currentUser() AND priority in (High, Highest)

# Unresolved blockers
project = PROJ AND priority = Blocker AND resolution is EMPTY

# Sprint scope
project = PROJ AND sprint in openSprints() AND status != Done ORDER BY priority DESC
```

---

## Common Issue Types

| Type     | Description              |
| -------- | ------------------------ |
| Bug      | Something isn't working  |
| Task     | A work item              |
| Story    | User story               |
| Epic     | Large feature/initiative |
| Sub-task | Part of another issue    |

---

## Priority Levels

| Priority | When to Use                       |
| -------- | --------------------------------- |
| Highest  | Critical blocker, production down |
| High     | Important, affects users          |
| Medium   | Normal priority (default)         |
| Low      | Nice to have                      |
| Lowest   | Cosmetic or minor                 |

---

## Status Transitions

Common workflow statuses:

```
To Do → In Progress → In Review → Done
```

Use `--include-transitions` flag to see available transitions for an issue.

---

## Time Format

Jira uses specific time format:

| Format   | Meaning         |
| -------- | --------------- |
| `30m`    | 30 minutes      |
| `2h`     | 2 hours         |
| `1d`     | 1 day (8 hours) |
| `1w`     | 1 week (5 days) |
| `2h 30m` | Combined        |

---

## API Endpoints

| Operation    | Endpoint                                  |
| ------------ | ----------------------------------------- |
| Get issue    | `GET /rest/api/2/issue/{key}`             |
| Create issue | `POST /rest/api/2/issue`                  |
| Update issue | `PUT /rest/api/2/issue/{key}`             |
| Add comment  | `POST /rest/api/2/issue/{key}/comment`    |
| Log work     | `POST /rest/api/2/issue/{key}/worklog`    |
| Search       | `POST /rest/api/2/search`                 |
| Transitions  | `GET /rest/api/2/issue/{key}/transitions` |

---

## Error Codes

| Code | Meaning                    |
| ---- | -------------------------- |
| 400  | Bad request (invalid data) |
| 401  | Unauthorized (check token) |
| 403  | Forbidden (no permission)  |
| 404  | Issue not found            |
| 429  | Rate limited               |
