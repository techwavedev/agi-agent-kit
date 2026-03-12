#!/usr/bin/env python3
"""
Script: agent_identity.py
Purpose: Agent identity management — Ed25519 keypair generation, signing, verification.

Usage:
    python3 execution/agent_identity.py init       # Generate or load identity
    python3 execution/agent_identity.py info       # Show identity info
    python3 execution/agent_identity.py sign --content "test"
    python3 execution/agent_identity.py verify --content "test" --signature <hex> --pubkey <hex>

Exit Codes:
    0 - Success
    1 - Identity not found
    2 - Verification failed
    3 - Operation error
"""

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

IDENTITY_DIR = Path.home() / ".agi-agent-kit" / "identity"

# Module-level cache — loaded once per process
_cached_identity = None


def get_identity_dir() -> Path:
    """Return identity directory, creating if needed."""
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    return IDENTITY_DIR


def generate_keypair() -> dict:
    """
    Generate Ed25519 keypair and save to IDENTITY_DIR.

    Creates: private_key.pem, public_key.pem, agent_id.txt
    Returns: {"agent_id": str, "public_key_hex": str, "created": True}
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    identity_dir = get_identity_dir()
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Save private key (PEM, PKCS8, unencrypted)
    priv_path = identity_dir / "private_key.pem"
    priv_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    # Restrict permissions: owner read/write only
    priv_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    # Save public key (PEM)
    pub_path = identity_dir / "public_key.pem"
    pub_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    # Derive agent_id = SHA-256 of raw 32-byte public key
    raw_pub = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    agent_id = hashlib.sha256(raw_pub).hexdigest()
    public_key_hex = raw_pub.hex()

    (identity_dir / "agent_id.txt").write_text(agent_id + "\n")

    return {"agent_id": agent_id, "public_key_hex": public_key_hex, "created": True}


def load_identity() -> dict:
    """
    Load existing identity from IDENTITY_DIR.

    Returns dict with agent_id, public_key_hex, private_key object.
    Returns None if no identity exists.
    """
    global _cached_identity
    if _cached_identity is not None:
        return _cached_identity

    priv_path = IDENTITY_DIR / "private_key.pem"
    pub_path = IDENTITY_DIR / "public_key.pem"
    id_path = IDENTITY_DIR / "agent_id.txt"

    if not priv_path.exists() or not pub_path.exists():
        return None

    from cryptography.hazmat.primitives import serialization

    private_key = serialization.load_pem_private_key(
        priv_path.read_bytes(), password=None
    )
    public_key = private_key.public_key()

    raw_pub = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    if id_path.exists():
        agent_id = id_path.read_text().strip()
    else:
        agent_id = hashlib.sha256(raw_pub).hexdigest()
        id_path.write_text(agent_id + "\n")

    _cached_identity = {
        "agent_id": agent_id,
        "public_key_hex": raw_pub.hex(),
        "private_key": private_key,
    }
    return _cached_identity


def get_or_create_identity() -> dict:
    """Load identity if exists, generate if not. Idempotent."""
    identity = load_identity()
    if identity:
        return identity

    result = generate_keypair()
    # Clear cache so next load_identity() reads from disk
    global _cached_identity
    _cached_identity = None
    return load_identity() or result


def _canonical_json(agent_id: str, content: str, timestamp: str, memory_type: str) -> bytes:
    """Build canonical JSON for signing (sorted keys, no whitespace)."""
    canonical = json.dumps(
        {"agent_id": agent_id, "content": content, "timestamp": timestamp, "type": memory_type},
        sort_keys=True,
        separators=(",", ":"),
    )
    return canonical.encode("utf-8")


def sign_memory_payload(content: str, memory_type: str, timestamp: str, agent_id: str) -> dict:
    """
    Sign a memory write.

    Returns:
        {
            "agent_id": str,
            "signature": str (hex),
            "content_hash": str (SHA-256 hex),
            "signed_fields": ["agent_id", "content", "timestamp", "type"]
        }
    """
    identity = load_identity()
    if not identity or "private_key" not in identity:
        raise RuntimeError("No identity loaded — cannot sign")

    canonical = _canonical_json(agent_id, content, timestamp, memory_type)
    content_hash = hashlib.sha256(canonical).hexdigest()
    signature = identity["private_key"].sign(canonical)

    return {
        "agent_id": agent_id,
        "signature": signature.hex(),
        "content_hash": content_hash,
        "signed_fields": ["agent_id", "content", "timestamp", "type"],
    }


def verify_signature(
    content: str,
    memory_type: str,
    timestamp: str,
    agent_id: str,
    signature_hex: str,
    pubkey_hex: str,
) -> bool:
    """Verify a memory signature against a public key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    canonical = _canonical_json(agent_id, content, timestamp, memory_type)
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))

    try:
        public_key.verify(bytes.fromhex(signature_hex), canonical)
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Agent identity management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Generate or load identity")
    subparsers.add_parser("info", help="Show identity info")

    sign_p = subparsers.add_parser("sign", help="Sign content")
    sign_p.add_argument("--content", required=True)

    verify_p = subparsers.add_parser("verify", help="Verify a signature")
    verify_p.add_argument("--content", required=True)
    verify_p.add_argument("--signature", required=True, help="Hex signature")
    verify_p.add_argument("--pubkey", required=True, help="Hex public key")
    verify_p.add_argument("--type", default="decision")
    verify_p.add_argument("--timestamp", default="")

    args = parser.parse_args()

    try:
        if args.command == "init":
            identity = get_or_create_identity()
            print(json.dumps({
                "status": "ok",
                "agent_id": identity["agent_id"],
                "public_key_hex": identity["public_key_hex"],
                "identity_dir": str(IDENTITY_DIR),
                "created": identity.get("created", False),
            }, indent=2))
            sys.exit(0)

        elif args.command == "info":
            identity = load_identity()
            if not identity:
                print(json.dumps({"status": "not_found", "identity_dir": str(IDENTITY_DIR)}))
                sys.exit(1)
            print(json.dumps({
                "status": "ok",
                "agent_id": identity["agent_id"],
                "public_key_hex": identity["public_key_hex"],
                "identity_dir": str(IDENTITY_DIR),
            }, indent=2))
            sys.exit(0)

        elif args.command == "sign":
            ts = datetime.now(timezone.utc).isoformat()
            identity = load_identity()
            if not identity:
                print(json.dumps({"status": "error", "message": "No identity. Run: agent_identity.py init"}), file=sys.stderr)
                sys.exit(1)
            result = sign_memory_payload(args.content, "decision", ts, identity["agent_id"])
            print(json.dumps(result, indent=2))
            sys.exit(0)

        elif args.command == "verify":
            valid = verify_signature(
                content=args.content,
                memory_type=args.type,
                timestamp=args.timestamp,
                agent_id=hashlib.sha256(bytes.fromhex(args.pubkey)).hexdigest(),
                signature_hex=args.signature,
                pubkey_hex=args.pubkey,
            )
            print(json.dumps({"valid": valid}))
            sys.exit(0 if valid else 2)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
