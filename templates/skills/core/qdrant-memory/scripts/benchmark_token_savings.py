#!/usr/bin/env python3
"""
Script: benchmark_token_savings.py
Purpose: Demonstrate real-world token savings with qdrant-memory skill.

Compares three scenarios:
1. NO CACHE: Every query goes to LLM with full context
2. WITH SKILL: Using skill knowledge but no caching
3. WITH QDRANT: Semantic cache + targeted context retrieval

Usage:
    # Start services first
    ollama serve &
    docker run -d -p 6333:6333 qdrant/qdrant
    
    # Run benchmark
    python3 benchmark_token_savings.py
    
    # Run with visualization
    python3 benchmark_token_savings.py --visualize

Output:
    Creates benchmark results in .tmp/qdrant_benchmark/
"""

import argparse
import json
import os
import sys
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from embedding_utils import get_embedding, check_embedding_service, EMBEDDING_PROVIDER
except ImportError:
    print("Error: Run from skills/qdrant-memory/scripts/ directory")
    sys.exit(1)

# Configuration
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
BENCHMARK_COLLECTION = "benchmark_cache"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../../.tmp/qdrant_benchmark")

# Simulated skill context (from gitlab skill as example)
SKILL_CONTEXT = """
# GitLab Skill Context

## Agent Installation
To install a GitLab agent on EKS:
1. Register the agent in GitLab UI (Infrastructure > Kubernetes clusters)
2. Create agent token and store as Kubernetes secret
3. Install via Helm: helm upgrade --install gitlab-agent gitlab/gitlab-agent
4. Verify: kubectl get pods -n gitlab-agent

## Common Troubleshooting
- Agent not connecting: Check firewall rules for KAS endpoint
- Certificate errors: Verify TLS configuration
- Token expired: Rotate agent token in GitLab UI

## GitOps Workflow
1. Create .gitlab/agents/<agent-name>/config.yaml
2. Define gitops project paths
3. Push manifests to monitored repository
4. Agent syncs automatically
"""

# Simulated conversation history (20K tokens worth)
CONVERSATION_HISTORY = """
User: How do I set up GitLab CI/CD?
Assistant: To set up GitLab CI/CD, create a .gitlab-ci.yml file in your repository root...

User: What about Docker integration?
Assistant: For Docker integration with GitLab CI/CD, you'll need to configure Docker-in-Docker (dind) or use Kaniko for building images...

User: Can you explain the stages concept?
Assistant: Stages in GitLab CI/CD define the order of job execution. Common stages include build, test, and deploy...

User: How do I cache dependencies?
Assistant: To cache dependencies, use the cache keyword in your .gitlab-ci.yml. For example, cache node_modules for npm projects...

User: What about artifacts?
Assistant: Artifacts are files created by jobs that can be passed to subsequent jobs. Use the artifacts keyword to define paths...

User: How do I set up environments?
Assistant: Environments in GitLab represent deployment targets. Define them using the environment keyword in your job...

User: Can I use variables?
Assistant: Yes, GitLab CI/CD supports various types of variables including predefined, custom, and protected variables...

User: How do I trigger pipelines?
Assistant: Pipelines can be triggered by pushes, merge requests, schedules, API calls, or manually from the UI...

User: What about parallel jobs?
Assistant: Use the parallel keyword to run multiple instances of a job. This is useful for splitting test suites...

User: How do I deploy to Kubernetes?
Assistant: For Kubernetes deployment, you can use kubectl commands directly or integrate with GitLab's Kubernetes agent...
""" * 10  # Repeat to simulate ~20K tokens

# Test queries - includes similar queries to test semantic cache
TEST_QUERIES = [
    # Unique queries
    "How do I install the GitLab agent on EKS?",
    "What are the troubleshooting steps for agent connection issues?",
    "How do I configure GitOps with GitLab?",
    "What is the process to register a new agent?",
    "How do I rotate the agent token?",
    
    # Repeated similar queries (should hit cache)
    "How can I set up a GitLab agent in EKS?",  # Similar to query 1
    "What should I check if my agent won't connect?",  # Similar to query 2
    "How do I use GitOps with GitLab agent?",  # Similar to query 3
    "Steps to install GitLab Kubernetes agent?",  # Similar to query 1
    "Agent not connecting, how to troubleshoot?",  # Similar to query 2
]


def count_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text) // 4


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


def setup_benchmark_collection() -> bool:
    """Create benchmark collection in Qdrant."""
    try:
        # Delete if exists
        try:
            qdrant_request("DELETE", f"/collections/{BENCHMARK_COLLECTION}")
        except:
            pass
        
        # Create new collection
        embedding_dim = len(get_embedding("test"))
        payload = {
            "vectors": {
                "size": embedding_dim,
                "distance": "Cosine"
            }
        }
        qdrant_request("PUT", f"/collections/{BENCHMARK_COLLECTION}", payload)
        return True
    except Exception as e:
        print(f"Error setting up collection: {e}")
        return False


