---
name: fastapi-router-py
description: "Create FastAPI routers with CRUD operations, authentication dependencies, and proper response models. Use when building REST API endpoints, creating new routes, implementing CRUD operations, or add..."
risk: unknown
source: community
date_added: "2026-02-27"
---

# FastAPI Router

Create FastAPI routers following established patterns with proper authentication, response models, and HTTP status codes.

## Quick Start

Copy the template from assets/template.py and replace placeholders:
- `{{ResourceName}}` → PascalCase name (e.g., `Project`)
- `{{resource_name}}` → snake_case name (e.g., `project`)
- `{{resource_plural}}` → plural form (e.g., `projects`)

## Authentication Patterns

```python
# Optional auth - returns None if not authenticated
current_user: Optional[User] = Depends(get_current_user)

# Required auth - raises 401 if not authenticated
current_user: User = Depends(get_current_user_required)
```

## Response Models

```python
@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str) -> Item:
    ...

@router.get("/items", response_model=list[Item])
async def list_items() -> list[Item]:
    ...
```

## HTTP Status Codes

```python
@router.post("/items", status_code=status.HTTP_201_CREATED)
@router.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
```

## Integration Steps

1. Create router in `src/backend/app/routers/`
2. Mount in `src/backend/app/main.py`
3. Create corresponding Pydantic models
4. Create service layer if needed
5. Add frontend API functions

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior API design decisions, database schema choices, and error handling patterns. Cache API response templates for consistent error formatting.

```bash
# Check for prior backend/API context before starting
python3 execution/memory_manager.py auto --query "API design patterns and architecture decisions for Fastapi Router Py"
```

### Storing Results

After completing work, store backend/API decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "API architecture: REST with HATEOAS, JWT auth, rate limiting at 100 req/min per tenant" \
  --type decision --project <project> \
  --tags fastapi-router-py backend
```

### Multi-Agent Collaboration

Share API contract changes with frontend agents so they update their client code, and with QA agents for test coverage.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented API endpoints — 5 new routes with OpenAPI spec and integration tests" \
  --project <project>
```

### Agent Team: Code Review

After implementation, dispatch `code_review_team` for two-stage review (spec compliance + code quality) before merging.

<!-- AGI-INTEGRATION-END -->
