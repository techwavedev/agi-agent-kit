---
name: game-design
description: Game design principles. GDD structure, balancing, player psychology, progression.
allowed-tools: Read, Glob, Grep
---

# Game Design Principles

> Design thinking for engaging games.

---

## 1. Core Loop Design

### The 30-Second Test

```
Every game needs a fun 30-second loop:
1. ACTION → Player does something
2. FEEDBACK → Game responds
3. REWARD → Player feels good
4. REPEAT
```

### Loop Examples

| Genre | Core Loop |
|-------|-----------|
| Platformer | Run → Jump → Land → Collect |
| Shooter | Aim → Shoot → Kill → Loot |
| Puzzle | Observe → Think → Solve → Advance |
| RPG | Explore → Fight → Level → Gear |

---

## 2. Game Design Document (GDD)

### Essential Sections

| Section | Content |
|---------|---------|
| **Pitch** | One-sentence description |
| **Core Loop** | 30-second gameplay |
| **Mechanics** | How systems work |
| **Progression** | How player advances |
| **Art Style** | Visual direction |
| **Audio** | Sound direction |

### Principles

- Keep it living (update regularly)
- Visuals help communicate
- Less is more (start small)

---

## 3. Player Psychology

### Motivation Types

| Type | Driven By |
|------|-----------|
| **Achiever** | Goals, completion |
| **Explorer** | Discovery, secrets |
| **Socializer** | Interaction, community |
| **Killer** | Competition, dominance |

### Reward Schedules

| Schedule | Effect | Use |
|----------|--------|-----|
| **Fixed** | Predictable | Milestone rewards |
| **Variable** | Addictive | Loot drops |
| **Ratio** | Effort-based | Grind games |

---

## 4. Difficulty Balancing

### Flow State

```
Too Hard → Frustration → Quit
Too Easy → Boredom → Quit
Just Right → Flow → Engagement
```

### Balancing Strategies

| Strategy | How |
|----------|-----|
| **Dynamic** | Adjust to player skill |
| **Selection** | Let player choose |
| **Accessibility** | Options for all |

---

## 5. Progression Design

### Progression Types

| Type | Example |
|------|---------|
| **Skill** | Player gets better |
| **Power** | Character gets stronger |
| **Content** | New areas unlock |
| **Story** | Narrative advances |

### Pacing Principles

- Early wins (hook quickly)
- Gradually increase challenge
- Rest beats between intensity
- Meaningful choices

---

## 6. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Design in isolation | Playtest constantly |
| Polish before fun | Prototype first |
| Force one way to play | Allow player expression |
| Punish excessively | Reward progress |

---

> **Remember:** Fun is discovered through iteration, not designed on paper.

## AGI Framework Integration

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags game-design <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
