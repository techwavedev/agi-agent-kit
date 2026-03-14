#!/usr/bin/env python3
"""
Script: agent_events.py
Purpose: Real-time agent event bus via Apache Pulsar.

Enables agents on different machines to:
  - Publish events when they store memories, make decisions, or complete tasks
  - Subscribe to events from other agents in their project/team
  - Coordinate work in real-time (not just poll Qdrant)

Topics follow the pattern: persistent://agi/memory/<project>

Graceful degradation: if Pulsar is not running, events are silently dropped
and agents fall back to polling Qdrant (which always works).

Usage:
    python3 agent_events.py health
    python3 agent_events.py publish --project myapp --event-type decision --content "Use PostgreSQL"
    python3 agent_events.py subscribe --project myapp --callback print
    python3 agent_events.py list-topics

Exit Codes:
    0 - Success
    1 - Error
"""

import argparse
import json
import os
import sys
import time
import threading
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PULSAR_URL = os.environ.get("PULSAR_URL", "pulsar://localhost:6650")
PULSAR_HTTP_URL = os.environ.get("PULSAR_HTTP_URL", "http://localhost:8080")
PULSAR_TENANT = os.environ.get("PULSAR_TENANT", "agi")
PULSAR_NAMESPACE = os.environ.get("PULSAR_NAMESPACE", "memory")

# Event types emitted by the memory system
EVENT_TYPES = [
    "memory_stored",       # Agent stored a new memory
    "decision_made",       # Agent made a decision
    "code_written",        # Agent wrote/modified code
    "error_resolved",      # Agent resolved an error
    "task_completed",      # Agent completed a task
    "access_granted",      # Access was granted to an entity
    "identity_registered", # New agent/developer registered
    "context_request",     # Agent is requesting context from peers
    "context_response",    # Agent is responding to a context request
]


# ═══════════════════════════════════════════════════════════════
# Pulsar Client (HTTP Admin API + binary protocol)
# ═══════════════════════════════════════════════════════════════

