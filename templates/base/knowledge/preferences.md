# Development Preferences

> Synced to Qdrant via `memory_manager.py knowledge-sync`. Retrieved semantically at dispatch time.

## Code Style

- (e.g. ESLint + Prettier with 2-space indent; black + isort for Python)

## Testing

- Prefer unit tests for pure functions, integration tests for API routes.
- Minimum 80% coverage on new code.
- Use the existing test runner — do not introduce a second framework.

## Git Workflow

- Branch names: `feat/<topic>`, `fix/<topic>`, `chore/<topic>`
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Squash merge into main.

## Dependency Management

- Pin exact versions in production dependencies.
- Audit new dependencies for license compatibility before adding.
