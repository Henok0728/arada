#!/usr/bin/env bash
# =============================================================================
# Lodge-Link Bootstrap Script
# Scaffolds the full project structure and pushes to GitHub.
# Run this ONCE from inside your empty project folder.
#
# Usage:
#   chmod +x bootstrap.sh
#   GITHUB_REPO="https://github.com/YOUR_ORG/lodge-link.git" ./bootstrap.sh
# =============================================================================

set -euo pipefail

GITHUB_REPO="${GITHUB_REPO:-}"
PROJECT_NAME="lodge-link"

# ─── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }

echo -e "\n${BOLD}╔══════════════════════════════════════════╗"
echo -e "║   Lodge-Link Project Bootstrap v1.0     ║"
echo -e "╚══════════════════════════════════════════╝${RESET}\n"

# ─── Preflight ────────────────────────────────────────────────────────────────
command -v git  >/dev/null 2>&1 || error "git is required but not installed."
command -v python3 >/dev/null 2>&1 || error "python3 is required but not installed."
[[ -z "$GITHUB_REPO" ]] && error "Set GITHUB_REPO env variable first.\n  Example: GITHUB_REPO=https://github.com/your-org/lodge-link.git ./bootstrap.sh"

info "Target repo: $GITHUB_REPO"

# ─── Git Init ─────────────────────────────────────────────────────────────────
if [[ ! -d ".git" ]]; then
  git init -b main
  success "Git repository initialized"
else
  warn "Git already initialized — skipping git init"
fi

# ─── Directory Scaffold ───────────────────────────────────────────────────────
info "Creating directory structure..."

mkdir -p \
  docs/phases \
  backend/app/{api/v1/routers,core,db/{models,repositories,migrations},schemas,services,workers} \
  backend/tests/{unit,integration} \
  frontend/src/{components,pages,hooks,lib,styles} \
  frontend/public \
  infrastructure/{docker,nginx,scripts} \
  .github/{workflows,ISSUE_TEMPLATE}

success "Directory structure created"

# ─── .gitignore ───────────────────────────────────────────────────────────────
cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
dist/
build/
*.egg
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Environment
.env
.env.local
.env.*.local
*.env

# Node
node_modules/
.next/
out/
.npm
*.log

# OS
.DS_Store
Thumbs.db
*.swp
*.swo

# IDE
.vscode/settings.json
.idea/
*.iml

# Docker
*.pid

# Database
*.sqlite3
dumps/

# Secrets — NEVER commit these
*.pem
*.key
secrets/
GITIGNORE

success ".gitignore created"

# ─── Python Backend Scaffold ──────────────────────────────────────────────────
info "Scaffolding backend..."

cat > backend/requirements.txt << 'EOF'
# Core
fastapi==0.111.0
uvicorn[standard]==0.29.0
gunicorn==22.0.0

# Database
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
psycopg2-binary==2.9.9

# Cache & Queue
redis==5.0.4
celery==5.4.0
kombu==5.3.4

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==42.0.8

# Validation
pydantic==2.7.1
pydantic-settings==2.2.1
email-validator==2.1.1

# HTTP Client
httpx==0.27.0

# Monitoring
structlog==24.1.0
sentry-sdk[fastapi]==2.1.1

# Testing
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.27.0
factory-boy==3.3.0
pytest-cov==5.0.0
EOF

cat > backend/requirements-dev.txt << 'EOF'
-r requirements.txt
ruff==0.4.4
mypy==1.10.0
pre-commit==3.7.1
ipython==8.24.0
EOF

cat > backend/pyproject.toml << 'EOF'
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
EOF

cat > backend/app/__init__.py << 'EOF'
# Lodge-Link Backend — FastAPI Application
EOF

cat > backend/app/main.py << 'EOF'
"""
Lodge-Link API Entry Point
--------------------------
Read CLAUDE.md and docs/Lodge-Link_Implementation_Plan.md before modifying.
Every architectural decision in this file has a documented rationale.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="Lodge-Link API",
    description="B2B Hotel Referral Switch Middleware — Ethiopian Hospitality Sector",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "lodge-link-api", "version": "0.1.0"}
EOF

cat > backend/app/core/__init__.py << 'EOF'
EOF

cat > backend/app/core/config.py << 'EOF'
"""
Central configuration — loaded once at startup.
All secrets come from environment variables, never from code.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_HASH_ALGORITHM: str = "sha256"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # SMS Gateway (AfricasTalking)
    AT_USERNAME: str = ""
    AT_API_KEY: str = ""
    AT_SENDER_ID: str = "LodgeLink"

    # Platform
    DEFAULT_COUNTRY: str = "ET"
    DEFAULT_CURRENCY: str = "ETB"
    REFERRAL_FANOUT_TIMEOUT_SECONDS: float = 3.0
    AVAILABILITY_CACHE_TTL_SECONDS: int = 90

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
EOF

