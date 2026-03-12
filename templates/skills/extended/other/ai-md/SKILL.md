---
name: ai-md
description: "Convert human-written CLAUDE.md into AI-native structured-label format. Battle-tested across 4 models. Same rules, fewer tokens, higher compliance."
risk: safe
source: community
date_added: "2026-03-11"
---

# AI.MD v4 — The Complete AI-Native Conversion System

## When to Use This Skill

- Use when your CLAUDE.md is long but AI still ignores your rules
- Use when token usage is too high from verbose system instructions
- Use when you want to optimize any LLM system prompt for compliance
- Use when migrating rules between AI tools (Claude, Codex, Gemini, Grok)

## What Is AI.MD?

AI.MD is a methodology for converting human-written `CLAUDE.md` (or any LLM system instructions)
into a structured-label format that AI models follow more reliably, using fewer tokens.

**The paradox we proved:** Adding more rules in natural language DECREASES compliance.
Converting the same rules to structured format RESTORES and EXCEEDS it.

```
Human prose (6 rules, 1 line)  → AI follows 4 of them
Structured labels (6 rules, 6 lines) → AI follows all 6
Same content. Different format. Different results.
```

---

## Why It Works: How LLMs Actually Process Instructions

LLMs don't "read" — they **attend**. Understanding this changes everything.

### Mechanism 1: Attention Splitting

When multiple rules share one line, the model's attention distributes across all tokens equally.
Each rule gets a fraction of the attention weight. Some rules get lost.

When each rule has its own line, the model processes it as a distinct unit.
Full attention weight on each rule.

```
# ONE LINE = attention splits 5 ways (some rules drop to near-zero weight)
EVIDENCE: no-fabricate no-guess | 禁用詞:應該是/可能是 → 先拿數據 | Read/Grep→行號 curl→數據 | "好像"/"覺得"→自己先跑test | guess=shame-wall

# FIVE LINES = each rule gets full attention
EVIDENCE:
  core: no-fabricate | no-guess | unsure=say-so
  banned: 應該是/可能是/感覺是/推測 → 先拿數據
  proof: all-claims-need(data/line#/source) | Read/Grep→行號 | curl→數據
  hear-doubt: "好像"/"覺得" → self-test(curl/benchmark) → 禁反問user
  violation: guess → shame-wall
```

### Mechanism 2: Zero-Inference Labels

Natural language forces the model to INFER meaning from context.
Labels DECLARE meaning explicitly. No inference needed = no misinterpretation.

```
# AI must infer: what does (防搞混) modify? what does 例外 apply to?
GATE-1: 收到任務→先用一句話複述(防搞混)(長對話中每個新任務都重新觸發) | 例外: signals命中「處理一下」=直接執行

# AI reads labels directly: trigger→action→exception. Zero ambiguity.
GATE-1 複述:
  trigger: new-task
  action: first-sentence="你要我做的是___"
  persist: 長對話中每個新任務都重新觸發
  exception: signal=處理一下 → skip
  yields-to: GATE-3
```

Key insight: Labels like `trigger:` `action:` `exception:` work across ALL languages.
The model doesn't need to parse Chinese/Japanese/English grammar to understand structure.
**Labels are the universal language between humans and AI.**

### Mechanism 3: Semantic Anchoring

Labeled sub-items create **matchable tags**. When a user's input contains a keyword,
the model matches it directly to the corresponding label — like a hash table lookup
instead of a full-text search.

```
# BURIED: AI scans the whole sentence, might miss the connection
加新功能→第一句問schema | 新增API/endpoint=必確認health-check.py覆蓋

# ANCHORED: label "new-api:" directly matches user saying "加個 API"
MOAT:
  new-feature: 第一句問schema/契約/關聯
  new-api: 必確認health-check.py覆蓋(GATE-5)
```

**Real proof:** This specific technique fixed a test case that failed 5 consecutive times
across all models. The label `new-api:` raised Codex T5 from ❌→✅ on first try.

---

## The Conversion Process: What Happens When You Give Me a CLAUDE.md

