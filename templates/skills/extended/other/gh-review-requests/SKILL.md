---
name: gh-review-requests
description: Fetch unread GitHub notifications for open PRs where review is requested from a specified team or opened by a team member. Use when asked to "find PRs I need to review", "show my review requests", "what needs my review", "fetch GitHub review requests", or "check team review queue".
allowed-tools: Bash
risk: safe
source: community
---

# GitHub Review Requests

Fetch unread `review_requested` notifications for open (unmerged) PRs, filtered by a GitHub team.

**Requires**: GitHub CLI (`gh`) authenticated.

## Step 1: Identify the Team

If the user has not specified a team, ask:

> Which GitHub team should I filter by? (e.g. `streaming-platform`)

Accept either a team slug (`streaming-platform`) or a display name ("Streaming Platform") — convert to lowercase-hyphenated slug before passing to the script.

## Step 2: Run the Script

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_review_requests.py --org getsentry --teams <team-slug>
```

To filter by multiple teams, pass a comma-separated list:

```bash
uv run ${CLAUDE_SKILL_ROOT}/scripts/fetch_review_requests.py --org getsentry --teams <team slugs>
```

### Script output

```json
{
  "total": 3,
  "prs": [
    {
      "notification_id": "12345",
      "title": "feat(kafka): add workflow to restart a broker",
      "url": "https://github.com/getsentry/ops/pull/19144",
      "repo": "getsentry/ops",
      "pr_number": 19144,
      "author": "bmckerry",
      "reasons": ["opened by: bmckerry"]
    }
  ]
}
```

`reasons` will contain one or both of:
- `"review requested from: <Team Name>"` — the team is a requested reviewer
- `"opened by: <login>"` — the PR author is a team member

## Step 3: Present Results

Display results as a markdown table with full URLs:

| # | Title | URL | Reason |
|---|-------|-----|--------|
| 1 | feat(kafka): add workflow to restart a broker | https://github.com/getsentry/ops/pull/19144 | opened by: evanh |

If `total` is 0, say: "No unread review requests found for that team."

## Fallback

If the script fails, run manually:

```bash
gh api notifications --paginate
```

Then for each `review_requested` notification, check:
- `gh api repos/{repo}/pulls/{number}` — skip if `state == "closed"` or `merged_at` is set
- `gh api repos/{repo}/pulls/{number}/requested_reviewers` — check `teams[].name`
- `gh api orgs/{org}/teams/{slug}/members` — check if author is a member

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior decisions and patterns to avoid re-discovering solutions. Cache results for instant retrieval in future sessions.

```bash
# Check for prior development context before starting
python3 execution/memory_manager.py auto --query "prior work and patterns related to Gh Review Requests"
```

### Storing Results

After completing work, store development decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Completed task with key insights documented for future reference" \
  --type decision --project <project> \
  --tags gh-review-requests default
```

### Multi-Agent Collaboration

Share outcomes with other agents so the team stays aligned and avoids duplicate work.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Task completed — results documented and shared with team" \
  --project <project>
```

<!-- AGI-INTEGRATION-END -->
