#!/usr/bin/env python3
"""
Script: semantic_cache.py
Purpose: Semantic caching for LLM responses using Qdrant vector similarity.

Usage:
    # Check cache
    python semantic_cache.py check --query "How do I reset my password?"
    
    # Store response
    python semantic_cache.py store --query "Password reset" --response "Go to settings..."
    
    # Clear cache
    python semantic_cache.py clear --older-than 7

Functions:
    check_cache(query, threshold) - Check for semantically similar cached response
    store_response(query, response, metadata) - Store query-response pair
    clear_cache(older_than_days) - Remove old cache entries

Exit Codes:
    0 - Success (cache hit or stored)
    1 - Cache miss (no similar query found)
    2 - Connection error
    3 - Embedding error
"""

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.environ.get("CACHE_COLLECTION", "semantic_cache")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_THRESHOLD = 0.92


def get_embedding(text: str) -> list:
    """Generate embedding using OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    payload = {
        "input": text,
        "model": EMBEDDING_MODEL
    }
    
    req = Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        method="POST"
    )
    
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        return result["data"][0]["embedding"]


def check_cache(query: str, threshold: float = DEFAULT_THRESHOLD) -> Optional[Dict[str, Any]]:
    """
    Check if a semantically similar query exists in cache.
    
    Args:
        query: The user query to check
        threshold: Minimum similarity score (0.0-1.0)
    
    Returns:
        Cached response dict if found, None otherwise
    """
    embedding = get_embedding(query)
    
    search_payload = {
        "vector": embedding,
        "limit": 1,
        "score_threshold": threshold,
        "with_payload": True
    }
    
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        data=json.dumps(search_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
        if result.get("result") and len(result["result"]) > 0:
            hit = result["result"][0]
            return {
                "cache_hit": True,
                "score": hit["score"],
                "query": hit["payload"].get("query"),
                "response": hit["payload"].get("response"),
                "timestamp": hit["payload"].get("timestamp"),
                "model": hit["payload"].get("model"),
                "tokens_saved": hit["payload"].get("token_count", 0)
            }
        return None
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def store_response(
    query: str, 
    response: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Store a query-response pair in the semantic cache.
    
    Args:
        query: The original query
        response: The LLM response
        metadata: Additional metadata (model, project, etc.)
    
    Returns:
        Storage confirmation with point ID
    """
    embedding = get_embedding(query)
    
    # Generate deterministic ID from query hash
    point_id = int(hashlib.md5(query.encode()).hexdigest()[:16], 16) % (2**63)
    
    payload = {
        "query": query,
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "cache",
        "token_count": len(response.split()),
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
    
    with urlopen(req, timeout=30) as response_obj:
        result = json.loads(response_obj.read().decode())
        
    return {
        "status": "stored",
        "point_id": point_id,
        "token_count": payload["token_count"],
        "result": result
    }


def clear_cache(older_than_days: int = 7) -> Dict[str, Any]:
    """
    Clear cache entries older than specified days.
    
    Args:
        older_than_days: Delete entries older than this
    
    Returns:
        Deletion result with count
    """
    cutoff = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
    
    delete_payload = {
        "filter": {
            "must": [
                {
                    "key": "timestamp",
                    "range": {
                        "lt": cutoff
                    }
                },
                {
                    "key": "type",
                    "match": {
                        "value": "cache"
                    }
                }
            ]
        }
    }
    
    req = Request(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/delete?wait=true",
        data=json.dumps(delete_payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
        
    return {
        "status": "cleared",
        "older_than_days": older_than_days,
        "cutoff_date": cutoff,
        "result": result
    }


def main():
    parser = argparse.ArgumentParser(description="Semantic cache operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check cache for query")
    check_parser.add_argument("--query", required=True, help="Query to check")
    check_parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                              help=f"Similarity threshold (default: {DEFAULT_THRESHOLD})")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store query-response pair")
    store_parser.add_argument("--query", required=True, help="Original query")
    store_parser.add_argument("--response", required=True, help="LLM response")
    store_parser.add_argument("--model", default="gpt-4", help="Model used")
    store_parser.add_argument("--project", help="Project name")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear old cache entries")
    clear_parser.add_argument("--older-than", type=int, default=7,
                              help="Delete entries older than N days")
    
    args = parser.parse_args()
    
    try:
        if args.command == "check":
            result = check_cache(args.query, args.threshold)
            if result:
                print(json.dumps(result, indent=2))
                sys.exit(0)
            else:
                print(json.dumps({"cache_hit": False, "query": args.query}))
                sys.exit(1)
                
        elif args.command == "store":
            metadata = {"model": args.model}
            if args.project:
                metadata["project"] = args.project
            result = store_response(args.query, args.response, metadata)
            print(json.dumps(result, indent=2))
            sys.exit(0)
            
        elif args.command == "clear":
            result = clear_cache(args.older_than)
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