success "Backend scaffolded"

# ─── Frontend Scaffold ────────────────────────────────────────────────────────
info "Scaffolding frontend..."

cat > frontend/package.json << 'EOF'
{
  "name": "lodge-link-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "react-i18next": "^14.1.2",
    "i18next": "^23.11.5",
    "axios": "^1.7.2",
    "zustand": "^4.5.2",
    "react-query": "^3.39.3"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.3",
    "postcss": "^8",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "14.2.3"
  }
}
EOF

cat > frontend/next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  // PWA support will be added via next-pwa in Phase 1
  reactStrictMode: true,
  i18n: {
    locales: ['en', 'am'],   // English + Amharic
    defaultLocale: 'en',
  },
}

module.exports = nextConfig
EOF

success "Frontend scaffolded"

# ─── Docker Compose ───────────────────────────────────────────────────────────
info "Creating Docker Compose..."

cat > docker-compose.yml << 'EOF'
version: "3.9"

# Lodge-Link Local Development Stack
# Mirrors production topology (FastAPI + PostgreSQL + Redis + Celery)

services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: lodge_link
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ./backend
      dockerfile: ../infrastructure/docker/Dockerfile.backend
    volumes:
      - ./backend:/app
    env_file: ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: ../infrastructure/docker/Dockerfile.backend
    volumes:
      - ./backend:/app
    env_file: ./backend/.env
    depends_on:
      - redis
      - db
    command: celery -A app.workers.celery_app worker --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: ../infrastructure/docker/Dockerfile.frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    command: npm run dev

volumes:
  postgres_data:
EOF

success "Docker Compose created"

# ─── Infrastructure Scripts ───────────────────────────────────────────────────
cat > infrastructure/scripts/init_db.sql << 'EOF'
-- Lodge-Link Database Initialization
-- Creates required extensions. Schema tables are created via Alembic migrations.
-- See docs/Lodge-Link_Implementation_Plan.md § 1.2 for schema design rationale.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Platform schema (shared, Lodge-Link managed)
CREATE SCHEMA IF NOT EXISTS platform;

-- Grant the app user access to platform schema
-- Individual hotel schemas (hotel_{slug}) are created during KYC onboarding
COMMENT ON SCHEMA platform IS 'Shared platform schema — Lodge-Link managed. See Implementation Plan § 1.2.';
EOF

cat > infrastructure/docker/Dockerfile.backend << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
EOF

cat > infrastructure/docker/Dockerfile.frontend << 'EOF'
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000
EOF

success "Infrastructure files created"

# ─── GitHub Actions CI ────────────────────────────────────────────────────────
info "Creating GitHub Actions workflows..."

cat > .github/workflows/ci.yml << 'EOF'
name: Lodge-Link CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: lodge_link_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint (ruff)
        run: cd backend && ruff check .
      - name: Type check (mypy)
        run: cd backend && mypy app/
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link_test
          REDIS_URL: redis://localhost:6379/0
          ENVIRONMENT: test
        run: cd backend && pytest --cov=app --cov-report=xml -v

  frontend-lint:
    name: Frontend Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run type-check
EOF

cat > .github/PULL_REQUEST_TEMPLATE.md << 'EOF'
## Summary
<!-- One paragraph: what does this PR do and why? -->

## Phase
- [ ] Phase 1 — MVP
- [ ] Phase 2 — Beta
- [ ] Phase 3 — Scale
- [ ] Phase 4 — AI-Optimize

## Feature Lock Reference
<!-- Paste the feature name from FEATURE_LOCKS.json that you claimed -->
Feature: `_______________`
Agent/Developer: `_______________`

## Linked to Implementation Plan Section
<!-- e.g., "Module 1 § 1.1 — FastAPI Backend" -->
Section: `_______________`

## Changes
- [ ] Backend (FastAPI)
- [ ] Frontend (Next.js / PWA)
- [ ] Database (migrations)
- [ ] Infrastructure (Docker / CI)
- [ ] Documentation

