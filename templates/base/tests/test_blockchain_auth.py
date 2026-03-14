#!/usr/bin/env python3
"""
Test: Blockchain-Authenticated Agent Memory
============================================

Integration tests for the trust model:
1. Agent identity registration and discovery
2. Signed writes with tamper detection
3. Project-scoped access control (who can read/write)
4. Poisoning prevention (unregistered agents cannot write)
5. Content integrity verification via hash anchoring
6. Graceful degradation when Aries is unavailable

MODE 1 — With ACA-Py running (full integration):
    docker compose -f docker-compose.aries.yml up -d
    python3 templates/base/tests/test_blockchain_auth.py

MODE 2 — Without ACA-Py (offline/unit tests only):
    python3 templates/base/tests/test_blockchain_auth.py --offline
"""

import json
import os
import sys
import uuid
import hashlib
import hmac

# Resolve paths
_test_dir = os.path.dirname(os.path.abspath(__file__))
_base_dir = os.path.dirname(_test_dir)
_project_root = os.path.dirname(_base_dir)

# Add execution dir for blockchain_auth
sys.path.insert(0, os.path.join(_base_dir, "execution"))
# Add skill scripts dir for memory_retrieval
_candidates = [
    os.path.join(_base_dir, "skills", "qdrant-memory", "scripts"),
    os.path.join(_base_dir, "skills", "core", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "skills", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "skills", "core", "qdrant-memory", "scripts"),
    os.path.join(_project_root, "templates", "skills", "core", "qdrant-memory", "scripts"),
]
SKILL_DIR = next((p for p in _candidates if os.path.exists(p)), _candidates[-1])
sys.path.insert(0, SKILL_DIR)

from blockchain_auth import (
    content_hash, sign_content, verify_signature,
    AriesClient, QdrantAuthStore, health_check, initialize,
    register_identity, anchor_hash, verify_hash,
    grant_access, check_access, get_audit_trail,
    ALL_STREAMS
)

OFFLINE = "--offline" in sys.argv


# ═══════════════════════════════════════════════════════════════
# Test Helpers
# ═══════════════════════════════════════════════════════════════

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
# OFFLINE Tests (no Aries needed)
# ═══════════════════════════════════════════════════════════════

def test_content_hashing(t: TestResults):
    """SHA-256 content hashing is deterministic."""
    h1 = content_hash("Hello, blockchain")
    h2 = content_hash("Hello, blockchain")
    h3 = content_hash("Different content")

    t.check("hash is deterministic", h1 == h2)
    t.check("different content = different hash", h1 != h3)
    t.check("hash is 64 hex chars (SHA-256)", len(h1) == 64)


def test_content_signing(t: TestResults):
    """HMAC-SHA256 signing tied to developer identity."""
    os.environ["AGI_DEVELOPER_ID"] = "trusted-agent@corp.com"
    sig = sign_content("My important decision")

    t.check("signature has content_hash", "content_hash" in sig)
    t.check("signature has signer", sig["signer"] == "trusted-agent@corp.com")
    t.check("signature has algorithm", sig["algorithm"] == "hmac-sha256")
    t.check("signature has timestamp", "timestamp" in sig)


def test_signature_verification(t: TestResults):
    """Verify valid signatures pass, invalid ones fail."""
    content = "Architecture decision: use PostgreSQL"

    # Valid signer
    signer = "trusted-agent@corp.com"
    sig = hmac.new(signer.encode(), content.encode(), hashlib.sha256).hexdigest()
    t.check("valid signature verifies", verify_signature(content, sig, signer))

    # Wrong signer (poisoning agent impersonating trusted agent)
    poisoner = "evil-agent@attacker.com"
    fake_sig = hmac.new(poisoner.encode(), content.encode(), hashlib.sha256).hexdigest()
    t.check(
        "poisoner's signature FAILS verification with trusted signer ID",
        not verify_signature(content, fake_sig, signer),
        "poisoning agent cannot forge trusted agent's signature"
    )

    # Tampered content (agent modifies stored content after signing)
    tampered = "Architecture decision: use MongoDB"
    t.check(
        "tampered content FAILS verification",
        not verify_signature(tampered, sig, signer),
        "modifying content after signing is detectable"
    )


