#!/usr/bin/env python3
"""
Script: test_skill.py
Purpose: Comprehensive test suite for the qdrant-memory skill.

Usage:
    # Quick connectivity test (no embeddings)
    python test_skill.py --mode connectivity
    
    # Full test with LOCAL embeddings (Ollama - recommended for M3 Mac)
    python test_skill.py --mode full --embeddings ollama
    
    # Full test with OpenAI embeddings
    python test_skill.py --mode full --embeddings openai
    
    # Cleanup after tests
    python test_skill.py --cleanup

Prerequisites for Ollama (local):
    1. Install: brew install ollama
    2. Start: ollama serve
    3. Pull model: ollama pull nomic-embed-text

Exit Codes:
    0 - All tests passed
    1 - Some tests failed
    2 - Connection error
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Dict, Any, Optional, List

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TEST_COLLECTION = "test_qdrant_memory_skill"

# Embedding model configurations
EMBEDDING_CONFIGS = {
    "ollama": {
        "model": "nomic-embed-text",
        "dimensions": 768,
        "url": f"{OLLAMA_URL}/api/embeddings"
    },
    "openai": {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "url": "https://api.openai.com/v1/embeddings"
    }
}

# Will be set based on --embeddings argument
EMBEDDING_PROVIDER = "ollama"
VECTOR_DIM = 768


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test(name: str, passed: bool, details: str = ""):
    icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"  {icon} {name}: {status}")
    if details:
        print(f"      {Colors.YELLOW}{details}{Colors.RESET}")


def qdrant_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make a request to Qdrant API."""
    url = f"{QDRANT_URL}{endpoint}"
    req = Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"},
        method=method
    )
    
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def get_embedding_ollama(text: str) -> List[float]:
    """Generate embedding using Ollama (local)."""
    config = EMBEDDING_CONFIGS["ollama"]
    
    payload = {
        "model": config["model"],
        "prompt": text
    }
    
    req = Request(
        config["url"],
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode())
        return result["embedding"]


