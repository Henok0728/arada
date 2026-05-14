# CLAUDE.md — Lodge-Link Agent Coordination File
> This file is read automatically by every Claude Code agent at the start of every session.
> It is the single source of truth for agent behavior. DO NOT contradict it in conversation.

---

## 🔴 READ THESE FIRST — Non-Negotiable Rules

1. **Read before you build.** Before writing a single line of code for any feature, locate and read the relevant section in `docs/Lodge-Link_Implementation_Plan.md`. The rationale for every architectural decision is documented there.

2. **Check the phase.** Read `PHASE_STATUS.json`. If `current_phase` is 1, you only build Phase 1 features. Features marked "Phase 2+" in the plan are **out of scope** until the phase status is updated.

3. **Claim before you build.** Read `FEATURE_LOCKS.json`. If the feature you intend to build shows `"status": "available"`, you MUST submit a PR that changes its status to `"claimed"` with your `agent_id` and `branch` BEFORE writing code. If it is `"claimed"` by another agent, **stop** — find a different available feature.

4. **Never hardcode market-specific values.** ETB, Telebirr, Amharic, Ethiopia — always use config or constants from `app/core/config.py`. The codebase must be ready for Kenya/Rwanda without a rewrite.

5. **No .env files committed.** Ever. If you need to add an env variable, add it to `.env.example` and document it in your PR.

6. **Tests are not optional.** Every backend endpoint you write requires at least one integration test in `backend/tests/`. Run `pytest` before submitting a PR.

---

## 📁 Project Architecture (Quick Reference)

```
lodge-link/
├── docs/
│   ├── Lodge-Link_Implementation_Plan.md   ← PRIMARY REFERENCE (read this)
│   └── phases/
│       ├── PHASE_1_MVP.md                  ← Active phase build spec
│       ├── PHASE_2_BETA.md
│       ├── PHASE_3_SCALE.md
│       └── PHASE_4_AI.md
├── CLAUDE.md                               ← You are here
├── AGENTS.md                               ← Multi-agent collaboration rules
├── PHASE_STATUS.json                       ← Current phase (check before building)
├── FEATURE_LOCKS.json                      ← Claim features here (prevent conflicts)
├── backend/                                ← FastAPI (Python 3.11)
│   └── app/
│       ├── api/v1/routers/                 ← HTTP route handlers (thin layer only)
│       ├── core/config.py                  ← All settings (pydantic-settings)
│       ├── db/models/                      ← SQLAlchemy ORM models
│       ├── db/repositories/                ← All DB queries live here (not in routes)
│       ├── schemas/                        ← Pydantic request/response models
│       ├── services/                       ← Business logic (referral engine, etc.)
│       └── workers/                        ← Celery async tasks
├── frontend/                               ← Next.js 14 (React, TypeScript, PWA)
└── infrastructure/                         ← Docker, Nginx, CI scripts
```

---

## 🏗️ Core Architecture Principles

### Backend (FastAPI)
- Routes are thin. Business logic belongs in `services/`, not in routers.
- All DB access goes through `db/repositories/`. No raw SQL in route handlers.
- Every outbound hotel check has a **3-second hard timeout** (`REFERRAL_FANOUT_TIMEOUT_SECONDS`). A slow hotel never blocks the fanout.
- Referral fanout uses `asyncio.gather()`. Never sequential hotel checks.
- API keys are **always SHA-256 hashed** before storage. The plaintext key is shown exactly once (at generation) and never stored.

### Database (PostgreSQL)
- The `platform` schema is shared. Hotel private schemas are `hotel_{slug}`.
- Row Level Security (RLS) must be enabled on ALL private hotel tables.
- Every migration is via Alembic. Never modify the schema directly in psql.
- PostGIS is installed. Use `GEOGRAPHY(POINT, 4326)` for hotel location, geo-radius queries via PostGIS functions.

### Connectivity Resilience (Non-Negotiable for Ethiopian Market)
- Redis cache (90s TTL) for all availability data.
- Celery queue (exponential backoff) for all outbound webhook notifications.
- AfricasTalking SMS dispatched for EVERY referral event (not just webhook failures).
- HMAC offline handshake code must validate **without any API call** (validated in Service Worker / local).

### Frontend (Next.js PWA)
- Emergency Referral Mode must be reachable in 3 taps maximum.
- Service Worker caches last 50 pending referrals in IndexedDB.
- All UI text must have both `en` and `am` (Amharic) translation keys in `i18n/`.
- Font: Noto Sans Ethiopic for Amharic text.

---

## 🔑 Key API Patterns

```python
# Key format:  ll_{env}_{48 chars base62}
# Storage:     SHA-256(prefix + "." + secret) — never the key itself
# Scopes:      availability:read, availability:write, referral:create,
#              referral:read, referral:confirm, trust:read, analytics:read

# Referral fanout pattern (always async gather, never sequential)
results = await asyncio.gather(*[
    fetch_hotel_availability(client, hotel, request, cache)
    for hotel in candidates
], return_exceptions=False)
```

---

## 🌍 Ethiopian Context (Always Apply)
- Peak demand events: Timkat (Jan 18–20), Ethiopian Christmas (Jan 7), Meskel (Sep 27), Fasika (Easter), Great Ethiopian Run (Nov).
- Payment: ETB primary. Telebirr + CBE Birr only. Never card-first.
- Commission collected post-stay (not pre-paid). Monthly invoicing.
- SMS is always dispatched alongside webhooks — not as a fallback, as a parallel channel.

---

## 🔀 Git Workflow
```
main        ← Production. Protected. Only merges from develop via reviewed PR.
develop     ← Integration branch. All phase work targets here.
phase1/     ← Feature branches: phase1/referral-fanout, phase1/auth-system
```
Never push directly to `main`. Never push directly to `develop`.
All merges to `develop` require a PR with the FEATURE_LOCKS.json entry updated.

---

## ✅ Before Submitting Any PR
- [ ] `FEATURE_LOCKS.json` — my feature is set to `"claimed"` (or I'm releasing it to `"released"`)
- [ ] `pytest` passes (backend)
- [ ] `npm run lint && npm run type-check` passes (frontend)
- [ ] No hardcoded ETB/Telebirr/Ethiopia strings outside of config
- [ ] No `.env` files committed
- [ ] I read the relevant `docs/Lodge-Link_Implementation_Plan.md` section