## Pre-merge Checklist
- [ ] I read the relevant section of `docs/Lodge-Link_Implementation_Plan.md` before writing code
- [ ] My changes do not conflict with any active feature lock in `FEATURE_LOCKS.json`
- [ ] I have not hardcoded any country-specific values (ETB, Telebirr, etc.) — used config instead
- [ ] Tests pass locally (`pytest` for backend, `npm run lint` for frontend)
- [ ] No `.env` files or secrets committed
- [ ] I updated `FEATURE_LOCKS.json` to release my claim after this PR merges
EOF

success "GitHub Actions created"

# ─── Phase Detail Documents ───────────────────────────────────────────────────
info "Creating phase documents..."

cat > docs/phases/PHASE_1_MVP.md << 'EOF'
# Phase 1 — MVP Build Spec
**Duration:** Months 1–4 | **Goal:** 20 hotels live in Addis Ababa, 100 referral events

## Exit Criteria (ALL must pass before Phase 2 begins)
- [ ] 10+ live hotels with KYC approved
- [ ] 50+ real referral events logged in `platform.referral_events`
- [ ] End-to-end referral flow functional: initiate → notify → accept → handshake code
- [ ] Offline handshake code validates correctly without API call
- [ ] Median referral response time < 1,500ms (measured via CloudWatch)
- [ ] Zero trust score disputes in first 30 days of operation
- [ ] SMS notifications delivered for 95%+ of referral events

## Features to Build (Dashboard-Tier Only)
### Backend
- [ ] `POST /v1/referrals` — initiate referral fanout
- [ ] `GET  /v1/availability` — query available hotels (cached)
- [ ] `POST /v1/referrals/{id}/accept` — hotel B accepts
- [ ] `POST /v1/referrals/{id}/decline` — hotel B declines
- [ ] `GET  /v1/referrals/{id}/handshake` — validate offline code
- [ ] `POST /v1/hotels/availability` — update room availability (dashboard input)
- [ ] `POST /v1/auth/register` — hotel registration (sandbox key issued)
- [ ] `POST /v1/auth/token` — JWT login
- [ ] API key generation + SHA-256 hashing (NEVER plaintext)
- [ ] Redis availability cache (90s TTL)
- [ ] Celery + Redis webhook queue with exponential backoff
- [ ] AfricasTalking SMS dispatch on every referral event
- [ ] HMAC offline handshake code generator + PWA validator
- [ ] PostgreSQL: platform schema + hotel private schemas + RLS

### Frontend (PWA)
- [ ] Landing page (English + Amharic, mobile-first)
- [ ] Hotel KYC onboarding flow
- [ ] Emergency Referral Mode (3-tap: room type → results → refer)
- [ ] Availability room grid (visual toggle, dashboard-tier)
- [ ] Handshake code display + SMS send button
- [ ] Service Worker: cache last 50 referrals in IndexedDB
- [ ] Offline mode banner + local code validation UI
- [ ] Amharic font (Noto Sans Ethiopic)

### Infrastructure
- [ ] Docker Compose (local dev stack)
- [ ] GitHub Actions CI (lint + test + build)
- [ ] Alembic initial migrations
- [ ] AWS deployment (ECS Fargate + RDS + ElastiCache) — manual deploy acceptable for MVP
- [ ] CloudWatch logging + p95 latency alert (> 1s threshold)

## Branching Rules
All Phase 1 work branches from `develop`. Branch name format:
`phase1/{feature-name}` e.g. `phase1/referral-fanout`, `phase1/auth-system`

## DO NOT build in Phase 1
- Trust score computation (Phase 2)
- Webhook-Lite or API-First integrations (Phase 2)
- ML / predictive demand (Phase 4)
- Corridor partnerships (Phase 3)
- Multi-country support activation (schema exists, logic stays dormant)
EOF

cat > docs/phases/PHASE_2_BETA.md << 'EOF'
# Phase 2 — Beta Build Spec
**Duration:** Months 5–9 | **Unlocks after:** All Phase 1 exit criteria pass

## Exit Criteria
- [ ] 75+ live hotels across 3 Ethiopian cities
- [ ] 500+ referral events/month sustained for 2 consecutive months
- [ ] Trust scores published for all hotels with 10+ referral events
- [ ] Price dispute rate < 2%
- [ ] Webhook-Lite integration live and tested with 5+ hotels
- [ ] Nightly Celery beat trust score recomputation running without errors

