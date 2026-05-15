"""
Lodge-Link Demo Seed Script (EMERGENCY RECOVERY MODE)
=====================================================
Force-runs to create 5 hotels, availability, trust scores, 2 accounts, and 5 pending referrals.
"""
import asyncio
import hashlib
import os
import secrets
import sys
import uuid
from datetime import date, datetime, timezone, timedelta

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lodge_link",
).replace("postgresql+asyncpg://", "postgresql://")


DEMO_HOTELS = [
    {
        "id": str(uuid.UUID("00000000-0000-0000-0000-000000000000")),
        "name": "Lodge-Link Platform",
        "slug": "lodge-link-admin",
        "city": "Addis Ababa",
        "address": "Bole",
        "phone_number": "+25100000000",
        "email": "admin@lodge-link.et",
        "country_code": "ET",
        "longitude": 38.0,
        "latitude": 9.0,
        "status": "ACTIVE",
        "category": "PREMIUM",
        "trust_score": 100,
        "is_referral_eligible": False,
        "is_platform_admin": True,
        "plan_name": "enterprise"
    },
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
        "is_platform_admin": False,
        "plan_name": "growth"
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
        "is_platform_admin": False,
        "plan_name": "starter"
    },
    {
        "id": str(uuid.UUID("66666666-6666-6666-6666-666666666666")),
        "name": "Lalibela Rock Hotel",
        "slug": "lalibela-rock",
        "city": "Lalibela",
        "address": "Church Road",
        "phone_number": "+251911000006",
        "email": "lalibela@demo.lodge-link.et",
        "country_code": "ET",
        "longitude": 39.04,
        "latitude": 12.03,
        "status": "PENDING_KYC",
        "category": "LUXURY",
        "trust_score": 0,
        "is_referral_eligible": False,
        "is_platform_admin": False,
        "plan_name": "starter"
    },
]

DEMO_USERS = [
    {
        "id": str(uuid.UUID("00000000-0000-0000-0000-000000000001")),
        "hotel_id": str(uuid.UUID("00000000-0000-0000-0000-000000000000")),
        "email": "admin@lodge-link.et",
        "full_name": "Platform Admin",
        "password": "DemoLodge2025",
        "role": "ADMIN",
    },
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
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        salt = secrets.token_hex(16)
        h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"$demo${salt}${h}"

async def seed(conn: asyncpg.Connection) -> None:
    now = datetime.now(timezone.utc)
    today_str = date.today().isoformat()
    tomorrow_str = (date.today() + timedelta(days=1)).isoformat()

    print("Seeding demo data (EMERGENCY OVERRIDE)...")

    # Force delete existing to avoid conflict in demo override
    # This ensures we get the busy dashboard state perfectly.
    await conn.execute("DELETE FROM platform.referrals")
    
    # Fetch plans to assign them
    plans = await conn.fetch("SELECT id, name FROM platform.plans")
    plan_map = {p["name"]: p["id"] for p in plans}
    
    for h in DEMO_HOTELS:
        point_wkt = f"SRID=4326;POINT({h['longitude']} {h['latitude']})"
        plan_id = plan_map.get(h.get("plan_name", "starter"))
        await conn.execute(
            """
            INSERT INTO platform.hotels
                (id, name, slug, city, address, phone_number, email, country_code,
                 location, status, category, is_referral_eligible, is_platform_admin, plan_id, created_at, updated_at)
            VALUES
                ($1,$2,$3,$4,$5,$6,$7,$8,
                 ST_GeogFromText($9),$10,$11,$12,$13,$14,$15,$16)
            ON CONFLICT (slug) DO UPDATE SET status = EXCLUDED.status, is_platform_admin = EXCLUDED.is_platform_admin
            """,
            uuid.UUID(h["id"]), h["name"], h["slug"], h["city"], h["address"],
            h["phone_number"], h["email"], h["country_code"],
            point_wkt, h["status"], h["category"], h.get("is_referral_eligible", True),
            h.get("is_platform_admin", False), plan_id,
            now, now,
        )

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
            uuid.UUID(u["id"]), uuid.UUID(u["hotel_id"]), u["email"], u["full_name"],
            pw_hash, u["role"], now, now,
        )

    # 5 Pending Referrals directed at Hotel A to look busy
    for i in range(5):
        ref_id = uuid.uuid4()
        session_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO platform.referrals
                (id, session_id, origin_hotel_id, destination_hotel_id, guest_name, guest_phone,
                 room_type, check_in_date, check_out_date, party_size, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'PENDING', $11, $12)
            """,
            ref_id, session_id, 
            uuid.UUID(DEMO_HOTELS[1]["id"]), # From Hotel B
            uuid.UUID(DEMO_HOTELS[0]["id"]), # To Hotel A
            f"VIP Guest {i+1}", f"+251911000{i}99", 
            "DOUBLE", today_str, tomorrow_str, 1, now, now
        )

    print("✓ Demo seed loaded with 5 pending referrals")

async def main() -> None:
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await seed(conn)
        await conn.close()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
