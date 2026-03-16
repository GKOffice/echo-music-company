# ECHO — Autonomous AI Music Company

> **Own the Sound** — 21 AI agents running a fully autonomous music label, 24/7.

---

## Overview

ECHO is a fully autonomous AI music company built on a 21-agent LangGraph framework. Every function of a modern music label — A&R, recording, distribution, marketing, legal, finance, and fan monetization — is handled by specialized AI agents operating in concert.

**ECHO Points** enable fans and investors to buy fractional royalty ownership stakes in individual tracks, earning streaming royalties proportional to their holdings.

**Six business lines:**
1. **ECHO Label** — Sign artists, develop careers, 21 AI agents working 24/7
2. **ECHO Publishing** — Worldwide royalty collection, sync licensing
3. **ECHO Open Platform** — À la carte services for independent artists
4. **ECHO For Labels** — White-label points infrastructure for external labels
5. **ECHO Points Store** — Fans buy fractional royalty rights on songs
6. **ECHO Producer Hub** — Beat marketplace with AI matching

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI + SQLAlchemy (async) + PostgreSQL 16 |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Agents** | LangGraph + LangChain + Anthropic Claude |
| **Message Bus** | Redis 7 (Streams + Pub/Sub) |
| **Database** | PostgreSQL 16 |
| **Cache/Queue** | Redis 7 |
| **Payments** | Stripe Connect |
| **Storage** | AWS S3 / Cloudflare R2 |
| **Containers** | Docker + Docker Compose |

---

## Project Structure

```
echo/
├── apps/
│   ├── api/              # FastAPI backend (port 8000)
│   │   ├── main.py       # App entry point, CORS, health check
│   │   ├── database.py   # SQLAlchemy async engine
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── routers/      # auth, artists, releases, points, agents, hub
│   ├── web/              # Next.js 14 Label Platform UI (port 3000)
│   │   ├── app/          # App Router: layout.tsx, page.tsx, globals.css
│   │   ├── package.json
│   │   ├── tailwind.config.js
│   │   └── Dockerfile
│   └── agents/           # LangGraph agent orchestration
│       ├── main.py       # Starts all 21 agents
│       ├── base_agent.py # Base class all agents inherit
│       ├── bus.py        # Redis message bus wrapper
│       ├── requirements.txt
│       ├── Dockerfile
│       └── agents/       # 21 specialized agent modules
│           ├── ceo.py, ar.py, production.py, distribution.py
│           ├── marketing.py, social.py, finance.py, legal.py
│           ├── analytics.py, creative.py, sync.py, artist_dev.py
│           ├── pr.py, comms.py, qc.py, infrastructure.py
│           ├── intake.py, merch.py, youtube.py, hub.py, vault.py
├── packages/
│   ├── db/               # Database schema + migrations
│   │   └── schema.sql    # Full 16-table PostgreSQL schema
│   ├── shared/           # Shared types and utilities
│   └── config/           # Shared configuration
├── infra/
│   ├── docker/           # Docker configs
│   └── scripts/          # Setup and deployment scripts
├── docker-compose.yml    # Full stack: postgres, redis, api, web, agents
├── .env.example          # All required env vars (no real values)
├── .gitignore
└── README.md
```

---

## The 21 Agents

| Agent | Role |
|-------|------|
| **CEO** | Orchestrates all agents, sets strategy, monitors KPIs |
| **A&R** | Discovers talent, scores submissions, manages signing pipeline |
| **Production** | Recording sessions, producer matching, master delivery |
| **Distribution** | DSP delivery (Spotify, Apple, etc.), release scheduling |
| **Marketing** | Campaign planning, playlist pitching, ad spend |
| **Social** | Content calendar, post scheduling, engagement monitoring |
| **Finance** | Royalty processing, advance tracking, recoupment |
| **Legal** | Contract drafting, copyright registration, DocuSign |
| **Analytics** | Streaming insights, ECHO scoring, artist reporting |
| **Creative** | Artwork review, brand guidelines, visual assets |
| **Sync** | Sync licensing pitches, brief processing, catalog search |
| **Artist Dev** | Growth plans, mentorship, brand workshops |
| **PR** | Press releases, media outreach, crisis comms |
| **Comms** | Email, WhatsApp, SMS, push notifications |
| **QC** | Audio quality, metadata validation, format compliance |
| **Infrastructure** | System health, backups, security scanning |
| **Intake** | Demo submission processing, deduplication, routing |
| **Merch** | Merch drops, store management, fulfillment |
| **YouTube** | Channel management, Content ID, Shorts strategy |
| **Hub** | Beat marketplace scoring, producer-artist matching |
| **Vault** | ECHO Points issuance, royalty distribution to holders |

