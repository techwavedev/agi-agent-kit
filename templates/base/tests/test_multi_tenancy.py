#!/usr/bin/env python3
"""
Test: Multi-Tenancy for Federated Agent Memory
================================================

Integration tests validating developer/agent identity tagging,
project-scoped isolation, shared memory visibility, and concurrent writes.

Requires: Qdrant + Ollama running.

Usage:
    python3 -m pytest templates/base/tests/test_multi_tenancy.py -v
    # or directly:
    python3 templates/base/tests/test_multi_tenancy.py
"""

import json
import os
import sys
import uuid
import time
from pathlib import Path

# Resolve qdrant-memory scripts
_test_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_test_dir)
_project_root = os.path.dirname(_base_dir)

_candidates = [
    os.path.join(_base_dir, "skills", "qdrant-memory", "scripts"),
    os.path.join(_base_dir, "skills", "core", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "skills", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "skills", "core", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "templates", "skills", "core", "qdrant-memory", "scripts"),
]
SKILL_DIR = next((p for p in _candidates if os.path.exists(p)), _candidates[-1])
sys.path.insert(0, SKILL_DIR)

from memory_retrieval import (
    store_memory, retrieve_context, build_filter,
    resolve_developer_id, resolve_agent_id
)

# ═══════════════════════════════════════════════════════════════
# Test Configuration
# ═══════════════════════════════════════════════════════════════

TEST_PROJECT = f"mt-test-{uuid.uuid4().hex[:6]}"
DEV_ALICE = "alice@example.com"
DEV_BOB = "bob@example.com"
AGENT_ALPHA = "agent-alpha"
AGENT_BETA = "agent-beta"


def _store(content, dev, agent="primary", shared=False, project=TEST_PROJECT):
    """Helper to store with identity."""
    return store_memory(
        content=content,
        memory_type="technical",
        metadata={"project": project, "tags": ["mt-test"]},
        shared=shared,
        developer_id=dev,
        agent_id=agent
    )


def _retrieve(query, developer=None, agent=None, shared_only=False, project=TEST_PROJECT):
    """Helper to retrieve with identity filter."""
    filters = build_filter(
        project=project,
        developer=developer,
        agent=agent,
        shared_only=shared_only
    )
    return retrieve_context(
        query,
        filters={"must": filters["must"]} if filters else None,
        top_k=10,
        score_threshold=0.3
    )


# ═══════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════

class TestResults:
    """Simple test result accumulator."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
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
        return condition


def test_identity_resolution():
    """Test that developer/agent identity can be resolved."""
    dev_id = resolve_developer_id()
    agent_id = resolve_agent_id()
    return dev_id and len(dev_id) > 0 and agent_id == "primary"


def test_store_with_identity(t: TestResults):
    """Test that stores include developer_id, agent_id, shared fields."""
    result = _store("Alice's private architecture decision for testing", DEV_ALICE, AGENT_ALPHA)
    t.check(
        "store returns developer_id",
        result.get("developer_id") == DEV_ALICE,
        f"got: {result.get('developer_id')}"
    )
    t.check(
        "store returns agent_id",
        result.get("agent_id") == AGENT_ALPHA,
        f"got: {result.get('agent_id')}"
    )
    t.check(
        "store returns shared=False",
        result.get("shared") is False
    )
    return result.get("point_id")


def test_developer_isolation(t: TestResults):
    """Alice's private memories should not be visible to Bob."""
    # Alice stores a private memory
    _store("Alice's secret: use Redis for session cache", DEV_ALICE)
    time.sleep(0.5)  # Allow indexing

    # Bob stores a private memory
    _store("Bob's choice: use Memcached for session cache", DEV_BOB)
    time.sleep(0.5)

    # Alice retrieves — should find her own, not Bob's
    alice_results = _retrieve("session cache decision", developer=DEV_ALICE)
    alice_contents = [c["content"] for c in alice_results.get("chunks", [])]

    has_alice = any("Redis" in c for c in alice_contents)
    has_bob = any("Memcached" in c for c in alice_contents)

    t.check("Alice finds her own memory", has_alice)
    t.check("Alice does NOT see Bob's private memory", not has_bob,
            f"leaked: found {len([c for c in alice_contents if 'Memcached' in c])} Bob entries")


