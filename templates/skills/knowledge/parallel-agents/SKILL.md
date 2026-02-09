---
name: parallel-agents
description: Platform-adaptive multi-agent orchestration. Uses Claude Code Agent Teams when available, subagents as fallback, and sequential persona switching on other platforms. Use when multiple independent tasks can run with different domain expertise or when comprehensive analysis requires multiple perspectives.
version: 2.0.0
---

# Multi-Agent Orchestration

> Platform-adaptive parallel agent coordination

## Overview

This skill enables coordinating multiple specialized agents across different AI platforms. It automatically detects the runtime environment and selects the best orchestration strategy:

| Platform                              | Strategy            | Parallelism         | Mechanism                      |
| ------------------------------------- | ------------------- | ------------------- | ------------------------------ |
| **Claude Code** (with Agent Teams)    | Native Agent Teams  | ✅ True parallel    | tmux/in-process sessions       |
| **Claude Code** (without Agent Teams) | Subagents           | ✅ Background tasks | `Task()` tool, `context: fork` |
| **Kiro IDE**                          | Autonomous Agent    | ✅ Async parallel   | Sandbox environments, PRs      |
| **Gemini / Antigravity**              | Sequential Personas | ❌ Sequential       | Persona switching via `@agent` |
| **Opencode / Other**                  | Sequential Personas | ❌ Sequential       | Persona switching via `@agent` |

---

## Platform Detection

Before orchestrating, detect the current platform:

```
IF environment has CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
  → Use Agent Teams (Strategy A)
ELSE IF environment is Claude Code (has Task tool, /agents command)
  → Use Subagents (Strategy B)
ELSE IF environment is Kiro IDE (.kiro/, POWER.md, autonomous agent available)
  → Use Autonomous Agent (Strategy D)
ELSE
  → Use Sequential Personas (Strategy C)
```

> **Important**: Always announce which strategy is being used so the user knows what to expect.

---

## Strategy A: Claude Code Agent Teams (Preferred)

> **Requires**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings or environment.

Agent Teams spawn **true parallel Claude Code sessions** as teammates. Each teammate runs in its own context with full tool access.

### Enabling Agent Teams

Users must enable via `settings.json` or environment:

```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

### How to Orchestrate with Agent Teams

**The lead agent (you) acts as Team Leader.** When a complex multi-domain task is detected:

1. **Analyze** the task and identify independent work streams
2. **Spawn teammates** with clear, self-contained prompts
3. **Assign tasks** to each teammate
4. **Monitor** progress and steer if needed
5. **Synthesize** results when teammates complete

#### Spawn a Team

```
Create an agent team with 3 teammates:
- "security-reviewer": Review the auth module at src/auth/ for security vulnerabilities. Focus on token handling and session management.
- "api-specialist": Analyze the API layer at src/api/ for best practices, error handling, and performance.
- "test-engineer": Identify test gaps across the project, focus on untested edge cases.

Use Sonnet for each teammate.
```

#### Team Display Modes

| Mode            | How                                            | Best For          |
| --------------- | ---------------------------------------------- | ----------------- |
| **In-process**  | All in one terminal. `Shift+Up/Down` to switch | Simple setups     |
| **Split panes** | Each gets own tmux/iTerm2 pane                 | Visual monitoring |

```json
{ "teammateMode": "in-process" }
```

#### Team Communication

- **Message teammate**: Tell the lead to message a specific teammate
- **Broadcast**: Send to all teammates (use sparingly — costs scale)
- **Task list**: Shared task board visible to all agents (`Ctrl+T`)
- **Idle notifications**: Teammates auto-notify lead when done

#### Quality Gates via Hooks

```json
{
  "hooks": {
    "TeammateIdle": [
      { "command": "npm test", "description": "Run tests before idle" }
    ],
    "TaskCompleted": [
      { "command": "./scripts/lint.sh", "description": "Lint on completion" }
    ]
  }
}
```

#### Cleanup

```
Clean up the team
```

### Agent Teams Best Practices

1. **Give enough context** — teammates don't share the lead's full conversation
2. **Size tasks well** — not too small (overhead), not too large (risk)
3. **Avoid file conflicts** — assign non-overlapping file sets to each teammate
4. **Wait before synthesizing** — let all teammates finish before combining results
5. **Start with research** — use research/review tasks before implementation tasks

---

## Strategy B: Claude Code Subagents (Fallback on Claude Code)

> When Agent Teams aren't enabled on Claude Code, use **subagents** for parallel work.

Subagents are isolated Claude Code sessions spawned via the `Task` tool. They can run in **foreground** (blocking) or **background** (concurrent).

### Built-in Subagents

| Agent               | Model    | Purpose                        |
| ------------------- | -------- | ------------------------------ |
| **Explore**         | Haiku    | Fast read-only codebase search |
| **Plan**            | Inherits | Research during plan mode      |
| **General-purpose** | Inherits | Complex multi-step operations  |

### Custom Subagents

Define in `.claude/agents/` or `~/.claude/agents/`:

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: acceptEdits
skills:
  - vulnerability-scanner
memory: project
---

You are a security reviewer. Analyze code for vulnerabilities, focusing on:

- Authentication and authorization flaws
- Input validation issues
- Secret exposure risks
- Dependency vulnerabilities

Report with severity ratings. Check your memory for patterns seen before.
```

