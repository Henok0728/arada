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