Here's the exact mental model I use when converting natural language instructions to AI.MD format.

### Phase 1: UNDERSTAND — Read Like a Compiler, Not a Human

I read the CLAUDE.md **as if I'm building a state machine**, not reading a document.

For each sentence, I ask:
1. **Is this a TRIGGER?** (What input activates this behavior?)
2. **Is this an ACTION?** (What should the AI do?)
3. **Is this a CONSTRAINT?** (What should the AI NOT do?)
4. **Is this METADATA?** (Priority, timing, persistence, exceptions?)
5. **Is this a HUMAN EXPLANATION?** (Why the rule exists — delete this)

Example analysis:

```
Input: "收到任務→先用一句話複述(防搞混)(長對話中每個新任務都重新觸發) | 例外: signals命中「處理一下」=直接執行"

Decomposition:
  ├─ TRIGGER:    "收到任務" → new-task
  ├─ ACTION:     "先用一句話複述" → first-sentence="你要我做的是___"
  ├─ DELETE:     "(防搞混)" → human motivation, AI doesn't need this
  ├─ METADATA:   "(長對話中每個新任務都重新觸發)" → persist: every-new-task
  └─ EXCEPTION:  "例外: signals命中「處理一下」=直接執行" → exception: signal=處理一下 → skip
```

### Phase 2: DECOMPOSE — Break Every `|` and `()` Into Atomic Rules

The #1 source of compliance failure is **compound rules**.
A single line with 3 rules separated by `|` looks like 1 instruction to AI.
It needs to be 3 separate instructions.

**The splitter test:** If you can put "AND" between two parts of a sentence,
they are separate rules and MUST be on separate lines.

```
# Input: one sentence hiding 4 rules
禁用詞:應該是/可能是→先拿數據 | "好像"/"覺得"→自己先跑test(不是問user)→有數據才能決定

# Analysis: I find 4 hidden rules
Rule 1: certain words are banned → use data instead
Rule 2: hearing doubt words → run self-test
Rule 3: don't ask the user for data → look it up yourself
Rule 4: preference claims → require A/B comparison before accepting

# Output: 4 atomic rules
banned: 應該是/可能是/感覺是/推測 → 先拿數據
hear-doubt: "好像"/"覺得" → self-test(curl/benchmark)
self-serve: 禁反問user(自己查)
compare: "覺得A比B好" → A/B實測先行
```

### Phase 3: LABEL — Assign Function Labels

Every atomic rule gets a label that declares its function.
I use a standard vocabulary of ~12 label types:

| Label | What It Declares | When to Use |
|-------|-----------------|-------------|
| `trigger:` | What input activates this | Every gate/rule needs one |
| `action:` | What the AI must do | The core behavior |
| `exception:` | When NOT to do it | Override cases |
| `not-triggered:` | Explicit negative examples | Prevent over-triggering |
| `format:` | Output format constraint | Position, structure requirements |
| `priority:` | Override relationship | When rules conflict |
| `yields-to:` | Which gate takes precedence | Inter-gate priority |
| `persist:` | Durability across turns | Rules that survive conversation flow |
| `timing:` | When in the workflow | Before/after/during constraints |
| `violation:` | Consequence of breaking | Accountability mechanism |
| `banned:` | Forbidden words/actions | Hard no-go list |
| `policy:` | Decision heuristic | When judgment is needed |

**The label selection technique:** I pick the label that would help a DIFFERENT AI model
(not the one being instructed) understand this rule's function if it saw ONLY the label.
If `trigger:` clearly tells you "this is what activates the rule" without reading anything else,
it's the right label.

### Phase 4: STRUCTURE — Build the Architecture

I organize rules into a hierarchy:

```
<gates>    = Hard stops (MUST check before any action)
<rules>    = Behavioral guidelines (HOW to act)
<rhythm>   = Workflow patterns (WHEN to do what)
<conn>     = Connection strings (FACTS — never compress)
<ref>      = On-demand references (don't load until needed)
<learn>    = Evolution rules (how the system improves)
```