### Subagent Frontmatter Reference

| Field             | Purpose             | Values                                                                       |
| ----------------- | ------------------- | ---------------------------------------------------------------------------- |
| `name`            | Identifier          | Any string                                                                   |
| `description`     | When to invoke      | Auto-delegation hint                                                         |
| `tools`           | Allowed tools       | `Read`, `Grep`, `Glob`, `Bash`, `Write`, `Edit`, `Task(agent)`               |
| `disallowedTools` | Blocked tools       | Same as above                                                                |
| `model`           | AI model            | `sonnet`, `opus`, `haiku`, `inherit`                                         |
| `permissionMode`  | Permission handling | `default`, `acceptEdits`, `dontAsk`, `delegate`, `bypassPermissions`, `plan` |
| `skills`          | Preloaded skills    | List of skill names                                                          |
| `mcpServers`      | MCP servers         | Server names from config                                                     |
| `hooks`           | Lifecycle hooks     | Hook definitions                                                             |
| `memory`          | Persistent memory   | `user`, `project`, `local`                                                   |
| `maxTurns`        | Turn limit          | Number                                                                       |

### Invoking Subagents

**Foreground** (blocking):

```
Use the security-reviewer subagent to audit the authentication module
```

**Background** (concurrent):

```
Run the security-reviewer subagent in the background to audit auth while I continue working
```

**Parallel research**:

```
Research the authentication, database, and API modules in parallel using separate subagents
```

**Chaining**:

```
Use the code-reviewer subagent to find issues, then use the optimizer subagent to fix them
```

### Restricting Subagent Spawning

A coordinator can restrict which subagents it spawns:

```markdown
---
name: coordinator
description: Coordinates work across specialized agents
tools: Task(worker, researcher), Read, Bash
---
```

This coordinator can only spawn `worker` and `researcher` subagents.

---

## Strategy C: Sequential Personas (Universal Fallback)

> For Gemini, Opencode, and other platforms without native agent parallelism.

### How It Works

The AI adopts different specialist personas sequentially, passing context between phases:

```
🤖 Applying knowledge of @security-auditor...
[Security analysis]

🤖 Applying knowledge of @backend-specialist...
[API analysis, informed by security findings]

🤖 Applying knowledge of @test-engineer...
[Test gap analysis, informed by both previous analyses]
```

### Native Agent Invocation

**Single Agent:**

```
Use the security-auditor agent to review authentication
```

**Sequential Chain:**

```
First, use the explorer-agent to discover project structure.
Then, use the backend-specialist to review API endpoints.
Finally, use the test-engineer to identify test gaps.
```

**With Context Passing:**

```
Use the frontend-specialist to analyze React components.
Based on those findings, have the test-engineer generate component tests.
```

---

## Strategy D: Kiro Autonomous Agent (On Kiro IDE)

> Kiro's Autonomous Agent provides async parallel task execution in sandboxed environments — the team-level equivalent of Claude Code's Agent Teams, but asynchronous and PR-based.

### How It Works

Unlike Claude Code Agent Teams (which are real-time interactive sessions), Kiro's Autonomous Agent:

- **Runs tasks in isolated sandbox environments** — full dev setup, no local impact
- **Opens pull requests** for each completed task — you review asynchronously
- **Maintains context** across tasks, repos, and PRs
- **Learns from your code reviews** — adapts to team patterns over time
- **Works across multiple repos** — coordinates related changes into linked PRs

### When to Use

✅ **Best for:**

- Async workflows where multiple tasks can run overnight or during focus time
- Cross-repo changes (e.g., update API contract + client SDK + documentation)
- Routine fixes, follow-ups, and status updates
- Tasks that benefit from sandboxed execution (no risk to local environment)

❌ **Not ideal for:**

- Real-time interactive collaboration (use Agent Teams on Claude Code instead)
- Quick single-file fixes (use direct agent invocation)

### Example: Multi-Task Delegation

```
Create a Kiro task:
  - "Refactor authentication module to use JWT refresh tokens"
  - Repository: backend-api
  - Let Kiro plan the implementation, execute in sandbox, and open a PR

Create another Kiro task:
  - "Update the React login flow to handle JWT refresh"
  - Repository: frontend-app
  - Reference the backend PR for API contract changes
```

