from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.session import get_db_session
from app.db.models.hotel import Hotel, HotelStatus
from app.db.models.user import User
from app.api.dependencies import get_current_user
from app.workers.email_tasks import send_kyc_submitted_email

router = APIRouter()

@router.post("/kyc/submit")
async def submit_kyc(
    business_registration_cert: UploadFile = File(...),
    tin_number: str = Form(None),
    eto_license: UploadFile = File(None),
    manager_id: UploadFile = File(...),
    physical_address: str = Form(None),
    gps_coordinates: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    if not business_registration_cert or not manager_id:
        raise HTTPException(status_code=400, detail="Business registration certificate and Manager ID are required")
    hotel = await db.get(Hotel, current_user.hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
        
    hotel.status = HotelStatus.PENDING_KYC
    # In a real system, we'd upload these to S3 and store the URLs in JSONB metadata
    
    # Queue email task
    try:
        send_kyc_submitted_email.delay(hotel.email, hotel.name)
    except Exception as e:
        print(f"Failed to queue KYC email: {e}")
    
    await db.commit()
    
    return {
        "kyc_status": hotel.status.value,
        "estimated_review_days": 3
    }
