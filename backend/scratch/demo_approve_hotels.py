import asyncio
import sys
from sqlalchemy import text, select
from app.db.session import AsyncSessionLocal
from app.db.models.hotel import Hotel, HotelStatus
from datetime import datetime, timezone

async def approve_all_sandbox_hotels():
    """
    Utility for Phase 1 Demo.
    Moves all 'SANDBOX' hotels to 'ACTIVE' status so they appear in referral fan-outs.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Hotel).where(Hotel.status == HotelStatus.SANDBOX)
        )
        hotels = result.scalars().all()
        
        if not hotels:
            print("No hotels found in SANDBOX status.")
            return

        print(f"Approving {len(hotels)} hotels...")
        for hotel in hotels:
            hotel.status = HotelStatus.ACTIVE
            hotel.kyc_approved_at = datetime.now(timezone.utc).isoformat()
            db.add(hotel)
            print(f"  [ACTIVE] {hotel.name} ({hotel.slug})")
        
        await db.commit()
        print("Done. All sandbox hotels are now LIVE and referral-eligible.")

if __name__ == "__main__":
    asyncio.run(approve_all_sandbox_hotels())