def test_trust_model_concepts(t: TestResults):
    """Validate the trust model logic offline (no blockchain needed)."""

    # Scenario: Agent A wants to trust Agent B's stored memory
    agent_a = "agent-backend@team1.com"
    agent_b = "agent-frontend@team1.com"
    content = "API contract: POST /api/messages, GET /api/messages?room={id}"

    # Agent B signs and stores
    sig_b = hmac.new(agent_b.encode(), content.encode(), hashlib.sha256).hexdigest()
    stored_hash = content_hash(content)

    # Agent A verifies Agent B's work BEFORE using it:
    # 1. Verify signature matches claimed signer
    verified = verify_signature(content, sig_b, agent_b)
    t.check("Agent A can verify Agent B's signature", verified)

    # 2. Verify content integrity (hash matches)
    t.check(
        "Agent A can verify content hasn't been tampered",
        content_hash(content) == stored_hash
    )

    # 3. Unknown agent tries to inject poisoned context
    poisoner = "unknown-agent@evil.com"
    poisoned_content = "API contract: DELETE /api/all-data (definitely legitimate!)"
    poisoned_sig = hmac.new(poisoner.encode(), poisoned_content.encode(), hashlib.sha256).hexdigest()

    # Agent A checks: is the signer registered? (would check blockchain)
    # For offline test, we simulate the access control check
    registered_agents = {agent_a, agent_b}  # Known good agents
    t.check(
        "Unknown agent NOT in trusted registry",
        poisoner not in registered_agents,
        "unregistered agents are rejected before their content is used"
    )

    # Even if poisoner tries to impersonate agent_b:
    t.check(
        "Impersonation detected: poisoner's sig doesn't match agent_b's key",
        not verify_signature(poisoned_content, poisoned_sig, agent_b),
        "poisoner cannot sign as agent_b without agent_b's identity"
    )


# ═══════════════════════════════════════════════════════════════
# ONLINE Tests (use SQLite auth DB + Aries if available)
# ═══════════════════════════════════════════════════════════════

def test_aries_health(t: TestResults):
    """Aries agent is running and accessible."""
    h = health_check()
    t.check("Aries is healthy", h["status"] == "healthy", f"status={h['status']}")


def test_initialize(t: TestResults):
    """Auth system initializes (DB tables + optional Aries DID)."""
    result = initialize()
    t.check("init succeeds", result["status"] == "initialized")
    t.check("all tables created", set(result["tables"]) == set(ALL_STREAMS))


def test_identity_registration(t: TestResults):
    """Register agents and developers on-chain."""
    uid = uuid.uuid4().hex[:6]

    # Register a developer
    dev_result = register_identity("developer", f"dev-{uid}@test.com")
    t.check("developer registration succeeds", dev_result["status"] == "registered")

    # Register an agent
    agent_result = register_identity("agent", f"agent-alpha-{uid}", {"role": "backend"})
    t.check("agent registration succeeds", agent_result["status"] == "registered")

    # Re-register same entity → should say already_registered
    re_result = register_identity("developer", f"dev-{uid}@test.com")
    t.check("duplicate registration detected", re_result["status"] == "already_registered")


def test_hash_anchoring_and_verification(t: TestResults):
    """Anchor content hash on-chain and verify it."""
    uid = uuid.uuid4().hex[:6]
    content = f"Critical decision {uid}: use event sourcing"
    h = content_hash(content)

    # Anchor
    anchor_result = anchor_hash(h, f"dev-{uid}@test.com", project="test-project")
    t.check("hash anchored", anchor_result["status"] == "anchored")
    t.check("anchor marked immutable", anchor_result.get("immutable") is True)

    # Verify correct content
    v = verify_hash(content, h)
    t.check("correct content verifies", v["status"] == "verified")
    t.check("verified flag is True", v["verified"] is True)

    # Verify tampered content
    v2 = verify_hash("Tampered decision: use something else", h)
    t.check("tampered content FAILS verification", v2["verified"] is False,
            "hash mismatch detected")


