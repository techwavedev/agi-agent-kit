#!/usr/bin/env python3
"""
Script: worktree_isolator.py
Purpose: Git worktree lifecycle manager for parallel agent isolation.
         Each parallel agent gets its own worktree (isolated repo copy),
         works on a dedicated branch, and merges back when done.

Usage:
    python3 execution/worktree_isolator.py create --agent <name> --run-id <id> [--base-branch <branch>]
    python3 execution/worktree_isolator.py merge --agent <name> --run-id <id> [--strategy merge|rebase]
    python3 execution/worktree_isolator.py cleanup --agent <name> --run-id <id>
    python3 execution/worktree_isolator.py status [--run-id <id>]
    python3 execution/worktree_isolator.py validate-partitions --partitions '<json>'

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Git error (worktree create/merge failed)
    3 - Merge conflict detected
    4 - Partition overlap detected
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def find_project_root():
    """Walk up from CWD to find the git root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    # Fallback
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    return current


def get_current_branch():
    """Get the current branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "main"


def get_project_name(root: Path) -> str:
    """Get a safe project name from the repo root."""
    return root.name.replace(" ", "-").lower()


def get_worktree_dir(root: Path) -> Path:
    """Return the worktree base directory on LOCAL filesystem.

    Uses /tmp/agi-worktrees/<project>/ to avoid cloud-synced filesystem
    slowness (e.g., Synology Drive, iCloud, OneDrive, Dropbox).
    Git worktrees share .git internals, so they work fine from /tmp.
    """
    project = get_project_name(root)
    wt_dir = Path(f"/tmp/agi-worktrees/{project}")
    wt_dir.mkdir(parents=True, exist_ok=True)
    return wt_dir


def branch_name_for_agent(agent: str, run_id: str) -> str:
    """Generate a deterministic branch name for an agent task."""
    safe_agent = agent.replace(" ", "-").lower()
    return f"worktree/{run_id}/{safe_agent}"


def worktree_path_for_agent(root: Path, agent: str, run_id: str) -> Path:
    """Generate the worktree directory path for an agent."""
    wt_dir = get_worktree_dir(root)
    safe_agent = agent.replace(" ", "-").lower()
    return wt_dir / f"{run_id}-{safe_agent}"


# ─── COMMANDS ───────────────────────────────────────────────────────────

def cmd_create(args):
    """Create an isolated worktree for an agent."""
    root = find_project_root()
    agent = args.agent
    run_id = args.run_id or str(uuid.uuid4())[:8]
    base_branch = args.base_branch or get_current_branch()

    branch = branch_name_for_agent(agent, run_id)
    wt_path = worktree_path_for_agent(root, agent, run_id)

    if wt_path.exists():
        print(json.dumps({
            "status": "error",
            "message": f"Worktree already exists at {wt_path}",
            "hint": "Use 'cleanup' first or choose a different run-id"
        }))
        sys.exit(2)

    # Create worktree with new branch (in /tmp for speed)
    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(wt_path), base_branch],
        capture_output=True, text=True, cwd=str(root)
    )

    if result.returncode != 0:
        print(json.dumps({
            "status": "error",
            "message": f"Failed to create worktree: {result.stderr.strip()}",
            "command": f"git worktree add -b {branch} {wt_path} {base_branch}"
        }))
        sys.exit(2)

    # Copy .env if it exists (NotebookLM research: .env doesn't auto-copy)
    env_file = root / ".env"
    if env_file.exists():
        shutil.copy2(str(env_file), str(wt_path / ".env"))

    # Write worktree metadata
    meta = {
        "agent": agent,
        "run_id": run_id,
        "branch": branch,
        "base_branch": base_branch,
        "worktree_path": str(wt_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    meta_file = wt_path / ".worktree_meta.json"
    meta_file.write_text(json.dumps(meta, indent=2))

    print(json.dumps({
        "status": "success",
        "agent": agent,
        "run_id": run_id,
        "branch": branch,
        "base_branch": base_branch,
        "worktree_path": str(wt_path),
        "message": f"Worktree ready. Agent '{agent}' can work in {wt_path}"
    }, indent=2))


def cmd_merge(args):
    """Merge an agent's worktree branch back to the base branch."""
    root = find_project_root()
    agent = args.agent
    run_id = args.run_id
    strategy = args.strategy or "merge"

    branch = branch_name_for_agent(agent, run_id)
    wt_path = worktree_path_for_agent(root, agent, run_id)

    # Read metadata to get base branch
    meta_file = wt_path / ".worktree_meta.json"
    if not meta_file.exists():
        print(json.dumps({
            "status": "error",
            "message": f"No worktree metadata found at {wt_path}"
        }))
        sys.exit(2)

    meta = json.loads(meta_file.read_text())
    base_branch = meta["base_branch"]

    # Check if there are any commits to merge
    result = subprocess.run(
        ["git", "log", f"{base_branch}..{branch}", "--oneline"],
        capture_output=True, text=True, cwd=str(root)
    )
    commits = result.stdout.strip()

    if not commits:
        print(json.dumps({
            "status": "success",
            "message": f"No commits to merge from {branch}",
            "commits": 0
        }))
        return

    commit_count = len(commits.splitlines())

    # Check for potential conflicts before merging
    result = subprocess.run(
        ["git", "merge-tree", "--write-tree", base_branch, branch],
        capture_output=True, text=True, cwd=str(root)
    )

    has_conflicts = result.returncode != 0

    if has_conflicts and "CONFLICT" in result.stdout:
        # Extract conflicting files
        conflict_lines = [
            l for l in result.stdout.splitlines()
            if "CONFLICT" in l
        ]
        print(json.dumps({
            "status": "conflict",
            "agent": agent,
            "branch": branch,
            "base_branch": base_branch,
            "conflicts": conflict_lines,
            "message": (
                f"Merge conflicts detected between {branch} and {base_branch}. "
                f"Manual resolution required."
            ),
            "resolution_hint": (
                f"cd {root} && git checkout {base_branch} && "
                f"git merge {branch} (then resolve conflicts)"
            )
        }, indent=2))
        sys.exit(3)

    # Perform the merge
    if strategy == "rebase":
        merge_cmd = ["git", "rebase", branch, "--onto", base_branch]
    else:
        merge_cmd = [
            "git", "merge", branch,
            "-m", f"Merge agent '{agent}' work from run {run_id}"
        ]

    # Stash any uncommitted work on base branch first
    subprocess.run(["git", "stash", "push", "-m", f"pre-merge-{run_id}"],
                    capture_output=True, text=True, cwd=str(root))

    # Checkout base branch
    subprocess.run(["git", "checkout", base_branch],
                    capture_output=True, text=True, cwd=str(root))

    # Merge
    result = subprocess.run(
        merge_cmd, capture_output=True, text=True, cwd=str(root)
    )

    if result.returncode != 0:
        # Abort merge and restore
        subprocess.run(["git", "merge", "--abort"],
                        capture_output=True, text=True, cwd=str(root))
        subprocess.run(["git", "stash", "pop"],
                        capture_output=True, text=True, cwd=str(root))

        print(json.dumps({
            "status": "conflict",
            "agent": agent,
            "branch": branch,
            "message": f"Merge failed: {result.stderr.strip()}",
            "resolution_hint": f"Manually merge: git merge {branch}"
        }, indent=2))
        sys.exit(3)

    # Pop stash if we stashed
    subprocess.run(["git", "stash", "pop"],
                    capture_output=True, text=True, cwd=str(root))

    print(json.dumps({
        "status": "success",
        "agent": agent,
        "branch": branch,
        "base_branch": base_branch,
        "strategy": strategy,
        "commits_merged": commit_count,
        "message": f"Successfully merged {commit_count} commit(s) from '{agent}'"
    }, indent=2))


