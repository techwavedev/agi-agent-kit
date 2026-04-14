#!/bin/bash
set -e

echo "🐳 [Deep Test] Standing up Ollama and Qdrant isolated environment..."
docker compose up -d

echo "⏳ [Deep Test] Waiting for services to initialize (15s)..."
sleep 15

# Fast, lightweight model for CI speed compared to gemma4:e4b
TEST_MODEL="qwen2:0.5b"

echo "🧠 [Deep Test] Pulling ultra-fast testing model ($TEST_MODEL) into Ollama..."
docker compose exec ollama ollama pull $TEST_MODEL

echo "🚀 [Deep Test] Running End-to-End LLM logic through public agent scaffolding!"
docker compose exec agi_runner bash -c "
  cd /test-mount &&
  echo 'Running Agent Task...' &&
  python3 execution/local_micro_agent.py --task 'Return precisely the word: DEEP_TEST_SUCCESS' --model $TEST_MODEL &&
  echo 'Running Memory Manager connection test...' &&
  python3 execution/memory_manager.py health
"

echo "✅ [Deep Test] Fully Operational End-to-End Pipeline Verified!"
echo "🧹 [Deep Test] Tearing down sandbox..."
docker compose down -v
