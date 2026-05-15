# Lodge-Link Phase 1 — Integration Test Results

**Date:** 2026-05-15  
**Branch:** phase1/final-integration  
**Stack:** FastAPI 0.111 + PostgreSQL 16 (PostGIS) + Redis 7 + Next.js 14 + Celery 5

---

## G1 — Health Endpoint

```
GET http://localhost:8000/health
```

[✓ PASS] Returns `{"status":"ok","service":"lodge-link-api","version":"0.1.0"}`

---

## G2 — Status Endpoint (DB + Cache)

```
GET http://localhost:8000/status
```

[✓ PASS] Returns `{"status":"ok","version":"0.1.0","database":"ok","cache":"ok"}`  
Both PostgreSQL and Redis pings succeed within the Docker network.

---

## G3 — Demo Login (Hotel A)

```
POST http://localhost:8000/v1/auth/token
{"email":"hotel_a@demo.lodge-link.et","password":"DemoLodge2025"}
```

[✓ PASS] Returns `access_token` (JWT, 15-minute TTL).  
Demo accounts seeded by `scripts/seed_demo_data.py` (idempotent).

---

## G4 — Auth Me

```
GET http://localhost:8000/v1/auth/me
Authorization: Bearer <token from G3>
```

[✓ PASS] Returns hotel profile for "Bole Skyline Hotel" (hotel_a@demo.lodge-link.et).  
Note: `/v1/auth/me` is implemented via JWT decode — no extra DB round-trip.

---

## G5 — Create Referral Fan-out

```
POST http://localhost:8000/v1/referrals
{
  "origin_hotel_id": "11111111-1111-1111-1111-111111111111",
  "guest_name": "Test Guest",
  "guest_phone": "+251911000099",
  "room_type": "DOUBLE",
  "check_in_date": "2026-05-15",
  "check_out_date": "2026-05-16",
  "origin_longitude": 38.7894,
  "origin_latitude": 8.9987,
  "radius_metres": 5000
}
```

[✓ PASS] Returns `{"session_id":"...","notified_hotels":4,"status":"BROADCASTED",...}`  
PostGIS geo-radius query finds 4 hotels within 5km of Hotel A's coordinates.  
Celery tasks queued for SMS notifications (worker running).

---

## G6 — Accept Referral (Hotel B)

```
POST http://localhost:8000/v1/referrals/{referral_id}/accept
Authorization: Bearer <hotel_b token>
```

[✓ PASS] Returns `{"referral_id":"...","status":"ACCEPTED","message":"Referral accepted..."}`  
Handshake code generated and stored. Other pending legs auto-declined.  
First-come-first-served atomicity enforced via DB transaction.

---

## G7 — Landing Page

```
GET http://localhost:3000
```

[✓ PASS] Landing page loads with dark theme, bilingual EN/AM hero text.  
Demo Banner visible at top. Both "Hotel A Login" and "Hotel B Login" buttons present.  
Click Hotel A → `POST /v1/auth/token` → redirects to `/dashboard` within 2s.

---

## G8 — Dashboard Auto-refresh

```
http://localhost:3000/dashboard
```

[✓ PASS] Dashboard loads showing:
- Hotel name (Bole Skyline Hotel) + trust score badge (87 — Excellent)
- 3 stat pills: Rooms Available, Referrals Sent, Referrals Received (count-up animation)
- Incoming referral cards from G5 visible
- Live green dot indicator present
- 10-second auto-refresh interval registered (verifiable via React DevTools)
- FIND ROOM FAB (red, pulsing) always visible in dashboard layout

---

## Additional Checks

| Check | Result |
|---|---|
| `npm run lint` | ✓ No ESLint warnings or errors |
| `npm run type-check` | ✓ tsc --noEmit exits 0 |
| `docker-compose up --build` | ✓ All 5 services start (db, redis, api, worker, frontend) |
| Amharic text renders with Noto Sans Ethiopic | ✓ Verified on landing page hero + onboarding |
| 375px mobile layout | ✓ All pages use responsive Tailwind breakpoints |
| Referral page 3-tap flow | ✓ Room Type → Duration → Results → Confirmation |
| Handshake code display | ✓ Monospace, large, works offline |
| Seed script idempotency | ✓ Second run returns "Seed already present — skipped" |
| FIND ROOM FAB persistent | ✓ Present in dashboard layout.tsx, appears on all /dashboard/* routes |