class PulsarClient:
    """Client for Apache Pulsar — HTTP admin API for management,
    pulsar-client library for pub/sub if available, HTTP producer/consumer as fallback."""

    def __init__(self, http_url=None, binary_url=None):
        self.http_url = (http_url or PULSAR_HTTP_URL).rstrip("/")
        self.binary_url = binary_url or PULSAR_URL
        self._available = None
        self._pulsar_lib = None
        self._producers = {}
        self._try_import_pulsar()

    def _try_import_pulsar(self):
        """Try to import the pulsar-client library (optional)."""
        try:
            import pulsar
            self._pulsar_lib = pulsar
        except ImportError:
            self._pulsar_lib = None

    def _http_request(self, method: str, path: str, data: dict = None) -> dict:
        """Make HTTP request to Pulsar admin API."""
        url = f"{self.http_url}{path}"
        body = json.dumps(data).encode() if data else None
        headers = {"Content-Type": "application/json"}
        req = Request(url, data=body, headers=headers, method=method)
        with urlopen(req, timeout=10) as resp:
            content = resp.read().decode()
            return json.loads(content) if content else {}

    def is_available(self) -> bool:
        """Check if Pulsar broker is reachable."""
        if self._available is not None:
            return self._available
        try:
            req = Request(
                f"{self.http_url}/admin/v2/brokers/healthcheck",
                method="GET"
            )
            with urlopen(req, timeout=5) as resp:
                self._available = resp.status == 200
        except Exception:
            self._available = False
        return self._available

    def get_status(self) -> dict:
        """Get broker status."""
        try:
            # Get cluster info
            clusters = self._http_request("GET", "/admin/v2/clusters")
            return {"status": "healthy", "clusters": clusters}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ensure_tenant_namespace(self):
        """Create tenant and namespace if they don't exist."""
        # Create tenant
        try:
            self._http_request("GET", f"/admin/v2/tenants/{PULSAR_TENANT}")
        except HTTPError as e:
            if e.code == 404:
                self._http_request("PUT", f"/admin/v2/tenants/{PULSAR_TENANT}", {
                    "allowedClusters": ["standalone"]
                })

        # Create namespace
        try:
            self._http_request("GET", f"/admin/v2/namespaces/{PULSAR_TENANT}/{PULSAR_NAMESPACE}")
        except HTTPError as e:
            if e.code == 404:
                self._http_request("PUT", f"/admin/v2/namespaces/{PULSAR_TENANT}/{PULSAR_NAMESPACE}")

    def topic_name(self, project: str) -> str:
        """Build a full topic name for a project."""
        safe_project = project.replace("/", "-").replace(" ", "-").lower()
        return f"persistent://{PULSAR_TENANT}/{PULSAR_NAMESPACE}/{safe_project}"

    def list_topics(self) -> list:
        """List all topics in the namespace."""
        try:
            return self._http_request(
                "GET",
                f"/admin/v2/persistent/{PULSAR_TENANT}/{PULSAR_NAMESPACE}"
            )
        except Exception:
            return []

    def publish(self, project: str, event: dict) -> dict:
        """Publish an event to a project topic."""
        if not self.is_available():
            return {"status": "unavailable", "reason": "Pulsar not running"}

        topic = self.topic_name(project)

        # Try native pulsar-client first (faster, binary protocol)
        if self._pulsar_lib:
            return self._publish_native(topic, event)

        # Fallback: HTTP producer
        return self._publish_http(topic, event)

    def _publish_native(self, topic: str, event: dict) -> dict:
        """Publish using native pulsar-client library."""
        try:
            if topic not in self._producers:
                client = self._pulsar_lib.Client(self.binary_url)
                self._producers[topic] = client.create_producer(topic)
            msg_id = self._producers[topic].send(
                json.dumps(event).encode("utf-8")
            )
            return {"status": "published", "topic": topic, "method": "native", "msg_id": str(msg_id)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _publish_http(self, topic: str, event: dict) -> dict:
        """Publish using HTTP producer API (no library needed)."""
        try:
            import base64
            encoded = base64.b64encode(json.dumps(event).encode()).decode()
            # Pulsar REST produce endpoint
            safe_topic = topic.replace("persistent://", "persistent/")
            url = f"{self.http_url}/topics/{safe_topic}"
            req = Request(
                url,
                data=json.dumps({"payload": encoded}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(req, timeout=10) as resp:
                return {"status": "published", "topic": topic, "method": "http"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def subscribe(self, project: str, subscription: str, callback, timeout_sec: int = 0):
        """Subscribe to a project topic (blocking or background).
        callback receives (event_dict) for each message.
        timeout_sec=0 means run forever in background thread."""
        if not self.is_available():
            return {"status": "unavailable", "reason": "Pulsar not running"}

        topic = self.topic_name(project)

        if self._pulsar_lib:
            return self._subscribe_native(topic, subscription, callback, timeout_sec)

        return {"status": "error", "message": "pulsar-client library required for subscription (pip install pulsar-client)"}

    def _subscribe_native(self, topic: str, subscription: str, callback, timeout_sec: int):
        """Subscribe using native pulsar-client library."""
        try:
            client = self._pulsar_lib.Client(self.binary_url)
            consumer = client.subscribe(
                topic,
                subscription,
                consumer_type=self._pulsar_lib.ConsumerType.Shared
            )

            def _consume():
                deadline = time.time() + timeout_sec if timeout_sec > 0 else float('inf')
                while time.time() < deadline:
                    try:
                        msg = consumer.receive(timeout_millis=1000)
                        event = json.loads(msg.data().decode())
                        callback(event)
                        consumer.acknowledge(msg)
                    except Exception:
                        continue

            if timeout_sec > 0:
                _consume()
            else:
                t = threading.Thread(target=_consume, daemon=True)
                t.start()

            return {"status": "subscribed", "topic": topic, "subscription": subscription}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Global client
_client = PulsarClient()


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def health_check() -> dict:
    """Check Pulsar broker health."""
    result = {"agent": "Apache Pulsar", "status": "not_running", "optional": True}
    if _client.is_available():
        status = _client.get_status()
        result["status"] = status.get("status", "unknown")
        result["topics"] = len(_client.list_topics())
        result["native_client"] = _client._pulsar_lib is not None
    return result


def publish_event(project: str, event_type: str, content: str,
                  developer_id: str = None, agent_id: str = None,
                  metadata: dict = None) -> dict:
    """Publish a memory event to project topic."""
    if not _client.is_available():
        return {"status": "unavailable", "reason": "Pulsar not running (events silently dropped)"}

    _client.ensure_tenant_namespace()

    event = {
        "event_type": event_type,
        "content": content,
        "developer_id": developer_id or os.environ.get("AGI_DEVELOPER_ID", "unknown"),
        "agent_id": agent_id or os.environ.get("AGI_AGENT_ID", "primary"),
        "project": project,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }

    return _client.publish(project, event)


def subscribe_events(project: str, subscription: str = None, callback=None,
                     timeout_sec: int = 0) -> dict:
    """Subscribe to events from a project."""
    if not _client.is_available():
        return {"status": "unavailable", "reason": "Pulsar not running"}

    sub_name = subscription or f"agi-{os.environ.get('AGI_DEVELOPER_ID', 'default')}"
    cb = callback or (lambda e: print(json.dumps(e, indent=2)))

    return _client.subscribe(project, sub_name, cb, timeout_sec)


def list_topics() -> dict:
    """List all active project topics."""
    if not _client.is_available():
        return {"topics": [], "status": "unavailable"}
    topics = _client.list_topics()
    return {"topics": topics, "count": len(topics)}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Agent event bus (Apache Pulsar)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check Pulsar health")

    pub = sub.add_parser("publish", help="Publish an event")
    pub.add_argument("--project", required=True)
    pub.add_argument("--event-type", required=True, choices=EVENT_TYPES)
    pub.add_argument("--content", required=True)

    sub_cmd = sub.add_parser("subscribe", help="Subscribe to events")
    sub_cmd.add_argument("--project", required=True)
    sub_cmd.add_argument("--subscription", default=None)
    sub_cmd.add_argument("--timeout", type=int, default=30, help="Seconds to listen (0=forever)")

    sub.add_parser("list-topics", help="List all active topics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "health":
        print(json.dumps(health_check(), indent=2))
    elif args.command == "publish":
        print(json.dumps(publish_event(args.project, args.event_type, args.content), indent=2))
    elif args.command == "subscribe":
        result = subscribe_events(args.project, args.subscription, timeout_sec=args.timeout)
        if result.get("status") != "subscribed":
            print(json.dumps(result, indent=2))
            sys.exit(1)
        print(f"Listening on {args.project} for {args.timeout}s...")
        time.sleep(args.timeout)
    elif args.command == "list-topics":
        print(json.dumps(list_topics(), indent=2))


if __name__ == "__main__":
    main()
