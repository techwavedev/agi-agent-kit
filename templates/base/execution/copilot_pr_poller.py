#!/usr/bin/env python3
"""
Script: execution/copilot_pr_poller.py
Purpose: Close the dispatch→PR feedback loop. After copilot_dispatch.py creates
         a GitHub issue assigned to @Copilot, this poller watches for the linked
         PR and reports state transitions (draft → ready → checks → merged) so
         the orchestrator can pick up the work.

Usage:
    # One-shot status check (for cron / MCP polling)
    python3 execution/copilot_pr_poller.py --issue https://github.com/owner/repo/issues/123
    python3 execution/copilot_pr_poller.py --run-id <run_id>

    # Register a target so check_delegations.py / poller cron picks it up
    python3 execution/copilot_pr_poller.py --issue <url> --run-id <id> --register-only

    # Block until ready or timeout
    python3 execution/copilot_pr_poller.py --issue <url> --watch --timeout 600

Exit Codes:
    0 - Success (status reported / target registered / watch resolved)
    1 - Invalid arguments
    2 - gh CLI missing or unauthenticated
    3 - Issue / PR not found
    4 - Watch timeout exceeded
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DELEGATIONS_DIR = REPO_ROOT / ".tmp" / "delegations"
ISSUE_URL_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/issues/(\d+)")


def die(code: int, msg: str) -> None:
    print(json.dumps({"status": "error", "code": code, "message": msg}), file=sys.stderr)
    sys.exit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_gh() -> None:
    if not shutil.which("gh"):
        die(2, "gh CLI not found in PATH")
    r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=5)
    if r.returncode != 0:
        die(2, "gh CLI not authenticated (run `gh auth login`)")


def parse_issue_url(url: str) -> tuple[str, str, int]:
    m = ISSUE_URL_RE.match(url.strip())
    if not m:
        die(1, f"Not a valid GitHub issue URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def delegation_path(run_id: str) -> Path:
    DELEGATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return DELEGATIONS_DIR / f"{run_id}.json"


def load_delegation(run_id: str) -> dict:
    p = delegation_path(run_id)
    if not p.exists():
        die(3, f"No delegation registered for run_id={run_id}")
    return json.loads(p.read_text())


def save_delegation(run_id: str, data: dict) -> Path:
    p = delegation_path(run_id)
    p.write_text(json.dumps(data, indent=2))
    return p


def find_linked_pr(owner: str, repo: str, issue_number: int) -> dict | None:
    """Find a PR that explicitly closes the given issue via GraphQL.

    Uses `closedByPullRequestsReferences` (linked via "Closes #N" or the
    Development sidebar) plus `timelineItems` for cross-referenced PRs that
    haven't yet declared a closes-link. This avoids false positives from
    fuzzy search across the whole repo.
    """
    query = """
    query($owner:String!, $repo:String!, $num:Int!) {
      repository(owner:$owner, name:$repo) {
        issue(number:$num) {
          closedByPullRequestsReferences(first:10, includeClosedPrs:true) {
            nodes { number state isDraft mergeable url title headRefName updatedAt }
          }
          timelineItems(first:30, itemTypes:[CROSS_REFERENCED_EVENT]) {
            nodes {
              ... on CrossReferencedEvent {
                source {
                  ... on PullRequest {
                    number state isDraft mergeable url title headRefName updatedAt
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}",
         "-F", f"owner={owner}", "-F", f"repo={repo}", "-F", f"num={issue_number}"],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)["data"]["repository"]["issue"]
    except (KeyError, ValueError, TypeError):
        return None
    if not data:
        return None
    candidates = list(data.get("closedByPullRequestsReferences", {}).get("nodes") or [])
    for ev in data.get("timelineItems", {}).get("nodes") or []:
        src = (ev or {}).get("source") or {}
        if src.get("number"):
            candidates.append(src)
    if not candidates:
        return None
    # Dedupe by number, keep richest record
    by_num: dict[int, dict] = {}
    for pr in candidates:
        by_num[pr["number"]] = pr
    prs = list(by_num.values())
    # mergeStateStatus not in GraphQL above (requires extra perms); leave as None
    for pr in prs:
        pr.setdefault("mergeStateStatus", None)
    # Prefer OPEN > MERGED > CLOSED, then highest number
    rank = {"OPEN": 0, "MERGED": 1, "CLOSED": 2}
    prs.sort(key=lambda p: (rank.get(p.get("state"), 9), -int(p["number"])))
    return prs[0]


def get_pr_checks(owner: str, repo: str, pr_number: int) -> dict:
    r = subprocess.run(
        ["gh", "pr", "checks", str(pr_number), "--repo", f"{owner}/{repo}", "--json",
         "name,state,conclusion"],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        return {"summary": "unknown", "checks": []}
    checks = json.loads(r.stdout or "[]")
    if not checks:
        return {"summary": "none", "checks": []}
    states = {c.get("conclusion") or c.get("state") for c in checks}
    if "FAILURE" in states or "CANCELLED" in states:
        summary = "failing"
    elif any(s in states for s in ("PENDING", "IN_PROGRESS", "QUEUED", None)):
        summary = "running"
    elif states <= {"SUCCESS", "SKIPPED", "NEUTRAL"}:
        summary = "passing"
    else:
        summary = "mixed"
    return {"summary": summary, "checks": checks}


def derive_state(pr: dict | None, checks: dict) -> str:
    if pr is None:
        return "no_pr"
    if pr["state"] == "MERGED":
        return "merged"
    if pr["state"] == "CLOSED":
        return "closed"
    if pr.get("isDraft"):
        return "draft"
    if checks["summary"] == "failing":
        return "checks_failing"
    if checks["summary"] == "running":
        return "checks_running"
    if checks["summary"] == "passing":
        return "ready_for_review"
    return "ready_for_review"


def broadcast(action: str, project: str = "agi-agent-kit") -> None:
    """Best-effort cross-agent broadcast on state change."""
    script = REPO_ROOT / "execution" / "cross_agent_context.py"
    if not script.exists():
        return
    subprocess.run(
        ["python3", str(script), "store", "--agent", "claude",
         "--action", action, "--project", project],
        capture_output=True, timeout=10,
    )


def poll_once(issue_url: str, run_id: str | None) -> dict:
    owner, repo, issue_number = parse_issue_url(issue_url)
    pr = find_linked_pr(owner, repo, issue_number)
    checks = get_pr_checks(owner, repo, pr["number"]) if pr else {"summary": "n/a", "checks": []}
    state = derive_state(pr, checks)
    snapshot = {
        "run_id": run_id,
        "issue_url": issue_url,
        "issue_number": issue_number,
        "repo": f"{owner}/{repo}",
        "pr_number": pr["number"] if pr else None,
        "pr_url": pr["url"] if pr else None,
        "pr_state": pr["state"] if pr else None,
        "draft": pr.get("isDraft") if pr else None,
        "mergeable": pr.get("mergeable") if pr else None,
        "merge_state": pr.get("mergeStateStatus") if pr else None,
        "checks": checks["summary"],
        "checks_detail": checks["checks"],
        "state": state,
        "polled_at": now_iso(),
    }
    if run_id:
        prev = {}
        p = delegation_path(run_id)
        if p.exists():
            try:
                prev = json.loads(p.read_text())
            except Exception:
                prev = {}
        merged = {**prev, **snapshot, "status": "polling"}
        # Preserve dispatch metadata if present
        for k in ("created_at", "dispatched_by", "team", "task"):
            if k in prev:
                merged[k] = prev[k]
        save_delegation(run_id, merged)
        if prev.get("state") != state:
            broadcast(f"copilot PR for {owner}/{repo}#{issue_number} → {state}")
    return snapshot


def register(issue_url: str, run_id: str, extra: dict | None = None) -> dict:
    owner, repo, issue_number = parse_issue_url(issue_url)
    data = {
        "run_id": run_id,
        "issue_url": issue_url,
        "issue_number": issue_number,
        "repo": f"{owner}/{repo}",
        "status": "dispatched",
        "state": "no_pr",
        "created_at": now_iso(),
        "polled_at": None,
        "pr_number": None,
        "pr_url": None,
    }
    if extra:
        data.update(extra)
    save_delegation(run_id, data)
    return data


def watch(issue_url: str, run_id: str | None, timeout: int, interval: int) -> dict:
    deadline = time.time() + timeout
    backoff = interval
    last_state = None
    while time.time() < deadline:
        snap = poll_once(issue_url, run_id)
        if snap["state"] != last_state:
            print(json.dumps({"event": "state_change", "from": last_state, "to": snap["state"],
                              "pr_url": snap["pr_url"]}), flush=True)
            last_state = snap["state"]
        if snap["state"] in ("merged", "closed", "ready_for_review", "checks_failing"):
            return snap
        time.sleep(min(backoff, 300))
        backoff = min(int(backoff * 1.5), 300)
    die(4, f"Watch timed out after {timeout}s; last state={last_state}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--issue", help="GitHub issue URL")
    parser.add_argument("--run-id", help="Dispatch run_id (for delegation tracking)")
    parser.add_argument("--register-only", action="store_true",
                        help="Just record the dispatch in .tmp/delegations/, no polling")
    parser.add_argument("--watch", action="store_true", help="Block until ready / merged / failing / timeout")
    parser.add_argument("--timeout", type=int, default=600, help="Watch timeout seconds (default 600)")
    parser.add_argument("--interval", type=int, default=30, help="Initial poll interval seconds (default 30)")
    args = parser.parse_args()

    issue_url = args.issue
    if not issue_url and args.run_id:
        d = load_delegation(args.run_id)
        issue_url = d.get("issue_url")
        if not issue_url:
            die(1, f"run_id={args.run_id} has no issue_url recorded")
    if not issue_url:
        die(1, "Provide --issue <url> or --run-id <id>")

    ensure_gh()

    if args.register_only:
        if not args.run_id:
            die(1, "--register-only requires --run-id")
        data = register(issue_url, args.run_id)
        print(json.dumps({"status": "registered", "delegation": data}, indent=2))
        return

    if args.watch:
        result = watch(issue_url, args.run_id, args.timeout, args.interval)
    else:
        result = poll_once(issue_url, args.run_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
