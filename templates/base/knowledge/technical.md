# Technical Context

> Synced to Qdrant via `memory_manager.py knowledge-sync`. Retrieved semantically at dispatch time.

## Architecture Overview

- (Describe the high-level system architecture here)

## Key Services & Integrations

- **Auth:** (e.g. Supabase Auth / Auth0)
- **Database:** (e.g. PostgreSQL via Prisma)
- **Cache:** (e.g. Redis for session + rate limiting)
- **Storage:** (e.g. S3-compatible object storage)
- **Queue:** (e.g. BullMQ / SQS)

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | Primary DB connection string | Yes |
| `REDIS_URL` | Cache / queue broker URL | Yes |
| (add more rows as needed) | | |

## Known Constraints

- (List any performance limits, quotas, or infra constraints relevant to coding decisions)
