# Prohibitions

> Synced to Qdrant via `memory_manager.py knowledge-sync`. Retrieved semantically at dispatch time.

## Never Do

- Do NOT use `eval()` or dynamic code execution.
- Do NOT hardcode credentials, API keys, or secrets in source files.
- Do NOT disable linting or type-checking with inline suppression comments unless accompanied by a documented reason.
- Do NOT introduce breaking changes to public APIs without a deprecation notice.
- Do NOT merge code that has failing tests.

## Avoid

- Avoid deeply nested conditionals (max 3 levels); extract helpers instead.
- Avoid large functions (>50 lines); split into focused helpers.
- Avoid global mutable state.
- Avoid third-party packages for tasks that can be done with the standard library.
