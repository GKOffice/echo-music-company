# 🎵 ECHO — AI Music Company

The world's first fully autonomous AI music company.

## What is ECHO?

ECHO is a complete AI-powered music company with 6 business lines:
1. **ECHO Label** — Sign artists, develop careers, 21 AI agents working 24/7
2. **ECHO Publishing** — Worldwide royalty collection, sync licensing
3. **ECHO Open Platform** — À la carte services for independent artists
4. **ECHO For Labels** — White-label points infrastructure for external labels
5. **ECHO Points Store + Exchange** — Fans buy fractional royalty rights on songs
6. **ECHO Producer Hub** — Beat marketplace with AI matching

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.12+) |
| Frontend | Next.js 14 (TypeScript) |
| Agents | LangGraph + 21 specialized AI agents |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 (Streams + Pub/Sub) |
| AI | Claude Opus/Sonnet + GPT-4o |
| Storage | AWS S3 / Cloudflare R2 |
| Payments | Stripe Connect |
| Containers | Docker + Docker Compose |

## Project Structure

```
echo/
├── apps/
│   ├── api/          # FastAPI backend (port 8000)
│   ├── web/          # Next.js 14 frontend (port 3000)
│   └── agents/       # 21 AI agents (LangGraph)
├── packages/
│   ├── db/           # Database schema + migrations
│   ├── shared/       # Shared TypeScript types
│   └── config/       # Shared configuration
├── infra/
│   └── scripts/      # Setup and deployment scripts
├── docker-compose.yml
└── .env.example
```

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd echo
cp .env.example .env
# Fill in your API keys in .env

# 2. Start infrastructure
docker-compose up -d postgres redis

# 3. Start all services
docker-compose up

# 4. Open
# API docs: http://localhost:8000/docs
# Web app: http://localhost:3000
```

## Build Status

| Phase | Status | Goal |
|-------|--------|------|
| Phase 0 | ✅ Done | Infrastructure + DB schema |
| Phase 1 | 🔄 In Progress | Core agents + dashboard |
| Phase 2 | ⏳ Upcoming | Sign first artist |
| Phase 3 | ⏳ Upcoming | First release live |

## Agent Architecture

21 autonomous agents communicate via Redis Streams:
- All agents inherit from `BaseAgent`
- Tasks dispatched via `MessageBus`
- Each agent has a dedicated Redis Stream queue
- QC gates between all agent handoffs

---

*Blueprint v18.0 · CEO: B (AI) · Owner: Mike B.*
