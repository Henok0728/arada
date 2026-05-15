from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.session import get_db_session
from app.db.models.hotel import Hotel, HotelStatus
from app.db.repositories.hotel import HotelRepository

router = APIRouter()

@router.get("/hotels", response_model=List[dict])
async def list_hotels_for_admin(
    db: AsyncSession = Depends(get_db_session)
):
    """List all hotels and their KYC status."""
    stmt = select(Hotel).order_by(Hotel.created_at.desc())
    result = await db.execute(stmt)
    hotels = result.scalars().all()
    
    return [
        {
            "id": str(h.id),
            "name": h.name,
            "city": h.city,
            "status": h.status,
            "email": h.email,
            "created_at": h.created_at
        }
        for h in hotels
    ]

@router.post("/hotels/{hotel_id}/verify")
async def verify_hotel(
    hotel_id: UUID,
    approve: bool,
    db: AsyncSession = Depends(get_db_session)
):
    """Approve or reject a hotel's KYC."""
    repo = HotelRepository(db)
    hotel = await repo.get_by_id(hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
        
    if approve:
        hotel.status = HotelStatus.ACTIVE
    else:
        hotel.status = HotelStatus.SUSPENDED
        
    await db.flush()
    return {"message": f"Hotel status updated to {hotel.status}"}
