# Melodio DB Migrations

## Current Status
Schema is managed via `packages/db/schema.sql` (applied on first Docker init).
Ad-hoc patches in this folder were applied manually during development.

## Migration History (ad-hoc, applied April 2026)
- `add_missing_columns.sql` — added bio, photo_url, social_links, stripe_connect fields, etc.
- `add_missing_tables.sql` — added deal_listings, deal_offers, deals, deal_messages, external_catalog, point_drops, exchange_orders
- `add_agent_memory.sql` — agent memory store table
- `add_waitlist.sql` — waitlist table

## Moving Forward — Use Alembic

Alembic is installed (`alembic==1.13.3` in requirements.txt).

### Setup (one-time, if not done)
```bash
cd apps/api
alembic init alembic
# Edit alembic/env.py to use async SQLAlchemy + DATABASE_URL from env
```

### Create a new migration
```bash
cd apps/api
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

### Check current revision
```bash
alembic current
```

### Rollback
```bash
alembic downgrade -1
```

## ⚠️ Before Railway Deploy
Run `alembic upgrade head` as part of the Railway deploy command (add to railway.toml start command):
```
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
```
