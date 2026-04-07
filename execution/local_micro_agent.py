#!/usr/bin/env python3
"""
Script: local_micro_agent.py
Purpose: Route small, deterministic tasks to local Ollama models (Gemma 4, GLM, etc.)
         to save cloud API tokens. Supports model registry, automatic fallback,
         structured JSON output, and cost tracking.

Usage:
    # Simple task
    python3 execution/local_micro_agent.py --task "Summarize this error message" --input-text "..."

    # With file input
    python3 execution/local_micro_agent.py --task "Extract function names" --input-file src/app.py

    # Force a specific model
    python3 execution/local_micro_agent.py --task "Classify this text" --model glm-4.7-flash

    # JSON output
    python3 execution/local_micro_agent.py --task "Parse these imports" --input-file x.py --json

    # List available models
    python3 execution/local_micro_agent.py list-models

    # Check health
    python3 execution/local_micro_agent.py health

Exit Codes:
    0 - Success
    1 - Ollama unreachable or model not available
    2 - Input file not found
    3 - Model inference error
    4 - All fallback models exhausted
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

CLOUD_FALLBACK_REGISTRY = [
    {"name": "gemini-1.5-flash", "env": "GEMINI_API_KEY"},
    {"name": "gpt-4o-mini", "env": "OPENAI_API_KEY"},
    {"name": "claude-3-haiku-20240307", "env": "ANTHROPIC_API_KEY"}
]

def load_env_vars() -> dict:
    env_vars = dict(os.environ)
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip("'").strip('"')
        except Exception:
            pass
    return env_vars

# Model registry: ordered by preference for different task types.
# "tier" determines routing: fast (small tasks), medium (reasoning), heavy (complex).
MODEL_REGISTRY = {
    "gemma4:e4b": {
        "tier": "fast",
        "params": "~4B effective",
        "strength": "code understanding, classification, extraction, summarization",
        "max_tokens": 2048,
        "context_window": 32768,
    },
    "glm-4.7-flash:latest": {
        "tier": "medium",
        "params": "~12B",
        "strength": "reasoning, analysis, code generation, multi-step logic",
        "max_tokens": 4096,
        "context_window": 32768,
    },
    "nomic-embed-text:latest": {
        "tier": "embedding",
        "params": "~137M",
        "strength": "embeddings only — not for generation",
        "max_tokens": 0,
        "context_window": 8192,
    },
}

# Fallback chain: if preferred model fails, try next
FALLBACK_CHAIN = ["gemma4:e4b", "glm-4.7-flash:latest"]

# Task patterns that are safe to route locally (used by task_router.py)
LOCAL_TASK_PATTERNS = [
    "summarize", "classify", "extract", "parse", "list", "count",
    "format", "convert", "rename", "sort", "filter", "validate",
    "check syntax", "find errors", "generate filename", "slug",
    "translate variable", "camelcase", "snake_case", "kebab-case",
    "commit message", "changelog entry", "one-liner", "tl;dr",
    "json schema", "regex", "glob pattern",
]


def ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_available_models() -> list:
    """Get list of models currently loaded in Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def select_model(preferred: str | None, task: str) -> str:
    """Select the best available model for a task.

    Priority: explicit --model > task-based heuristic > first available in chain.
    """
    available = get_available_models()
    env_vars = load_env_vars()
    cloud_available = [c["name"] for c in CLOUD_FALLBACK_REGISTRY if env_vars.get(c["env"])]
    
    if not available and not cloud_available:
        print(json.dumps({
            "status": "error",
            "message": "No local Ollama models or Cloud API Keys (.env) available."
        }), file=sys.stderr)
        sys.exit(1)

    # Explicit model requested
    if preferred:
        if preferred in available:
            return preferred
        # Try fuzzy match (e.g. "gemma4" matches "gemma4:e4b")
        for m in available:
            if preferred in m or m.startswith(preferred):
                return m
        # Try cloud models if requested
        if preferred in cloud_available:
            return preferred
            
        print(json.dumps({
            "status": "error",
            "message": f"Model '{preferred}' not found. Available Local: {available}. Available Cloud: {cloud_available}."
        }), file=sys.stderr)
        sys.exit(1)

    # Task-based heuristic: if task looks like it needs reasoning, use medium tier
    task_lower = task.lower()
    needs_reasoning = any(kw in task_lower for kw in [
        "analyze", "explain", "debug", "architect", "design", "compare",
        "review", "refactor", "implement", "write code", "generate code",
        "plan", "reason", "think step"
    ])

    if needs_reasoning:
        # Prefer medium tier
        for model in ["glm-4.7-flash:latest", "gemma4:e4b"]:
            if model in available:
                return model
    else:
        # Prefer fast tier
        for model in FALLBACK_CHAIN:
            if model in available:
                return model

    # Last resort local
    for m in available:
        info = MODEL_REGISTRY.get(m, {})
        if info.get("tier") != "embedding":
            return m

    # Total fallback to cloud if no viable local model
    if cloud_available:
        return cloud_available[0]

    return available[0] if available else None


