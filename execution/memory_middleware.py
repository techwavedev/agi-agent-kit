#!/usr/bin/env python3
"""
Script: memory_middleware.py
Purpose: Automatic memory integration middleware for all agent operations.
         Provides semantic caching and context retrieval for token optimization.

This middleware is the CORE of the agent's memory system. It:
1. Checks semantic cache before any LLM call (100% token savings on hit)
2. Retrieves relevant context from long-term memory (80-95% context reduction)
3. Stores responses and decisions for future retrieval
4. Tracks token savings metrics

Usage:
    # Import and use as wrapper
    from execution.memory_middleware import MemoryMiddleware, memory_wrap
    
    # Option 1: Decorator
    @memory_wrap
    def my_function(query):
        return llm_call(query)
    
    # Option 2: Context manager
    with MemoryMiddleware() as memory:
        cached = memory.check_cache(query)
        if cached:
            return cached
        response = llm_call(query)
        memory.store(query, response)

Environment Variables:
    MEMORY_ENABLED     - Enable/disable memory (default: true)
    QDRANT_URL         - Qdrant server URL (default: http://localhost:6333)
    EMBEDDING_PROVIDER - ollama, bedrock, or openai (default: ollama)
    CACHE_THRESHOLD    - Similarity threshold for cache hits (default: 0.92)

Exit Codes:
    0 - Success
    1 - Configuration error
    2 - Qdrant connection error
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from pathlib import Path

# Add skills directory to path for imports
SKILLS_DIR = Path(__file__).parent.parent / "skills" / "qdrant-memory" / "scripts"
if SKILLS_DIR.exists():
    sys.path.insert(0, str(SKILLS_DIR))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Try to import embedding utilities from qdrant-memory skill
try:
    from embedding_utils import get_embedding, get_embedding_dimension
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class MemoryMiddleware:
    """
    Automatic memory integration for all agent operations.
    
    Provides:
    - Semantic cache checking (before LLM calls)
    - Context retrieval (relevant memories as context)
    - Response storage (after LLM calls)
    - Token savings tracking
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "qdrant_url": "http://localhost:6333",
        "cache_collection": "semantic_cache",
        "memory_collection": "agent_memory",
        "cache_threshold": 0.92,
        "memory_threshold": 0.7,
        "cache_ttl_days": 7,
        "max_context_chunks": 5,
        "enabled": True,
    }
    
    # Singleton instance for global state
    _instance = None
    _metrics = {
        "cache_hits": 0,
        "cache_misses": 0,
        "tokens_saved": 0,
        "queries_processed": 0,
    }
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if self._initialized:
            return
            
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._load_environment()
        self._client = None
        self._embedding_dim = None
        self._initialized = True
        
        # Check if memory is disabled
        if not self.config["enabled"]:
            print("⚠️  Memory middleware disabled via configuration")
            return
            
        # Validate dependencies
        if not QDRANT_AVAILABLE:
            print("⚠️  qdrant-client not installed. Run: pip install qdrant-client")
            self.config["enabled"] = False
            return
            
        if not EMBEDDINGS_AVAILABLE:
            print("⚠️  Embedding utilities not available. Check qdrant-memory skill installation.")
            self.config["enabled"] = False
            return
        
        # Initialize connection
        self._connect()
    
    def _load_environment(self):
        """Load configuration from environment variables."""
        env_mapping = {
            "MEMORY_ENABLED": ("enabled", lambda x: x.lower() != "false"),
            "QDRANT_URL": ("qdrant_url", str),
            "CACHE_THRESHOLD": ("cache_threshold", float),
            "CACHE_TTL_DAYS": ("cache_ttl_days", int),
        }
        
        for env_var, (config_key, converter) in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    self.config[config_key] = converter(value)
                except ValueError:
                    pass
    
    def _connect(self) -> bool:
        """Establish connection to Qdrant."""
        try:
            self._client = QdrantClient(url=self.config["qdrant_url"])
            # Test connection
            self._client.get_collections()
            self._embedding_dim = get_embedding_dimension()
            return True
        except Exception as e:
            print(f"⚠️  Qdrant connection failed: {e}")
            self.config["enabled"] = False
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if memory middleware is enabled and connected."""
        return self.config["enabled"] and self._client is not None
    
    def _generate_id(self, text: str) -> str:
        """Generate a unique ID from text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def check_cache(self, query: str, metadata_filter: Optional[Dict] = None) -> Optional[Dict]:
        """
        Check semantic cache for a similar query.
        
        Args:
            query: The query to check
            metadata_filter: Optional filter for cache entries
            
        Returns:
            Cached response dict if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        self._metrics["queries_processed"] += 1
        
        try:
            # Generate embedding for query
            embedding = get_embedding(query)
            
            # Build filter
            search_filter = None
            if metadata_filter:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in metadata_filter.items()
                ]
                search_filter = Filter(must=conditions)
            
            # Search cache
            results = self._client.search(
                collection_name=self.config["cache_collection"],
                query_vector=embedding,
                query_filter=search_filter,
                limit=1,
                score_threshold=self.config["cache_threshold"],
            )
            
            if results:
                self._metrics["cache_hits"] += 1
                payload = results[0].payload
                self._metrics["tokens_saved"] += payload.get("token_count", 0)
                
                return {
                    "response": payload.get("response"),
                    "cached_at": payload.get("timestamp"),
                    "similarity": results[0].score,
                    "cache_hit": True,
                }
            
            self._metrics["cache_misses"] += 1
            return None
            
        except Exception as e:
            print(f"⚠️  Cache check error: {e}")
            return None
    
    def retrieve_context(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve relevant context from long-term memory.
        
        Args:
            query: The query to find context for
            memory_types: Optional list of memory types to filter (decision, code, error, etc.)
            top_k: Maximum number of context chunks to return
            
        Returns:
            List of relevant context chunks with metadata
        """
        if not self.is_enabled:
            return []
        
        try:
            embedding = get_embedding(query)
            
            # Build filter for memory types
            search_filter = None
            if memory_types:
                search_filter = Filter(
                    should=[
                        FieldCondition(key="type", match=MatchValue(value=t))
                        for t in memory_types
                    ]
                )
            
            results = self._client.search(
                collection_name=self.config["memory_collection"],
                query_vector=embedding,
                query_filter=search_filter,
                limit=min(top_k, self.config["max_context_chunks"]),
                score_threshold=self.config["memory_threshold"],
            )
            
            return [
                {
                    "content": r.payload.get("content"),
                    "type": r.payload.get("type"),
                    "timestamp": r.payload.get("timestamp"),
                    "relevance": r.score,
                    "metadata": {k: v for k, v in r.payload.items() 
                               if k not in ("content", "type", "timestamp")}
                }
                for r in results
            ]
            
        except Exception as e:
            print(f"⚠️  Context retrieval error: {e}")
            return []
    
    def store_response(
        self,
        query: str,
        response: str,
        metadata: Optional[Dict] = None,
        cache: bool = True,
    ) -> bool:
        """
        Store a query-response pair in the cache.
        
        Args:
            query: The original query
            response: The generated response
            metadata: Optional metadata (model, project, tags, etc.)
            cache: Whether to store in cache collection
            
        Returns:
            True if stored successfully
        """
        if not self.is_enabled:
            return False
        
        try:
            embedding = get_embedding(query)
            point_id = self._generate_id(query)
            
            payload = {
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "token_count": len(response.split()),
                **(metadata or {})
            }
            
            collection = self.config["cache_collection"] if cache else self.config["memory_collection"]
            
            self._client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️  Store error: {e}")
            return False
    
    def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Store a memory in long-term storage.
        
        Args:
            content: The content to remember
            memory_type: Type of memory (decision, code, error, conversation, technical)
            metadata: Optional metadata (project, tags, etc.)
            
        Returns:
            True if stored successfully
        """
        if not self.is_enabled:
            return False
        
        try:
            embedding = get_embedding(content)
            point_id = self._generate_id(content + memory_type)
            
            payload = {
                "content": content,
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            self._client.upsert(
                collection_name=self.config["memory_collection"],
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️  Memory store error: {e}")
            return False
    
    def get_metrics(self) -> Dict:
        """Get current memory metrics."""
        return {
            **self._metrics,
            "cache_hit_rate": (
                self._metrics["cache_hits"] / max(1, self._metrics["queries_processed"]) * 100
            ),
            "enabled": self.is_enabled,
        }
    
    def clear_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count of removed entries."""
        if not self.is_enabled:
            return 0
        
        try:
            cutoff = (datetime.now() - timedelta(days=self.config["cache_ttl_days"])).isoformat()
            
            # Note: This requires Qdrant 1.7+ for delete by filter
            result = self._client.delete(
                collection_name=self.config["cache_collection"],
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="timestamp",
                            range={"lt": cutoff}
                        )
                    ]
                ),
            )
            return result.deleted if hasattr(result, 'deleted') else 0
            
        except Exception as e:
            print(f"⚠️  Cache cleanup error: {e}")
            return 0