## New Features
### Backend
- [ ] Trust score algorithm (5 components, Module 3 § 3.1)
- [ ] Nightly Celery beat job: `trust_recalculation.py`
- [ ] Guest feedback SMS survey system (post-checkout trigger)
- [ ] Price reconciliation post-stay flow
- [ ] Webhook-Lite: pre-built availability update widget endpoint
- [ ] Structured in-platform messaging (template-based only)
- [ ] PostGIS geo-radius hotel queries
- [ ] Scoped API key permissions enforced at middleware
- [ ] Read replica routing for analytics queries
- [ ] Hotel private schema auto-provisioning script

### Frontend
- [ ] Trust score breakdown dashboard per hotel
- [ ] Structured handshake messaging UI (template selection)
- [ ] Guest feedback survey page (SMS-linked, no login)
- [ ] Multi-city hotel map with geo-radius filter
- [ ] Demand alert banner (Meskel/Timkat warning 2 weeks ahead)
- [ ] Hotel analytics dashboard (referrals sent/received/fulfilled)
EOF

cat > docs/phases/PHASE_3_SCALE.md << 'EOF'
# Phase 3 — Scale Build Spec
**Duration:** Months 10–18 | **Unlocks after:** All Phase 2 exit criteria pass

## New Features
- API-First PMS integration framework
- Multi-country: Kenya (KE) region config activation
- Corridor API: ride-hailing partner integration
- Kafka event streaming for high-volume availability updates
- Partner developer portal (self-service sandbox)
- SOC 2 Type I readiness
EOF

cat > docs/phases/PHASE_4_AI.md << 'EOF'
# Phase 4 — AI-Optimize Build Spec
**Duration:** Months 19–30 | **Unlocks after:** All Phase 3 exit criteria pass

## New Features
- XGBoost occupancy forecasting model (MLflow-managed)
- Vibe Matching collaborative filtering
- ML microservice (separate FastAPI instance)
- Feature store (Redis-backed)
- 5-market East African expansion
- Digital Tourist Corridor API (unified package endpoint)
EOF

success "Phase documents created"

# ─── PHASE_STATUS.json ────────────────────────────────────────────────────────
cat > PHASE_STATUS.json << 'EOF'
{
  "_comment": "Single source of truth for build phase progression. Updated by team lead after exit criteria review. Agents READ this before starting work to know which phase is active.",
  "current_phase": 1,
  "phase_name": "MVP",
  "phase_start_date": null,
  "phases": {
    "1": {
      "name": "MVP",
      "status": "in_progress",
      "exit_criteria_passed": false,
      "unlocked_at": null,
      "completed_at": null,
      "spec_document": "docs/phases/PHASE_1_MVP.md"
    },
    "2": {
      "name": "Beta",
      "status": "locked",
      "exit_criteria_passed": false,
      "unlocked_at": null,
      "completed_at": null,
      "spec_document": "docs/phases/PHASE_2_BETA.md"
    },
    "3": {
      "name": "Scale",
      "status": "locked",
      "exit_criteria_passed": false,
      "unlocked_at": null,
      "completed_at": null,
      "spec_document": "docs/phases/PHASE_3_SCALE.md"
    },
    "4": {
      "name": "AI-Optimize",
      "status": "locked",
      "exit_criteria_passed": false,
      "unlocked_at": null,
      "completed_at": null,
      "spec_document": "docs/phases/PHASE_4_AI.md"
    }
  }
}
EOF

success "PHASE_STATUS.json created"

