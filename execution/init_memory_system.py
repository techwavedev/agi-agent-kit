#!/usr/bin/env python3
"""
Script: init_memory_system.py
Purpose: Initialize the complete memory system with required Qdrant collections.

This script sets up:
1. semantic_cache - For query-response caching
2. agent_memory - For long-term memory storage

Usage:
    python execution/init_memory_system.py [--dimension 768] [--force]

Arguments:
    --dimension, -d  Embedding dimension (768 for Ollama, 1024 for Bedrock, 1536 for OpenAI)
    --force, -f      Recreate collections if they exist
    --qdrant-url     Qdrant server URL (default: http://localhost:6333)

Exit Codes:
    0 - Success
    1 - Qdrant not available
    2 - Collection creation failed
"""

import argparse
import json
import sys
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams, Distance, 
        PayloadSchemaType,
        TextIndexParams, TokenizerType,
    )
except ImportError:
    print(json.dumps({
        "status": "error",
        "message": "qdrant-client not installed. Run: pip install qdrant-client"
    }), file=sys.stderr)
    sys.exit(1)


# Collection configurations
COLLECTIONS = {
    "semantic_cache": {
        "description": "Query-response cache for semantic deduplication",
        "ttl_days": 7,
        "payload_indexes": ["query", "timestamp", "model"],
    },
    "agent_memory": {
        "description": "Long-term memory for decisions, code patterns, and knowledge",
        "ttl_days": None,  # Permanent
        "payload_indexes": ["type", "project", "timestamp", "tags"],
    },
}


def create_collection(client: QdrantClient, name: str, dimension: int, config: dict, force: bool = False):
    """Create a single collection with proper configuration."""
    
    # Check if exists
    collections = [c.name for c in client.get_collections().collections]
    
    if name in collections:
        if force:
            print(f"  ⚠️  Deleting existing collection: {name}")
            client.delete_collection(name)
        else:
            print(f"  ✓ Collection exists: {name}")
            return True
    
    # Create collection
    try:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=dimension,
                distance=Distance.COSINE,
            ),
        )
        print(f"  ✓ Created collection: {name}")
        
        # Create payload indexes for efficient filtering
        for field in config.get("payload_indexes", []):
            try:
                if field in ["tags"]:
                    # Array field
                    client.create_payload_index(
                        collection_name=name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                elif field in ["timestamp"]:
                    # Keep as keyword for now (datetime filtering)
                    client.create_payload_index(
                        collection_name=name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                else:
                    # Text/keyword field
                    client.create_payload_index(
                        collection_name=name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                print(f"    ✓ Indexed field: {field}")
            except Exception as e:
                print(f"    ⚠️  Could not index {field}: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to create {name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Initialize agent memory system")
    parser.add_argument("--dimension", "-d", type=int, default=768,
                       help="Embedding dimension (768=Ollama, 1024=Bedrock, 1536=OpenAI)")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Recreate collections if they exist")
    parser.add_argument("--qdrant-url", default="http://localhost:6333",
                       help="Qdrant server URL")
    
    args = parser.parse_args()
    
    print("🧠 Initializing Agent Memory System")
    print(f"   Qdrant URL: {args.qdrant_url}")
    print(f"   Embedding dimension: {args.dimension}")
    print()
    
    # Connect to Qdrant
    try:
        client = QdrantClient(url=args.qdrant_url)
        # Test connection
        client.get_collections()
        print("✓ Connected to Qdrant")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print()
        print("Start Qdrant with:")
        print("  docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant")
        sys.exit(1)
    
    print()
    print("Creating collections...")
    
    # Create all collections
    success = True
    for name, config in COLLECTIONS.items():
        if not create_collection(client, name, args.dimension, config, args.force):
            success = False
    
    print()
    
    if success:
        print("✅ Memory system initialized successfully!")
        print()
        print("Collections ready:")
        for name, config in COLLECTIONS.items():
            info = client.get_collection(name)
            print(f"  • {name}: {info.points_count} points, {config['description']}")
        
        print()
        print("Next steps:")
        print("  1. Ensure embedding provider is running (ollama serve)")
        print("  2. Memory middleware will auto-activate for all operations")
        print("  3. Use 'no cache' or 'fresh' to skip caching when needed")
        
        print()
        print(json.dumps({
            "status": "success",
            "collections": list(COLLECTIONS.keys()),
            "dimension": args.dimension,
            "timestamp": datetime.now().isoformat(),
        }))
        sys.exit(0)
    else:
        print("❌ Some collections failed to initialize")
        sys.exit(2)


if __name__ == "__main__":
    main()