Both tasks run in parallel in isolated environments. When complete, you get two linked PRs to review.

### Integration with Kiro Powers

The Autonomous Agent automatically uses installed Powers for expertise. If the Supabase Power is installed and the task involves database changes, the agent activates the Supabase Power for best-practice guidance.

---

## Orchestration Patterns (Platform-Independent)

These patterns work across all strategies. The platform dictates whether they run in parallel or sequentially.

### Pattern 1: Comprehensive Analysis

```
Agents: explorer → [domain-agents] → synthesis

1. explorer-agent: Map codebase structure
2. security-auditor: Security posture
3. backend-specialist: API quality
4. frontend-specialist: UI/UX patterns
5. test-engineer: Test coverage
6. Synthesize all findings
```

**On Claude Code Agent Teams**: Steps 2-5 run as parallel teammates
**On Claude Code Subagents**: Steps 2-5 run as background subagents
**On Kiro IDE**: Steps 2-5 dispatched as autonomous agent tasks (async, PR-based)
**On Other Platforms**: Steps 1-5 run sequentially with context passing

### Pattern 2: Feature Review

```
Agents: affected-domain-agents → test-engineer

1. Identify affected domains (backend? frontend? both?)
2. Invoke relevant domain agents
3. test-engineer verifies changes
4. Synthesize recommendations
```

### Pattern 3: Security Audit

```
Agents: security-auditor → penetration-tester → synthesis

1. security-auditor: Configuration and code review
2. penetration-tester: Active vulnerability testing
3. Synthesize with prioritized remediation
```

### Pattern 4: Cross-Layer Feature Implementation

```
Agents: database-architect → backend-specialist → frontend-specialist → test-engineer

1. database-architect: Schema changes
2. backend-specialist: API endpoints
3. frontend-specialist: UI components
4. test-engineer: Full-stack tests
```

**On Agent Teams**: Split into backend teammate + frontend teammate + test teammate

---

## Available Agents

| Agent                   | Expertise        | Trigger Phrases                        |
| ----------------------- | ---------------- | -------------------------------------- |
| `orchestrator`          | Coordination     | "comprehensive", "multi-perspective"   |
| `security-auditor`      | Security         | "security", "auth", "vulnerabilities"  |
| `penetration-tester`    | Security Testing | "pentest", "red team", "exploit"       |
| `backend-specialist`    | Backend          | "API", "server", "Node.js", "Express"  |
| `frontend-specialist`   | Frontend         | "React", "UI", "components", "Next.js" |
| `test-engineer`         | Testing          | "tests", "coverage", "TDD"             |
| `devops-engineer`       | DevOps           | "deploy", "CI/CD", "infrastructure"    |
| `database-architect`    | Database         | "schema", "Prisma", "migrations"       |
| `mobile-developer`      | Mobile           | "React Native", "Flutter", "mobile"    |
| `api-designer`          | API Design       | "REST", "GraphQL", "OpenAPI"           |
| `debugger`              | Debugging        | "bug", "error", "not working"          |
| `explorer-agent`        | Discovery        | "explore", "map", "structure"          |
| `documentation-writer`  | Documentation    | "write docs", "create README"          |
| `performance-optimizer` | Performance      | "slow", "optimize", "profiling"        |
| `project-planner`       | Planning         | "plan", "roadmap", "milestones"        |
| `seo-specialist`        | SEO              | "SEO", "meta tags", "search ranking"   |
| `game-developer`        | Game Development | "game", "Unity", "Godot", "Phaser"     |

---

## Synthesis Protocol

After all agents/teammates complete, synthesize:

```markdown
## Orchestration Synthesis

### Task Summary

[What was accomplished]

### Strategy Used

[Agent Teams / Subagents / Sequential — and why]

### Agent Contributions

| Agent              | Finding      |
| ------------------ | ------------ |
| security-auditor   | Found X      |
| backend-specialist | Identified Y |

### Consolidated Recommendations

1. **Critical**: [Issue from Agent A]
2. **Important**: [Issue from Agent B]
3. **Nice-to-have**: [Enhancement from Agent C]

### Action Items

- [ ] Fix critical security issue
- [ ] Refactor API endpoint
- [ ] Add missing tests
```

---

## Best Practices

1. **Platform-first** — Always use the highest-capability strategy available
2. **Announce strategy** — Tell the user which orchestration mode is being used
3. **Logical order** — Discovery → Analysis → Implementation → Testing
4. **Share context** — Pass relevant findings between agents/teammates
5. **Single synthesis** — One unified report, not separate outputs
6. **Verify changes** — Always include test-engineer for code modifications
7. **Avoid file conflicts** — Assign non-overlapping file scopes to parallel agents