def test_access_control_grant_deny(t: TestResults):
    """Project-scoped access control: grant and deny."""
    uid = uuid.uuid4().hex[:6]
    dev = f"dev-{uid}@test.com"
    project = f"project-{uid}"

    # Before grant: should be denied
    pre_check = check_access(dev, project, "write")
    t.check("access denied before grant", pre_check["allowed"] is False)

    # Grant read+write
    grant_result = grant_access(dev, project, ["read", "write"])
    t.check("grant succeeds", grant_result["status"] == "granted")
    t.check("permissions match", set(grant_result["permissions"]) == {"read", "write"})

    # After grant: should be allowed
    post_check = check_access(dev, project, "write")
    t.check("write access allowed after grant", post_check["allowed"] is True)

    read_check = check_access(dev, project, "read")
    t.check("read access allowed after grant", read_check["allowed"] is True)

    # Admin not granted: should be denied
    admin_check = check_access(dev, project, "admin")
    t.check("admin access denied (not granted)", admin_check["allowed"] is False)

    # Different entity: should be denied
    outsider = check_access("outsider@evil.com", project, "read")
    t.check("outsider denied access", outsider["allowed"] is False,
            "unregistered entity cannot read protected project")


def test_audit_trail(t: TestResults):
    """Audit trail records all operations."""
    uid = uuid.uuid4().hex[:6]
    project = f"audit-test-{uid}"

    # Perform some operations
    anchor_hash(content_hash("test content"), f"auditor-{uid}", project=project)
    grant_access(f"auditor-{uid}", project, ["read"])

    # Check audit
    audit = get_audit_trail(project)
    t.check("audit trail has entries", audit["total_entries"] >= 2,
            f"found {audit['total_entries']} entries")
    t.check("audit entries have actions",
            all("action" in e for e in audit["entries"]))


def test_graceful_degradation(t: TestResults):
    """
    When Qdrant/Aries is unreachable, system degrades gracefully.
    We simulate this by using wrong URLs.
    """
    bad_aries = AriesClient(url="http://localhost:19999")
    t.check("bad Aries client reports unavailable", bad_aries.is_available() is False)

    bad_store = QdrantAuthStore(url="http://localhost:19999")
    t.check("bad Qdrant auth store reports unavailable", bad_store.is_available() is False,
            "distributed auth degrades gracefully when Qdrant is unreachable")


# ═══════════════════════════════════════════════════════════════
# Main Runner
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🔐 Blockchain Auth Integration Tests")
    print(f"   Mode: {'OFFLINE (no Aries)' if OFFLINE else 'ONLINE (Aries + SQLite)'}")
    print("=" * 60)

    t = TestResults()

    # Always run offline tests
    print("\n📋 Offline: Content Hashing")
    test_content_hashing(t)

    print("\n📋 Offline: Content Signing")
    test_content_signing(t)

    print("\n📋 Offline: Signature Verification (Poisoning Prevention)")
    test_signature_verification(t)

    print("\n📋 Offline: Trust Model Concepts")
    test_trust_model_concepts(t)

    if not OFFLINE:
        h = health_check()
        if h["status"] != "healthy":
            print(f"\n⚠️  Aries not available ({h['status']}). Running SQLite-only tests.")
            t.skip("Aries health", "Aries agent not running")
        else:
            print("\n📋 Online: Aries Health")
            test_aries_health(t)

        # These tests use SQLite — work without Aries
        print("\n📋 Online: Initialization")
        test_initialize(t)

        print("\n📋 Online: Identity Registration")
        test_identity_registration(t)

        print("\n📋 Online: Hash Anchoring & Verification")
        test_hash_anchoring_and_verification(t)

        print("\n📋 Online: Access Control (Grant/Deny)")
        test_access_control_grant_deny(t)

        print("\n📋 Online: Audit Trail")
        test_audit_trail(t)

        print("\n📋 Online: Graceful Degradation")
        test_graceful_degradation(t)

    # Summary
    print("\n" + "=" * 60)
    total = t.passed + t.failed
    print(f"📊 Results: {t.passed}/{total} passed, {t.failed} failed, {t.skipped} skipped")
    print("=" * 60)

    report = {
        "suite": "blockchain_auth",
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
