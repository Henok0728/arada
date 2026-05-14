# Lodge-Link: Comprehensive B2B Middleware Implementation Plan
### A Production-Grade "Referral Switch" for the Ethiopian Hospitality & Tourism Sector
**Document Version:** 1.0 | **Classification:** Internal Architecture & Strategy | **Audience:** Engineering, Product, and Business Leadership

---

> **North Star Principle:** This platform is not a booking engine. It is a **trust infrastructure layer** — invisible when it works, and catastrophic when it doesn't. Every architectural decision must be evaluated against two criteria: *reliability* and *data integrity*.

---

## Table of Contents

1. [Module 1: Core Technical Requirements & Frameworks](#module-1)
2. [Module 2: The Middleware & Integration Strategy](#module-2)
3. [Module 3: The Trust & Collaboration Engine](#module-3)
4. [Module 4: Landing Page & B2B UX](#module-4)
5. [Module 5: Future ML & "Smarties" Integration](#module-5)
6. [Module 6: The Ethiopian Context Implementation](#module-6)
7. [Module 7: Scaling & Long-term Roadmap](#module-7)
8. [Module 8: Phased Development Plan](#module-8)

---

<a name="module-1"></a>
## MODULE 1: Core Technical Requirements & Frameworks

### 1.1 — The Backend: FastAPI (Python) as the Referral Switch Engine

#### Why FastAPI Is Non-Negotiable for This Use Case

A hotel referral API is fundamentally a **fanout problem**: when Hotel A marks itself as full, the system must simultaneously query Hotels B, C, D, and E for availability, compare results, apply trust scoring, and return a ranked list — all within a window that feels instantaneous to the receptionist on the other end (target: < 800ms end-to-end).

Synchronous frameworks like Flask would block the thread on each outbound availability check. FastAPI's **ASGI-native async/await** model handles all five hotel checks concurrently on a single thread via the event loop, collapsing 5× 200ms checks into a single ~200ms round-trip wall time.

**Type Hinting as a Contract Layer:**
FastAPI uses Pydantic models for request/response validation. In a multi-tenant B2B platform where one malformed payload from Hotel A's PMS could corrupt Hotel B's referral queue, Pydantic's runtime validation is not a convenience — it is a **data integrity firewall**. Every payload that enters or exits the system is validated against a strict schema before any database write occurs.

#### Core Stack Specification

```
Runtime:         Python 3.11+ (asyncio native)
Framework:       FastAPI 0.111+
ASGI Server:     Uvicorn + Gunicorn (multi-worker)
Process Manager: Supervisor (production) / Docker (containerized)
Task Queue:      Celery + Redis (async background jobs)
Cache Layer:     Redis 7 (availability TTL cache, session store)
API Gateway:     Kong or AWS API Gateway (rate limiting, auth)
```

#### Application Structure

```
lodge_link/
├── api/
│   ├── v1/
│   │   ├── routers/
│   │   │   ├── referrals.py         # Core referral switch logic
│   │   │   ├── availability.py      # Hotel availability polling
│   │   │   ├── hotels.py            # Hotel management endpoints
│   │   │   ├── trust.py             # Trust score endpoints
│   │   │   └── handshakes.py        # Collaboration confirmations
│   │   └── dependencies.py          # Auth, tenant resolution
├── core/
│   ├── config.py                    # Settings (pydantic-settings)
│   ├── security.py                  # Key hashing, HMAC validation
│   └── exceptions.py                # Domain-specific exceptions
├── db/
│   ├── models/                      # SQLAlchemy ORM models
│   ├── repositories/                # Data access layer (no raw SQL in routes)
│   └── migrations/                  # Alembic migration scripts
├── schemas/
│   ├── referral.py                  # Pydantic request/response models
│   ├── hotel.py
│   └── trust.py
├── services/
│   ├── referral_engine.py           # Core fanout & matching logic
│   ├── trust_calculator.py          # Trust score computation
│   ├── notification.py              # SMS/push/webhook dispatch
│   └── cache_manager.py             # Redis availability cache
└── workers/
    ├── availability_sync.py         # Periodic PMS polling
    └── trust_recalculation.py       # Nightly trust score refresh
```

#### The Referral Fanout: Concurrency in Practice

```python
# services/referral_engine.py

import asyncio
import httpx
from typing import List
from schemas.referral import ReferralRequest, HotelAvailabilityResult
from services.cache_manager import CacheManager
from db.repositories.hotel_repo import HotelRepository

async def fetch_single_hotel_availability(
    client: httpx.AsyncClient,
    hotel: dict,
    request: ReferralRequest,
    cache: CacheManager
) -> HotelAvailabilityResult | None:
    """
    Check one hotel's availability. Checks Redis cache first (TTL: 90 seconds).
    Falls back to live API call with a hard 3-second timeout.
    """
    cache_key = f"avail:{hotel['id']}:{request.check_in}:{request.check_out}:{request.room_type}"
    
    cached = await cache.get(cache_key)
    if cached:
        return HotelAvailabilityResult(**cached, source="cache")
    
    try:
        response = await client.post(
            hotel["webhook_url"],
            json=request.model_dump(),
            headers={"X-Lodge-Link-Key": hotel["outbound_key"]},
            timeout=3.0   # Hard wall: never let one slow hotel block the fanout
        )
        result = HotelAvailabilityResult(**response.json(), hotel_id=hotel["id"])
        await cache.set(cache_key, result.model_dump(), ttl=90)
        return result
    except (httpx.TimeoutException, httpx.ConnectError):
        # Do not raise. Log and return None. Partial results > no results.
        await log_connectivity_event(hotel["id"], "timeout")
        return None

async def execute_referral_fanout(
    request: ReferralRequest,
    candidate_hotels: List[dict],
    cache: CacheManager
) -> List[HotelAvailabilityResult]:
    """
    Fan out to all candidate hotels concurrently. Return only hotels with
    confirmed availability, sorted by trust score descending.
    """
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_single_hotel_availability(client, hotel, request, cache)
            for hotel in candidate_hotels
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Filter out timeouts (None) and sort by composite score
    available = [r for r in results if r is not None and r.has_availability]
    available.sort(key=lambda h: (h.trust_score, -h.price_delta), reverse=True)
    return available
```

---

### 1.2 — The Database: PostgreSQL Multi-Tenancy Schema

#### Tenancy Model: Schema-Per-Tenant (Hybrid Approach)

For a B2B platform where **"a competitor must never see your data"** is a legal and trust promise, we reject the naive row-level tenant column approach (`WHERE tenant_id = X`) as insufficient alone. We implement a **hybrid model**:

- **Shared Schema** for platform-wide data (trust scores, referral links between hotels, public availability signals)
- **Private Schema per hotel** for their internal booking data, rate configurations, and guest contact details

This provides both the operational simplicity of a shared database and the hard data isolation of schema separation.

```sql
-- ============================================================
-- PLATFORM SCHEMA (Shared, Platform-Managed)
-- ============================================================

CREATE SCHEMA platform;

-- Core hotel registry
CREATE TABLE platform.hotels (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                TEXT UNIQUE NOT NULL,          -- 'blue-nile-lodge'
    display_name        TEXT NOT NULL,
    city                TEXT NOT NULL,
    region              TEXT NOT NULL,
    geo_point           GEOGRAPHY(POINT, 4326),        -- PostGIS for radius queries
    tier                TEXT CHECK (tier IN ('budget', 'mid', 'premium', 'luxury')),
    integration_level   TEXT CHECK (integration_level IN ('api', 'webhook', 'dashboard')),
    is_active           BOOLEAN DEFAULT FALSE,         -- Requires KYC approval
    kyc_verified_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- API key registry (hashed; never stored in plaintext)
CREATE TABLE platform.api_keys (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id            UUID NOT NULL REFERENCES platform.hotels(id) ON DELETE CASCADE,
    key_hash            TEXT NOT NULL UNIQUE,          -- SHA-256(key_prefix + secret)
    key_prefix          TEXT NOT NULL,                 -- 'll_live_' or 'll_test_'
    environment         TEXT CHECK (environment IN ('live', 'sandbox')),
    scopes              TEXT[] NOT NULL DEFAULT '{}',  -- ['referral:read', 'availability:write']
    last_used_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_keys_hash ON platform.api_keys (key_hash);

-- Trust scores (computed nightly, visible platform-wide)
CREATE TABLE platform.trust_scores (
    hotel_id            UUID PRIMARY KEY REFERENCES platform.hotels(id),
    composite_score     NUMERIC(4,2) CHECK (composite_score BETWEEN 0 AND 100),
    fulfillment_rate    NUMERIC(5,4),  -- 0.0 to 1.0
    price_honesty_score NUMERIC(4,2),
    response_time_p50   INTEGER,       -- milliseconds
    guest_feedback_avg  NUMERIC(3,2),
    referral_volume_30d INTEGER,
    computed_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Referral events (the core ledger)
CREATE TABLE platform.referral_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_hotel_id     UUID NOT NULL REFERENCES platform.hotels(id),
    destination_hotel_id UUID NOT NULL REFERENCES platform.hotels(id),
    guest_token         TEXT NOT NULL,   -- Anonymized guest ID (no PII here)
    room_type           TEXT NOT NULL,
    check_in            DATE NOT NULL,
    check_out           DATE NOT NULL,
    quoted_rate_etb     NUMERIC(10,2),
    status              TEXT CHECK (status IN ('pending', 'accepted', 'declined', 'fulfilled', 'no_show')),
    handshake_code      TEXT UNIQUE,     -- 6-digit offline handshake code
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

-- Corridor partners (future: ride-hailing, tour guides)
CREATE TABLE platform.corridor_partners (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_type        TEXT CHECK (partner_type IN ('ride_hailing', 'tour_guide', 'restaurant', 'activity')),
    partner_name        TEXT NOT NULL,
    api_endpoint        TEXT,
    is_active           BOOLEAN DEFAULT FALSE,
    coverage_regions    TEXT[]
);

-- ============================================================
-- PER-HOTEL PRIVATE SCHEMA (Created during KYC onboarding)
-- Schema name: hotel_{hotel_slug}
-- Example: hotel_blue_nile_lodge
-- ============================================================

-- Template for dynamic schema creation (executed via migration script)
CREATE SCHEMA hotel_{slug};

-- Internal rate configuration (NEVER exposed to platform schema)
CREATE TABLE hotel_{slug}.rate_configs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_type           TEXT NOT NULL,
    base_rate_etb       NUMERIC(10,2) NOT NULL,
    weekend_multiplier  NUMERIC(4,2) DEFAULT 1.0,
    seasonal_rules      JSONB,           -- {timkat: 1.4, meskel: 1.3}
    max_referral_discount NUMERIC(4,2) DEFAULT 0.0,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Internal booking ledger (isolated, hotel-owned)
CREATE TABLE hotel_{slug}.bookings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    referral_event_id   UUID,           -- FK to platform.referral_events (soft link)
    guest_name          TEXT,
    guest_phone         TEXT,           -- Encrypted at rest (pgcrypto)
    room_number         TEXT,
    check_in            DATE NOT NULL,
    check_out           DATE NOT NULL,
    rate_etb            NUMERIC(10,2),
    source              TEXT CHECK (source IN ('direct', 'lodgelink_referral', 'walk_in')),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Row-Level Security: Belt-and-suspenders even within the private schema
ALTER TABLE hotel_{slug}.bookings ENABLE ROW LEVEL SECURITY;
CREATE POLICY hotel_isolation ON hotel_{slug}.bookings
    USING (current_setting('app.current_hotel_slug') = '{slug}');
```

#### Connection Pool & Tenant Routing

```python
# db/tenant_router.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings

async def get_tenant_session(hotel_slug: str) -> AsyncSession:
    """
    Sets the PostgreSQL session variable before any query executes.
    This activates Row Level Security policies automatically.
    """
    engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as session:
        # Set tenant context — RLS policies read this
        await session.execute(
            f"SET app.current_hotel_slug = '{hotel_slug}'"
        )
        yield session
```

---

### 1.3 — Connectivity Resilience: The Ethiopian Market Fallback Strategy

Internet connectivity in Ethiopia varies significantly: Addis Ababa may have stable 4G/fiber, while lodges in Lalibela, Simien Mountains, or Omo Valley operate on 2G/intermittent satellite. The platform must never be **binary** (fully up or fully broken).

#### The Three-Layer Resilience Stack

**Layer 1: Aggressive Client-Side Caching (Redis TTL)**
Availability data is cached at the API Gateway layer with a 90-second TTL. A hotel with a connectivity blip still serves referral results from cache for up to 90 seconds without the client experiencing failure.

**Layer 2: Outbound Webhook Queue (Celery + Redis)**
When Lodge-Link needs to notify Hotel B of an incoming referral and Hotel B's connection is down, the notification is not lost — it is enqueued in a **persistent Redis queue** with exponential backoff retry (1s → 2s → 4s → 8s → max 15 min). As soon as Hotel B reconnects, the message delivers automatically.

```python
# workers/availability_sync.py

from celery import Celery
from celery.utils.log import get_task_logger

app = Celery('lodge_link', broker='redis://redis:6379/0', backend='redis://redis:6379/1')
logger = get_task_logger(__name__)

@app.task(
    bind=True,
    max_retries=8,
    default_retry_delay=2,     # seconds, doubles each retry
    acks_late=True,            # Message not removed from queue until task succeeds
    reject_on_worker_lost=True # Re-queue if worker dies mid-task
)
def dispatch_referral_notification(self, hotel_id: str, referral_event_id: str):
    """
    Send referral notification to a hotel's webhook endpoint.
    Retries with exponential backoff for up to ~68 minutes.
    """
    try:
        hotel = get_hotel_config(hotel_id)
        payload = build_referral_payload(referral_event_id)
        response = send_webhook(hotel["webhook_url"], payload)
        response.raise_for_status()
        logger.info(f"Referral {referral_event_id} delivered to hotel {hotel_id}")
    except Exception as exc:
        wait = 2 ** self.request.retries  # Exponential backoff
        logger.warning(f"Retry {self.request.retries} for hotel {hotel_id}: {exc}")
        raise self.retry(exc=exc, countdown=wait)
```

**Layer 3: The Offline Handshake Code (Zero-Internet Fallback)**
This is the most important resilience feature for the Ethiopian context. When a guest is referred to Hotel B and arrives with no internet available, the physical handshake code (generated at referral creation and printed/SMS'd to the guest) serves as proof of referral. See Module 6 for full detail.

**Layer 4: SMS as the Transport Layer**
For dashboard-tier hotels in low-connectivity areas, the referral notification is also dispatched via SMS using a local Ethiopian SMS gateway (e.g., **AfricasTalking Ethiopia** or **Ethio Telecom SMS API**). This guarantees delivery even when data is unavailable.

```python
# services/notification.py

async def dispatch_referral_notification(
    hotel: Hotel,
    referral: ReferralEvent
) -> None:
    """
    Multi-channel notification with SMS as guaranteed fallback.
    """
    # Attempt 1: Webhook (instant, data-dependent)
    dispatch_referral_notification.delay(hotel.id, referral.id)  # Celery task
    
    # Attempt 2: SMS (always sent, data-independent)
    sms_body = (
        f"LodgeLink: Guest arriving from {referral.source_hotel.display_name}. "
        f"Room type: {referral.room_type}. "
        f"Code: {referral.handshake_code}. "
        f"Check-in: {referral.check_in}."
    )
    await sms_gateway.send(to=hotel.manager_phone, body=sms_body)
```

---

<a name="module-2"></a>
## MODULE 2: The Middleware & Integration Strategy

### 2.1 — Three Integration Levels

The Ethiopian hotel market is deeply heterogeneous. A one-size-fits-all API integration would exclude 80% of potential partners. We meet hotels where they are.

#### Level 1: API-First (Modern PMS Integration)

**Target Hotels:** Premium chains, Marriott-affiliated properties, Radisson, and any hotel running OPERA, Mews, Cloudbeds, or a custom PMS.

**How It Works:** The hotel's PMS sends real-time availability updates to Lodge-Link via a bidirectional REST API. Lodge-Link receives live webhooks on every booking/cancellation and maintains a sub-minute-fresh availability state.

```
Hotel PMS ──POST /v1/availability/update──► Lodge-Link API
Lodge-Link ──GET  /v1/referrals/incoming──► Hotel PMS (via registered webhook)
```

**Technical Requirements from the Hotel:**
- Ability to register a webhook endpoint that Lodge-Link can call
- Ability to parse a standardized Lodge-Link JSON payload
- Maintenance of an API key rotation schedule

#### Level 2: Webhook-Lite (Mid-Tier Integration)

**Target Hotels:** Independent 20–80 room hotels with basic software (Excel, simple booking software, Booking.com admin panel). They cannot modify their software but they have a smartphone and stable enough internet.

**How It Works:** Lodge-Link provides a **pre-built integration widget** — a small JavaScript snippet or a mobile-friendly URL. The hotel manager opens a Lodge-Link dashboard shortcut on their phone morning/evening and clicks "Update Availability" — a form that takes 45 seconds to complete. Lodge-Link polls these updates every 30 minutes and caches them.

Outbound referrals arrive via **Webhook to a Lodge-Link-hosted endpoint**, not the hotel's own server. The hotel pulls referrals from the Lodge-Link dashboard.

#### Level 3: The Web Dashboard (Zero-Tech Integration)

**Target Hotels:** Guesthouses, eco-lodges, and family-run establishments in Lalibela, Axum, or Arbaminch with minimal digital infrastructure. The manager has a phone but no computer literacy beyond WhatsApp.

**How It Works:** Fully managed through the Lodge-Link web dashboard, which is a Progressive Web App (PWA) installable on any Android phone. The receptionist marks rooms available/unavailable by tapping a visual room grid (no text input required). Referral notifications arrive as SMS + in-app alerts. Confirmations are done with a single "Accept" button.

The receptionist never writes code. They never touch an API. Their entire interaction model is: **mark rooms → receive alerts → tap Accept → see handshake code**.

---

### 2.2 — API Key Architecture

#### Key Types and Scopes

```
Key Format:  ll_{environment}_{random_base62_48chars}
Examples:
  ll_live_4mK9xPqR2nVwZb1cDfHjLsYeGiNtOuA3kXmBvWz7pQ8rCdEhJl
  ll_test_2aB5nMkRvXqZwPjLcDhGiYeNtOuA9kFmBvWz3pQ7rCdEhJlS1xT
```

**Never store the key itself. Store only `SHA-256(key_prefix + "." + secret_portion)`.**

| Key Type | Prefix | Scope | Use Case |
|---|---|---|---|
| Live Secret Key | `ll_live_` | Full scopes | Server-to-server API calls from PMS |
| Test Secret Key | `ll_test_` | Full scopes (sandbox data) | Development & integration testing |
| Live Public Key | `ll_pub_live_` | `availability:read` only | Dashboard frontend (safe to expose) |
| Webhook Signing Secret | `ll_whsec_` | N/A (HMAC signing only) | Verify incoming webhooks from Lodge-Link |
| Partner Key | `ll_partner_` | `corridor:read`, `referral:create` | Ride-hailing and tour guide partners |

**Available Scopes:**
```
availability:read          # Query room availability
availability:write         # Update room availability
referral:create            # Initiate a referral to another hotel
referral:read              # View incoming/outgoing referrals
referral:confirm           # Accept or decline incoming referrals
trust:read                 # Read public trust scores
analytics:read             # Access own performance analytics
admin:hotels               # Manage hotel profile (restricted to platform admins)
corridor:read              # Access corridor partner data (future)
```

---

### 2.3 — KYC Requirements for Live Key Issuance

A sandbox key is issued instantly. A **live key** requires completing a structured KYC process. This is not bureaucracy — it is the mechanism by which the platform's trust network maintains its integrity. A hotel that can vanish without accountability destroys the trust of every other hotel on the platform.

#### KYC Gate Requirements

**Tier 1 (Sandbox Key — Instant):**
- Valid business email
- Phone number (SMS verified)
- Hotel name and city declared

**Tier 2 (Live Key — 3–5 Business Days):**

*Legal Verification:*
- Business Registration Certificate (from Ethiopian Ministry of Trade)
- Tax Identification Number (TIN)
- Operating License from Ethiopian Tourism Organization (ETO)
- Manager's National ID (Kebele ID or Passport)

*Operational Verification:*
- Minimum 6 months of operating history OR two existing platform hotel endorsements
- Physical address verification (GPS coordinates + street photo)
- 3 confirmed test referral cycles completed in sandbox

*Platform Agreement:*
- Signed Lodge-Link Partner Agreement (digital signature via DocuSign)
- Agreement to referral commission rate (1.5–3% of first night's rate)
- Agreement to referral response SLA (must respond to incoming referral within 15 minutes during business hours)

*Technical Readiness (API/Webhook levels only):*
- Successful completion of webhook endpoint validation test
- Rate configuration submitted and reviewed

---

<a name="module-3"></a>
## MODULE 3: The Trust & Collaboration Engine

### 3.1 — The Trust Score Algorithm

The trust score is the **invisible hand** that sorts referral results. A hotel with a score of 87 appears before a hotel with a score of 62, even if the lower-scoring hotel is slightly cheaper. The score is recomputed nightly using the previous 90-day window of activity. A minimum of 10 referral events is required before a score is published (cold start = NULL, displayed as "New Partner").

#### Composite Score Formula

```
Trust Score = (
    (Fulfillment Rate     × 0.35) +   -- Highest weight: Did you actually take the guest?
    (Response Time Score  × 0.20) +   -- Did you respond within 15 minutes?
    (Price Honesty Score  × 0.20) +   -- Did the guest pay what was quoted?
    (Guest Feedback Score × 0.15) +   -- What did guests say about the referred stay?
    (Volume Bonus         × 0.10)     -- Rewarding consistent, active partners
) × 100
```

#### Component Definitions

**1. Fulfillment Rate (35%)**
`referrals_with_status='fulfilled' / total_referrals_accepted`

A hotel that accepts referrals but consistently has "no room available when the guest arrives" is the single most damaging failure mode. This metric destroys trust between hotels faster than anything else.

**2. Response Time Score (20%)**
Based on median time between referral notification and hotel's Accept/Decline action during business hours (7am–10pm local time).
```
< 5 minutes:   Score = 1.0
5–15 minutes:  Score = 0.8
15–30 minutes: Score = 0.5
> 30 minutes:  Score = 0.2
No response:   Score = 0.0 (and referral is auto-re-routed)
```

**3. Price Honesty Score (20%)**
Post-stay reconciliation: the guest is asked (via SMS) "Did you pay approximately [quoted_rate_etb] ETB per night?" Binary response (Yes/No). 
`price_honesty_score = positive_responses / total_responses`

This is critical for Ethiopian market trust. Price surprises at check-in are a known pain point that destroys cross-referral confidence.

**4. Guest Feedback Score (15%)**
A 5-question SMS survey sent 24 hours post-checkout (kept to 5 questions to maximize response rate). Scored 1–5 and normalized to 0–1. Questions focus on: cleanliness, reception attitude, value-for-money, room accuracy, and likelihood to return.

**5. Volume Bonus (10%)**
Logarithmic scale rewarding consistency, not just volume:
```
< 5 referrals/month:  Bonus = 0.0
5–15/month:           Bonus = 0.3
15–30/month:          Bonus = 0.7
30+/month:            Bonus = 1.0
```

#### Trust Score Decay & Penalties

- A score older than 90 days of inactivity decays at 0.5 points/week
- A single **verified fraud event** (e.g., guest charged significantly more than quoted) triggers an immediate score suspension and manual review
- Three unfulfilled referrals in a 30-day window triggers an automated "Probation" flag and a reduced visibility penalty

---

### 3.2 — Collaboration Tools: The In-Platform Handshake System

Hotels must communicate to confirm referrals without exposing their private WhatsApp numbers, direct phone lines, or internal pricing logic to each other.

#### The "Handshake" Protocol

**Step 1: Referral Initiated**
Hotel A's receptionist initiates a referral via dashboard. Lodge-Link generates:
- A unique **Referral ID** (internal UUID)
- A **Handshake Code** (6-character alphanumeric, e.g., `HTL-7K2M`) — human-speakable over phone if needed
- A **Guest Token** (anonymized, no PII transmitted between hotels)

**Step 2: Hotel B Receives Notification**
Hotel B sees in their Lodge-Link dashboard:
- Guest arrival details (room type, check-in/out dates, party size)
- Quoted rate range from Hotel A's request
- Guest tier (budget / standard / premium) — derived from Hotel A's assessment, no PII
- A 15-minute countdown timer

Hotel B does **not** see: Guest's name, phone number, email, or Hotel A's internal booking details.

**Step 3: Handshake Confirmation**
When Hotel B accepts:
- Lodge-Link sends Hotel A a confirmation with the Handshake Code
- Lodge-Link sends the guest (via Hotel A) the Handshake Code + Hotel B's public info
- The guest presents the Handshake Code at Hotel B's reception
- Hotel B's receptionist validates the code in the dashboard (one-tap) → referral marked `fulfilled`

**Step 4: Post-Stay Reconciliation**
48 hours after check-out date:
- SMS survey sent to guest (anonymized link)
- Price reconciliation prompt to Hotel B (did guest pay quoted rate Y/N)
- Both responses feed into trust score update

#### In-Platform Secure Messaging (Structured, Not Freeform)

To prevent hotels from exchanging contact info on-platform (which would allow them to bypass Lodge-Link entirely), messaging between hotels is **template-driven, not freeform**:

```
Available Message Templates:
• "We have availability — confirming your referral."
• "We're at capacity tonight but can accommodate from [date]."
• "Please clarify: room type required (single/double/suite)?"
• "Guest has special needs — please confirm you can accommodate."
• "Referral confirmed. Handshake code sent to guest."
```

Free-text messaging is not offered in MVP. This is a deliberate trust and business model decision: if hotels need to negotiate directly, they exit the platform's commission flow, which is a business risk. Structured templates handle 95% of real-world coordination needs.

---

<a name="module-4"></a>
## MODULE 4: Landing Page & B2B UX

### 4.1 — The Landing Page: 30-Second Conversion Design

The target audience is a **hotel owner or general manager** who:
- Is busy and skeptical of "tech platforms"
- Has been promised things before and been disappointed
- Cares about one thing: not losing a guest to the street

The landing page does not sell technology. It sells **one outcome**: *"The next time you're full, your guest doesn't leave angry — they go to a trusted partner hotel, and you still get the credit."*

#### Above-the-Fold (0–5 seconds)
```
Headline:    "You're Full Tonight. Your Guest Doesn't Have to Leave Empty-Handed."
Subheadline: "Lodge-Link connects your hotel to a trusted network. When you can't
              host a guest, we find them a room — and you maintain the relationship."
CTA Button:  [Join the Network — Free for 30 Days]
Trust Bar:   "Trusted by 47 hotels across Addis Ababa, Lalibela, and Hawassa"
```

#### Social Proof Section (5–15 seconds)
- 3 short testimonials from real hotel managers with photos and hotel names
- "How It Works in 3 Steps" — visual flow diagram (Hotel A full → Switch activates → Guest goes to Hotel B → Hotel A gets trust credit)
- A live counter: "23 referrals successfully completed today"

#### Feature Section (15–25 seconds)
Rather than listing features, frame them as **problems solved**:
```
❌ Before Lodge-Link                    ✅ With Lodge-Link
"Sorry, we're full" [guest leaves]      "Let me find you an option right now"
Calling partner hotels manually          One click, real-time availability
Guest remembers the stress               Guest remembers your help
No data on where guests go               Full analytics dashboard
```

#### The 30-Second CTA
A frictionless signup form: business email + phone number only. The commitment is a 30-day sandbox trial, not a contract. The psychological barrier to entry must be near zero.

---

### 4.2 — The Receptionist UI: 10-Second Referral Flow

This is the most critical UX in the entire product. A frustrated walk-in guest is standing at Hotel A's desk. The hotel is full. The receptionist has **10 seconds** to find a solution before the guest walks out.

**Design Constraints:**
- Works on a 7-inch Android tablet (most common front-desk device in Ethiopian hotels)
- One-handed operation preferred
- No more than 3 taps to initiate a referral
- Results appear in under 2 seconds
- Works if hotel internet is slow (< 2G speeds) via cached availability data

#### UI Flow: The Emergency Referral Mode

```
TAP 1: Receptionist taps large red "FIND ROOM" button
       (persistent in bottom-right corner of all dashboard screens)

       ┌────────────────────────────────────┐
       │  🔴  FIND A ROOM NEARBY             │
       │                                    │
       │  Room Type: [Single] [Double] [Suite]│
       │  Tonight Only? [YES]  Select dates  │
       │                                    │
       │  [SEARCH NOW →]                    │
       └────────────────────────────────────┘

TAP 2: Receptionist selects room type and taps SEARCH NOW

       (System returns results in <2s using cached availability)
       
       ┌────────────────────────────────────────────────┐
       │  3 rooms available nearby                      │
       │                                                │
       │  🏨 Blue Nile Lodge         ★★★★  Trust: 94   │
       │     0.3 km away · Double · 850 ETB/night       │
       │     [REFER GUEST →]                            │
       │                                                │
       │  🏨 Addis Heights Hotel     ★★★   Trust: 81   │
       │     0.8 km away · Double · 720 ETB/night       │
       │     [REFER GUEST →]                            │
       │                                                │
       │  🏨 Panorama Guesthouse     ★★    Trust: 73   │
       │     1.2 km away · Double · 590 ETB/night       │
       │     [REFER GUEST →]                            │
       └────────────────────────────────────────────────┘

TAP 3: Receptionist taps REFER GUEST on best option

       ┌────────────────────────────────────┐
       │  ✅ Referral Sent!                  │
       │                                    │
       │  Guest Code:  HTL-7K2M             │
       │                                    │
       │  Give this code to your guest.     │
       │  Blue Nile Lodge is expecting them.│
       │                                    │
       │  [Print Code]  [Share via SMS]     │
       └────────────────────────────────────┘
```

**The receptionist can now turn to the guest and say:**
*"I have a room for you at Blue Nile Lodge, 5 minutes away, 850 birr per night. Here is your code — just show this at their reception and they'll know to expect you."*

Total elapsed time: 8–12 seconds. Guest experience: rescued.

---

<a name="module-5"></a>
## MODULE 5: Future ML & "Smarties" Integration

### 5.1 — Predictive Demand: Pre-Emptive Referral Signals

The current system is **reactive**: Hotel A is full, then Lodge-Link activates. The ML layer makes it **proactive**: Lodge-Link tells Hotel A they will be full in 6 hours and suggests starting to refer low-priority walk-ins now to preserve room for confirmed bookings.

#### Phase 1 Data Collection (Months 1–12)
Before any ML model can be trained, we must collect the training data. Every interaction is logged:
- Daily occupancy rates per hotel per room type
- Referral volume and timing patterns
- Seasonal demand signals (Ethiopian holidays, festivals, events calendar)
- Day-of-week patterns
- Lead time distributions (how far in advance bookings come in)
- Weather data correlation (via public API)

#### Phase 2 Model Architecture: Occupancy Forecasting

**Model: Gradient Boosted Trees (XGBoost) for Short-Term Forecasting**

XGBoost is preferred over LSTMs for the initial deployment because:
- More interpretable (hotel managers can understand "Meskel weekend drives 40% occupancy spike")
- Requires less training data (LSTM needs ~2+ years; XGBoost works with 6–9 months)
- Faster inference (critical for real-time dashboard)
- Easier to audit and explain to non-technical hotel partners

```python
# services/demand_forecaster.py (Phase 2+ implementation)

import xgboost as xgb
import pandas as pd
from datetime import datetime, timedelta

FEATURE_COLUMNS = [
    'day_of_week',           # 0-6
    'days_until_date',       # Forecast horizon
    'is_ethiopian_holiday',  # Binary flag
    'holiday_type',          # Encoded: timkat, meskel, christmas, etc.
    'days_since_holiday',    # Proximity effect
    'rolling_7d_occupancy',  # Recent trend
    'rolling_30d_occupancy', # Medium-term trend  
    'city_event_flag',       # Marathon, conference, etc.
    'season_code',           # Dry/wet/shoulder
    'hotel_tier_encoded',    # budget/mid/premium
    'historical_same_dow_occupancy',  # Same day last year
]

def build_forecast_features(hotel_id: str, target_date: datetime) -> pd.Series:
    """Build feature vector for a single hotel + date prediction."""
    ...

def predict_occupancy(hotel_id: str, target_date: datetime, model: xgb.XGBRegressor) -> dict:
    """
    Returns occupancy probability with confidence interval.
    e.g., {"predicted_occupancy": 0.87, "ci_lower": 0.79, "ci_upper": 0.94, "confidence": "high"}
    """
    features = build_forecast_features(hotel_id, target_date)
    prediction = model.predict(features.values.reshape(1, -1))[0]
    return {
        "predicted_occupancy": round(float(prediction), 3),
        "alert_threshold_crossed": prediction > 0.85,
        "suggested_action": "begin_referral_mode" if prediction > 0.85 else "normal"
    }
```

**Dashboard Notification (When Threshold Crossed):**
```
🔔 Demand Alert — Tonight
Your hotel is predicted to reach 90%+ capacity by 6 PM.
We recommend enabling Referral Mode now for walk-in guests.
[Enable Referral Mode]  [Dismiss]
```

#### Phase 3: LSTM for Multi-Day Seasonal Forecasting
Once 18+ months of data exists per hotel, we introduce LSTMs (PyTorch) for 7-day ahead forecasting, capturing longer seasonal dependencies that XGBoost's feature engineering cannot easily encode. The LSTM is deployed as a separate microservice (not embedded in the main API) and called asynchronously.

---

### 5.2 — Dynamic "Vibe" Matching: The Smartie Layer

Beyond price, guests choose hotels based on intangible factors: atmosphere, crowd type, proximity to specific experiences. The Smartie layer learns to match the *right* guest to the *right* hotel, increasing post-referral satisfaction rates.

#### Guest Persona Classification

Guest personas are inferred — never directly asked — from signals provided by Hotel A at the moment of referral:

```python
class GuestPersonaSignals(BaseModel):
    """
    Hotel A fills these in during the referral. Takes 10 seconds.
    No guest data collected directly by Lodge-Link.
    """
    party_type: str          # solo_traveler, couple, family_with_kids, business_group
    experience_preference:   # adventure, cultural, relaxation, nightlife, pilgrim
    price_sensitivity: str   # budget_conscious, moderate, premium, price_insensitive
    special_notes: str       # "Looking for WiFi" / "Needs quiet room" / "Religious traveler"
```

#### Hotel "Vibe" Profile (Maintained by Platform)

Each hotel completes a one-time Vibe Profile during onboarding, updated quarterly:

```python
class HotelVibeProfile(BaseModel):
    ambiance: List[str]         # ['quiet', 'business_friendly', 'family_oriented', 'social']
    nearby_attractions: List[str] # ['lalibela_churches', 'simien_mountains', 'city_center']
    special_amenities: List[str]  # ['prayer_room', 'pool', 'shuttle', 'restaurant', 'wifi']
    typical_guest_type: str       # 'pilgrims', 'business', 'backpackers', 'families'
    vibe_tags: List[str]          # ['peaceful', 'lively', 'cultural', 'modern', 'traditional']
```

#### The Matching Logic (Collaborative Filtering → Embeddings)

**Phase 1 (Rule-Based):** Simple weighted tag overlap between guest signals and hotel vibe profiles. Fast to implement, interpretable, works with small data.

**Phase 2 (ML-Based):** Train a collaborative filtering model on historical referral outcomes — specifically, which persona + hotel combinations resulted in high guest feedback scores (≥ 4/5) vs. low scores. Use these as implicit preference signals to learn hotel embeddings and persona embeddings in a shared latent space. At referral time, use cosine similarity to rank hotels by "vibe fit" score, blended with trust score.

This is the difference between "here's the nearest available hotel" and "here's the hotel that travelers like you love."

---

<a name="module-6"></a>
## MODULE 6: The Ethiopian Context Implementation

### 6.1 — Localized Logic: Seasonal & Cultural Intelligence

Ethiopia's tourism is profoundly seasonal and calendar-driven. The platform must have this context built into its core logic, not bolted on later.

#### Ethiopian Holiday & Peak Season Calendar (Hardcoded + Configurable)

```python
# core/ethiopian_calendar.py

from datetime import date
from typing import NamedTuple

class PeakEvent(NamedTuple):
    name: str
    name_am: str              # Amharic name
    typical_start: str        # MM-DD (Gregorian approximate)
    duration_days: int
    demand_multiplier: float  # Expected occupancy uplift
    primary_cities: list

ETHIOPIAN_PEAK_EVENTS = [
    PeakEvent("Timkat (Epiphany)", "ጥምቀት", "01-18", 3, 2.4, ["Gondar", "Lalibela", "Addis Ababa"]),
    PeakEvent("Ethiopian Christmas", "ገና", "01-07", 3, 1.8, ["Lalibela", "Addis Ababa"]),
    PeakEvent("Meskel (True Cross)", "መስቀል", "09-27", 2, 1.9, ["Addis Ababa", "Gondar"]),
    PeakEvent("Ethiopian New Year", "እንቁጣጣሽ", "09-11", 2, 1.6, ["Addis Ababa", "Bahir Dar"]),
    PeakEvent("Fasika (Easter)", "ፋሲካ", "04-19", 4, 1.7, ["Lalibela", "Gondar", "Addis Ababa"]),
    PeakEvent("Great Ethiopian Run", "ታላቁ ሩጫ", "11-15", 2, 2.1, ["Addis Ababa"]),
    PeakEvent("Ashenda Festival", "አሸንዳ", "08-22", 3, 1.5, ["Tigray", "Gondar"]),
    PeakEvent("Dry Season Peak", "የደረቅ ወቅት", "10-15", 120, 1.4, ["all"]),  # Oct–Feb tourism high
]

def get_upcoming_peaks(city: str, days_ahead: int = 30) -> list[PeakEvent]:
    """Return peaks affecting a specific city in the next N days."""
    ...

def get_demand_multiplier(city: str, target_date: date) -> float:
    """Get combined demand multiplier for a city on a specific date."""
    ...
```

#### Amharic Language Support (i18n Architecture)

The dashboard UI must be bilingual from day one (English + Amharic). Arabic/Tigrinya support in Phase 2.

```
Translation Key Structure:
  en.json:  { "referral.find_room": "Find a Room", ... }
  am.json:  { "referral.find_room": "ክፍል ፈልግ", ... }

Framework: react-i18next (frontend) / Babel (backend error messages)
Font Support: Noto Sans Ethiopic (covers Ge'ez script perfectly)
Direction: LTR for both Amharic and English
```

#### Payment Mentality & Commission Model

Ethiopian business culture is relationship-first. The commission model must reflect this:
- Commission (1.5–3%) is collected post-stay, not pre-paid (reduces perceived risk)
- ETB (Ethiopian Birr) is the primary currency; all rates displayed in ETB
- Payment via CBE Birr, Telebirr (most widely used mobile money in Ethiopia), or bank transfer
- Invoicing is monthly, not per-transaction (reduces friction, easier for hotel accounting)

---

### 6.2 — Offline Handshakes: Zero-Internet Referral Fulfillment

This scenario is real and will happen: A guest arrives at Hotel B. Hotel B's internet is down. Hotel B cannot open their Lodge-Link dashboard to validate the referral. What happens?

#### The Offline Handshake Protocol

**Pre-Conditions (must happen while internet is available):**
1. When Hotel A initiates a referral, the **Handshake Code** is generated and cryptographically signed by Lodge-Link's servers
2. Hotel B receives the Handshake Code via SMS immediately (not just via dashboard)
3. Hotel B's Lodge-Link PWA **caches the last 50 pending referrals** locally using IndexedDB

**At Hotel B Reception (No Internet):**

The guest shows the 6-character code: `HTL-7K2M`

Hotel B's receptionist opens the Lodge-Link PWA, which loads from cache:
```
[OFFLINE MODE — Referrals cached at 2:34 PM]

Pending Referral:
Code:        HTL-7K2M  ✓ MATCH FOUND
From:        Sheraton Addis
Room Type:   Double Room
Arrival:     Tonight
Status:      Confirmed (cached)

[CONFIRM CHECK-IN]  →  Syncs to server when internet returns
```

The check-in is confirmed locally. The action is **queued** and will sync automatically when connectivity is restored. The guest receives service. The trust score event is recorded retroactively.

**Cryptographic Offline Validation:**
The Handshake Code is not just a random string. It includes a time-based HMAC component that allows the PWA to verify it was genuinely generated by Lodge-Link's servers — even without calling home. This prevents fraudulent "fake codes" being presented to Hotel B.

```python
import hmac, hashlib, time, base64

def generate_handshake_code(referral_id: str, secret: bytes) -> str:
    """
    Generates a code that is:
    1. Readable by humans (6 chars)
    2. Independently verifiable offline by the PWA
    3. Time-bounded (valid for 24h window)
    """
    time_window = int(time.time() // 86400)  # 24-hour window
    payload = f"{referral_id}:{time_window}"
    digest = hmac.new(secret, payload.encode(), hashlib.sha256).digest()
    code = base64.b32encode(digest)[:6].decode()
    return f"HTL-{code}"

def verify_handshake_code_offline(code: str, referral_id: str, secret: bytes) -> bool:
    """Can be executed in the PWA service worker with the cached secret."""
    expected = generate_handshake_code(referral_id, secret)
    return hmac.compare_digest(code, expected)
```

---

<a name="module-7"></a>
## MODULE 7: Scaling & Long-term Roadmap

### 7.1 — The "Digital Tourist Corridor" Expansion

Lodge-Link's hotel network is the **anchor**. Once trust is established and the network effect is active (target: 100+ hotels in 3 cities), the platform becomes the natural hub for the entire guest journey.

#### Corridor Expansion Sequence

**Stage 1 (MVP): Hotel ↔ Hotel**
Pure referral network. The foundational trust layer.

**Stage 2 (Month 12–18): Hotel → Airport Transfer**
Integration with ride-hailing services like **Jiren Ride** (Ethiopian ride-hailing) and **Ride** (formerly Ride Ethiopia). When a guest is referred to Hotel B across the city, Lodge-Link offers to arrange a vehicle.

API integration model:
```python
# services/corridor/ride_hailing.py

async def request_corridor_transfer(
    referral_event: ReferralEvent,
    guest_location: str,
    destination_hotel: Hotel,
    partner: CorridorPartner
) -> TransferBooking:
    """
    Called when guest accepts a referral and opts-in to transport.
    Commission: Lodge-Link earns 5% of ride fare from partner.
    """
```

**Stage 3 (Month 18–24): Hotel → Certified Tour Guide**
Lodge-Link maintains a database of ETO-certified tour guides in each region. Hotels can refer guests to vetted guides. Guides pay a platform subscription (not commission) — this aligns incentives for guide quality.

**Stage 4 (Month 24+): The Tourist Corridor API**
A unified public API that any Ethiopian travel service can query:
```
GET /v1/corridor/packages?city=lalibela&nights=3
Returns: Recommended hotel + guide + transport package combinations
         based on trust scores, guest persona, and corridor partner availability
```

This transforms Lodge-Link from a **hotel B2B tool** into the **infrastructure layer for Ethiopian tourism**.

---

### 7.2 — Global Scaling: Writing East Africa-Ready Code Today

Every architectural decision made today must avoid re-writes when expanding to Kenya, Rwanda, Tanzania, or Uganda.

#### Multi-Country Database Design

```sql
-- All tables include region/country from day one, even when only Ethiopia exists
ALTER TABLE platform.hotels ADD COLUMN country_code CHAR(2) DEFAULT 'ET';
ALTER TABLE platform.hotels ADD COLUMN currency_code CHAR(3) DEFAULT 'ETB';
ALTER TABLE platform.referral_events ADD COLUMN commission_currency CHAR(3) DEFAULT 'ETB';

-- Region-aware configuration table
CREATE TABLE platform.region_configs (
    country_code        CHAR(2) PRIMARY KEY,
    currency_code       CHAR(3) NOT NULL,
    tax_rate            NUMERIC(5,4),
    sms_gateway         TEXT,              -- Country-specific SMS provider
    payment_methods     TEXT[],            -- ['telebirr', 'mpesa', 'mtn_momo']
    regulatory_body     TEXT,              -- Ethiopian Tourism Organization, etc.
    kyc_requirements    JSONB,             -- Country-specific KYC fields
    supported_languages TEXT[],            -- ['am', 'en'] for ET; ['sw', 'en'] for KE
    is_active           BOOLEAN DEFAULT FALSE
);

INSERT INTO platform.region_configs VALUES 
    ('ET', 'ETB', 0.15, 'africas_talking_et', ARRAY['telebirr', 'cbe_birr'], 
     'Ethiopian Tourism Organization', '{}', ARRAY['am', 'en'], TRUE),
    ('KE', 'KES', 0.16, 'africas_talking_ke', ARRAY['mpesa', 'airtel_money'],
     'Kenya Tourism Board', '{}', ARRAY['sw', 'en'], FALSE),
    ('RW', 'RWF', 0.18, 'africas_talking_rw', ARRAY['mtn_momo', 'airtel_money'],
     'Rwanda Development Board', '{}', ARRAY['rw', 'fr', 'en'], FALSE);
```

#### Internationalization in the Application Layer

```python
# core/config.py

class RegionConfig(BaseModel):
    country_code: str
    currency: str
    tax_rate: float
    sms_gateway: str
    payment_methods: List[str]
    languages: List[str]

class Settings(BaseSettings):
    # Never hardcode country-specific values in business logic
    # Always resolve through region config
    DEFAULT_COUNTRY: str = "ET"
    
    def get_region_config(self, country_code: str) -> RegionConfig:
        return self._region_configs[country_code]
```

**Code Rules for Multi-Market Readiness:**
1. Never hardcode `ETB` — always use `hotel.currency_code`
2. Never hardcode Telebirr — always use `region_config.payment_methods[0]`
3. Never hardcode Amharic date formatting — use `babel` library with locale context
4. All SMS templates live in the database, not in code
5. Referral commission rates are region-configured, not application constants

---

<a name="module-8"></a>
## MODULE 8: Phased Development Plan — The Unified Thinking Checklist

> **Unification Principle:** Each phase must leave the system in a state where *security has not been compromised, data integrity has not been weakened, and the UX has not degraded* before the next phase begins. No "we'll fix it in Phase 2" debt is carried forward.

---

### PHASE 1: MVP (Months 1–4)
**Goal:** A working referral switch for 10–20 hotels in Addis Ababa. Manual KYC. Dashboard-tier integration only. Prove the concept with real referral events.

#### Infrastructure Tasks
- [ ] Provision PostgreSQL 16 on AWS RDS (Multi-AZ for failover)
- [ ] Deploy FastAPI backend on AWS ECS (Fargate) — single region (eu-west-1 nearest affordable for Africa)
- [ ] Set up Redis (ElastiCache) for session management and availability cache
- [ ] Configure AWS S3 for document storage (KYC uploads, scanned licenses)
- [ ] Deploy via Docker Compose (development) → ECS Task Definitions (production)
- [ ] Set up GitHub Actions CI/CD pipeline: lint → test → build → deploy
- [ ] Implement Alembic migrations from day 1 (no schema changes via psql directly)
- [ ] Configure CloudWatch logging and alerting (p95 API latency > 1s → PagerDuty alert)
- [ ] Integrate AfricasTalking SMS gateway for Ethiopia

#### Security Tasks
- [ ] Implement API key generation, hashing, and validation (SHA-256, never plaintext)
- [ ] HTTPS enforced everywhere (AWS Certificate Manager + ALB)
- [ ] JWT-based session auth for dashboard users (15-minute access token, 7-day refresh)
- [ ] PostgreSQL RLS policies activated on all private hotel schema tables
- [ ] Secrets management via AWS Secrets Manager (no .env files in production)
- [ ] Rate limiting: 100 req/min per API key (Kong or AWS WAF)
- [ ] OWASP Top 10 review before launch: SQL injection, XSS, IDOR, broken auth
- [ ] KYC document encryption at rest (AES-256 via pgcrypto for sensitive fields)
- [ ] Audit log table: every data-modifying action logged with actor + timestamp

#### UX Tasks
- [ ] Landing page (English + Amharic) — conversion-optimized, mobile-first
- [ ] Hotel onboarding flow (KYC form, document upload, sandbox activation)
- [ ] Receptionist dashboard: Emergency Referral Mode (3-tap flow)
- [ ] Availability management grid (visual room toggle for dashboard-tier hotels)
- [ ] Handshake Code display and SMS dispatch
- [ ] Offline PWA baseline: cache last 50 referrals via IndexedDB Service Worker
- [ ] Amharic font support (Noto Sans Ethiopic loaded via Google Fonts CDN)

**Phase 1 Exit Criteria:** 10 live hotels, 50 real referral events, 0 trust score disputes, < 1s median referral response time.

---

### PHASE 2: Beta (Months 5–9)
**Goal:** Expand to 50–100 hotels across 3 cities (Addis Ababa, Lalibela, Bahir Dar). Introduce Webhook-Lite integration. Activate trust scoring. Begin collecting training data for ML.

#### Infrastructure Tasks
- [ ] Deploy Celery + Redis worker pool (minimum 4 workers) for webhook queue
- [ ] Implement multi-city database partitioning (partition `referral_events` by city/region)
- [ ] Add read replicas to PostgreSQL (analytics queries must not touch primary)
- [ ] Implement per-hotel private schemas with automated provisioning script
- [ ] Set up data pipeline for trust score computation (nightly Celery beat job)
- [ ] SMS gateway redundancy: secondary gateway (Ethio Telecom direct) as fallback
- [ ] Implement structured application logging (JSON → CloudWatch → Grafana dashboard)
- [ ] Load testing: simulate 500 concurrent referral requests (Locust framework)
- [ ] Introduce PostGIS extension for geo-radius hotel queries

#### Security Tasks
- [ ] Scoped API key implementation (permissions enforced at middleware layer)
- [ ] Webhook HMAC signature verification (outbound webhooks signed, hotels can verify)
- [ ] KYC verification workflow with admin review queue
- [ ] Automated fraud detection: flag hotels with > 3 unfulfilled referrals in 30 days
- [ ] Add MFA option for hotel admin accounts (TOTP via Authenticator app)
- [ ] Penetration test by external security firm before Beta launch
- [ ] GDPR/Ethiopian data protection compliance review (guest data minimization audit)

#### UX Tasks
- [ ] Webhook-Lite integration guide (step-by-step for non-technical managers)
- [ ] Trust Score dashboard: hotel sees their own score breakdown
- [ ] Structured in-platform messaging (template-based Handshake communication)
- [ ] Multi-language SMS notifications (Amharic + English templates)
- [ ] Hotel analytics dashboard: referrals sent, received, fulfilled, revenue attributed
- [ ] Mobile PWA optimization: 90+ Lighthouse score on 3G connection
- [ ] Guest feedback SMS survey system (5 questions, link-based, no app required)
- [ ] Seasonal demand alerts (Meskel/Timkat warnings 2 weeks in advance)

**Phase 2 Exit Criteria:** 75 live hotels, 500+ referral events/month, trust scores published for all hotels with 10+ events, < 2% price dispute rate.

---

### PHASE 3: Scale (Months 10–18)
**Goal:** API-First integration for premium hotels. Expand to Kenya (Nairobi). Begin corridor partnerships (ride-hailing). Achieve operational profitability.

#### Infrastructure Tasks
- [ ] Multi-region deployment: add af-south-1 (Cape Town) for lower African latency
- [ ] Implement API-First PMS integration framework (OPERA, Mews, Cloudbeds adapters)
- [ ] Deploy Kafka for high-volume event streaming (availability updates at scale)
- [ ] Introduce dedicated analytics database (Redshift or BigQuery) for ML training data
- [ ] Service mesh (Istio or AWS App Mesh) for microservice observability
- [ ] Global CDN for dashboard static assets (CloudFront with Africa edge locations)
- [ ] Corridor partner API module: ride-hailing integration (Jiren Ride)
- [ ] Implement `region_configs` table and multi-country routing in API layer
- [ ] Kenya SMS gateway integration (Safaricom M-PESA payment, AfricasTalking)

#### Security Tasks
- [ ] Country-specific data residency compliance (Kenya data must stay in Kenya region)
- [ ] SOC 2 Type I readiness assessment
- [ ] API key rotation automation (30-day prompted rotation for live keys)
- [ ] Partner key issuance for corridor partners (scoped to `corridor:read` only)
- [ ] Comprehensive security logging: all API key usage, auth failures, admin actions

#### UX Tasks
- [ ] API-First integration documentation (Swagger UI + Postman collection)
- [ ] Partner developer portal (self-service sandbox, webhook testing console)
- [ ] Corridor booking UI: "Arrange Transfer" button on referral confirmation screen
- [ ] Demand alert notifications (push via PWA + SMS)
- [ ] Kenya market landing page (Swahili + English, KES pricing)
- [ ] Hotel performance benchmarking: "Your trust score vs. city average"
- [ ] Admin moderation dashboard: dispute resolution, KYC review queue

**Phase 3 Exit Criteria:** 300+ hotels across 2 countries, 3,000+ referrals/month, 2 corridor partners live, breakeven achieved.

---

### PHASE 4: AI-Optimize (Months 19–30)
**Goal:** Deploy predictive demand ML model. Introduce Vibe Matching. Expand to 3–5 East African markets. Build toward Digital Tourist Corridor API.

#### Infrastructure Tasks
- [ ] ML model serving infrastructure: FastAPI microservice wrapping XGBoost model
- [ ] MLflow for model versioning, experiment tracking, and deployment pipeline
- [ ] Feature store (Feast or custom Redis-backed) for real-time feature serving
- [ ] A/B testing framework: split traffic between trust-score-only and trust+vibe-match ranking
- [ ] Data lake architecture (S3 + Glue + Athena) for cross-market ML training
- [ ] Automated retraining pipeline: nightly XGBoost refresh on new 90-day window
- [ ] Tanzania and Rwanda infrastructure provisioning (per region_configs pattern)
- [ ] Tourist Corridor API: unified endpoint for packages (hotel + guide + transport)

#### Security Tasks
- [ ] ML model fairness audit: ensure Vibe Matching doesn't encode discriminatory proxies
- [ ] SOC 2 Type II certification
- [ ] Data anonymization pipeline: strip PII before ML training data ingestion
- [ ] Regular third-party security audits (quarterly)
- [ ] Bug bounty program launch

#### UX Tasks
- [ ] Predictive demand alerts in receptionist dashboard ("Full tonight by 6 PM — enable referral mode?")
- [ ] Vibe Match UI: receptionist selects guest persona signals (5 taps), system ranks hotels by fit
- [ ] ML insight cards: "Hotels like yours refer most on Friday evenings during Meskel week"
- [ ] Cross-corridor booking flow: hotel referral + transport + guide in one confirmation
- [ ] Partner analytics API: corridor partners can query their Lodge-Link-attributed bookings
- [ ] Multi-market manager portal: hotel chains can manage properties across Ethiopia + Kenya
- [ ] Public Trust Leaderboard (optional opt-in): top-trusted hotels per city per quarter

**Phase 4 Exit Criteria:** ML model live with 15%+ improvement in referral fulfillment rate vs. pure trust-score sorting, 5 East African markets active, Tourist Corridor API in public beta.

---

## Appendix A: Technology Stack Summary

| Layer | Technology | Rationale |
|---|---|---|
| API Framework | FastAPI (Python 3.11) | Async-native, Pydantic validation |
| Database | PostgreSQL 16 + PostGIS | Multi-tenancy, geo queries, ACID |
| Cache | Redis 7 | Availability TTL, session, queue broker |
| Task Queue | Celery + Redis | Async webhook delivery, nightly jobs |
| Search | PostGIS geo-radius | Native to PostgreSQL, no extra service |
| Frontend | React (Next.js) + PWA | Offline capability, mobile-first |
| SMS | AfricasTalking API | Pan-Africa, Ethiopia coverage |
| Mobile Payments | Telebirr, CBE Birr | Market-dominant Ethiopian providers |
| ML (Phase 2+) | XGBoost → PyTorch LSTM | Demand forecasting |
| Infrastructure | AWS (ECS Fargate, RDS, ElastiCache) | Managed, scalable, Africa regions |
| CI/CD | GitHub Actions + Docker | Reproducible builds, fast deploys |
| Monitoring | CloudWatch + Grafana + PagerDuty | Real-time alerting |

---

## Appendix B: Critical KPIs by Phase

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target | Phase 4 Target |
|---|---|---|---|---|
| Hotels on Platform | 20 | 100 | 300 | 1,000+ |
| Monthly Referrals | 100 | 500 | 3,000 | 15,000+ |
| Referral Fulfillment Rate | 70% | 80% | 88% | 93% |
| API Response Time (p95) | < 1.5s | < 1.0s | < 800ms | < 600ms |
| Price Dispute Rate | < 5% | < 2% | < 1% | < 0.5% |
| Markets Active | 1 (ET) | 1 (ET) | 2 (ET+KE) | 5+ |
| Monthly Active Hotels | 15 | 75 | 250 | 800+ |

---

*Document prepared for Lodge-Link founding team. Version 1.0. All architecture decisions subject to revision based on market feedback and technical constraints discovered during Phase 1 build.*