def run_cloud_inference(model: str, prompt: str, temperature: float = 0.0,
                        max_tokens: int = 1024, json_mode: bool = False,
                        system_prompt: str | None = None) -> dict:
    """Run inference against a cloud provider completely seamlessly via standard libraries."""
    env_vars = load_env_vars()
    start = time.time()
    try:
        if model.startswith("gemini"):
            api_key = env_vars.get("GEMINI_API_KEY")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            sys_text = f"{system_prompt}\n" if system_prompt else ""
            payload = {
                "contents": [{"parts": [{"text": sys_text + prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}
            }
            if json_mode:
                payload["generationConfig"]["responseMimeType"] = "application/json"
                
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                output = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                
        elif model.startswith("gpt"):
            api_key = env_vars.get("OPENAI_API_KEY")
            url = "https://api.openai.com/v1/chat/completions"
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
                
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                output = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
        elif model.startswith("claude"):
            api_key = env_vars.get("ANTHROPIC_API_KEY")
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            if system_prompt:
                payload["system"] = system_prompt
                
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                content_blocks = result.get("content", [])
                output = content_blocks[0].get("text", "").strip() if content_blocks else ""
                
        elapsed = time.time() - start
        return {
            "status": "success",
            "model": model,
            "response": output,
            "metrics": {
                "elapsed_seconds": round(elapsed, 2),
                "is_cloud": True
            },
            "cloud_tokens_saved": 0 # Used cloud provider directly
        }
    except Exception as e:
        return {"status": "error", "model": model, "message": str(e)}

def run_inference(model: str, prompt: str, temperature: float = 0.0,
                  max_tokens: int = 1024, json_mode: bool = False,
                  system_prompt: str | None = None) -> dict:
    """Route inference securely to either local Ollama or Cloud API."""
    env_vars = load_env_vars()
    cloud_available = [c["name"] for c in CLOUD_FALLBACK_REGISTRY if env_vars.get(c["env"])]
    if model in cloud_available:
        return run_cloud_inference(model, prompt, temperature, max_tokens, json_mode, system_prompt)

    # Run inference against Ollama
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    if json_mode:
        payload["format"] = "json"

    json_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json_data,
        headers={"Content-Type": "application/json"},
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - start

            output_text = result.get("response", "").strip()
            eval_count = result.get("eval_count", 0)
            prompt_eval_count = result.get("prompt_eval_count", 0)

            return {
                "status": "success",
                "model": model,
                "response": output_text,
                "metrics": {
                    "elapsed_seconds": round(elapsed, 2),
                    "prompt_tokens": prompt_eval_count,
                    "completion_tokens": eval_count,
                    "total_tokens": prompt_eval_count + eval_count,
                    "tokens_per_second": round(eval_count / elapsed, 1) if elapsed > 0 else 0,
                },
                "cloud_tokens_saved": prompt_eval_count + eval_count,
            }
    except urllib.error.URLError as e:
        return {"status": "error", "model": model, "message": f"Connection failed: {e}"}
    except Exception as e:
        return {"status": "error", "model": model, "message": str(e)}


def run_with_fallback(task: str, context: str, preferred_model: str | None,
                      temperature: float, max_tokens: int, json_mode: bool) -> dict:
    """Run inference with automatic fallback through the model chain."""
    model = select_model(preferred_model, task)

    # Build prompt
    prompt = task
    if context:
        prompt += f"\n\n---\nContent:\n```\n{context}\n```"

    system = (
        "You are a precise, deterministic assistant for small code and text tasks. "
        "Give direct, concise answers. No preamble or explanation unless asked."
    )
    if json_mode:
        system += " Always respond with valid JSON."

    result = run_inference(model, prompt, temperature, max_tokens, json_mode, system)

    if result["status"] == "success":
        return result

    # Fallback: try other models locally first
    tried = {model}
    for fallback in FALLBACK_CHAIN:
        if fallback in tried:
            continue
        available = get_available_models()
        if fallback not in available:
            continue
        tried.add(fallback)
        result = run_inference(fallback, prompt, temperature, max_tokens, json_mode, system)
        if result["status"] == "success":
            result["fallback_from"] = model
            return result

    # Total Fallback: Escalate to cheapest cloud APIs if all local engines exhaust
    env_vars = load_env_vars()
    cloud_available = [c["name"] for c in CLOUD_FALLBACK_REGISTRY if env_vars.get(c["env"])]
    for cloud_model in cloud_available:
        if cloud_model in tried:
            continue
        tried.add(cloud_model)
        result = run_cloud_inference(cloud_model, prompt, temperature, max_tokens, json_mode, system)
        if result["status"] == "success":
            result["fallback_from"] = model
            return result

    return {
        "status": "error",
        "message": f"All models exhausted. Tried: {list(tried)}",
        "models_tried": list(tried),
    }


def cmd_list_models():
    """List available models with their capabilities."""
    available = get_available_models()
    output = {"available_models": [], "ollama_url": OLLAMA_URL}

    for m in available:
        info = MODEL_REGISTRY.get(m, {"tier": "unknown", "strength": "unknown"})
        output["available_models"].append({
            "name": m,
            "tier": info.get("tier", "unknown"),
            "strength": info.get("strength", "unknown"),
            "in_registry": m in MODEL_REGISTRY,
        })

    print(json.dumps(output, indent=2))


def cmd_health():
    """Health check: Ollama connectivity, models, registry."""
    available = get_available_models()
    registered = [m for m in available if m in MODEL_REGISTRY]
    gen_models = [m for m in available
                  if MODEL_REGISTRY.get(m, {}).get("tier") != "embedding"]

    health = {
        "status": "healthy" if len(gen_models) > 0 else "degraded",
        "ollama_reachable": ollama_available(),
        "ollama_url": OLLAMA_URL,
        "models_available": len(available),
        "generation_models": gen_models,
        "registered_models": registered,
        "fallback_chain_coverage": [m for m in FALLBACK_CHAIN if m in available],
    }
    print(json.dumps(health, indent=2))
    sys.exit(0 if health["status"] == "healthy" else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Local Micro-Agent: route small tasks to local Ollama models"
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("list-models", help="List available local models")
    subparsers.add_parser("health", help="Check Ollama and model health")

    parser.add_argument("--model", type=str, default=None,
                        help="Force a specific model (default: auto-select)")
    parser.add_argument("--task", type=str,
                        help="The instruction/task for the local model")
    parser.add_argument("--input-file", type=str,
                        help="Path to a file to include as context")
    parser.add_argument("--input-text", type=str,
                        help="Direct text to include as context")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Temperature (default: 0.0 for deterministic)")
    parser.add_argument("--max-tokens", type=int, default=1024,
                        help="Max tokens to generate (default: 1024)")
    parser.add_argument("--json", action="store_true",
                        help="Force JSON format response")
    parser.add_argument("--raw", action="store_true",
                        help="Output only the model response text (no metadata)")

    args = parser.parse_args()

    # Subcommands
    if args.command == "list-models":
        cmd_list_models()
        sys.exit(0)
    if args.command == "health":
        cmd_health()

    # Main inference path
    if not args.task:
        parser.error("--task is required for inference")

    # Load context
    context = ""
    if args.input_file:
        p = Path(args.input_file)
        if not p.exists():
            print(json.dumps({
                "status": "error",
                "message": f"Input file not found: {args.input_file}"
            }), file=sys.stderr)
            sys.exit(2)
        context = p.read_text(encoding="utf-8", errors="replace")
        # Truncate if too large for local models (keep under 16K chars)
        if len(context) > 16000:
            context = context[:8000] + "\n\n[... truncated ...]\n\n" + context[-4000:]
    elif args.input_text:
        context = args.input_text

    result = run_with_fallback(
        task=args.task,
        context=context,
        preferred_model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        json_mode=args.json,
    )

    if result["status"] != "success":
        print(json.dumps(result), file=sys.stderr)
        sys.exit(3 if "model" in result else 4)

    if args.raw:
        print(result["response"])
    else:
        print(json.dumps(result, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
