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
