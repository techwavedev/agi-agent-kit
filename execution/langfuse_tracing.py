#!/usr/bin/env python3
"""
Script: langfuse_tracing.py
Purpose: Shared Langfuse client for the AGI Agent Kit framework.
         Provides a singleton client, trace helpers, and health check.
         Gracefully degrades to no-ops when Langfuse is not configured.

Usage (as library):
    from langfuse_tracing import get_client, trace_operation, check_langfuse, flush

Usage (CLI):
    python3 execution/langfuse_tracing.py health
    python3 execution/langfuse_tracing.py flush
    python3 execution/langfuse_tracing.py summary --since 60

Environment Variables:
    LANGFUSE_ENABLED     - "true" to enable (default: false)
    LANGFUSE_HOST        - Server URL (default: http://localhost:3000)
    LANGFUSE_PUBLIC_KEY  - API public key
    LANGFUSE_SECRET_KEY  - API secret key
    LANGFUSE_PROJECT     - Default project tag (default: agi-agent-kit)
    LANGFUSE_RELEASE     - Release tag (default: local-dev)

Exit Codes:
    0 - Success / Langfuse reachable
    1 - Langfuse not configured (keys missing)
    2 - Langfuse unreachable
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from functools import wraps
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ─── Configuration ───────────────────────────────────────────────────────────

LANGFUSE_ENABLED = os.environ.get("LANGFUSE_ENABLED", "false").lower() == "true"
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PROJECT = os.environ.get("LANGFUSE_PROJECT", "agi-agent-kit")
LANGFUSE_RELEASE = os.environ.get("LANGFUSE_RELEASE", "local-dev")

_client = None
_initialized = False


# ─── Client Management ──────────────────────────────────────────────────────

def _is_configured() -> bool:
    """Check if Langfuse has valid credentials."""
    return bool(LANGFUSE_ENABLED and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)


def get_client():
    """Get or create the singleton Langfuse client. Returns None if not configured."""
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True

    if not _is_configured():
        return None

    try:
        from langfuse import Langfuse
        _client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
            release=LANGFUSE_RELEASE,
            enabled=True,
        )
        return _client
    except ImportError:
        return None
    except Exception:
        return None


def flush():
    """Flush any pending Langfuse events. Safe to call even if disabled."""
    client = get_client()
    if client:
        try:
            client.flush()
            return True
        except Exception:
            pass
    return False


def shutdown():
    """Flush and shutdown the Langfuse client."""
    global _client, _initialized
    if _client:
        try:
            _client.flush()
            _client.shutdown()
        except Exception:
            pass
    _client = None
    _initialized = False


# ─── Tracing Helpers ─────────────────────────────────────────────────────────

def trace_operation(name: str, metadata: dict = None, user_id: str = None,
                    session_id: str = None, tags: list = None):
    """
    Create a Langfuse trace for a framework operation.
    Returns a trace object, or a no-op stub if Langfuse is disabled.
    """
    client = get_client()
    if not client:
        return _NoOpTrace()

    trace_tags = [LANGFUSE_PROJECT]
    if tags:
        trace_tags.extend(tags)

    try:
        return client.trace(
            name=name,
            metadata=metadata or {},
            user_id=user_id or "agent",
            session_id=session_id,
            tags=trace_tags,
            release=LANGFUSE_RELEASE,
        )
    except Exception:
        return _NoOpTrace()


def observe_function(name: str = None, op_type: str = "span"):
    """
    Decorator to trace a function call as a Langfuse span/generation.
    Gracefully no-ops if Langfuse is unavailable.

    Usage:
        @observe_function("memory_store", op_type="span")
        def store_memory(content, type, metadata):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = get_client()
            if not client:
                return func(*args, **kwargs)

            trace_name = name or func.__name__
            start = time.time()
            trace = None
            span = None
            try:
                trace = client.trace(
                    name=trace_name,
                    tags=[LANGFUSE_PROJECT, op_type],
                    release=LANGFUSE_RELEASE,
                )
                span = trace.span(
                    name=trace_name,
                    input=_safe_serialize(args, kwargs),
                )
            except Exception:
                pass

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                if span:
                    try:
                        span.end(
                            output=_safe_output(result),
                            metadata={"duration_ms": round(duration_ms, 2)},
                        )
                    except Exception:
                        pass
                return result
            except Exception as e:
                if span:
                    try:
                        span.end(
                            output={"error": str(e)},
                            level="ERROR",
                        )
                    except Exception:
                        pass
                raise
        return wrapper
    return decorator


