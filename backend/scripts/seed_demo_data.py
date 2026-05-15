"""
Lodge-Link Demo Seed Script
============================
Idempotent seed for Phase 1 demo environment.
Creates 5 demo hotels, availability, trust scores, and 2 demo accounts.

Usage:
    python -m scripts.seed_demo_data

Requirements:
    DATABASE_URL env var must be set (postgresql+asyncpg://...)
    psycopg2 or asyncpg must be available
"""
import asyncio
import hashlib
import os
import secrets
import sys
import uuid
from datetime import date, datetime, timezone

# Use asyncpg directly — no imports from app/
try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link",
).replace("postgresql+asyncpg://", "postgresql://")


# ── Demo Data ──────────────────────────────────────────────────────────────

DEMO_HOTELS = [
    {
        "id": str(uuid.UUID("11111111-1111-1111-1111-111111111111")),
        "name": "Bole Skyline Hotel",
        "slug": "bole-skyline",
        "city": "Addis Ababa",
        "address": "Bole Road, Near Edna Mall",
        "phone_number": "+251911000001",
        "email": "hotel_a@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 38.7894,
        "latitude": 8.9987,
        "status": "ACTIVE",
        "category": "STANDARD",
        "trust_score": 87,
        "is_referral_eligible": True,
    },
    {
        "id": str(uuid.UUID("22222222-2222-2222-2222-222222222222")),
        "name": "Entoto View Lodge",
        "slug": "entoto-view",
        "city": "Addis Ababa",
        "address": "Entoto Road, Yeka Sub-City",
        "phone_number": "+251911000002",
        "email": "hotel_b@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 38.7600,
        "latitude": 9.0300,
        "status": "ACTIVE",
        "category": "PREMIUM",
        "trust_score": 92,
        "is_referral_eligible": True,
    },
    {
        "id": str(uuid.UUID("33333333-3333-3333-3333-333333333333")),
        "name": "Piassa Heritage Inn",
        "slug": "piassa-heritage",
        "city": "Addis Ababa",
        "address": "Piassa Square, Arada Sub-City",
        "phone_number": "+251911000003",
        "email": "piassa@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 38.7489,
        "latitude": 9.0249,
        "status": "ACTIVE",
        "category": "BUDGET",
        "trust_score": 73,
        "is_referral_eligible": True,
    },
    {
        "id": str(uuid.UUID("44444444-4444-4444-4444-444444444444")),
        "name": "Kazanchis Business Hotel",
        "slug": "kazanchis-biz",
        "city": "Addis Ababa",
        "address": "Kazanchis District, 5th Floor Plaza",
        "phone_number": "+251911000004",
        "email": "kazanchis@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 38.7600,
        "latitude": 9.0100,
        "status": "ACTIVE",
        "category": "STANDARD",
        "trust_score": 81,
        "is_referral_eligible": True,
    },
    {
        "id": str(uuid.UUID("55555555-5555-5555-5555-555555555555")),
        "name": "Megenagna Grand Hotel",
        "slug": "megenagna-grand",
        "city": "Addis Ababa",
        "address": "Megenagna Roundabout, Yeka",
        "phone_number": "+251911000005",
        "email": "megenagna@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 38.8100,
        "latitude": 9.0250,
        "status": "ACTIVE",
        "category": "PREMIUM",
        "trust_score": 95,
        "is_referral_eligible": True,
    },
]

DEMO_USERS = [
    {
        "id": str(uuid.UUID("aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
        "hotel_id": str(uuid.UUID("11111111-1111-1111-1111-111111111111")),
        "email": "hotel_a@demo.lodge-link.et",
        "full_name": "Abebe Girma (Hotel A Demo)",
        "password": "DemoLodge2025",
        "role": "ADMIN",
    },
    {
        "id": str(uuid.UUID("bbbbbbb2-bbbb-bbbb-bbbb-bbbbbbbbbbbb")),
        "hotel_id": str(uuid.UUID("22222222-2222-2222-2222-222222222222")),
        "email": "hotel_b@demo.lodge-link.et",
        "full_name": "Bethlehem Tadesse (Hotel B Demo)",
        "password": "DemoLodge2025",
        "role": "ADMIN",
    },
]


def hash_password(password: str) -> str:
    """Simplified bcrypt-compatible hash for demo (use passlib in production)."""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # Fallback — not secure, only for demo bootstrap
        salt = secrets.token_hex(16)
        h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"$demo${salt}${h}"


async def seed(conn: asyncpg.Connection) -> None:
    now = datetime.now(timezone.utc).isoformat()
    today = date.today().isoformat()

    # Check if already seeded
    existing = await conn.fetchval(
        "SELECT COUNT(*) FROM platform.hotels WHERE email = $1",
        "hotel_a@demo.lodge-link.et",
    )
    if existing and existing > 0:
        print("✓ Seed already present — skipped")
        return

    print("Seeding demo data...")

    # Hotels
    for h in DEMO_HOTELS:
        point_wkt = f"SRID=4326;POINT({h['longitude']} {h['latitude']})"
        await conn.execute(
            """
            INSERT INTO platform.hotels
                (id, name, slug, city, address, phone_number, email, country_code,
                 location, status, category, is_referral_eligible, created_at, updated_at)
            VALUES
                ($1,$2,$3,$4,$5,$6,$7,$8,
                 ST_GeogFromText($9),$10,$11,$12,$13,$14)
            ON CONFLICT (slug) DO NOTHING
            """,
            h["id"], h["name"], h["slug"], h["city"], h["address"],
            h["phone_number"], h["email"], h["country_code"],
            point_wkt, h["status"], h["category"], h["is_referral_eligible"],
            now, now,
        )

    # Users
    for u in DEMO_USERS:
        pw_hash = hash_password(u["password"])
        await conn.execute(
            """
            INSERT INTO platform.users
                (id, hotel_id, email, full_name, hashed_password, role,
                 is_active, is_verified, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5,$6,true,true,$7,$8)
            ON CONFLICT (email) DO NOTHING
            """,
            u["id"], u["hotel_id"], u["email"], u["full_name"],
            pw_hash, u["role"], now, now,
        )

    print("✓ Demo seed loaded")
    print(f"  Hotels:  {len(DEMO_HOTELS)}")
    print(f"  Users:   hotel_a@demo.lodge-link.et / DemoLodge2025")
    print(f"           hotel_b@demo.lodge-link.et / DemoLodge2025")


async def main() -> None:
    print(f"Connecting to: {DATABASE_URL[:40]}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    try:
        await seed(conn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