# ─── FEATURE_LOCKS.json ───────────────────────────────────────────────────────
cat > FEATURE_LOCKS.json << 'EOF'
{
  "_comment": "Feature claiming system. Before building any feature, an agent or developer MUST claim it here via a PR that updates this file. Prevents two agents building the same thing. Claimed features show agent_id and branch. Released = merged to develop.",
  "_instructions": "To claim: set status='claimed', add your agent_id (e.g. 'claude-dev-1' or 'fatima-laptop'), branch, and claimed_at. To release: set status='released', add released_at after your PR merges.",
  "phase_1": {
    "backend_auth_system": {
      "description": "JWT auth, hotel registration, API key generation + SHA-256 hashing",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 2 § 2.3 — KYC & API Key Architecture"
    },
    "backend_referral_fanout": {
      "description": "POST /v1/referrals, asyncio fanout, Redis cache, timeout handling",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 1 § 1.1 — FastAPI Fanout"
    },
    "backend_availability_api": {
      "description": "GET /v1/availability, POST /v1/hotels/availability, Redis TTL cache layer",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 1 § 1.1 — Availability Check"
    },
    "backend_handshake_system": {
      "description": "HMAC handshake code generator, offline validation endpoint, Celery SMS dispatch",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 6 § 6.2 — Offline Handshake"
    },
    "backend_database_schema": {
      "description": "Alembic migrations: platform schema, hotel private schemas, RLS policies, PostGIS",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 1 § 1.2 — PostgreSQL Schema"
    },
    "backend_celery_workers": {
      "description": "Celery app setup, webhook queue with exponential backoff, SMS worker",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 1 § 1.3 — Connectivity Resilience"
    },
    "frontend_landing_page": {
      "description": "Marketing landing page, English + Amharic, mobile-first, conversion CTA",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 4 § 4.1 — Landing Page"
    },
    "frontend_emergency_referral_ui": {
      "description": "3-tap Emergency Referral Mode, results list, trust score display",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 4 § 4.2 — Receptionist UI"
    },
    "frontend_availability_grid": {
      "description": "Visual room availability toggle grid for dashboard-tier hotels",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 2 § 2.1 — Level 3 Dashboard"
    },
    "frontend_onboarding_kyc": {
      "description": "Hotel KYC registration flow, document upload, sandbox activation screen",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 2 § 2.3 — KYC Requirements"
    },
    "frontend_pwa_offline": {
      "description": "Service Worker setup, IndexedDB cache for 50 referrals, offline banner, local code validation",
      "status": "available",
      "agent_id": null,
      "branch": null,
      "claimed_at": null,
      "released_at": null,
      "plan_ref": "Module 6 § 6.2 — Offline Handshake"
    },
    "infrastructure_docker": {
      "description": "Dockerfiles for backend + frontend, docker-compose.yml, init_db.sql",
      "status": "released",
      "agent_id": "bootstrap-script",
      "branch": "main",
      "claimed_at": "bootstrap",
      "released_at": "bootstrap",
      "plan_ref": "Module 8 — Phase 1 Infrastructure"
    },
    "infrastructure_ci_github_actions": {
      "description": "GitHub Actions CI: lint, type-check, test, build for backend + frontend",
      "status": "released",
      "agent_id": "bootstrap-script",
      "branch": "main",
      "claimed_at": "bootstrap",
      "released_at": "bootstrap",
      "plan_ref": "Module 8 — Phase 1 Infrastructure"
    }
  }
}
EOF

success "FEATURE_LOCKS.json created"

# ─── CLAUDE.md (The Agent's Bible) ───────────────────────────────────────────
info "Writing CLAUDE.md — the agent coordination file..."

cat > CLAUDE.md << 'CLAUDEMD'
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
CLAUDEMD

success "CLAUDE.md written"

# ─── AGENTS.md ────────────────────────────────────────────────────────────────
cat > AGENTS.md << 'EOF'
# AGENTS.md — Multi-Agent Collaboration Protocol
**Lodge-Link Development Team**

This document defines how multiple AI agents (and human developers) work on this codebase simultaneously without logical conflicts.

---

## The Golden Rule
**The `docs/Lodge-Link_Implementation_Plan.md` is the constitution. `PHASE_STATUS.json` is the law. `FEATURE_LOCKS.json` is the traffic controller.**

When in doubt, a feature's behavior is whatever the Implementation Plan says it should be, scoped to the active phase.

---

## Agent Identity
Each agent session must have a unique `agent_id`. Use the format: `{name}-{machine}`.
Examples: `claude-fatima-laptop`, `claude-abel-desktop`, `claude-dev-1`

This ID goes in `FEATURE_LOCKS.json` when you claim a feature.

---

## The Feature Claim Protocol (Mandatory)

### Step 1 — Before touching any code
```bash
# Read current phase
cat PHASE_STATUS.json

# Read available features for current phase
cat FEATURE_LOCKS.json
```

### Step 2 — Claim your feature
Create a tiny PR that ONLY updates `FEATURE_LOCKS.json`:
```json
"backend_referral_fanout": {
  "status": "claimed",
  "agent_id": "claude-abel-desktop",
  "branch": "phase1/referral-fanout",
  "claimed_at": "2025-01-15T09:00:00Z",
  "released_at": null
}
```

### Step 3 — Build the feature on your branch
Branch: `phase1/{feature-name}`

### Step 4 — Release the claim on merge
When your PR merges to `develop`, update the entry:
```json
"status": "released",
"released_at": "2025-01-18T14:30:00Z"
```

---

## Conflict Prevention Rules