def cmd_cleanup(args):
    """Remove a worktree and optionally delete its branch."""
    root = find_project_root()
    agent = args.agent
    run_id = args.run_id

    branch = branch_name_for_agent(agent, run_id)
    wt_path = worktree_path_for_agent(root, agent, run_id)

    # Remove worktree
    if wt_path.exists():
        result = subprocess.run(
            ["git", "worktree", "remove", str(wt_path), "--force"],
            capture_output=True, text=True, cwd=str(root)
        )
        if result.returncode != 0:
            # Force remove directory if git worktree remove fails
            shutil.rmtree(str(wt_path), ignore_errors=True)
            subprocess.run(
                ["git", "worktree", "prune"],
                capture_output=True, text=True, cwd=str(root)
            )

    # Delete branch (only if merged or --force)
    if not args.keep_branch:
        subprocess.run(
            ["git", "branch", "-d", branch],
            capture_output=True, text=True, cwd=str(root)
        )

    print(json.dumps({
        "status": "success",
        "agent": agent,
        "run_id": run_id,
        "worktree_removed": str(wt_path),
        "branch_deleted": not args.keep_branch,
        "message": f"Cleaned up worktree for agent '{agent}'"
    }, indent=2))


def cmd_status(args):
    """Show all active agent worktrees."""
    root = find_project_root()

    # List git worktrees
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True, text=True, cwd=str(root)
    )

    worktrees = []
    current_wt = {}

    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current_wt:
                worktrees.append(current_wt)
            current_wt = {"path": line.split(" ", 1)[1]}
        elif line.startswith("HEAD "):
            current_wt["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current_wt["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line == "detached":
            current_wt["detached"] = True

    if current_wt:
        worktrees.append(current_wt)

    # Filter to agent worktrees (in .worktrees/ dir)
    agent_worktrees = []
    for wt in worktrees:
        wt_path = Path(wt["path"])
        meta_file = wt_path / ".worktree_meta.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text())
            wt["meta"] = meta
            if args.run_id and meta.get("run_id") != args.run_id:
                continue
            agent_worktrees.append(wt)

    print(json.dumps({
        "status": "success",
        "total_worktrees": len(worktrees),
        "agent_worktrees": len(agent_worktrees),
        "worktrees": agent_worktrees
    }, indent=2))


def cmd_validate_partitions(args):
    """
    Validate that file partitions for parallel agents don't overlap.
    Input: JSON mapping agent names to file glob patterns they'll modify.

    Example:
    {
      "agent-1": ["src/api/**", "src/models/**"],
      "agent-2": ["src/ui/**", "tests/**"],
      "agent-3": ["docs/**", "README.md"]
    }
    """
    try:
        partitions = json.loads(args.partitions)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)

    root = find_project_root()
    import glob as globmod

    # Resolve glob patterns to actual files
    resolved = {}
    for agent, patterns in partitions.items():
        files = set()
        for pattern in patterns:
            matches = globmod.glob(str(root / pattern), recursive=True)
            files.update(str(Path(m).relative_to(root)) for m in matches if Path(m).is_file())
        resolved[agent] = files

    # Check for overlaps
    overlaps = []
    agents = list(resolved.keys())
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a1, a2 = agents[i], agents[j]
            shared = resolved[a1] & resolved[a2]
            if shared:
                overlaps.append({
                    "agents": [a1, a2],
                    "shared_files": sorted(shared)
                })

    if overlaps:
        print(json.dumps({
            "status": "overlap_detected",
            "overlaps": overlaps,
            "message": (
                "File partitions overlap! Parallel agents may conflict. "
                "Reassign files so each agent has exclusive ownership."
            )
        }, indent=2))
        sys.exit(4)

    print(json.dumps({
        "status": "success",
        "partitions_valid": True,
        "agents": {a: len(f) for a, f in resolved.items()},
        "message": "No overlaps detected. Safe to dispatch in parallel."
    }, indent=2))


