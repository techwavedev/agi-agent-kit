#!/usr/bin/env python3
"""
Script: dashboard/server.py
Purpose: Lightweight HTTP server for the team-run dashboard.
         Serves dashboard/index.html and exposes .tmp/team-runs/ state files
         via a simple JSON API so the browser can read them without CORS issues.

Usage:
    # From project root:
    python3 dashboard/server.py

    # Custom port / host:
    python3 dashboard/server.py --port 8765 --host 0.0.0.0

    # Custom state dir (default: .tmp/team-runs relative to project root):
    python3 dashboard/server.py --state-dir /path/to/.tmp/team-runs

Arguments:
    --port       Port to listen on (default: 8765)
    --host       Bind address (default: 127.0.0.1)
    --state-dir  Directory containing per-run state.json files
    --open       Open the browser automatically after starting

Exit Codes:
    0 - Server stopped cleanly
    1 - Startup error
"""

import argparse
import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent.parent
    for candidate in [current] + list(current.parents):
        if (candidate / "AGENTS.md").exists() or (candidate / "package.json").exists():
            return candidate
    return current


DASHBOARD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = find_project_root()


def get_state_dir(override: str = None) -> Path:
    if override:
        return Path(override)
    return PROJECT_ROOT / ".tmp" / "team-runs"


def load_all_states(state_dir: Path) -> list:
    """Read every state.json and return a list of dicts, newest first."""
    if not state_dir.exists():
        return []
    results = []
    for sf in sorted(state_dir.glob("*/state.json"), reverse=True):
        try:
            results.append(json.loads(sf.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return results


def load_single_state(state_dir: Path, run_id: str) -> dict | None:
    sf = state_dir / run_id / "state.json"
    if not sf.exists():
        return None
    try:
        return json.loads(sf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


class DashboardHandler(BaseHTTPRequestHandler):
    state_dir: Path = None  # set by factory

    def log_message(self, fmt, *args):  # quieter logs
        print(f"[dashboard] {self.address_string()} - {fmt % args}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        # ── Static assets ──────────────────────────────────────────────────
        if path in ("/", "/index.html"):
            self._send_file(DASHBOARD_DIR / "index.html", "text/html; charset=utf-8")
            return

        # ── API: list all runs ──────────────────────────────────────────────
        if path == "/api/runs":
            states = load_all_states(self.state_dir)
            self._send_json(states)
            return

        # ── API: list active runs only ─────────────────────────────────────
        if path == "/api/runs/active":
            states = [s for s in load_all_states(self.state_dir)
                      if s.get("status") in ("pending", "running")]
            self._send_json(states)
            return

        # ── API: single run ────────────────────────────────────────────────
        if path.startswith("/api/runs/"):
            run_id = path[len("/api/runs/"):]
            state = load_single_state(self.state_dir, run_id)
            if state is None:
                self._send_json({"error": "run not found"}, 404)
            else:
                self._send_json(state)
            return

        self.send_error(404, "Not found")


def make_handler(state_dir: Path):
    """Return a DashboardHandler subclass bound to state_dir."""
    class _H(DashboardHandler):
        pass
    _H.state_dir = state_dir
    return _H


def main():
    parser = argparse.ArgumentParser(description="Team-run dashboard server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--state-dir", default=None,
                        help="Path to team-runs directory (default: .tmp/team-runs)")
    parser.add_argument("--open", action="store_true",
                        help="Open browser automatically")
    args = parser.parse_args()

    state_dir = get_state_dir(args.state_dir)
    handler = make_handler(state_dir)
    server = HTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}"
    print(f"[dashboard] Serving at {url}")
    print(f"[dashboard] Reading state from: {state_dir}")
    print(f"[dashboard] Press Ctrl-C to stop")

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[dashboard] Stopped.")
    sys.exit(0)


if __name__ == "__main__":
    main()