**Why this order matters:**
Gates come first because they MUST be checked before anything else.
The model processes instructions top-to-bottom. Priority = position.

**Grouping technique:** Rules that share a DOMAIN become sub-items under one heading.

```
# FLAT (bad): 7 unrelated rules, model treats equally
1. no guessing
2. backup before editing
3. use tables for output
4. check health after deploy
5. don't say "應該是"
6. test before reporting
7. all claims need proof

# GROUPED (good): 3 domains, model understands hierarchy
EVIDENCE:               ← domain: truthfulness
  core: no-guess
  banned: 應該是
  proof: all-claims-need-data

SCOPE:                  ← domain: safety
  pre-change: backup
  pre-run: check-health

OUTPUT:                 ← domain: format
  format: tables+numbers
```

### Phase 5: RESOLVE — Handle Conflicts and Edge Cases

This is the most critical and least obvious phase. Natural language instructions
often contain **hidden conflicts** that humans resolve with intuition but AI cannot.

**Technique: Conflict Detection Matrix**

I check every pair of gates/rules for conflicts:

```
GATE-1 (複述: repeat task) vs GATE-3 (保護檔: backup first)
→ CONFLICT: If user says "edit .env", should AI repeat the task first, or backup first?
→ RESOLUTION: priority: GATE-3 > GATE-1 (safety before courtesy)
             yields-to: GATE-3 (explicit in GATE-1)

GATE-4 (報結論: cite evidence) vs bug-close (記錄根因: write root cause)
→ CONFLICT: bug-close requires stating root cause, but GATE-4 bans definitive claims
→ RESOLUTION: timing: GATE-4 is pre-conclusion brake; bug-close is post-verification record
             GATE-4 not-triggered when bug already verified

EVIDENCE (no-guess) vs user says "處理一下" (just do it)
→ CONFLICT: should AI verify assumptions or execute immediately?
→ RESOLUTION: signal "處理一下" = user has decided, skip confirmation
```

**Technique: Not-Triggered Lists**

For any rule that could over-trigger, I add explicit negative examples:

```
GATE-4 報結論:
  trigger: 最終歸因/根因判定/不可逆建議
  not-triggered: 中間進度數字 | 純指標查詢 | 工具原始輸出 | 已知事實 | 轉述文件
```

This was discovered because Gemini 2.5 Pro kept triggering GATE-4 on simple number queries
like "成功率怎麼樣?". Adding `not-triggered: 純指標查詢` fixed it immediately.

### Phase 6: TEST — Multi-Model Validation (Non-Negotiable)

**This is not optional.** Every conversion MUST be validated by 2+ different LLM models.

Why? Because a format that works perfectly for Claude might confuse GPT, and vice versa.
The whole point of AI.MD is that it works ACROSS models.

**The exam protocol we developed:**