def memory_wrap(func: Callable = None, *, 
                cache: bool = True, 
                retrieve_context: bool = True,
                memory_types: Optional[List[str]] = None):
    """
    Decorator to wrap functions with automatic memory integration.
    
    Usage:
        @memory_wrap
        def my_function(query):
            return llm_response
        
        @memory_wrap(cache=False)  # Disable caching for this function
        def volatile_function(query):
            return real_time_data
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            memory = MemoryMiddleware()
            
            # Extract query from args/kwargs
            query = args[0] if args else kwargs.get("query", str(kwargs))
            
            # Check cache first
            if cache:
                cached = memory.check_cache(query)
                if cached:
                    print(f"💾 Cache hit! Saved ~{cached.get('similarity', 0):.0%} similar query")
                    return cached["response"]
            
            # Retrieve context if enabled
            context = []
            if retrieve_context:
                context = memory.retrieve_context(query, memory_types=memory_types)
                if context:
                    # Inject context into kwargs
                    kwargs["_memory_context"] = context
            
            # Execute function
            result = fn(*args, **kwargs)
            
            # Store response in cache
            if cache and isinstance(result, str):
                memory.store_response(query, result)
            
            return result
        
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


# Global instance for direct access
_global_memory = None

def get_memory() -> MemoryMiddleware:
    """Get the global memory middleware instance."""
    global _global_memory
    if _global_memory is None:
        _global_memory = MemoryMiddleware()
    return _global_memory


def disable_memory():
    """Disable memory middleware for the current session."""
    memory = get_memory()
    memory.config["enabled"] = False
    print("🔇 Memory middleware disabled for this session")


def enable_memory():
    """Re-enable memory middleware."""
    memory = get_memory()
    memory.config["enabled"] = True
    if memory._client is None:
        memory._connect()
    print("🔊 Memory middleware enabled")


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Middleware CLI")
    parser.add_argument("--status", action="store_true", help="Show memory status")
    parser.add_argument("--metrics", action="store_true", help="Show metrics")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--cleanup", action="store_true", help="Clean expired cache")
    
    args = parser.parse_args()
    
    memory = MemoryMiddleware()
    
    if args.status:
        print(json.dumps({
            "enabled": memory.is_enabled,
            "qdrant_url": memory.config["qdrant_url"],
            "cache_collection": memory.config["cache_collection"],
            "memory_collection": memory.config["memory_collection"],
        }, indent=2))
    
    elif args.metrics:
        print(json.dumps(memory.get_metrics(), indent=2))
    
    elif args.test:
        if memory.is_enabled:
            print("✅ Memory middleware connected successfully")
            print(f"   Qdrant: {memory.config['qdrant_url']}")
            print(f"   Embedding dimension: {memory._embedding_dim}")
        else:
            print("❌ Memory middleware not available")
            sys.exit(1)
    
    elif args.cleanup:
        removed = memory.clear_expired_cache()
        print(f"🧹 Removed {removed} expired cache entries")
    
    else:
        parser.print_help()