def check_semantic_cache(query: str, threshold: float = 0.88) -> Optional[Dict]:
    """Check if similar query exists in cache."""
    try:
        embedding = get_embedding(query)
        
        search_payload = {
            "vector": embedding,
            "limit": 1,
            "score_threshold": threshold,
            "with_payload": True
        }
        
        result = qdrant_request(
            "POST", 
            f"/collections/{BENCHMARK_COLLECTION}/points/search",
            search_payload
        )
        
        if result.get("result") and len(result["result"]) > 0:
            hit = result["result"][0]
            return {
                "cache_hit": True,
                "score": hit["score"],
                "response": hit["payload"].get("response"),
                "original_query": hit["payload"].get("query")
            }
        return None
    except Exception as e:
        return None


def store_in_cache(query: str, response: str) -> bool:
    """Store query-response pair in semantic cache."""
    try:
        embedding = get_embedding(query)
        point_id = int(hashlib.md5(query.encode()).hexdigest()[:16], 16) % (2**63)
        
        payload = {
            "points": [{
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "query": query,
                    "response": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }]
        }
        
        qdrant_request("PUT", f"/collections/{BENCHMARK_COLLECTION}/points?wait=true", payload)
        return True
    except Exception as e:
        return False


def simulate_llm_response(query: str) -> str:
    """Simulate an LLM response (would be actual LLM call in production)."""
    # In production, this would call the actual LLM
    # For benchmark, we return a simulated response
    return f"[Simulated response for: {query[:50]}...] This would be the LLM's detailed answer about {query.split()[3:6]}..."


