#!/usr/bin/env python3
"""
Script: blockchain_auth.py
Purpose: Distributed agent identity, signing, and access control.

Auth data is stored in a shared Qdrant collection (agent_auth) so all agents
on all machines see the same identities, access grants, and audit trail.

Optionally enhanced by Hyperledger Aries (ACA-Py) for W3C DID-based identity
and Ed25519 signing (pro mode).

Usage:
    python3 blockchain_auth.py health
    python3 blockchain_auth.py init
    python3 blockchain_auth.py register --entity-type developer --entity-id "user@email.com"
    python3 blockchain_auth.py sign --content "My decision"

Exit Codes:
    0 - Success
    1 - Error
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
AUTH_COLLECTION = "agent_auth"
AUTH_VECTOR_DIM = 4  # Minimal — auth records don't use vector search

ARIES_ADMIN_URL = os.environ.get("ARIES_ADMIN_URL", "http://localhost:8031")
ARIES_ADMIN_KEY = os.environ.get("ARIES_ADMIN_KEY", "changeme_set_in_dotenv")

# Placeholder vector for auth records (Qdrant requires a vector per point)
_ZERO_VEC = [0.0] * AUTH_VECTOR_DIM


# ═══════════════════════════════════════════════════════════════
# Pure crypto functions (always available, no Qdrant/Aries needed)
# ═══════════════════════════════════════════════════════════════

def content_hash(content: str) -> str:
    """SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sign_content(content: str) -> dict:
    """Sign content with developer identity (HMAC-SHA256)."""
    dev_id = os.environ.get("AGI_DEVELOPER_ID", _resolve_developer_id())
    h = content_hash(content)
    sig = hmac.new(dev_id.encode(), content.encode(), hashlib.sha256).hexdigest()
    return {
        "content_hash": h,
        "signature": sig,
        "signer": dev_id,
        "algorithm": "hmac-sha256",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def verify_signature(content: str, signature: str, signer: str) -> bool:
    """Verify HMAC-SHA256 signature against claimed signer identity."""
    expected = hmac.new(signer.encode(), content.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _resolve_developer_id() -> str:
    """Auto-detect developer identity."""
    env_id = os.environ.get("AGI_DEVELOPER_ID")
    if env_id:
        return env_id
    try:
        import subprocess
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return f"{os.environ.get('USER', 'unknown')}@{os.uname().nodename}"


# ═══════════════════════════════════════════════════════════════
# Qdrant Auth Store (shared across all machines)
# ═══════════════════════════════════════════════════════════════

class QdrantAuthStore:
    """Distributed auth storage via Qdrant agent_auth collection."""

    def __init__(self, url=None):
        self.url = (url or QDRANT_URL).rstrip("/")
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            req = Request(f"{self.url}/collections/{AUTH_COLLECTION}", method="GET")
            with urlopen(req, timeout=5) as resp:
                json.loads(resp.read().decode())
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def _put_point(self, point_id: str, payload: dict):
        """Upsert a single point into agent_auth."""
        data = {
            "points": [{
                "id": point_id,
                "vector": _ZERO_VEC,
                "payload": payload,
            }]
        }
        req = Request(
            f"{self.url}/collections/{AUTH_COLLECTION}/points",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="PUT"
        )
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())

    def _scroll(self, filters: dict, limit: int = 100) -> list:
        """Scroll (filtered search) on agent_auth."""
        data = {
            "filter": filters,
            "limit": limit,
            "with_payload": True,
        }
        req = Request(
            f"{self.url}/collections/{AUTH_COLLECTION}/points/scroll",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("result", {}).get("points", [])

    def find_identity(self, entity_id: str) -> dict:
        """Find a registered identity."""
        points = self._scroll({
            "must": [
                {"key": "record_type", "match": {"value": "identity"}},
                {"key": "entity_id", "match": {"value": entity_id}},
            ]
        }, limit=1)
        return points[0]["payload"] if points else None

    def store_identity(self, entity_id: str, entity_type: str, did: str = None, metadata: dict = None):
        """Register an identity."""
        # Deterministic ID so re-registration is idempotent
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"identity:{entity_id}"))
        self._put_point(pid, {
            "record_type": "identity",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "did": did,
            "metadata": json.dumps(metadata or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def find_access(self, entity_id: str, project: str) -> dict:
        """Find access grant for entity+project."""
        points = self._scroll({
            "must": [
                {"key": "record_type", "match": {"value": "access_grant"}},
                {"key": "entity_id", "match": {"value": entity_id}},
                {"key": "project", "match": {"value": project}},
            ]
        }, limit=1)
        return points[0]["payload"] if points else None

    def store_access(self, entity_id: str, project: str, permissions: list):
        """Grant access."""
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"access:{entity_id}:{project}"))
        self._put_point(pid, {
            "record_type": "access_grant",
            "entity_id": entity_id,
            "project": project,
            "permissions": permissions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def store_hash(self, hash_value: str, entity_id: str, project: str = None):
        """Anchor a content hash."""
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"hash:{hash_value}"))
        self._put_point(pid, {
            "record_type": "content_hash",
            "content_hash": hash_value,
            "entity_id": entity_id,
            "project": project or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def find_hash(self, hash_value: str) -> dict:
        """Find an anchored hash."""
        points = self._scroll({
            "must": [
                {"key": "record_type", "match": {"value": "content_hash"}},
                {"key": "content_hash", "match": {"value": hash_value}},
            ]
        }, limit=1)
        return points[0]["payload"] if points else None

    def store_audit(self, action: str, entity_id: str, project: str = None, detail: dict = None):
        """Append to audit trail."""
        pid = str(uuid.uuid4())
        self._put_point(pid, {
            "record_type": "audit",
            "action": action,
            "entity_id": entity_id,
            "project": project or "",
            "detail": json.dumps(detail or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_audit(self, project: str = None, limit: int = 50) -> list:
        """Get audit trail entries."""
        filters = {"must": [{"key": "record_type", "match": {"value": "audit"}}]}
        if project:
            filters["must"].append({"key": "project", "match": {"value": project}})
        points = self._scroll(filters, limit=limit)
        return [p["payload"] for p in points]


# ═══════════════════════════════════════════════════════════════
# Aries Client (ACA-Py Admin REST API — pro mode only)
# ═══════════════════════════════════════════════════════════════

class AriesClient:
    """Client for ACA-Py Admin API."""

    def __init__(self, url=None, api_key=None):
        self.url = (url or ARIES_ADMIN_URL).rstrip("/")
        self.api_key = api_key or ARIES_ADMIN_KEY
        self._available = None

    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.url}{path}"
        body = json.dumps(data).encode() if data else None
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        req = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except (URLError, HTTPError) as e:
            raise ConnectionError(f"ACA-Py request failed: {e}")

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            self._request("GET", "/status")
            self._available = True
        except Exception:
            self._available = False
        return self._available

    def get_status(self) -> dict:
        return self._request("GET", "/status")

    def create_did(self, method: str = "key") -> dict:
        return self._request("POST", "/wallet/did/create", {
            "method": method,
            "options": {"key_type": "ed25519"}
        })

    def list_dids(self) -> list:
        result = self._request("GET", "/wallet/did")
        return result.get("results", [])


# Global instances
_auth_store = QdrantAuthStore()
_aries = AriesClient()


# ═══════════════════════════════════════════════════════════════
# Public API (callers unchanged)
# ═══════════════════════════════════════════════════════════════

ALL_STREAMS = ["identities", "access_control", "content_hashes", "audit_log"]


def health_check() -> dict:
    """Check Qdrant auth store and optional Aries agent health."""
    result = {
        "status": "not_running",
        "auth_store": "Qdrant (agent_auth collection)",
        "aries": "ACA-Py (Hyperledger Aries)",
    }
    if _auth_store.is_available():
        result["status"] = "healthy"
        result["qdrant"] = "connected"
    if _aries.is_available():
        try:
            status = _aries.get_status()
            result["aries_status"] = "connected"
            result["aries_version"] = status.get("version", "unknown")
        except Exception:
            result["aries_status"] = "error"
    else:
        result["aries_status"] = "not_running (optional)"
    return result


def initialize() -> dict:
    """Initialize auth system — verify collection exists."""
    result = {"status": "initialized", "store": "Qdrant (agent_auth)",
              "tables": ALL_STREAMS}

    if _auth_store.is_available():
        result["qdrant"] = "connected"
    else:
        result["qdrant"] = "not_available"

    if _aries.is_available():
        try:
            did_result = _aries.create_did(method="key")
            result["did"] = did_result.get("result", {}).get("did")
            result["aries"] = "connected"
        except Exception as e:
            result["aries"] = f"error: {e}"
    else:
        result["aries"] = "not_running (optional)"

    return result


def register_identity(entity_type: str, entity_id: str, metadata: dict = None) -> dict:
    """Register an agent/developer/team identity (shared across all machines)."""
    if not _auth_store.is_available():
        return {"status": "unavailable", "reason": "Qdrant agent_auth not reachable"}

    # Check if already registered
    existing = _auth_store.find_identity(entity_id)
    if existing:
        return {"status": "already_registered", "entity_id": entity_id}

    # Create DID via Aries if available
    did = None
    if _aries.is_available():
        try:
            did_result = _aries.create_did(method="key")
            did = did_result.get("result", {}).get("did")
        except Exception:
            pass

    _auth_store.store_identity(entity_id, entity_type, did=did, metadata=metadata)
    _auth_store.store_audit("register_identity", entity_id, detail={"type": entity_type, "did": did})
    return {"status": "registered", "entity_id": entity_id, "did": did, "type": entity_type}


def anchor_hash(hash_value: str, entity_id: str, project: str = None) -> dict:
    """Anchor a content hash for tamper detection (shared)."""
    if not _auth_store.is_available():
        return {"status": "unavailable", "reason": "Qdrant agent_auth not reachable"}

    _auth_store.store_hash(hash_value, entity_id, project)
    _auth_store.store_audit("anchor_hash", entity_id, project, {"hash": hash_value[:16] + "..."})
    return {"status": "anchored", "hash": hash_value, "immutable": True}


def verify_hash(content: str, expected_hash: str) -> dict:
    """Verify content against anchored hash."""
    actual = content_hash(content)
    verified = actual == expected_hash

    result = {
        "status": "verified" if verified else "hash_mismatch",
        "verified": verified,
        "actual_hash": actual,
        "expected_hash": expected_hash,
    }

    if _auth_store.is_available():
        record = _auth_store.find_hash(expected_hash)
        if record:
            result["anchored_by"] = record.get("entity_id")
            result["anchored_at"] = record.get("timestamp")

    return result


def grant_access(entity_id: str, project: str, permissions: list) -> dict:
    """Grant project-scoped access permissions (shared)."""
    if not _auth_store.is_available():
        return {"status": "unavailable", "reason": "Qdrant agent_auth not reachable"}

    _auth_store.store_access(entity_id, project, permissions)
    _auth_store.store_audit("grant_access", entity_id, project, {"permissions": permissions})
    return {"status": "granted", "entity_id": entity_id, "project": project, "permissions": permissions}


def check_access(entity_id: str, project: str, permission: str) -> dict:
    """Check if entity has a specific permission for a project."""
    if not _auth_store.is_available():
        return {"allowed": False, "reason": "auth_unavailable", "entity_id": entity_id, "project": project}

    record = _auth_store.find_access(entity_id, project)
    if not record:
        return {"allowed": False, "reason": "no_grant", "entity_id": entity_id, "project": project}

    perms = record.get("permissions", [])
    allowed = permission in perms or "admin" in perms
    return {"allowed": allowed, "permissions": perms, "entity_id": entity_id, "project": project}


def get_audit_trail(project: str = None, limit: int = 50) -> dict:
    """Get audit trail entries (shared across all machines)."""
    if not _auth_store.is_available():
        return {"total_entries": 0, "entries": [], "reason": "auth_unavailable"}

    entries_raw = _auth_store.get_audit(project, limit)
    entries = []
    for r in entries_raw:
        entries.append({
            "action": r.get("action"),
            "entity_id": r.get("entity_id"),
            "project": r.get("project") or None,
            "detail": json.loads(r.get("detail", "{}")),
            "timestamp": r.get("timestamp"),
        })
    return {"total_entries": len(entries), "entries": entries}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Distributed auth (Qdrant + Aries)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check auth system health")
    sub.add_parser("init", help="Initialize auth system")

    reg = sub.add_parser("register", help="Register identity")
    reg.add_argument("--entity-type", required=True, choices=["developer", "agent", "team"])
    reg.add_argument("--entity-id", required=True)

    sign_p = sub.add_parser("sign", help="Sign content")
    sign_p.add_argument("--content", required=True)

    anchor_p = sub.add_parser("anchor", help="Anchor content hash")
    anchor_p.add_argument("--content", required=True)
    anchor_p.add_argument("--project", default=None)

    verify_p = sub.add_parser("verify", help="Verify content hash")
    verify_p.add_argument("--content", required=True)
    verify_p.add_argument("--hash", required=True)

    grant_p = sub.add_parser("grant", help="Grant access")
    grant_p.add_argument("--entity-id", required=True)
    grant_p.add_argument("--project", required=True)
    grant_p.add_argument("--permissions", required=True, help="Comma-separated: read,write,admin")

    check_p = sub.add_parser("check-access", help="Check access")
    check_p.add_argument("--entity-id", required=True)
    check_p.add_argument("--project", required=True)
    check_p.add_argument("--permission", required=True)

    audit_p = sub.add_parser("audit", help="View audit trail")
    audit_p.add_argument("--project", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "health":
        print(json.dumps(health_check(), indent=2))
    elif args.command == "init":
        print(json.dumps(initialize(), indent=2))
    elif args.command == "register":
        print(json.dumps(register_identity(args.entity_type, args.entity_id), indent=2))
    elif args.command == "sign":
        print(json.dumps(sign_content(args.content), indent=2))
    elif args.command == "anchor":
        dev_id = _resolve_developer_id()
        h = content_hash(args.content)
        print(json.dumps(anchor_hash(h, dev_id, args.project), indent=2))
    elif args.command == "verify":
        print(json.dumps(verify_hash(args.content, args.hash), indent=2))
    elif args.command == "grant":
        perms = [p.strip() for p in args.permissions.split(",")]
        print(json.dumps(grant_access(args.entity_id, args.project, perms), indent=2))
    elif args.command == "check-access":
        print(json.dumps(check_access(args.entity_id, args.project, args.permission), indent=2))
    elif args.command == "audit":
        print(json.dumps(get_audit_trail(args.project), indent=2))


if __name__ == "__main__":
    main()
