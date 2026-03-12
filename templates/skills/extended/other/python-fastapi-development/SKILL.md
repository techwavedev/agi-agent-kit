---
name: python-fastapi-development
description: "Python FastAPI backend development with async patterns, SQLAlchemy, Pydantic, authentication, and production API patterns."
category: granular-workflow-bundle
risk: safe
source: personal
date_added: "2026-02-27"
---

# Python/FastAPI Development Workflow

## Overview

Specialized workflow for building production-ready Python backends with FastAPI, featuring async patterns, SQLAlchemy ORM, Pydantic validation, and comprehensive API patterns.

## When to Use This Workflow

Use this workflow when:
- Building new REST APIs with FastAPI
- Creating async Python backends
- Implementing database integration with SQLAlchemy
- Setting up API authentication
- Developing microservices

## Workflow Phases

### Phase 1: Project Setup

#### Skills to Invoke
- `app-builder` - Application scaffolding
- `python-development-python-scaffold` - Python scaffolding
- `fastapi-templates` - FastAPI templates
- `uv-package-manager` - Package management

#### Actions
1. Set up Python environment (uv/poetry)
2. Create project structure
3. Configure FastAPI app
4. Set up logging
5. Configure environment variables

#### Copy-Paste Prompts
```
Use @fastapi-templates to scaffold a new FastAPI project
```

```
Use @python-development-python-scaffold to set up Python project structure
```

### Phase 2: Database Setup

#### Skills to Invoke
- `prisma-expert` - Prisma ORM (alternative)
- `database-design` - Schema design
- `postgresql` - PostgreSQL setup
- `pydantic-models-py` - Pydantic models

#### Actions
1. Design database schema
2. Set up SQLAlchemy models
3. Create database connection
4. Configure migrations (Alembic)
5. Set up session management

#### Copy-Paste Prompts
```
Use @database-design to design PostgreSQL schema
```

```
Use @pydantic-models-py to create Pydantic models for API
```

### Phase 3: API Routes

#### Skills to Invoke
- `fastapi-router-py` - FastAPI routers
- `api-design-principles` - API design
- `api-patterns` - API patterns

#### Actions
1. Design API endpoints
2. Create API routers
3. Implement CRUD operations
4. Add request validation
5. Configure response models

#### Copy-Paste Prompts
```
Use @fastapi-router-py to create API endpoints with CRUD operations
```

```
Use @api-design-principles to design RESTful API
```

### Phase 4: Authentication

#### Skills to Invoke
- `auth-implementation-patterns` - Authentication
- `api-security-best-practices` - API security

#### Actions
1. Choose auth strategy (JWT, OAuth2)
2. Implement user registration
3. Set up login endpoints
4. Create auth middleware
5. Add password hashing

#### Copy-Paste Prompts
```
Use @auth-implementation-patterns to implement JWT authentication
```

### Phase 5: Error Handling

#### Skills to Invoke
- `fastapi-pro` - FastAPI patterns
- `error-handling-patterns` - Error handling

#### Actions
1. Create custom exceptions
2. Set up exception handlers
3. Implement error responses
4. Add request logging
5. Configure error tracking

#### Copy-Paste Prompts
```
Use @fastapi-pro to implement comprehensive error handling
```

### Phase 6: Testing

#### Skills to Invoke
- `python-testing-patterns` - pytest testing
- `api-testing-observability-api-mock` - API testing

#### Actions
1. Set up pytest
2. Create test fixtures
3. Write unit tests
4. Implement integration tests
5. Configure test database

#### Copy-Paste Prompts
```
Use @python-testing-patterns to write pytest tests for FastAPI
```

### Phase 7: Documentation

#### Skills to Invoke
- `api-documenter` - API documentation
- `openapi-spec-generation` - OpenAPI specs

#### Actions
1. Configure OpenAPI schema
2. Add endpoint documentation
3. Create usage examples
4. Set up API versioning
5. Generate API docs

#### Copy-Paste Prompts
```
Use @api-documenter to generate comprehensive API documentation
```

### Phase 8: Deployment

#### Skills to Invoke
- `deployment-engineer` - Deployment
- `docker-expert` - Containerization

#### Actions
1. Create Dockerfile
2. Set up docker-compose
3. Configure production settings
4. Set up reverse proxy
5. Deploy to cloud

#### Copy-Paste Prompts
```
Use @docker-expert to containerize FastAPI application
```

## Technology Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI |
| Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Database | PostgreSQL |
| Migrations | Alembic |
| Auth | JWT, OAuth2 |
| Testing | pytest |

## Quality Gates

- [ ] All tests passing (>80% coverage)
- [ ] Type checking passes (mypy)
- [ ] Linting clean (ruff, black)
- [ ] API documentation complete
- [ ] Security scan passed
- [ ] Performance benchmarks met

## Related Workflow Bundles

- `development` - General development
- `database` - Database operations
- `security-audit` - Security testing
- `api-development` - API patterns

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Cache workflow configurations and automation patterns. Retrieve prior pipeline designs to avoid re-building similar flows from scratch.

```bash
# Check for prior workflow/automation context before starting
python3 execution/memory_manager.py auto --query "automation patterns and workflow configurations for Python Fastapi Development"
```

### Storing Results

After completing work, store workflow/automation decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Workflow: automated data pipeline with retry logic, dead-letter queue, and Slack alerts on failure" \
  --type technical --project <project> \
  --tags python-fastapi-development workflow
```

### Multi-Agent Collaboration

Share workflow state with other agents so they can trigger, monitor, or extend the automation.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Workflow automation deployed — pipeline processing 1000+ events/day with 99.9% success rate" \
  --project <project>
```

### Playbook Engine

Combine this skill with others using the Playbook Engine (`execution/workflow_engine.py`) for guided multi-step automation with progress tracking.

<!-- AGI-INTEGRATION-END -->