1. Write 8 test inputs that simulate REAL user behavior (not textbook examples)
2. Include "trap" questions where two rules conflict
3. Include "negative" tests where a rule should NOT trigger
4. DO NOT hint which rules are being tested (the AI shouldn't know)
5. Run each model independently
6. Score each answer: ✅ full compliance, ⚠️ partial, ❌ miss
7. If ANY model's score drops after conversion → revert that specific change

**The 8-question template we used:**

```
T1: Simple task (does GATE-1 trigger?)
T2: Database write attempt (does GATE-2 catch it?)
T3: Protected file edit (does GATE-3 fire FIRST, before GATE-1?)
T4: Root cause analysis (does GATE-4 require all 4 questions?)
T5: Business API addition (does AI mention health-check.py?)
T6: User says "好像X比Y好" (does AI run comparison or just accept it?)
T7: User says "處理一下" (does AI skip GATE-1 confirmation?)
T8: Simple metric query (does GATE-4 NOT trigger?)
```

---

## Special Techniques Discovered During Battle-Testing

### Technique 1: Bilingual Label Strategy

Labels in English, output strings in the user's language.
English labels are shorter AND more universally understood by all models.
But the actual text the AI produces must stay in the user's language.

```
action: first-sentence="你要我做的是___"    ← AI outputs Chinese
format: must-be-line-1                      ← structural constraint in English
banned: 應該是/可能是                        ← forbidden words stay in original language
```

**Why this works:** English label vocabulary (`trigger`, `action`, `exception`) maps directly
to concepts in every model's training data. Chinese grammar labels (觸發條件, 執行動作, 例外情況)
are less standardized across models.

### Technique 2: State Machine Gates

Instead of treating rules as a flat list, model them as a **state machine**:
- Each gate has a `trigger` (input state)
- Each gate has an `action` (transition)
- Gates have `priority` (which fires first when multiple match)
- Gates have `yields-to` (explicit conflict resolution)

This gives AI a clear execution model:
```
Input arrives → Check GATE-3 first (highest priority) → Check GATE-1 → Check GATE-2 → ...
```

Instead of:
```
Input arrives → Read all rules → Try to figure out which one applies → Maybe miss one
```

### Technique 3: XML Section Tags for Semantic Boundaries

Using `<gates>`, `<rules>`, `<rhythm>`, `<conn>` as section delimiters
creates hard boundaries that prevent rule-bleed (where the model confuses
which section a rule belongs to).

```xml
<gates label="硬性閘門 | 優先序: gates>rules>rhythm | 缺一項=STOP">
...gates here...
</gates>

<rules>
...rules here...
</rules>
```

The `label` attribute on the opening tag serves as a section-level instruction:
"these are hard gates, this is their priority, missing = stop"

### Technique 4: Cross-Reference Instead of Duplicate

When the same concept appears in multiple rules, DON'T repeat it.
Use a cross-reference label.

```
# BAD: health-check mentioned in 3 places
GATE-5: ...check health-check.py...
MOAT: ...must check health-check.py...
SCOPE: ...verify health-check.py exists...

# GOOD: single source of truth + cross-reference
GATE-5 驗收:
  checks:
    新增API → 確認health-check.py覆蓋

MOAT:
  new-api: 必確認health-check.py覆蓋(GATE-5)    ← cross-ref, not duplicate
```

### Technique 5: The "What Not Why" Principle

Delete ALL text that exists to explain WHY a rule exists.
AI needs WHAT to do, not WHY.

```
# DELETE these human explanations:
(防搞混)                     → motivation
(不是大爆破,是每次順手一點)    → metaphor
(想清楚100倍後才做現在的)     → backstory
(因為用戶是非工程師)          → justification

# KEEP only the actionable instruction:
action: first-sentence="你要我做的是___"
refactor: 同區塊連續第3次修改 → extract
```

Every deleted explanation saves tokens AND removes noise that could confuse the model
about what it should actually DO.

---

## Two-Stage Workflow

### Stage 1: PREVIEW — Measure, Don't Touch

```bash
echo "=== Current Token Burn ==="
claude_md=$(wc -c < ~/.claude/CLAUDE.md 2>/dev/null || echo 0)
rules=$(cat ~/.claude/rules/*.md 2>/dev/null | wc -c || echo 0)
total=$((claude_md + rules))
tokens=$((total / 4))
echo "CLAUDE.md:     $claude_md bytes"
echo "rules/*.md:    $rules bytes"
echo "Total:         $total bytes ≈ $tokens tokens/turn"
echo "50-turn session: ≈ $((tokens * 50)) tokens on instructions alone"
```

Then: Read all auto-loaded files. Identify redundancy, prose overhead, and duplicate rules.

**Ask user before proceeding: "Want to distill?"**

### Stage 2: DISTILL — Convert with Safety Net

1. **Backup**: `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak-pre-distill`
2. **Phase 1-5**: Run the full conversion process above
3. **Phase 6**: Run multi-model test (minimum 2 models, 8 questions)
4. **Report**: Show before/after scores

```
=== AI.MD Conversion Complete ===

Before: {old} bytes ({old_score} compliance)
After:  {new} bytes ({new_score} compliance)
Saved:  {percent}% bytes, +{delta} compliance points

Backup: ~/.claude/CLAUDE.md.bak-pre-distill
Restore: cp ~/.claude/CLAUDE.md.bak-pre-distill ~/.claude/CLAUDE.md
```

---

## AI-Native Template

```xml
# PROJECT-NAME | lang:xx | for-AI-parsing | optimize=results-over-format

<user>
identity, tone, signals, decision-style (key: value pairs)
</user>

<gates label="硬性閘門 | 優先序: gates>rules>rhythm | 缺一項=STOP">

GATE-1 name:
  trigger: ...
  action: ...
  exception: ...
  yields-to: ...

GATE-2 name:
  trigger: ...
  action: ...
  policy: ...

</gates>

<rules>

RULE-NAME:
  core: ...
  banned: ...
  hear-X: ... → action
  violation: ...

</rules>

<rhythm>
workflow patterns as key: value pairs
</rhythm>

<conn>
connection strings (keep exact — NEVER compress facts/credentials/URLs)
</conn>

<ref label="on-demand Read only">
file-path → purpose
</ref>

<learn>
how system evolves over time
</learn>
```

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|------------|-----|
| Human prose in CLAUDE.md | Structured labels | Prose requires inference; labels are direct |
| Multiple rules on one line | One concept per line | Attention splits across dense lines |
| Parenthetical explanations | Remove them | AI needs "what" not "why" |
| Same rule in 3 places | Single source + cross-ref | Duplicates can diverge and confuse |
| 20+ flat rules | 5-7 domains with sub-items | Hierarchy helps model organize behavior |
| Compress without testing | Validate with 2+ models | What works for Claude might fail for GPT |
| Assume format doesn't matter | Test it — it does | Same content, different format = different compliance |
| Chinese-only labels | English labels + native output | English labels are more universal across models |
| Flat rule list | State machine with priorities | Clear execution order prevents missed rules |

---

## Real-World Results

Tested 2026-03, washinmura.jp CLAUDE.md, 5 rounds, 4 models:

| Round | Change | Codex (GPT-5.3) | Gemini 2.5 Pro | Claude Opus 4.6 |
|-------|--------|-----------------|----------------|-----------------|
| R1 (baseline prose) | — | 8/8 | 7/8 | 8/8 |
| R2 (added rules) | +gates +examples | 7/8 | 6/8 | — |
| R3 (refined prose) | +exceptions +non-triggers | 6/8 | 6.5/8 | — |
| R4 (AI-native convert) | structured labels | **8/8** | **7/8** | **8/8** |

Key findings:
1. **More prose rules = worse compliance** (R1→R3: scores dropped as rules grew)
2. **Structured format = restored + exceeded** (R4: back to max despite more rules)
3. **Cross-model consistency**: Format that works for one model works for all (except Grok)
4. **Semantic anchoring**: The `new-api:` label fix was the single most impactful change

**The uncomfortable truth: Your beautiful, carefully-written CLAUDE.md
might be HURTING your AI's performance. Structure > Prose. Always.**

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache compliance check results to avoid re-running expensive AWS API calls. Retrieve prior audit findings to track remediation progress across sessions.

```bash
# Check for prior security context before starting
python3 execution/memory_manager.py auto --query "prior security audit results for Ai Md"
```

### Storing Results

After completing work, store security decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Audit findings: 3 critical IAM misconfigurations found and remediated" \
  --type technical --project <project> \
  --tags ai-md security
```

### Multi-Agent Collaboration

Share security findings with other agents so they avoid introducing vulnerabilities in their code changes.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Completed security audit — 3 critical findings fixed, compliance score 94%" \
  --project <project>
```

### Signed Audit Trail

All security findings are cryptographically signed with the agent's Ed25519 identity, providing tamper-proof audit logs for compliance reporting.

### Semantic Cache for Compliance

Cache compliance check results (`semantic_cache.py`) to avoid redundant AWS API calls. Cache hit at similarity >0.92 returns prior results instantly.

<!-- AGI-INTEGRATION-END -->
