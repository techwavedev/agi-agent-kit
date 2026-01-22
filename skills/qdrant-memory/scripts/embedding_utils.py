#!/usr/bin/env python3
"""
Shared embedding utilities for the qdrant-memory skill.
Supports both Ollama (local/private) and OpenAI (cloud) embeddings.

Usage:
    from embedding_utils import get_embedding, get_embedding_dimension
    
    embedding = get_embedding("Your text here")
    dim = get_embedding_dimension()

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default) or "openai"
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    OPENAI_API_KEY      - Required for OpenAI provider
    EMBEDDING_MODEL     - Model name (defaults based on provider)
"""

import json
import os
from typing import List
from urllib.request import Request, urlopen
from urllib.error import URLError

# Configuration with Ollama as default (local/private)
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "ollama")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Model configurations
PROVIDER_CONFIGS = {
    "ollama": {
        "default_model": "nomic-embed-text",
        "dimensions": {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
        },
        "default_dim": 768
    },
    "openai": {
        "default_model": "text-embedding-3-small",
        "dimensions": {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        },
        "default_dim": 1536
    }
}

EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", 
    PROVIDER_CONFIGS.get(EMBEDDING_PROVIDER, {}).get("default_model", "nomic-embed-text")
)


def get_embedding_dimension() -> int:
    """Get the dimension for the current embedding configuration."""
    config = PROVIDER_CONFIGS.get(EMBEDDING_PROVIDER, PROVIDER_CONFIGS["ollama"])
    return config["dimensions"].get(EMBEDDING_MODEL, config["default_dim"])


def get_embedding_ollama(text: str) -> List[float]:
    """Generate embedding using Ollama (local)."""
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    
    req = Request(
        f"{OLLAMA_URL}/api/embeddings",
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


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding using the configured provider.
    
    Default: Ollama (local/private)
    Override with EMBEDDING_PROVIDER=openai for cloud.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        ValueError: If provider is not configured correctly
        URLError: If unable to connect to embedding service
    """
    if EMBEDDING_PROVIDER == "ollama":
        return get_embedding_ollama(text)
    elif EMBEDDING_PROVIDER == "openai":
        return get_embedding_openai(text)
    else:
        raise ValueError(f"Unknown embedding provider: {EMBEDDING_PROVIDER}. Use 'ollama' or 'openai'.")


def check_embedding_service() -> dict:
    """
    Check if the embedding service is available.
    
    Returns:
        Dict with status and details
    """
    try:
        if EMBEDDING_PROVIDER == "ollama":
            req = Request(f"{OLLAMA_URL}/api/tags", method="GET")
            with urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode())
                models = [m["name"] for m in result.get("models", [])]
                has_model = any(EMBEDDING_MODEL in m for m in models)
                return {
                    "status": "ok" if has_model else "missing_model",
                    "provider": "ollama",
                    "url": OLLAMA_URL,
                    "model": EMBEDDING_MODEL,
                    "available_models": models,
                    "message": f"Model '{EMBEDDING_MODEL}' ready" if has_model else f"Run: ollama pull {EMBEDDING_MODEL}"
                }
        else:
            # For OpenAI, just check if key is set
            if not OPENAI_API_KEY:
                return {
                    "status": "missing_key",
                    "provider": "openai",
                    "model": EMBEDDING_MODEL,
                    "message": "Set OPENAI_API_KEY environment variable"
                }
            return {
                "status": "ok",
                "provider": "openai",
                "model": EMBEDDING_MODEL,
                "message": "OpenAI API key configured"
            }
    except URLError as e:
        return {
            "status": "connection_error",
            "provider": EMBEDDING_PROVIDER,
            "message": str(e)
        }


if __name__ == "__main__":
    # Quick test
    import sys
    
    print(f"Embedding Provider: {EMBEDDING_PROVIDER}")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dimensions: {get_embedding_dimension()}")
    print()
    
    status = check_embedding_service()
    print(f"Service Status: {status['status']}")
    print(f"Message: {status['message']}")
    
    if status["status"] == "ok":
        try:
            embedding = get_embedding("Test embedding generation")
            print(f"\n✓ Embedding generated: {len(embedding)} dimensions")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            sys.exit(1)