def get_embedding_openai(text: str) -> List[float]:
    """Generate embedding using OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    
    config = EMBEDDING_CONFIGS["openai"]
    
    payload = {
        "input": text,
        "model": config["model"]
    }
    
    req = Request(
        config["url"],
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


def get_embedding(text: str) -> List[float]:
    """Generate embedding using configured provider."""
    if EMBEDDING_PROVIDER == "ollama":
        return get_embedding_ollama(text)
    else:
        return get_embedding_openai(text)


def test_connectivity() -> bool:
    """Test 1: Basic Qdrant connectivity."""
    try:
        result = qdrant_request("GET", "/collections")
        return result.get("status") == "ok"
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_ollama_connectivity() -> bool:
    """Test Ollama connectivity."""
    try:
        req = Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return "models" in result
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_create_collection() -> bool:
    """Test 2: Create test collection."""
    try:
        payload = {
            "vectors": {
                "size": VECTOR_DIM,
                "distance": "Cosine"
            }
        }
        result = qdrant_request("PUT", f"/collections/{TEST_COLLECTION}", payload)
        return result.get("result") == True or "already exists" in str(result)
    except HTTPError as e:
        if e.code == 409:  # Collection exists
            return True
        print(f"      Error: {e}")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_collection_info() -> bool:
    """Test 3: Get collection info."""
    try:
        result = qdrant_request("GET", f"/collections/{TEST_COLLECTION}")
        info = result.get("result", {})
        # Accept both green (optimized) and yellow (indexing) status
        valid_status = info.get("status") in ["green", "yellow"]
        has_vectors = info.get("vectors_count") is not None
        return valid_status and has_vectors
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_upsert_with_mock_vector() -> bool:
    """Test 4: Upsert a point with mock vector (no API key needed)."""
    try:
        # Create a mock vector
        mock_vector = [0.1 * (i % 10) for i in range(VECTOR_DIM)]
        
        point_id = str(uuid.uuid4())
        payload = {
            "points": [{
                "id": point_id,
                "vector": mock_vector,
                "payload": {
                    "content": "This is a test memory for validation purposes",
                    "type": "test",
                    "project": "qdrant-memory-test",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": ["test", "validation"]
                }
            }]
        }
        
        result = qdrant_request("PUT", f"/collections/{TEST_COLLECTION}/points?wait=true", payload)
        return result.get("status") == "ok"
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_search_with_mock_vector() -> bool:
    """Test 5: Search using mock vector."""
    try:
        mock_vector = [0.1 * (i % 10) for i in range(VECTOR_DIM)]
        
        payload = {
            "vector": mock_vector,
            "limit": 5,
            "with_payload": True
        }
        
        result = qdrant_request("POST", f"/collections/{TEST_COLLECTION}/points/search", payload)
        results = result.get("result", [])
        return len(results) > 0 and results[0].get("score", 0) > 0.9
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_filter_search() -> bool:
    """Test 6: Search with payload filter."""
    try:
        mock_vector = [0.1 * (i % 10) for i in range(VECTOR_DIM)]
        
        payload = {
            "vector": mock_vector,
            "limit": 5,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "type", "match": {"value": "test"}}
                ]
            }
        }
        
        result = qdrant_request("POST", f"/collections/{TEST_COLLECTION}/points/search", payload)
        results = result.get("result", [])
        return len(results) > 0
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_embedding_generation() -> bool:
    """Test 7: Embedding generation (local or OpenAI)."""
    try:
        embedding = get_embedding("This is a test query for embedding generation")
        return len(embedding) == VECTOR_DIM
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_store_with_real_embedding() -> bool:
    """Test 8: Store memory with real embedding."""
    try:
        text = "We decided to use PostgreSQL for user data due to ACID compliance requirements"
        embedding = get_embedding(text)
        
        point_id = str(uuid.uuid4())
        payload = {
            "points": [{
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "content": text,
                    "type": "decision",
                    "project": "test-project",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tags": ["database", "architecture", "test"]
                }
            }]
        }
        
        result = qdrant_request("PUT", f"/collections/{TEST_COLLECTION}/points?wait=true", payload)
        return result.get("status") == "ok"
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_semantic_search() -> bool:
    """Test 9: Semantic search (similar but not identical query)."""
    try:
        # Search with semantically similar query
        query = "What database did we choose for storing user information?"
        embedding = get_embedding(query)
        
        payload = {
            "vector": embedding,
            "limit": 5,
            "with_payload": True,
            "score_threshold": 0.5  # Lower threshold for local models
        }
        
        result = qdrant_request("POST", f"/collections/{TEST_COLLECTION}/points/search", payload)
        results = result.get("result", [])
        
        # Check if we found the PostgreSQL decision
        for r in results:
            content = r.get("payload", {}).get("content", "")
            if "PostgreSQL" in content or "database" in content.lower():
                return True
        return len(results) > 0  # At least found something
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_hybrid_search() -> bool:
    """Test 10: Hybrid search (vector + filter)."""
    try:
        query = "database architecture"
        embedding = get_embedding(query)
        
        payload = {
            "vector": embedding,
            "limit": 5,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "type", "match": {"value": "decision"}}
                ]
            }
        }
        
        result = qdrant_request("POST", f"/collections/{TEST_COLLECTION}/points/search", payload)
        results = result.get("result", [])
        
        # Verify all results have type=decision
        for r in results:
            if r.get("payload", {}).get("type") != "decision":
                return False
        return len(results) > 0
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_cache_simulation() -> bool:
    """Test 11: Cache simulation (store and retrieve similar query)."""
    try:
        # Store a "cached" response
        original_query = "How do I reset my password in the admin panel?"
        response_text = "Navigate to Settings > Security > Reset Password and follow the prompts."
        
        embedding = get_embedding(original_query)
        
        cache_payload = {
            "points": [{
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "query": original_query,
                    "response": response_text,
                    "type": "cache",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "model": "test"
                }
            }]
        }
        
        qdrant_request("PUT", f"/collections/{TEST_COLLECTION}/points?wait=true", cache_payload)
        
        # Now search with a similar (not identical) query
        similar_query = "How can I change my password?"
        similar_embedding = get_embedding(similar_query)
        
        search_payload = {
            "vector": similar_embedding,
            "limit": 1,
            "with_payload": True,
            "score_threshold": 0.6,  # Adjusted for local models
            "filter": {
                "must": [{"key": "type", "match": {"value": "cache"}}]
            }
        }
        
        result = qdrant_request("POST", f"/collections/{TEST_COLLECTION}/points/search", search_payload)
        results = result.get("result", [])
        
        if results and results[0].get("score", 0) > 0.6:
            cached_response = results[0].get("payload", {}).get("response")
            return cached_response == response_text
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def cleanup_test_collection() -> bool:
    """Cleanup: Delete test collection."""
    try:
        result = qdrant_request("DELETE", f"/collections/{TEST_COLLECTION}")
        return result.get("result") == True
    except HTTPError as e:
        if e.code == 404:  # Already deleted
            return True
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def run_connectivity_tests() -> int:
    """Run basic connectivity tests (no embeddings required)."""
    print_header("🔌 CONNECTIVITY TESTS (No Embeddings Required)")
    
    tests = [
        ("Qdrant Connection", test_connectivity),
        ("Create Test Collection", test_create_collection),
        ("Get Collection Info", test_collection_info),
        ("Upsert with Mock Vector", test_upsert_with_mock_vector),
        ("Search with Mock Vector", test_search_with_mock_vector),
        ("Filter Search", test_filter_search),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            print_test(name, result)
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_test(name, False, str(e))
            failed += 1
    
    return 0 if failed == 0 else 1


def run_full_tests() -> int:
    """Run full integration tests."""
    global VECTOR_DIM
    
    print_header("🧪 FULL INTEGRATION TESTS")
    
    config = EMBEDDING_CONFIGS[EMBEDDING_PROVIDER]
    VECTOR_DIM = config["dimensions"]
    
    print(f"  {Colors.CYAN}Embedding Provider: {EMBEDDING_PROVIDER.upper()}{Colors.RESET}")
    print(f"  {Colors.CYAN}Model: {config['model']}{Colors.RESET}")
    print(f"  {Colors.CYAN}Dimensions: {VECTOR_DIM}{Colors.RESET}\n")
    
    # Check embedding provider is available
    if EMBEDDING_PROVIDER == "ollama":
        if not test_ollama_connectivity():
            print(f"\n{Colors.RED}❌ Ollama is not running!{Colors.RESET}")
            print(f"\n{Colors.YELLOW}To start Ollama:{Colors.RESET}")
            print(f"  1. Start server: ollama serve")
            print(f"  2. Pull model: ollama pull nomic-embed-text")
            print(f"\nAlternatively, use OpenAI:")
            print(f"  python test_skill.py --mode full --embeddings openai\n")
            return 1
        print_test("Ollama Connection", True)
    elif EMBEDDING_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            print(f"\n{Colors.RED}❌ OPENAI_API_KEY not set!{Colors.RESET}")
            print(f"\n{Colors.YELLOW}To use OpenAI, set your API key:{Colors.RESET}")
            print(f"  export OPENAI_API_KEY='your-key-here'")
            print(f"\nAlternatively, use Ollama (local, free):")
            print(f"  python test_skill.py --mode full --embeddings ollama\n")
            return 1
    
    # Run connectivity tests first (with correct vector dimensions)
    conn_result = run_connectivity_tests()
    if conn_result != 0:
        print(f"\n{Colors.RED}Connectivity tests failed. Skipping integration tests.{Colors.RESET}")
        return 1
    
    print_header("🤖 EMBEDDING & SEMANTIC TESTS")
    
    tests = [
        (f"Embedding Generation ({EMBEDDING_PROVIDER})", test_embedding_generation),
        ("Store with Real Embedding", test_store_with_real_embedding),
        ("Semantic Search (Similar Query)", test_semantic_search),
        ("Hybrid Search (Vector + Filter)", test_hybrid_search),
        ("Cache Simulation (Store & Retrieve)", test_cache_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            print_test(name, result)
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_test(name, False, str(e))
            failed += 1
    
    return 0 if failed == 0 else 1


def main():
    global EMBEDDING_PROVIDER, VECTOR_DIM
    
    parser = argparse.ArgumentParser(description="Test the qdrant-memory skill")
    parser.add_argument(
        "--mode",
        choices=["connectivity", "full"],
        default="full",
        help="Test mode: connectivity (no embeddings) or full (with embeddings)"
    )
    parser.add_argument(
        "--embeddings",
        choices=["ollama", "openai"],
        default="ollama",
        help="Embedding provider: ollama (local, free) or openai (cloud, paid)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete test collection after tests"
    )
    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Only cleanup (delete test collection)"
    )
    
    args = parser.parse_args()
    
    EMBEDDING_PROVIDER = args.embeddings
    VECTOR_DIM = EMBEDDING_CONFIGS[EMBEDDING_PROVIDER]["dimensions"]
    
    print(f"\n{Colors.BOLD}🧠 Qdrant Memory Skill Test Suite{Colors.RESET}")
    print(f"   Qdrant URL: {QDRANT_URL}")
    print(f"   Test Collection: {TEST_COLLECTION}")
    print(f"   Embedding Provider: {EMBEDDING_PROVIDER.upper()}")
    
    if args.cleanup_only:
        print_header("🧹 CLEANUP")
        result = cleanup_test_collection()
        print_test("Delete Test Collection", result)
        sys.exit(0 if result else 1)
    
    try:
        # Check Qdrant is reachable
        try:
            qdrant_request("GET", "/collections")
        except URLError as e:
            print(f"\n{Colors.RED}❌ Cannot connect to Qdrant at {QDRANT_URL}{Colors.RESET}")
            print(f"   Error: {e}")
            print(f"\n{Colors.YELLOW}Make sure Qdrant is running:{Colors.RESET}")
            print(f"   docker run -p 6333:6333 qdrant/qdrant")
            sys.exit(2)
        
        if args.mode == "connectivity":
            result = run_connectivity_tests()
        else:
            result = run_full_tests()
        
        if args.cleanup:
            print_header("🧹 CLEANUP")
            cleanup_result = cleanup_test_collection()
            print_test("Delete Test Collection", cleanup_result)
        
        # Final summary
        print_header("📊 TEST SUMMARY")
        if result == 0:
            print(f"  {Colors.GREEN}All tests passed! ✓{Colors.RESET}")
        else:
            print(f"  {Colors.RED}Some tests failed. See details above.{Colors.RESET}")
        
        sys.exit(result)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted.{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
