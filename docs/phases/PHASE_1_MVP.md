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
