# Lodge-Link

> B2B Hotel Referral Switch Middleware — Ethiopian Hospitality & Tourism Sector

Lodge-Link is an interoperability layer between hotels. When Hotel A is full or budget-incompatible, the platform suggests and facilitates a real-time referral to Hotel B or C.

## Quick Start (Development)

```bash
# 1. Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your values

# 2. Start all services
docker-compose up -d

# 3. Run database migrations
docker-compose exec api alembic upgrade head

# 4. Verify
curl http://localhost:8000/health
```

## Documentation
- **Architecture:** `docs/Lodge-Link_Implementation_Plan.md`
- **Active Phase:** `docs/phases/PHASE_1_MVP.md`
- **Agent Rules:** `CLAUDE.md` + `AGENTS.md`
- **Phase Status:** `PHASE_STATUS.json`
- **Feature Claims:** `FEATURE_LOCKS.json`

## For AI Agents
Read `CLAUDE.md` first. Always. Then `PHASE_STATUS.json`. Then `FEATURE_LOCKS.json`.
Do not build features for phases that are locked.

## Team
See `AGENTS.md` for multi-agent collaboration protocol.
