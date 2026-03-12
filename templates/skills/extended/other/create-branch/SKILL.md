---
name: create-branch
description: Create a git branch following Sentry naming conventions. Use when asked to "create a branch", "new branch", "start a branch", "make a branch", "switch to a new branch", or when starting new work on the default branch.
argument-hint: '[optional description of the work]'
---

# Create Branch

Create a git branch with the correct type prefix and a descriptive name following Sentry conventions.

## Step 1: Get the Username Prefix

Run `gh api user --jq .login` to get the GitHub username.

If the command fails (e.g. not authenticated), ask the user for their preferred prefix.

## Step 2: Determine the Branch Description

**If `$ARGUMENTS` is provided**, use it as the description of the work.

**If no arguments**, check for local changes:

```bash
git diff
git diff --cached
git status --short
```

- **Changes exist**: read the diff content to understand what the work is about and generate a description.
- **No changes**: ask the user what they are about to work on.

## Step 3: Classify the Type

Pick the type from this table based on the description:

| Type      | Use when                                                              |
| --------- | --------------------------------------------------------------------- |
| `feat`    | New user-facing functionality                                         |
| `fix`     | Broken behavior now works                                             |
| `ref`     | Same behavior, different structure                                    |
| `chore`   | Deps, config, version bumps, updating existing tooling — no new logic |
| `perf`    | Same behavior, faster                                                 |
| `style`   | CSS, formatting, visual-only                                          |
| `docs`    | Documentation only                                                    |
| `test`    | Tests only                                                            |
| `ci`      | CI/CD config                                                          |
| `build`   | Build system                                                          |
| `meta`    | Repo metadata changes                                                 |
| `license` | License changes                                                       |

When unsure: `feat` for new things (including new scripts, skills, or tools), `ref` for restructuring existing things, `chore` only when updating/maintaining something that already exists.

## Step 4: Generate and Propose

Build the branch name as `<username>/<type>/<short-description>`.

Rules for `<short-description>`:

- Kebab-case, lowercase
- 3 to 6 words, concise but clear
- Describe the change, not file names
- Only use ASCII letters, digits, and hyphens — no spaces, dots, colons, tildes, or other git-forbidden characters

Present it to the user and ask if they want to use it, modify it, or change the type.

### Examples

| Work description                           | Branch name                                 |
| ------------------------------------------ | ------------------------------------------- |
| Dropdown menu not closing on outside click | `priscila/fix/dropdown-not-closing-on-blur` |
| Adding search to conversations page        | `priscila/feat/add-search-to-conversations` |
| Restructuring drawer components            | `priscila/ref/simplify-drawer-components`   |
| Updating test fixtures                     | `priscila/chore/update-test-fixtures`       |
| Bumping @sentry/react to latest version    | `priscila/chore/bump-sentry-react`          |
| Adding a new agent skill                   | `priscila/feat/add-create-branch-skill`     |

## Step 5: Create the Branch

Once confirmed, detect the current and default branch:

```bash
git branch --show-current
git remote | grep -qx origin && echo origin || git remote | head -1
git symbolic-ref refs/remotes/<remote>/HEAD 2>/dev/null | sed 's|refs/remotes/<remote>/||' | tr -d '[:space:]'
```

If `symbolic-ref` fails, fall back to `git branch --list main master`: use the one that exists; if both or neither exist, ask the user.

If `git branch --show-current` is empty (detached HEAD), show the current commit (`git rev-parse --short HEAD`) and ask whether to branch from it or switch to the default branch first.

Otherwise, if the current branch is not the default branch, warn the user and ask whether to branch from the current branch or switch to the default branch first.

If the user wants to switch to the default branch, handle any uncommitted changes appropriately (offer to stash them if present), then run `git checkout <default-branch>`. On any failure, restore stashed changes if applicable and stop.

Before creating the branch, check that the name doesn't already exist locally or on the remote (`git show-ref`). If it does, ask the user to choose a different name.

Create the branch:

```bash
git checkout -b <branch-name>
```

Restore any stashed changes after the branch is created.

## References

- [Sentry Branch Naming](https://develop.sentry.dev/sdk/getting-started/standards/code-submission/#branch-naming)

---

<!-- AGI-INTEGRATION-START -->

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags create-branch <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