def score_trace(trace_id: str, name: str, value: float, comment: str = None):
    """Score a trace (e.g., cache_hit=1, retrieval_quality=0.8)."""
    client = get_client()
    if not client:
        return
    try:
        client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )
    except Exception:
        pass


# ─── Health Check ────────────────────────────────────────────────────────────

def check_langfuse() -> dict:
    """Check Langfuse connectivity and configuration."""
    result = {
        "status": "disabled",
        "configured": _is_configured(),
        "host": LANGFUSE_HOST,
        "has_keys": bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY),
        "sdk_installed": False,
    }

    # Check SDK
    try:
        import langfuse  # noqa: F401
        result["sdk_installed"] = True
        result["sdk_version"] = getattr(langfuse, "__version__", "unknown")
    except ImportError:
        result["hint"] = "pip install langfuse"
        return result

    if not _is_configured():
        result["status"] = "not_configured"
        if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
            result["hint"] = (
                "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env. "
                "Get them from http://localhost:3000 > Settings > API Keys"
            )
        return result

    # Check server connectivity
    try:
        req = Request(
            f"{LANGFUSE_HOST}/api/public/health",
            method="GET",
            headers={"Accept": "application/json"},
        )
        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result["status"] = "ok" if data.get("status") == "OK" else "degraded"
            result["server_version"] = data.get("version", "unknown")
    except (URLError, HTTPError) as e:
        result["status"] = "unreachable"
        result["error"] = str(e)
        result["hint"] = "Start Langfuse: docker compose -f docker-compose.langfuse.yml up -d"
    except Exception as e:
        result["status"] = f"error: {e}"

    # Verify API key auth
    if result["status"] == "ok":
        try:
            import base64
            credentials = base64.b64encode(
                f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
            ).decode()
            req = Request(
                f"{LANGFUSE_HOST}/api/public/projects",
                method="GET",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Basic {credentials}",
                },
            )
            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                projects = data.get("data", [])
                result["projects"] = [p.get("name") for p in projects]
                result["auth"] = "ok"
        except HTTPError as e:
            if e.code == 401:
                result["auth"] = "invalid_keys"
                result["hint"] = "API keys are invalid. Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY"
            else:
                result["auth"] = f"error: {e.code}"
        except Exception as e:
            result["auth"] = f"error: {e}"

    return result


# ─── Session Metrics ─────────────────────────────────────────────────────────

def get_session_summary(since_minutes: int = 60) -> dict:
    """
    Query Langfuse API for traces from the current session.
    Returns counts, latencies, and error rates.
    """
    result = {
        "status": "disabled",
        "traces": 0,
        "errors": 0,
        "avg_latency_ms": 0,
        "operations": {},
    }

    if not _is_configured():
        return result

    try:
        import base64
        credentials = base64.b64encode(
            f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
        ).decode()

        # Query recent traces
        from_time = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).isoformat()
        req = Request(
            f"{LANGFUSE_HOST}/api/public/traces?limit=100&orderBy=timestamp.desc",
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {credentials}",
            },
        )
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

        traces = data.get("data", [])

        # Filter by time window
        recent = []
        for t in traces:
            ts = t.get("timestamp", "")
            if ts >= from_time:
                recent.append(t)

        result["status"] = "ok"
        result["traces"] = len(recent)

        # Aggregate by operation name
        ops = {}
        total_latency = 0
        error_count = 0
        for t in recent:
            name = t.get("name", "unknown")
            latency = t.get("latency")  # in seconds if present
            if name not in ops:
                ops[name] = {"count": 0, "errors": 0, "total_latency_ms": 0}
            ops[name]["count"] += 1
            if latency is not None:
                lat_ms = latency * 1000 if latency < 100 else latency  # handle s vs ms
                ops[name]["total_latency_ms"] += lat_ms
                total_latency += lat_ms
            # Check for errors in metadata or tags
            tags = t.get("tags", [])
            if "error" in tags or t.get("level") == "ERROR":
                ops[name]["errors"] += 1
                error_count += 1

        # Compute averages
        for name, op in ops.items():
            if op["count"] > 0 and op["total_latency_ms"] > 0:
                op["avg_latency_ms"] = round(op["total_latency_ms"] / op["count"], 1)
            del op["total_latency_ms"]

        result["errors"] = error_count
        result["operations"] = ops
        if recent:
            result["avg_latency_ms"] = round(total_latency / len(recent), 1) if total_latency > 0 else 0

    except ImportError:
        result["status"] = "sdk_missing"
    except (URLError, HTTPError) as e:
        result["status"] = f"error: {e}"
    except Exception as e:
        result["status"] = f"error: {e}"

    return result