| Scenario | Rule |
|---|---|
| Two agents want the same feature | First to have a merged claim PR wins. Second agent picks another available feature. |
| Agent is blocked waiting for another feature | Check if any other `"available"` feature unblocks you. If genuinely blocked, flag in PR comments — don't build the dependency yourself without claiming it. |
| Feature has no owner and is urgently needed | Team lead can force-claim it in `FEATURE_LOCKS.json` directly to `main`. |
| Agent gets abandoned mid-feature | After 48h of no commit activity on a claimed feature, the claim can be revoked by team lead. |

---

## Module Ownership (Default Assignment Guidance)

These are suggestions, not locks. Check `FEATURE_LOCKS.json` for actual claims.

| Module | Suggested Team |
|---|---|
| Backend API + Database | Backend agents |
| Frontend PWA + i18n | Frontend agents |
| Celery workers + SMS | Backend agents |
| Docker / CI / Infrastructure | DevOps lead |
| CLAUDE.md / AGENTS.md / Docs | Team lead only |

---

## Shared State — What Everyone Must Read Every Session
1. `CLAUDE.md` — always (auto-read by Claude Code)
2. `PHASE_STATUS.json` — before starting work
3. `FEATURE_LOCKS.json` — before claiming or building anything
4. The relevant section of `docs/Lodge-Link_Implementation_Plan.md`

---

## What Happens When Phase 1 Is Done?
A human team lead reviews all Phase 1 exit criteria (defined in `docs/phases/PHASE_1_MVP.md`).
If all boxes are checked, they update `PHASE_STATUS.json`:
```json
"1": { "status": "completed", "completed_at": "2025-05-01T00:00:00Z" },
"2": { "status": "in_progress", "unlocked_at": "2025-05-01T00:00:00Z" }
"current_phase": 2
```
Agents automatically operate under Phase 2 rules from that point forward.
EOF

success "AGENTS.md written"

# ─── .env.example ────────────────────────────────────────────────────────────
cat > backend/.env.example << 'EOF'
# Copy to .env and fill in values. Never commit .env.
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=generate-a-strong-random-key-here

# Database (local Docker default)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link

# Redis (local Docker default)
REDIS_URL=redis://localhost:6379/0

# AfricasTalking SMS Gateway (get from africastalking.com)
AT_USERNAME=sandbox
AT_API_KEY=your-africastalking-api-key
AT_SENDER_ID=LodgeLink

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Platform defaults (do not change without updating region_configs table)
DEFAULT_COUNTRY=ET
DEFAULT_CURRENCY=ETB
EOF

success ".env.example created"

# ─── README.md ────────────────────────────────────────────────────────────────
cat > README.md << 'EOF'
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
EOF

success "README.md created"

# ─── Git Commit & Push ────────────────────────────────────────────────────────
echo ""
info "Staging all files..."
git add -A

info "Creating initial commit..."
git commit -m "chore: bootstrap Lodge-Link project scaffold

- Full directory structure (backend/frontend/infrastructure)
- FastAPI backend skeleton with config, main.py, Dockerfile
- Next.js frontend skeleton with i18n, TypeScript, PWA config
- Docker Compose: PostgreSQL 16 + PostGIS, Redis, FastAPI, Celery, Next.js
- GitHub Actions CI: backend tests + frontend lint
- CLAUDE.md: agent coordination and architecture rules
- AGENTS.md: multi-agent feature lock protocol
- PHASE_STATUS.json: phase progression tracker (Phase 1 active)
- FEATURE_LOCKS.json: feature claiming system (all Phase 1 features available)
- docs/Lodge-Link_Implementation_Plan.md: master architecture document
- docs/phases/: per-phase build specs with exit criteria
- .env.example: documented environment variables
- .gitignore: comprehensive ignore rules

Co-authored-by: Lodge-Link Bootstrap Script"

info "Adding remote origin..."
git remote add origin "$GITHUB_REPO" 2>/dev/null || git remote set-url origin "$GITHUB_REPO"

info "Pushing to GitHub..."
git push -u origin main

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗"
echo -e "║   Bootstrap Complete! 🚀                 ║"
echo -e "╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${CYAN}Repository:${RESET} $GITHUB_REPO"
echo -e "  ${CYAN}Phase:${RESET}      1 (MVP) — All features available to claim"
echo -e "  ${CYAN}Next step:${RESET}  See AGENT_PROMPT.md for the first agent prompt"
echo ""
echo -e "  ${YELLOW}Team members: clone the repo, then run:${RESET}"
echo -e "  git clone $GITHUB_REPO"
echo -e "  cp backend/.env.example backend/.env"
echo -e "  docker-compose up -d"
echo ""