---

## Running Locally

### Prerequisites
- Docker + Docker Compose
- Node.js 20+ (for local web dev)
- Python 3.12+ (for local API/agents dev)

### Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Start everything
docker-compose up -d

# 3. Services running at:
#    API:      http://localhost:8000
#    Web:      http://localhost:3000
#    API Docs: http://localhost:8000/docs
#    Postgres: localhost:5432
#    Redis:    localhost:6379
```

### Local Development

```bash
# API (FastAPI)
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Web (Next.js)
cd apps/web
npm install
npm run dev

# Agents
cd apps/agents
pip install -r requirements.txt
python main.py
```

---

## API Reference

```
GET  /health                                System health check
POST /api/v1/auth/register                  Register user
POST /api/v1/auth/token                     Login (returns JWT)
GET  /api/v1/auth/me                        Current user

GET  /api/v1/artists/                       List artists
POST /api/v1/artists/                       Create artist
GET  /api/v1/artists/{id}                   Get artist
GET  /api/v1/artists/{id}/releases          Artist releases
GET  /api/v1/artists/{id}/royalties         Artist royalties

GET  /api/v1/releases/                      List releases
POST /api/v1/releases/                      Create release
GET  /api/v1/releases/{id}                  Get release
GET  /api/v1/releases/{id}/tracks           Release tracks
POST /api/v1/releases/{id}/tracks           Add track

POST /api/v1/points/purchase                Buy ECHO Points
GET  /api/v1/points/my-portfolio            Portfolio view
GET  /api/v1/points/track/{id}/availability Check availability

POST /api/v1/agents/tasks                   Create agent task
GET  /api/v1/agents/tasks                   List tasks
POST /api/v1/agents/messages                Publish message
GET  /api/v1/agents/agents                  List all agents

GET  /api/v1/hub/beats                      Browse beats
POST /api/v1/hub/beats                      Submit beat
GET  /api/v1/hub/beats/{id}                 Get beat
```

---

## Database Schema

16 tables:
- `users` + `sessions` — Auth with 2FA, device tracking
- `artists` + `producers` — Roster and producer network
- `releases` + `tracks` — Catalog management
- `echo_points` — Fractional royalty ownership
- `royalties` — Multi-source royalty tracking (streaming, mechanical, sync, etc.)
- `contracts` — DocuSign-backed deal management
- `agent_tasks` + `agent_messages` — Agent bus log
- `submissions` — Demo intake pipeline
- `contacts` — CRM
- `audit_log` — Full audit trail
- `hub_beats` — Beat marketplace

---

## Design System

| Token | Value |
|-------|-------|
| Background | `#0a0a0f` |
| Surface | `#13131a` |
| Primary (Purple) | `#8b5cf6` |
| Accent (Green) | `#10b981` |
| Text | `#f9fafb` |

---

## Build Status

| Phase | Name | Status |
|-------|------|--------|
| 01 | Scout | Complete |
| 02 | Sign | Complete |
| **03** | **Release Engine** | **In Progress** |
| 04 | Monetize (ECHO Points) | Upcoming |
| 05 | Scale (Sync + Catalog) | Upcoming |

---

## Agent Architecture

All 21 agents inherit from `BaseAgent` which provides:
- Async PostgreSQL connection pool via `asyncpg`
- Redis message bus (pub/sub + streams) via `bus.py`
- Task processing loop — each agent reads from its own Redis Stream
- DB helpers: `db_fetch`, `db_fetchrow`, `db_execute`
- Audit logging: `log_audit`
- Inter-agent messaging: `send_message`, `broadcast`

---

*Blueprint v18.0 · CEO: AI · Phase 3 in progress*