# ─── Internal Helpers ────────────────────────────────────────────────────────

def _safe_serialize(args, kwargs) -> dict:
    """Safely serialize function args for Langfuse input."""
    try:
        serialized = {}
        for i, a in enumerate(args):
            if isinstance(a, (str, int, float, bool)):
                serialized[f"arg_{i}"] = a
            elif isinstance(a, dict):
                serialized[f"arg_{i}"] = {k: str(v)[:200] for k, v in a.items()}
            else:
                serialized[f"arg_{i}"] = str(a)[:200]
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                serialized[k] = v
            else:
                serialized[k] = str(v)[:200]
        return serialized
    except Exception:
        return {"args": "serialization_error"}


def _safe_output(result) -> dict:
    """Safely serialize function output for Langfuse."""
    try:
        if isinstance(result, dict):
            return {k: str(v)[:500] for k, v in result.items()}
        return {"result": str(result)[:500]}
    except Exception:
        return {"result": "serialization_error"}


class _NoOpTrace:
    """Stub trace that silently ignores all calls."""
    def __getattr__(self, name):
        def noop(*args, **kwargs):
            return _NoOpTrace()
        return noop


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Langfuse tracing management for AGI Agent Kit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Check Langfuse connectivity and configuration")

    subparsers.add_parser("flush", help="Flush pending Langfuse events")

    summary_parser = subparsers.add_parser("summary", help="Session trace summary")
    summary_parser.add_argument("--since", type=int, default=60, help="Minutes to look back (default: 60)")
    summary_parser.add_argument("--json", action="store_true", dest="json_output")

    args = parser.parse_args()

    if args.command == "health":
        result = check_langfuse()
        print(json.dumps(result, indent=2))
        if result["status"] == "ok":
            print(f"\n  Langfuse ready at {LANGFUSE_HOST}")
            if result.get("projects"):
                print(f"  Projects: {', '.join(result['projects'])}")
            sys.exit(0)
        elif result["status"] == "not_configured":
            print(f"\n  Langfuse not configured — {result.get('hint', 'set env vars')}")
            sys.exit(1)
        else:
            print(f"\n  Langfuse: {result['status']}")
            if result.get("hint"):
                print(f"  Hint: {result['hint']}")
            sys.exit(2)

    elif args.command == "flush":
        if flush():
            print("Langfuse events flushed.")
        else:
            print("Langfuse not active — nothing to flush.")
        sys.exit(0)

    elif args.command == "summary":
        result = get_session_summary(args.since)
        if getattr(args, "json_output", False):
            print(json.dumps(result, indent=2))
        else:
            if result["status"] == "disabled":
                print("  Langfuse tracing disabled (not configured)")
                sys.exit(1)
            elif result["status"] != "ok":
                print(f"  Langfuse error: {result['status']}")
                sys.exit(2)
            else:
                print(f"\n  Langfuse Traces (last {args.since}m)")
                print(f"  Total: {result['traces']}  Errors: {result['errors']}  Avg latency: {result['avg_latency_ms']}ms")
                if result["operations"]:
                    print(f"\n  {'Operation':<35} {'Count':>6} {'Errors':>7} {'Avg ms':>8}")
                    print(f"  {'─'*35} {'─'*6} {'─'*7} {'─'*8}")
                    for name, op in sorted(result["operations"].items(), key=lambda x: x[1]["count"], reverse=True):
                        print(f"  {name:<35} {op['count']:>6} {op['errors']:>7} {op.get('avg_latency_ms', 0):>8.1f}")
                else:
                    print("  No operations recorded.")
                print()
        sys.exit(0)


if __name__ == "__main__":
    main()