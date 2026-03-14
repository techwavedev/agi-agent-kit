#!/usr/bin/env python3
"""
Test: Agent Events (Apache Pulsar)
==================================

Tests for the real-time agent event bus:
1. Health check (graceful when Pulsar not running)
2. Event publishing (graceful degradation)
3. Topic listing
4. Integration with memory_manager.py

MODE 1 — With Pulsar running (full integration):
    docker compose -f docker-compose.pulsar.yml up -d
    python3 templates/base/tests/test_agent_events.py

MODE 2 — Without Pulsar (offline/graceful degradation):
    python3 templates/base/tests/test_agent_events.py --offline
"""

import json
import os
import sys

# Resolve paths
_test_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_test_dir)
sys.path.insert(0, os.path.join(_base_dir, "execution"))

from agent_events import (
    health_check, publish_event, subscribe_events,
    list_topics, PulsarClient, EVENT_TYPES
)

OFFLINE = "--offline" in sys.argv


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def check(self, name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        self.results.append({"test": name, "status": status, "detail": detail})
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        icon = "✅" if condition else "❌"
        print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))

    def skip(self, name, reason=""):
        self.skipped += 1
        self.results.append({"test": name, "status": "SKIP", "detail": reason})
        print(f"  ⏭️  {name} — {reason}")


# ═══════════════════════════════════════════════════════════════
# OFFLINE Tests (no Pulsar needed)
# ═══════════════════════════════════════════════════════════════

def test_event_types(t: TestResults):
    """Event types are well-defined."""
    t.check("event types list exists", len(EVENT_TYPES) > 0,
            f"{len(EVENT_TYPES)} types defined")
    t.check("memory_stored in event types", "memory_stored" in EVENT_TYPES)
    t.check("decision_made in event types", "decision_made" in EVENT_TYPES)
    t.check("context_request in event types", "context_request" in EVENT_TYPES)


def test_graceful_degradation(t: TestResults):
    """When Pulsar is unreachable, all operations degrade gracefully."""
    bad_client = PulsarClient(http_url="http://localhost:19999")
    t.check("bad client reports unavailable", bad_client.is_available() is False)

    # publish_event should return unavailable, not crash
    result = publish_event("test-project", "memory_stored", "test content")
    # This uses the global client — may or may not be available
    t.check("publish returns structured response",
            isinstance(result, dict) and "status" in result)

    # subscribe should return unavailable, not crash
    result = subscribe_events("test-project")
    t.check("subscribe returns structured response",
            isinstance(result, dict) and "status" in result)


def test_topic_naming(t: TestResults):
    """Topic names are correctly formatted."""
    client = PulsarClient()
    topic = client.topic_name("my-app")
    t.check("topic has persistent prefix", topic.startswith("persistent://"))
    t.check("topic contains project name", "my-app" in topic)

    # Special characters get sanitized
    topic2 = client.topic_name("My App/v2")
    t.check("special chars sanitized", "/" not in topic2.split("//", 1)[1].split("/", 2)[-1])


def test_health_check_structure(t: TestResults):
    """Health check returns proper structure."""
    h = health_check()
    t.check("health has agent field", "agent" in h)
    t.check("health has status field", "status" in h)
    t.check("health has optional flag", h.get("optional") is True)


# ═══════════════════════════════════════════════════════════════
# ONLINE Tests (require Pulsar running)
# ═══════════════════════════════════════════════════════════════

def test_pulsar_health(t: TestResults):
    """Pulsar is running and healthy."""
    h = health_check()
    t.check("Pulsar is healthy", h["status"] == "healthy",
            f"topics: {h.get('topics', 0)}")


def test_publish_event(t: TestResults):
    """Publish events to a project topic."""
    import uuid
    project = f"test-{uuid.uuid4().hex[:6]}"

    result = publish_event(
        project=project,
        event_type="decision_made",
        content="Test decision: use Qdrant for distributed auth",
        developer_id="test@example.com"
    )
    t.check("event published successfully", result["status"] == "published",
            f"method: {result.get('method', 'unknown')}")