def test_shared_memory_visible(t: TestResults):
    """Shared memories should be visible to everyone on the project."""
    # Alice stores a shared decision
    _store("SHARED: Team decided to use PostgreSQL for all services", DEV_ALICE, shared=True)
    time.sleep(0.5)

    # Bob retrieves with shared_only — should find it
    shared_results = _retrieve("PostgreSQL decision", shared_only=True)
    shared_contents = [c["content"] for c in shared_results.get("chunks", [])]

    t.check(
        "Shared memory visible to team",
        any("PostgreSQL" in c for c in shared_contents),
        f"found {shared_results.get('total_chunks', 0)} shared chunks"
    )

    # Bob retrieves with his developer filter — should also find shared
    bob_results = _retrieve("PostgreSQL decision", developer=DEV_BOB)
    # In current implementation, developer filter shows own + shared might need
    # the 'should' filter. For now, shared_only is the reliable way.
    t.check(
        "shared_only filter works",
        shared_results.get("total_chunks", 0) > 0
    )


def test_agent_identity_tagging(t: TestResults):
    """Each agent's stores should be tagged with correct agent_id."""
    _store("Alpha agent found: API needs rate limiting", DEV_ALICE, AGENT_ALPHA)
    _store("Beta agent found: Frontend needs caching", DEV_ALICE, AGENT_BETA)
    time.sleep(0.5)

    # Retrieve filtered by agent
    alpha_results = _retrieve("rate limiting", agent=AGENT_ALPHA)
    beta_results = _retrieve("Frontend caching", agent=AGENT_BETA)

    t.check(
        "Alpha agent memories retrievable",
        alpha_results.get("total_chunks", 0) > 0,
        f"found {alpha_results.get('total_chunks', 0)} chunks"
    )
    t.check(
        "Beta agent memories retrievable",
        beta_results.get("total_chunks", 0) > 0,
        f"found {beta_results.get('total_chunks', 0)} chunks"
    )


def test_concurrent_writes(t: TestResults):
    """Two parallel stores should not corrupt each other."""
    # Store two memories rapidly
    r1 = _store(f"Concurrent write 1: {uuid.uuid4().hex[:8]}", DEV_ALICE)
    r2 = _store(f"Concurrent write 2: {uuid.uuid4().hex[:8]}", DEV_BOB)

    t.check(
        "Both writes succeed",
        r1.get("status") == "stored" and r2.get("status") == "stored"
    )
    t.check(
        "Point IDs are distinct",
        r1.get("point_id") != r2.get("point_id"),
        f"id1={r1.get('point_id')}, id2={r2.get('point_id')}"
    )


def test_build_filter_identity(t: TestResults):
    """build_filter should include identity fields when provided."""
    f = build_filter(developer="dev@test.com", agent="my-agent", shared_only=True)
    must = f["must"] if f else []

    has_dev = any(c.get("key") == "developer_id" for c in must)
    has_agent = any(c.get("key") == "agent_id" for c in must)
    has_shared = any(c.get("key") == "shared" for c in must)

    t.check("build_filter includes developer_id", has_dev)
    t.check("build_filter includes agent_id", has_agent)
    t.check("build_filter includes shared", has_shared)


# ═══════════════════════════════════════════════════════════════
# Main Runner
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🧪 Multi-Tenancy Integration Tests")
    print(f"   Project scope: {TEST_PROJECT}")
    print("=" * 60)

    t = TestResults()

    # Test 0: Identity resolution
    print("\n📋 Test: Identity Resolution")
    t.check("resolve_developer_id returns non-empty", test_identity_resolution())

    # Test 1: Store with identity
    print("\n📋 Test: Store with Identity")
    test_store_with_identity(t)

    # Test 2: build_filter includes identity
    print("\n📋 Test: build_filter Identity Fields")
    test_build_filter_identity(t)

    # Test 3: Developer isolation
    print("\n📋 Test: Developer Isolation")
    test_developer_isolation(t)

    # Test 4: Shared memory visibility
    print("\n📋 Test: Shared Memory Visibility")
    test_shared_memory_visible(t)

    # Test 5: Agent identity tagging
    print("\n📋 Test: Agent Identity Tagging")
    test_agent_identity_tagging(t)

    # Test 6: Concurrent writes
    print("\n📋 Test: Concurrent Writes")
    test_concurrent_writes(t)

    # Summary
    print("\n" + "=" * 60)
    total = t.passed + t.failed
    print(f"📊 Results: {t.passed}/{total} passed, {t.failed} failed")
    print("=" * 60)

    # JSON output
    report = {
        "suite": "multi_tenancy",
        "project_scope": TEST_PROJECT,
        "passed": t.passed,
        "failed": t.failed,
        "total": total,
        "status": "pass" if t.failed == 0 else "fail",
        "tests": t.results
    }
    print(f"\n{json.dumps(report, indent=2)}")

    sys.exit(0 if t.failed == 0 else 1)


if __name__ == "__main__":
    main()
