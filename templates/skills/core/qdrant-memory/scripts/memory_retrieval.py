#!/usr/bin/env python3
"""
Script: memory_retrieval.py
Purpose: Long-term memory retrieval for context optimization.

Supports both Ollama (local/private) and OpenAI (cloud) embeddings.
Default: Ollama with nomic-embed-text model.

Usage:
    # Retrieve relevant context (uses Ollama by default)
    python3 memory_retrieval.py retrieve --query "database architecture decisions"
    
    # Store memory
    python3 memory_retrieval.py store --content "We chose PostgreSQL..." --type decision
    
    # List memories
    python3 memory_retrieval.py list --type decision --project api-catalogue

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default) or "openai"
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    OPENAI_API_KEY      - Required for OpenAI provider
    QDRANT_URL          - Qdrant server URL (default: http://localhost:6333)
    MEMORY_COLLECTION   - Collection name (default: agent_memory)

Functions:
    retrieve_context(query, filters, top_k) - Get relevant memory chunks
    store_memory(content, memory_type, metadata) - Store new memory
    list_memories(filters) - List memories with filtering

Exit Codes:
    0 - Success
    1 - No results found
    2 - Connection error
    3 - Operation error
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Import shared embedding utilities (supports Ollama and OpenAI)
try:
    from embedding_utils import get_embedding
except ImportError:
    # Fallback if run from different directory
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from embedding_utils import get_embedding

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("MEMORY_COLLECTION", "agent_memory")


def retrieve_context(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 5,
    score_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context from long-term memory.
    
    Instead of passing 20K tokens of conversation history,
    this returns only the top-K most relevant chunks (500-1000 tokens).
    
    Args:
        query: Natural language query
        filters: Qdrant filter conditions (type, project, tags, etc.)
        top_k: Number of results to return
        score_threshold: Minimum similarity score
    
    Returns:
        List of relevant memory chunks with metadata
    """
    embedding = get_embedding(query)
    
    search_payload = {
        "vector": embedding,
        "limit": top_k,
        "score_threshold": score_threshold,
        "with_payload": True
    }
    
    if filters:
        search_payload["filter"] = filters
    
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        data=json.dumps(search_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
        chunks = []
        total_tokens = 0
        
        for hit in result.get("result", []):
            content = hit["payload"].get("content", "")
            token_estimate = len(content.split())
            total_tokens += token_estimate
            
            chunks.append({
                "content": content,
                "score": hit["score"],
                "type": hit["payload"].get("type"),
                "project": hit["payload"].get("project"),
                "timestamp": hit["payload"].get("timestamp"),
                "tags": hit["payload"].get("tags", []),
                "token_estimate": token_estimate
            })
        
        return {
            "chunks": chunks,
            "total_chunks": len(chunks),
            "total_tokens_estimate": total_tokens,
            "query": query
        }
        
    except HTTPError as e:
        if e.code == 404:
            return {"chunks": [], "total_chunks": 0, "total_tokens_estimate": 0}
        raise


def store_memory(
    content: str,
    memory_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a new memory in long-term storage.
    
    Args:
        content: The memory content (text)
        memory_type: Category (decision, code, error, conversation, technical)
        metadata: Additional metadata (project, tags, etc.)
    
    Returns:
        Storage confirmation
    """
    embedding = get_embedding(content)
    
    # Generate UUID for memory
    point_id = str(uuid.uuid4())
    
    payload = {
        "content": content,
        "type": memory_type,
        "timestamp": datetime.utcnow().isoformat(),
        "token_count": len(content.split()),
        **(metadata or {})
    }
    
    upsert_payload = {
        "points": [
            {
                "id": point_id,
                "vector": embedding,
                "payload": payload
            }
        ]
    }
    
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
        data=json.dumps(upsert_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        
    return {
        "status": "stored",
        "point_id": point_id,
        "type": memory_type,
        "token_count": payload["token_count"],
        "result": result
    }


def list_memories(
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List memories with optional filtering.
    
    Args:
        filters: Qdrant filter conditions
        limit: Maximum number of results
    
    Returns:
        List of memories matching filters
    """
    scroll_payload = {
        "limit": limit,
        "with_payload": True,
        "with_vector": False
    }
    
    if filters:
        scroll_payload["filter"] = filters
    
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
        data=json.dumps(scroll_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        
    memories = []
    for point in result.get("result", {}).get("points", []):
        memories.append({
            "id": point["id"],
            "type": point["payload"].get("type"),
            "content_preview": point["payload"].get("content", "")[:200] + "...",
            "project": point["payload"].get("project"),
            "timestamp": point["payload"].get("timestamp"),
            "tags": point["payload"].get("tags", [])
        })
    
    return {
        "memories": memories,
        "count": len(memories),
        "has_more": result.get("result", {}).get("next_page_offset") is not None
    }


def build_filter(type_filter: str = None, project: str = None, tags: List[str] = None) -> Dict:
    """Build Qdrant filter from arguments."""
    must = []
    
    if type_filter:
        must.append({"key": "type", "match": {"value": type_filter}})
    if project:
        must.append({"key": "project", "match": {"value": project}})
    if tags:
        must.append({"key": "tags", "match": {"any": tags}})
    
    return {"must": must} if must else None


def main():
    parser = argparse.ArgumentParser(description="Long-term memory operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve relevant context")
    retrieve_parser.add_argument("--query", required=True, help="Search query")
    retrieve_parser.add_argument("--type", help="Filter by memory type")
    retrieve_parser.add_argument("--project", help="Filter by project")
    retrieve_parser.add_argument("--tags", nargs="+", help="Filter by tags")
    retrieve_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    retrieve_parser.add_argument("--threshold", type=float, default=0.7, help="Score threshold")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store new memory")
    store_parser.add_argument("--content", required=True, help="Memory content")
    store_parser.add_argument("--type", required=True, 
                              choices=["decision", "code", "error", "conversation", "technical"],
                              help="Memory type")
    store_parser.add_argument("--project", help="Project name")
    store_parser.add_argument("--tags", nargs="+", help="Tags for the memory")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List memories")
    list_parser.add_argument("--type", help="Filter by memory type")
    list_parser.add_argument("--project", help="Filter by project")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results")
    
    args = parser.parse_args()
    
    try:
        if args.command == "retrieve":
            filters = build_filter(
                type_filter=getattr(args, "type", None),
                project=args.project,
                tags=args.tags
            )
            result = retrieve_context(
                args.query,
                filters={"must": filters["must"]} if filters else None,
                top_k=args.top_k,
                score_threshold=args.threshold
            )
            print(json.dumps(result, indent=2))
            sys.exit(0 if result["total_chunks"] > 0 else 1)
            
        elif args.command == "store":
            metadata = {}
            if args.project:
                metadata["project"] = args.project
            if args.tags:
                metadata["tags"] = args.tags
                
            result = store_memory(args.content, args.type, metadata)
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
        elif args.command == "list":
            filters = build_filter(
                type_filter=getattr(args, "type", None),
                project=args.project
            )
            result = list_memories(
                filters={"must": filters["must"]} if filters else None,
                limit=args.limit
            )
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
    except URLError as e:
        print(json.dumps({
            "status": "error",
            "type": "connection_error",
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "type": type(e).__name__,
            "message": str(e)
        }), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
