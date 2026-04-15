#!/usr/bin/env bash
# ask_design.sh — thin wrapper that forwards a design question to the notebooklm skill.
#
# Usage:
#   bash skills/claude-code-design/scripts/ask_design.sh "<question>" [--notebook-id ID | --notebook-url URL]
#
# Behavior:
#   - If no --notebook-id / --notebook-url is passed, uses the active notebook in the
#     notebooklm library (expected to be the Claude Code Design notebook).
#   - Emits a hint to stderr if no notebook is registered yet.
#
# Exit codes:
#   0 success, 1 missing args, >1 underlying notebooklm error.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: ask_design.sh \"<question>\" [--notebook-id ID | --notebook-url URL]" >&2
  exit 1
fi

QUESTION="$1"
shift || true

# Locate repo root by walking up until skills/notebooklm exists.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
while [[ "$REPO_ROOT" != "/" && ! -d "$REPO_ROOT/skills/notebooklm" ]]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done

if [[ ! -d "$REPO_ROOT/skills/notebooklm" ]]; then
  echo "error: could not locate skills/notebooklm from $SCRIPT_DIR" >&2
  exit 2
fi

RUN_PY="$REPO_ROOT/skills/notebooklm/scripts/run.py"
if [[ ! -f "$RUN_PY" ]]; then
  echo "error: expected wrapper at $RUN_PY" >&2
  exit 2
fi

# Hint if no Claude Code Design notebook is registered.
if ! python "$RUN_PY" notebook_manager.py search --query "claude code design" 2>/dev/null | grep -qi "claude code"; then
  echo "hint: no 'Claude Code Design' notebook found in library; answer may fall back to defaults" >&2
fi

exec python "$RUN_PY" ask_question.py --question "$QUESTION" "$@"