def cmd_create_all(args):
    """Create worktrees for all agents in a parallel dispatch."""
    try:
        agents = json.loads(args.agents)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)

    root = find_project_root()
    run_id = args.run_id or str(uuid.uuid4())[:8]
    base_branch = args.base_branch or get_current_branch()
    results = []

    for agent in agents:
        branch = branch_name_for_agent(agent, run_id)
        wt_path = worktree_path_for_agent(root, agent, run_id)

        if wt_path.exists():
            results.append({
                "agent": agent, "status": "skipped",
                "message": "Worktree already exists"
            })
            continue

        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(wt_path), base_branch],
            capture_output=True, text=True, cwd=str(root)
        )

        if result.returncode != 0:
            results.append({
                "agent": agent, "status": "error",
                "message": result.stderr.strip()
            })
            continue

        # Copy .env
        env_file = root / ".env"
        if env_file.exists():
            shutil.copy2(str(env_file), str(wt_path / ".env"))

        # Write metadata
        meta = {
            "agent": agent,
            "run_id": run_id,
            "branch": branch,
            "base_branch": base_branch,
            "worktree_path": str(wt_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        (wt_path / ".worktree_meta.json").write_text(json.dumps(meta, indent=2))

        results.append({
            "agent": agent, "status": "success",
            "branch": branch, "worktree_path": str(wt_path)
        })

    print(json.dumps({
        "status": "success",
        "run_id": run_id,
        "base_branch": base_branch,
        "agents": results
    }, indent=2))


def cmd_merge_all(args):
    """Sequentially merge all agent branches from a run back to base."""
    root = find_project_root()
    run_id = args.run_id
    strategy = args.strategy or "merge"

    # Find all worktrees for this run
    wt_dir = get_worktree_dir(root)
    results = []
    failed = []

    for item in sorted(wt_dir.iterdir()):
        if not item.is_dir() or not item.name.startswith(run_id):
            continue
        meta_file = item / ".worktree_meta.json"
        if not meta_file.exists():
            continue

        meta = json.loads(meta_file.read_text())
        agent = meta["agent"]
        branch = meta["branch"]
        base_branch = meta["base_branch"]

        # Check commits
        log_result = subprocess.run(
            ["git", "log", f"{base_branch}..{branch}", "--oneline"],
            capture_output=True, text=True, cwd=str(root)
        )
        commits = log_result.stdout.strip()

        if not commits:
            results.append({
                "agent": agent, "status": "skipped",
                "message": "No commits to merge"
            })
            continue

        commit_count = len(commits.splitlines())

        # Checkout base and merge
        subprocess.run(["git", "checkout", base_branch],
                        capture_output=True, text=True, cwd=str(root))

        merge_result = subprocess.run(
            ["git", "merge", branch,
             "-m", f"Merge agent '{agent}' work from run {run_id}"],
            capture_output=True, text=True, cwd=str(root)
        )

        if merge_result.returncode != 0:
            subprocess.run(["git", "merge", "--abort"],
                            capture_output=True, text=True, cwd=str(root))
            failed.append(agent)
            results.append({
                "agent": agent, "status": "conflict",
                "message": merge_result.stderr.strip(),
                "commits": commit_count
            })
        else:
            results.append({
                "agent": agent, "status": "merged",
                "commits": commit_count
            })

    print(json.dumps({
        "status": "success" if not failed else "partial",
        "run_id": run_id,
        "merged": [r for r in results if r["status"] == "merged"],
        "conflicts": [r for r in results if r["status"] == "conflict"],
        "skipped": [r for r in results if r["status"] == "skipped"],
        "message": (
            f"All agents merged successfully"
            if not failed
            else f"Conflicts in: {', '.join(failed)}. Resolve manually."
        )
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Git worktree manager for parallel agent isolation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create isolated worktree for an agent")
    p_create.add_argument("--agent", required=True, help="Agent name/ID")
    p_create.add_argument("--run-id", help="Run ID (auto-generated if omitted)")
    p_create.add_argument("--base-branch", help="Branch to base worktree on (default: current)")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge agent's worktree branch back")
    p_merge.add_argument("--agent", required=True, help="Agent name/ID")
    p_merge.add_argument("--run-id", required=True, help="Run ID")
    p_merge.add_argument("--strategy", choices=["merge", "rebase"], default="merge")

    # cleanup
    p_cleanup = subparsers.add_parser("cleanup", help="Remove worktree and branch")
    p_cleanup.add_argument("--agent", required=True, help="Agent name/ID")
    p_cleanup.add_argument("--run-id", required=True, help="Run ID")
    p_cleanup.add_argument("--keep-branch", action="store_true", help="Keep the branch after cleanup")

    # status
    p_status = subparsers.add_parser("status", help="List all active agent worktrees")
    p_status.add_argument("--run-id", help="Filter by run ID")

    # validate-partitions
    p_validate = subparsers.add_parser("validate-partitions",
                                        help="Check file partitions for overlap")
    p_validate.add_argument("--partitions", required=True,
                            help="JSON mapping agents to file globs")

    # create-all
    p_create_all = subparsers.add_parser("create-all",
                                          help="Create worktrees for all agents in a run")
    p_create_all.add_argument("--agents", required=True, help="JSON array of agent names")
    p_create_all.add_argument("--run-id", help="Shared run ID")
    p_create_all.add_argument("--base-branch", help="Base branch")

    # merge-all
    p_merge_all = subparsers.add_parser("merge-all",
                                         help="Merge all agent branches from a run")
    p_merge_all.add_argument("--run-id", required=True, help="Run ID")
    p_merge_all.add_argument("--strategy", choices=["merge", "rebase"], default="merge")

    args = parser.parse_args()

    commands = {
        "create": cmd_create,
        "merge": cmd_merge,
        "cleanup": cmd_cleanup,
        "status": cmd_status,
        "validate-partitions": cmd_validate_partitions,
        "create-all": cmd_create_all,
        "merge-all": cmd_merge_all,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
