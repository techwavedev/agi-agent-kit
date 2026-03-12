#!/usr/bin/env python3
"""
Script: init_collection.py
Purpose: Initialize Qdrant collections for semantic caching and memory storage.

Usage:
    python init_collection.py --collection agent_memory --dimension 1536
    python init_collection.py --collection semantic_cache --dimension 1536 --distance cosine

Arguments:
    --collection  Collection name (required)
    --dimension   Vector dimension (default: 1536 for OpenAI embeddings)
    --distance    Distance metric: cosine, euclid, dot (default: cosine)
    --url         Qdrant URL (default: http://localhost:6333)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Connection error
    3 - Collection creation error
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def create_collection(url: str, name: str, dimension: int, distance: str) -> dict:
    """Create a Qdrant collection with optimized settings."""
    
    distance_map = {
        "cosine": "Cosine",
        "euclid": "Euclid", 
        "dot": "Dot"
    }
    
    payload = {
        "vectors": {
            "size": dimension,
            "distance": distance_map.get(distance.lower(), "Cosine")
        },
        "optimizers_config": {
            "indexing_threshold": 10000,
            "memmap_threshold": 20000
        },
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100,
            "full_scan_threshold": 10000
        }
    }
    
    req = Request(
        f"{url}/collections/{name}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        if e.code == 409:
            return {"status": "exists", "message": f"Collection '{name}' already exists"}
        raise


def create_payload_index(url: str, collection: str, field: str, field_type: str) -> dict:
    """Create payload index for efficient filtering."""
    
    schema_map = {
        "keyword": "keyword",
        "integer": "integer",
        "float": "float",
        "bool": "bool",
        "datetime": "datetime",
        "text": "text"
    }
    
    payload = {
        "field_name": field,
        "field_schema": schema_map.get(field_type, "keyword")
    }
    
    req = Request(
        f"{url}/collections/{collection}/index",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError:
        return {"status": "index_exists"}


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Qdrant collection for agent memory"
    )
    parser.add_argument(
        "--collection", 
        required=True,
        help="Collection name"
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=1536,
        help="Vector dimension (default: 1536)"
    )
    parser.add_argument(
        "--distance",
        choices=["cosine", "euclid", "dot"],
        default="cosine",
        help="Distance metric (default: cosine)"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        help="Qdrant URL"
    )
    
    args = parser.parse_args()
    
    print(f"🔧 Initializing collection: {args.collection}")
    print(f"   URL: {args.url}")
    print(f"   Dimension: {args.dimension}")
    print(f"   Distance: {args.distance}")
    
    try:
        # Create collection
        result = create_collection(
            args.url, 
            args.collection, 
            args.dimension, 
            args.distance
        )
        print(f"✅ Collection created: {result}")
        
        # Create standard payload indexes
        indexes = [
            ("type", "keyword"),
            ("project", "keyword"),
            ("timestamp", "datetime"),
            ("tags", "keyword"),
            ("model", "keyword"),
            ("token_count", "integer"),
            ("score_threshold", "float")
        ]
        
        print("📑 Creating payload indexes...")
        for field, field_type in indexes:
            idx_result = create_payload_index(
                args.url, 
                args.collection, 
                field, 
                field_type
            )
            print(f"   {field}: {idx_result.get('status', 'created')}")
        
        print(json.dumps({
            "status": "success",
            "collection": args.collection,
            "dimension": args.dimension,
            "distance": args.distance
        }))
        sys.exit(0)
        
    except URLError as e:
        print(json.dumps({
            "status": "error",
            "type": "connection_error",
            "message": f"Cannot connect to Qdrant at {args.url}: {e}"
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
