#!/usr/bin/env python3
"""
Shared embedding utilities for the qdrant-memory skill.
Supports Ollama (local), OpenAI (cloud), and Amazon Bedrock (AWS) embeddings.

Usage:
    from embedding_utils import get_embedding, get_embedding_dimension
    
    embedding = get_embedding("Your text here")
    dim = get_embedding_dimension()

Environment Variables:
    EMBEDDING_PROVIDER  - "ollama" (default), "openai", or "bedrock"
    
    # Ollama (local/private)
    OLLAMA_URL          - Ollama server URL (default: http://localhost:11434)
    
    # OpenAI (cloud)
    OPENAI_API_KEY      - Required for OpenAI provider
    
    # Amazon Bedrock (AWS - uses your Kiro subscription)
    AWS_PROFILE         - AWS profile name (default: uses default profile)
    AWS_REGION          - AWS region (default: eu-west-1)
    
    EMBEDDING_MODEL     - Model name (defaults based on provider)

Pricing Comparison:
    - Ollama: FREE (local)
    - Bedrock Titan Embed V2: ~$0.02/1M tokens (cheapest cloud)
    - OpenAI text-embedding-3-small: ~$0.02/1M tokens
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
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

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
    },
    "bedrock": {
        "default_model": "amazon.titan-embed-text-v2:0",
        "dimensions": {
            "amazon.titan-embed-text-v2:0": 1024,
            "amazon.titan-embed-text-v1": 1536,
            "cohere.embed-english-v3": 1024,
            "cohere.embed-multilingual-v3": 1024,
        },
        "default_dim": 1024
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


def get_embedding_bedrock(text: str) -> List[float]:
    """
    Generate embedding using Amazon Bedrock.
    
    Uses boto3 with AWS credentials from:
    - AWS_PROFILE environment variable
    - ~/.aws/credentials (default profile)
    - IAM role (if running on AWS)
    
    No secrets stored in code - uses standard AWS authentication.
    """
    try:
        import boto3
    except ImportError:
        raise ImportError(
            "boto3 is required for Bedrock embeddings. Install with: pip install boto3"
        )
    
    # Create Bedrock client using AWS profile/credentials
    session = boto3.Session(region_name=AWS_REGION)
    bedrock = session.client("bedrock-runtime")
    
    # Prepare request based on model
    if "titan-embed" in EMBEDDING_MODEL:
        # Amazon Titan Embed format
        body = json.dumps({
            "inputText": text
        })
        content_type = "application/json"
        accept = "application/json"
    elif "cohere" in EMBEDDING_MODEL:
        # Cohere Embed format
        body = json.dumps({
            "texts": [text],
            "input_type": "search_document"
        })
        content_type = "application/json"
        accept = "application/json"
    else:
        raise ValueError(f"Unsupported Bedrock model: {EMBEDDING_MODEL}")
    
    # Invoke the model
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        body=body,
        contentType=content_type,
        accept=accept
    )
    
    # Parse response
    result = json.loads(response["body"].read())
    
    if "titan-embed" in EMBEDDING_MODEL:
        return result["embedding"]
    elif "cohere" in EMBEDDING_MODEL:
        return result["embeddings"][0]
    
    return result.get("embedding", result.get("embeddings", [[]])[0])


def get_embedding(text: str) -> List[float]:
    """
    Generate embedding using the configured provider.
    
    Default: Ollama (local/private)
    Override with EMBEDDING_PROVIDER environment variable.
    
    Providers:
        - ollama: Local, free, private (default)
        - bedrock: AWS Titan Embed V2 (~$0.02/1M tokens)
        - openai: OpenAI API (~$0.02/1M tokens)
    
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
    elif EMBEDDING_PROVIDER == "bedrock":
        return get_embedding_bedrock(text)
    else:
        raise ValueError(
            f"Unknown embedding provider: {EMBEDDING_PROVIDER}. "
            f"Use 'ollama', 'openai', or 'bedrock'."
        )


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
        elif EMBEDDING_PROVIDER == "openai":
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
        elif EMBEDDING_PROVIDER == "bedrock":
            try:
                import boto3
                session = boto3.Session(region_name=AWS_REGION)
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                return {
                    "status": "ok",
                    "provider": "bedrock",
                    "model": EMBEDDING_MODEL,
                    "region": AWS_REGION,
                    "account": identity.get("Account", "unknown"),
                    "message": f"AWS authenticated (account: {identity.get('Account', 'unknown')})"
                }
            except ImportError:
                return {
                    "status": "missing_boto3",
                    "provider": "bedrock",
                    "message": "Install boto3: pip install boto3"
                }
            except Exception as e:
                return {
                    "status": "auth_error",
                    "provider": "bedrock",
                    "message": f"AWS auth failed: {e}"
                }
        else:
            return {
                "status": "unknown_provider",
                "provider": EMBEDDING_PROVIDER,
                "message": f"Unknown provider. Use 'ollama', 'openai', or 'bedrock'."
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