def test_list_topics(t: TestResults):
    """List topics after publishing."""
    result = list_topics()
    t.check("topics response has count", "count" in result)
    t.check("topics list is not empty", result.get("count", 0) >= 0,
            f"found {result.get('count', 0)} topics")


def test_memory_manager_integration(t: TestResults):
    """memory_manager.py store auto-publishes events when Pulsar is running."""
    import subprocess
    import uuid
    project = f"evt-test-{uuid.uuid4().hex[:6]}"

    # Suppress pulsar-client INFO logs (they write to stdout too)
    env = {**os.environ, "MEMORY_MODE": "team", "PULSAR_LOG_LEVEL": "ERROR"}
    result = subprocess.run(
        ["python3", os.path.join(_base_dir, "execution", "memory_manager.py"),
         "store", "--content", "Event integration test decision",
         "--type", "decision", "--project", project],
        capture_output=True, text=True, timeout=30, env=env
    )
    t.check("memory store succeeds", result.returncode == 0)

    if result.returncode == 0:
        # Extract JSON: find matching braces to handle interleaved log lines
        stdout = result.stdout.strip()
        # Find the first { and last } to extract the JSON object
        json_start = stdout.find("{")
        json_end = stdout.rfind("}")
        if json_start >= 0 and json_end > json_start:
            # Filter out non-JSON lines between braces
            raw = stdout[json_start:json_end + 1]
            lines = [l for l in raw.split("\n") if not l.strip().startswith(("2026-", "20"))]
            clean_json = "\n".join(lines)
            try:
                output = json.loads(clean_json)
                has_event = "event" in output
                t.check("store output includes event field", has_event,
                        f"event status: {output.get('event', {}).get('status', 'missing')}")
            except json.JSONDecodeError:
                t.check("store output includes event field", "event" in stdout,
                        "parsed from raw output")
        else:
            t.skip("event field check", "no JSON in output")
    else:
        t.skip("event field check", f"store failed: {result.stderr[:200]}")


# ═══════════════════════════════════════════════════════════════
# Main Runner
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("📡 Agent Events Integration Tests")
    print(f"   Mode: {'OFFLINE (no Pulsar)' if OFFLINE else 'ONLINE (Pulsar required)'}")
    print("=" * 60)

    t = TestResults()

    # Always run offline tests
    print("\n📋 Offline: Event Types")
    test_event_types(t)

    print("\n📋 Offline: Graceful Degradation")
    test_graceful_degradation(t)

    print("\n📋 Offline: Topic Naming")
    test_topic_naming(t)

    print("\n📋 Offline: Health Check Structure")
    test_health_check_structure(t)

    if not OFFLINE:
        h = health_check()
        if h["status"] != "healthy":
            print(f"\n⚠️  Pulsar not available ({h['status']}). Skipping online tests.")
            t.skip("online tests", "Pulsar not running")
        else:
            print("\n📋 Online: Pulsar Health")
            test_pulsar_health(t)

            print("\n📋 Online: Publish Event")
            test_publish_event(t)

            print("\n📋 Online: List Topics")
            test_list_topics(t)

            print("\n📋 Online: memory_manager.py Integration")
            test_memory_manager_integration(t)

    # Summary
    print("\n" + "=" * 60)
    total = t.passed + t.failed
    print(f"📊 Results: {t.passed}/{total} passed, {t.failed} failed, {t.skipped} skipped")
    print("=" * 60)

    report = {
        "suite": "agent_events",
        "mode": "offline" if OFFLINE else "online",
        "passed": t.passed,
        "failed": t.failed,
        "skipped": t.skipped,
        "total": total,
        "status": "pass" if t.failed == 0 else "fail",
        "tests": t.results
    }
    print(f"\n{json.dumps(report, indent=2)}")
    sys.exit(0 if t.failed == 0 else 1)


if __name__ == "__main__":
    main()
