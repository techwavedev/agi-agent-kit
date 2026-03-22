#!/usr/bin/env python3
"""
Script: langfuse_dashboard.py
Purpose: CLI dashboard for querying Langfuse traces, latencies, error rates,
         and comparing performance before/after framework changes.
         This is the primary tool for developers to measure improvement effectiveness.

Usage:
    python3 execution/langfuse_dashboard.py overview
    python3 execution/langfuse_dashboard.py overview --since 120
    python3 execution/langfuse_dashboard.py compare --before 60 --after 30
    python3 execution/langfuse_dashboard.py traces --name memory_store --limit 20
    python3 execution/langfuse_dashboard.py errors --since 60
    python3 execution/langfuse_dashboard.py slow --threshold 2000 --since 120

Environment Variables:
    LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY (from .env)

Exit Codes:
    0 - Success
    1 - Langfuse not configured
    2 - Langfuse unreachable
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")


def _auth_header() -> str:
    return base64.b64encode(
        f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
    ).decode()


def _api_get(path: str, timeout: int = 10) -> dict:
    """Make authenticated GET request to Langfuse API."""
    req = Request(
        f"{LANGFUSE_HOST}{path}",
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {_auth_header()}",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode())


def _check_configured():
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        print(f"Dashboard URL: {LANGFUSE_HOST}")
        sys.exit(1)


def _fetch_traces(since_minutes: int, limit: int = 200, name_filter: str = None) -> list:
    """Fetch traces from Langfuse API within time window."""
    params = f"limit={limit}&orderBy=timestamp.desc"
    data = _api_get(f"/api/public/traces?{params}")
    traces = data.get("data", [])

    # Filter by time
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()
    filtered = [t for t in traces if t.get("timestamp", "") >= cutoff]

    # Filter by name if specified
    if name_filter:
        filtered = [t for t in filtered if name_filter.lower() in t.get("name", "").lower()]

    return filtered


def _aggregate_traces(traces: list) -> dict:
    """Aggregate trace data into operation-level metrics."""
    ops = {}
    for t in traces:
        name = t.get("name", "unknown")
        if name not in ops:
            ops[name] = {
                "count": 0,
                "errors": 0,
                "latencies_ms": [],
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
            }
        op = ops[name]
        op["count"] += 1

        # Latency
        latency = t.get("latency")
        if latency is not None:
            lat_ms = latency * 1000 if latency < 100 else latency
            op["latencies_ms"].append(lat_ms)

        # Errors
        tags = t.get("tags", [])
        if "error" in tags or t.get("level") == "ERROR":
            op["errors"] += 1

        # Token usage (from observations/generations within the trace)
        usage = t.get("usage", {}) or {}
        op["input_tokens"] += usage.get("input", 0) or 0
        op["output_tokens"] += usage.get("output", 0) or 0
        op["total_cost"] += usage.get("totalCost", 0) or t.get("totalCost", 0) or 0

    # Compute stats
    for name, op in ops.items():
        lats = op["latencies_ms"]
        if lats:
            lats.sort()
            op["avg_ms"] = round(sum(lats) / len(lats), 1)
            op["p50_ms"] = round(lats[len(lats) // 2], 1)
            op["p95_ms"] = round(lats[int(len(lats) * 0.95)], 1) if len(lats) >= 2 else op["avg_ms"]
            op["min_ms"] = round(lats[0], 1)
            op["max_ms"] = round(lats[-1], 1)
        else:
            op["avg_ms"] = op["p50_ms"] = op["p95_ms"] = op["min_ms"] = op["max_ms"] = 0
        del op["latencies_ms"]
        op["error_rate"] = round(op["errors"] / op["count"] * 100, 1) if op["count"] > 0 else 0

    return ops


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_overview(args):
    """Show high-level overview of framework tracing metrics."""
    traces = _fetch_traces(args.since)
    ops = _aggregate_traces(traces)

    total_traces = sum(o["count"] for o in ops.values())
    total_errors = sum(o["errors"] for o in ops.values())
    total_cost = sum(o["total_cost"] for o in ops.values())

    print(f"\n  Langfuse Dashboard — last {args.since} minutes")
    print(f"  {'═' * 60}")
    print(f"  Total traces: {total_traces}  |  Errors: {total_errors}  |  Est. cost: ${total_cost:.4f}")
    print(f"  Dashboard: {LANGFUSE_HOST}")

    if not ops:
        print("\n  No traces found in this time window.")
        return

    print(f"\n  {'Operation':<30} {'Count':>6} {'Err%':>6} {'Avg':>8} {'P50':>8} {'P95':>8} {'Max':>8}")
    print(f"  {'─' * 30} {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")

    for name, op in sorted(ops.items(), key=lambda x: x[1]["count"], reverse=True):
        err_str = f"{op['error_rate']}%" if op['error_rate'] > 0 else "—"
        print(f"  {name:<30} {op['count']:>6} {err_str:>6} {op['avg_ms']:>7.0f}ms {op['p50_ms']:>7.0f}ms {op['p95_ms']:>7.0f}ms {op['max_ms']:>7.0f}ms")

    print()

    if args.json:
        print(json.dumps({"traces": total_traces, "errors": total_errors, "operations": ops}, indent=2))


def cmd_compare(args):
    """Compare metrics between two time windows (before vs after a change)."""
    now_min = datetime.now(timezone.utc)

    # "after" = last N minutes, "before" = the N minutes before that
    after_traces = _fetch_traces(args.after)
    before_traces = _fetch_traces(args.before + args.after)

    # Remove "after" traces from "before" set
    after_ids = {t.get("id") for t in after_traces}
    before_traces = [t for t in before_traces if t.get("id") not in after_ids]

    before_ops = _aggregate_traces(before_traces)
    after_ops = _aggregate_traces(after_traces)

    all_names = sorted(set(list(before_ops.keys()) + list(after_ops.keys())))

    print(f"\n  Performance Comparison")
    print(f"  Before: {args.before + args.after}-{args.after}min ago ({len(before_traces)} traces)")
    print(f"  After:  last {args.after}min ({len(after_traces)} traces)")
    print(f"  {'═' * 72}")

    print(f"\n  {'Operation':<25} {'Before':>12} {'After':>12} {'Change':>12} {'Verdict':>10}")
    print(f"  {'─' * 25} {'─' * 12} {'─' * 12} {'─' * 12} {'─' * 10}")

    for name in all_names:
        b = before_ops.get(name, {})
        a = after_ops.get(name, {})
        b_avg = b.get("avg_ms", 0)
        a_avg = a.get("avg_ms", 0)
        b_count = b.get("count", 0)
        a_count = a.get("count", 0)

        if b_avg > 0 and a_avg > 0:
            pct_change = ((a_avg - b_avg) / b_avg) * 100
            change_str = f"{pct_change:+.1f}%"
            if pct_change < -10:
                verdict = "FASTER"
            elif pct_change > 10:
                verdict = "SLOWER"
            else:
                verdict = "~same"
        elif a_avg > 0:
            change_str = "new"
            verdict = "—"
        else:
            change_str = "gone"
            verdict = "—"

        b_str = f"{b_avg:.0f}ms ({b_count}x)" if b_count > 0 else "—"
        a_str = f"{a_avg:.0f}ms ({a_count}x)" if a_count > 0 else "—"

        print(f"  {name:<25} {b_str:>12} {a_str:>12} {change_str:>12} {verdict:>10}")

    # Error rate comparison
    b_errors = sum(o.get("errors", 0) for o in before_ops.values())
    a_errors = sum(o.get("errors", 0) for o in after_ops.values())
    print(f"\n  Error totals: {b_errors} -> {a_errors}")
    print()


def cmd_traces(args):
    """List individual traces filtered by name."""
    traces = _fetch_traces(args.since, limit=args.limit, name_filter=args.name)

    print(f"\n  Recent Traces" + (f" (filter: {args.name})" if args.name else ""))
    print(f"  {'─' * 70}")

    for t in traces[:args.limit]:
        ts = t.get("timestamp", "")[:19]
        name = t.get("name", "unknown")
        latency = t.get("latency")
        lat_str = f"{latency * 1000:.0f}ms" if latency and latency < 100 else (f"{latency:.0f}ms" if latency else "—")
        tags = t.get("tags", [])
        level = t.get("level", "")
        status = "ERR" if level == "ERROR" or "error" in tags else "ok"

        print(f"  {ts}  {name:<30} {lat_str:>8}  {status}")

    print(f"\n  Showing {min(len(traces), args.limit)} of {len(traces)} traces")
    print(f"  Full details: {LANGFUSE_HOST}/traces")
    print()


def cmd_errors(args):
    """Show recent error traces."""
    traces = _fetch_traces(args.since)
    errors = [t for t in traces if t.get("level") == "ERROR" or "error" in t.get("tags", [])]

    print(f"\n  Error Traces (last {args.since}m)")
    print(f"  {'─' * 70}")

    if not errors:
        print("  No errors found.")
    else:
        for t in errors[:20]:
            ts = t.get("timestamp", "")[:19]
            name = t.get("name", "unknown")
            metadata = t.get("metadata", {})
            error_msg = metadata.get("error", "")[:60] if metadata else ""
            print(f"  {ts}  {name:<30}  {error_msg}")

    print(f"\n  Total errors: {len(errors)} / {len(traces)} traces ({len(errors)/len(traces)*100:.1f}% error rate)" if traces else "")
    print()


def cmd_slow(args):
    """Show traces slower than threshold."""
    traces = _fetch_traces(args.since)
    threshold_s = args.threshold / 1000  # convert ms to s

    slow = []
    for t in traces:
        latency = t.get("latency")
        if latency is not None:
            lat_ms = latency * 1000 if latency < 100 else latency
            if lat_ms >= args.threshold:
                slow.append((t, lat_ms))

    slow.sort(key=lambda x: x[1], reverse=True)

    print(f"\n  Slow Traces (>{args.threshold}ms, last {args.since}m)")
    print(f"  {'─' * 70}")

    if not slow:
        print(f"  No traces slower than {args.threshold}ms.")
    else:
        for t, lat_ms in slow[:20]:
            ts = t.get("timestamp", "")[:19]
            name = t.get("name", "unknown")
            print(f"  {ts}  {name:<30} {lat_ms:>8.0f}ms")

    print(f"\n  {len(slow)} slow traces / {len(traces)} total")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Langfuse observability dashboard for AGI Agent Kit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Overall metrics for the last hour
  python3 execution/langfuse_dashboard.py overview

  # Compare before/after a change (last 30min vs previous 60min)
  python3 execution/langfuse_dashboard.py compare --before 60 --after 30

  # Find slow operations
  python3 execution/langfuse_dashboard.py slow --threshold 1000

  # List recent memory_store traces
  python3 execution/langfuse_dashboard.py traces --name memory_store
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # overview
    ov = subparsers.add_parser("overview", help="High-level metrics overview")
    ov.add_argument("--since", type=int, default=60, help="Minutes to look back (default: 60)")
    ov.add_argument("--json", action="store_true", help="Also output JSON")

    # compare
    cp = subparsers.add_parser("compare", help="Compare before/after performance")
    cp.add_argument("--before", type=int, default=60, help="'Before' window in minutes (default: 60)")
    cp.add_argument("--after", type=int, default=30, help="'After' window in minutes (default: 30)")

    # traces
    tr = subparsers.add_parser("traces", help="List individual traces")
    tr.add_argument("--name", help="Filter by operation name (substring match)")
    tr.add_argument("--since", type=int, default=60, help="Minutes to look back (default: 60)")
    tr.add_argument("--limit", type=int, default=20, help="Max traces to show (default: 20)")

    # errors
    er = subparsers.add_parser("errors", help="Show error traces")
    er.add_argument("--since", type=int, default=60, help="Minutes to look back (default: 60)")

    # slow
    sl = subparsers.add_parser("slow", help="Show traces slower than threshold")
    sl.add_argument("--threshold", type=int, default=2000, help="Latency threshold in ms (default: 2000)")
    sl.add_argument("--since", type=int, default=120, help="Minutes to look back (default: 120)")

    args = parser.parse_args()
    _check_configured()

    try:
        if args.command == "overview":
            cmd_overview(args)
        elif args.command == "compare":
            cmd_compare(args)
        elif args.command == "traces":
            cmd_traces(args)
        elif args.command == "errors":
            cmd_errors(args)
        elif args.command == "slow":
            cmd_slow(args)
    except (URLError, HTTPError) as e:
        print(f"Langfuse unreachable: {e}")
        print(f"Is Langfuse running? docker compose -f docker-compose.langfuse.yml up -d")
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()