def run_benchmark() -> Dict[str, Any]:
    """Run the full benchmark comparing three scenarios."""
    
    print("\n" + "="*60)
    print("🧪 QDRANT MEMORY BENCHMARK")
    print("="*60)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    # Check Qdrant
    try:
        qdrant_request("GET", "/collections")
        print("  ✓ Qdrant is running")
    except:
        print("  ✗ Qdrant not available. Start with: docker run -p 6333:6333 qdrant/qdrant")
        return {}
    
    # Check embeddings
    status = check_embedding_service()
    if status["status"] != "ok":
        print(f"  ✗ Embedding service: {status['message']}")
        return {}
    print(f"  ✓ Embeddings: {EMBEDDING_PROVIDER} ({status.get('model', 'unknown')})")
    
    # Setup collection
    if not setup_benchmark_collection():
        return {}
    print("  ✓ Benchmark collection created")
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "embedding_provider": EMBEDDING_PROVIDER,
        "queries_tested": len(TEST_QUERIES),
        "scenarios": {}
    }
    
    # =========================================================================
    # SCENARIO 1: No Cache (Every query uses full context)
    # =========================================================================
    print("\n" + "-"*60)
    print("📊 SCENARIO 1: NO CACHE (Full context every time)")
    print("-"*60)
    
    scenario1_tokens = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "queries": []
    }
    
    for query in TEST_QUERIES:
        # Full context = conversation history + skill context + query
        full_prompt = f"{CONVERSATION_HISTORY}\n\n{SKILL_CONTEXT}\n\nUser: {query}"
        input_tokens = count_tokens(full_prompt)
        
        response = simulate_llm_response(query)
        output_tokens = count_tokens(response)
        
        scenario1_tokens["input_tokens"] += input_tokens
        scenario1_tokens["output_tokens"] += output_tokens
        scenario1_tokens["queries"].append({
            "query": query,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": False
        })
    
    scenario1_tokens["total_tokens"] = scenario1_tokens["input_tokens"] + scenario1_tokens["output_tokens"]
    results["scenarios"]["no_cache"] = scenario1_tokens
    
    print(f"  Total queries: {len(TEST_QUERIES)}")
    print(f"  Input tokens: {scenario1_tokens['input_tokens']:,}")
    print(f"  Output tokens: {scenario1_tokens['output_tokens']:,}")
    print(f"  TOTAL TOKENS: {scenario1_tokens['total_tokens']:,}")
    
    # =========================================================================
    # SCENARIO 2: With Skill (Targeted context, no cache)
    # =========================================================================
    print("\n" + "-"*60)
    print("📊 SCENARIO 2: WITH SKILL (Targeted context, no cache)")
    print("-"*60)
    
    scenario2_tokens = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "queries": []
    }
    
    for query in TEST_QUERIES:
        # Skill context only (no full history)
        targeted_prompt = f"{SKILL_CONTEXT}\n\nUser: {query}"
        input_tokens = count_tokens(targeted_prompt)
        
        response = simulate_llm_response(query)
        output_tokens = count_tokens(response)
        
        scenario2_tokens["input_tokens"] += input_tokens
        scenario2_tokens["output_tokens"] += output_tokens
        scenario2_tokens["queries"].append({
            "query": query,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": False
        })
    
    scenario2_tokens["total_tokens"] = scenario2_tokens["input_tokens"] + scenario2_tokens["output_tokens"]
    results["scenarios"]["with_skill"] = scenario2_tokens
    
    skill_savings = (1 - scenario2_tokens["total_tokens"] / scenario1_tokens["total_tokens"]) * 100
    print(f"  Total queries: {len(TEST_QUERIES)}")
    print(f"  Input tokens: {scenario2_tokens['input_tokens']:,}")
    print(f"  Output tokens: {scenario2_tokens['output_tokens']:,}")
    print(f"  TOTAL TOKENS: {scenario2_tokens['total_tokens']:,}")
    print(f"  💰 Savings vs No Cache: {skill_savings:.1f}%")
    
    # =========================================================================
    # SCENARIO 3: With Qdrant (Semantic cache + targeted retrieval)
    # =========================================================================
    print("\n" + "-"*60)
    print("📊 SCENARIO 3: WITH QDRANT (Semantic cache + retrieval)")
    print("-"*60)
    
    scenario3_tokens = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "embedding_calls": 0,
        "queries": []
    }
    
    for i, query in enumerate(TEST_QUERIES):
        scenario3_tokens["embedding_calls"] += 1
        
        # Check semantic cache first
        cache_result = check_semantic_cache(query)
        
        if cache_result:
            # CACHE HIT - no LLM call needed!
            scenario3_tokens["cache_hits"] += 1
            input_tokens = 0  # No LLM input
            output_tokens = 0  # No LLM output
            cache_hit = True
            print(f"  ✓ Query {i+1}: CACHE HIT (score: {cache_result['score']:.3f})")
        else:
            # CACHE MISS - call LLM with targeted context
            scenario3_tokens["cache_misses"] += 1
            targeted_prompt = f"{SKILL_CONTEXT}\n\nUser: {query}"
            input_tokens = count_tokens(targeted_prompt)
            
            response = simulate_llm_response(query)
            output_tokens = count_tokens(response)
            cache_hit = False
            
            # Store in cache for future
            store_in_cache(query, response)
            print(f"  ○ Query {i+1}: Cache miss, stored for future")
        
        scenario3_tokens["input_tokens"] += input_tokens
        scenario3_tokens["output_tokens"] += output_tokens
        scenario3_tokens["queries"].append({
            "query": query,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": cache_hit
        })
    
    scenario3_tokens["total_tokens"] = scenario3_tokens["input_tokens"] + scenario3_tokens["output_tokens"]
    results["scenarios"]["with_qdrant"] = scenario3_tokens
    
    qdrant_savings = (1 - scenario3_tokens["total_tokens"] / scenario1_tokens["total_tokens"]) * 100
    print(f"\n  Total queries: {len(TEST_QUERIES)}")
    print(f"  Cache hits: {scenario3_tokens['cache_hits']} ({scenario3_tokens['cache_hits']/len(TEST_QUERIES)*100:.0f}%)")
    print(f"  Cache misses: {scenario3_tokens['cache_misses']}")
    print(f"  Input tokens: {scenario3_tokens['input_tokens']:,}")
    print(f"  Output tokens: {scenario3_tokens['output_tokens']:,}")
    print(f"  TOTAL TOKENS: {scenario3_tokens['total_tokens']:,}")
    print(f"  💰 Savings vs No Cache: {qdrant_savings:.1f}%")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*60)
    print("📈 BENCHMARK SUMMARY")
    print("="*60)
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│ Scenario                  │ Tokens    │ Savings vs Baseline │
├─────────────────────────────────────────────────────────────┤
│ 1. No Cache (baseline)    │ {scenario1_tokens['total_tokens']:>8,} │ -                   │
│ 2. With Skill             │ {scenario2_tokens['total_tokens']:>8,} │ {skill_savings:>6.1f}%             │
│ 3. With Qdrant            │ {scenario3_tokens['total_tokens']:>8,} │ {qdrant_savings:>6.1f}%             │
└─────────────────────────────────────────────────────────────┘
    """)
    
    print(f"🎯 Qdrant Memory saved {qdrant_savings:.0f}% tokens compared to no caching!")
    print(f"   That's {scenario1_tokens['total_tokens'] - scenario3_tokens['total_tokens']:,} tokens saved in just {len(TEST_QUERIES)} queries.\n")
    
    return results


def generate_visualization(results: Dict[str, Any], output_dir: str):
    """Generate HTML visualization of benchmark results."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios = results.get("scenarios", {})
    no_cache = scenarios.get("no_cache", {})
    with_skill = scenarios.get("with_skill", {})
    with_qdrant = scenarios.get("with_qdrant", {})
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qdrant Memory Benchmark Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; 
            margin-bottom: 2rem;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
        }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h3 {{ color: #00d4ff; margin-bottom: 1rem; }}
        .stat {{ font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }}
        .stat.green {{ color: #10b981; }}
        .stat.blue {{ color: #3b82f6; }}
        .stat.purple {{ color: #8b5cf6; }}
        .label {{ color: #888; font-size: 0.9rem; }}
        .savings {{ 
            display: inline-block;
            background: linear-gradient(90deg, #10b981, #059669);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 0.5rem;
        }}
        .chart-container {{ 
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-title {{ color: #00d4ff; margin-bottom: 1rem; font-size: 1.25rem; }}
        .meta {{ text-align: center; color: #666; margin-top: 2rem; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Qdrant Memory Benchmark</h1>
        
        <div class="cards">
            <div class="card">
                <h3>📦 No Cache (Baseline)</h3>
                <div class="stat blue">{no_cache.get('total_tokens', 0):,}</div>
                <div class="label">Total Tokens</div>
                <p style="margin-top: 1rem; color: #888;">Full context sent every query</p>
            </div>
            
            <div class="card">
                <h3>🎯 With Skill</h3>
                <div class="stat purple">{with_skill.get('total_tokens', 0):,}</div>
                <div class="label">Total Tokens</div>
                <div class="savings">{((1 - with_skill.get('total_tokens', 1) / max(no_cache.get('total_tokens', 1), 1)) * 100):.0f}% saved</div>
            </div>
            
            <div class="card">
                <h3>🚀 With Qdrant</h3>
                <div class="stat green">{with_qdrant.get('total_tokens', 0):,}</div>
                <div class="label">Total Tokens</div>
                <div class="savings">{((1 - with_qdrant.get('total_tokens', 1) / max(no_cache.get('total_tokens', 1), 1)) * 100):.0f}% saved</div>
                <p style="margin-top: 0.5rem; color: #10b981;">
                    {with_qdrant.get('cache_hits', 0)} cache hits / {results.get('queries_tested', 0)} queries
                </p>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Token Usage Comparison</div>
            <canvas id="barChart" height="100"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Cache Performance</div>
            <canvas id="pieChart" height="100"></canvas>
        </div>
        
        <div class="meta">
            <p>Benchmark run: {results.get('timestamp', 'N/A')}</p>
            <p>Embedding Provider: {results.get('embedding_provider', 'N/A')}</p>
            <p>Queries Tested: {results.get('queries_tested', 0)}</p>
        </div>
    </div>
    
    <script>
        // Bar Chart - Token Comparison
        new Chart(document.getElementById('barChart'), {{
            type: 'bar',
            data: {{
                labels: ['No Cache', 'With Skill', 'With Qdrant'],
                datasets: [{{
                    label: 'Input Tokens',
                    data: [{no_cache.get('input_tokens', 0)}, {with_skill.get('input_tokens', 0)}, {with_qdrant.get('input_tokens', 0)}],
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderRadius: 8
                }}, {{
                    label: 'Output Tokens',
                    data: [{no_cache.get('output_tokens', 0)}, {with_skill.get('output_tokens', 0)}, {with_qdrant.get('output_tokens', 0)}],
                    backgroundColor: 'rgba(139, 92, 246, 0.8)',
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.1)' }} }}
                }},
                plugins: {{
                    legend: {{ labels: {{ color: '#eee' }} }}
                }}
            }}
        }});
        
        // Pie Chart - Cache Performance
        new Chart(document.getElementById('pieChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Cache Hits', 'Cache Misses'],
                datasets: [{{
                    data: [{with_qdrant.get('cache_hits', 0)}, {with_qdrant.get('cache_misses', 0)}],
                    backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(239, 68, 68, 0.5)'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ labels: {{ color: '#eee' }}, position: 'bottom' }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    # Save HTML
    html_path = os.path.join(output_dir, "benchmark_results.html")
    with open(html_path, "w") as f:
        f.write(html_content)
    
    # Save JSON
    json_path = os.path.join(output_dir, "benchmark_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Visualization saved to:")
    print(f"   HTML: {html_path}")
    print(f"   JSON: {json_path}")
    
    return html_path


def main():
    parser = argparse.ArgumentParser(description="Benchmark qdrant-memory token savings")
    parser.add_argument("--visualize", action="store_true", help="Generate HTML visualization")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory for results")
    args = parser.parse_args()
    
    results = run_benchmark()
    
    if results and args.visualize:
        html_path = generate_visualization(results, args.output)
        
        # Try to open in browser
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
        except:
            pass


if __name__ == "__main__":
    main()
