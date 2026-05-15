from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Any
import uuid

from app.db.session import get_db_session
from app.schemas.admin import (
    AdminStatsResponse, HotelStats, ReferralStats, RevenueStats, TrustStats, ApiKeyStats,
    KycQueueItem, KycApproveRequest, KycApproveResponse, KycRejectRequest, KycRequestInfoRequest,
    SuspendRequest, PlanCreate, PlanUpdate, PlanResponse, AssignPlanRequest, AuditLogResponse
)
from app.db.models.user import User
from app.db.models.hotel import Hotel, HotelStatus
from app.db.models.referral import Referral, ReferralStatus
from app.db.models.api_key import APIKey, ENV_LIVE
from app.db.models.plan import Plan
from app.db.models.audit_log import AuditLog
from app.api.dependencies import get_admin_user
from app.services.auth import generate_api_key
from app.workers.email_tasks import send_kyc_approval_email, send_kyc_rejection_email, send_welcome_email

router = APIRouter()

@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    # Dummy data for now, ideally this would aggregate from db.
    return AdminStatsResponse(
        hotels=HotelStats(total=10, active=5, pending_kyc=3, suspended=2),
        referrals=ReferralStats(total_all_time=100, last_30_days=40, last_7_days=10, fulfillment_rate=0.85, avg_response_time_seconds=120.0),
        revenue=RevenueStats(commission_earned_etb_all_time=50000.0, commission_earned_etb_30d=15000.0, commission_earned_etb_7d=3500.0),
        trust=TrustStats(avg_platform_trust_score=8.5, hotels_with_score=8, hotels_without_score=2),
        api_keys=ApiKeyStats(live_keys_issued=5, sandbox_keys_active=10, keys_revoked=1)
    )

@router.get("/kyc/queue", response_model=List[dict])
async def get_kyc_queue(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(Hotel).where(Hotel.status == HotelStatus.PENDING_KYC))
    hotels = result.scalars().all()
    queue = []
    for h in hotels:
        queue.append({
            "hotel_id": str(h.id),
            "slug": h.slug,
            "display_name": h.name,
            "email": h.email,
            "phone": h.phone_number,
            "city": h.city,
            "submitted_at": h.created_at.isoformat(),
            "documents": ["business_registration_cert.pdf", "manager_id.jpg"],
            "days_waiting": 1
        })
    return queue

@router.get("/kyc/{hotel_id}")
async def get_kyc_details(
    hotel_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {"hotel": {"id": str(hotel.id), "name": hotel.name, "status": hotel.status.value}}

@router.post("/kyc/{hotel_id}/approve", response_model=KycApproveResponse)
async def approve_kyc(
    hotel_id: uuid.UUID,
    req: KycApproveRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    hotel.status = HotelStatus.ACTIVE
    hotel.kyc_approved_at = func.now()
    
    plaintext_key, key_hash, key_prefix = generate_api_key(ENV_LIVE)
    
    api_key_record = APIKey(
        hotel_id=hotel.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        environment=ENV_LIVE,
        scopes=["*"],
        name="Live production key",
        is_active=True,
    )
    db.add(api_key_record)
    
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="kyc_approved",
        target_type="hotel",
        target_id=hotel.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    # Send email (fails gracefully if Redis is down)
    try:
        send_kyc_approval_email.delay(hotel.email, hotel.name)
    except Exception as e:
        print(f"Failed to queue approval email: {e}")
    
    return KycApproveResponse(live_api_key=plaintext_key)

@router.post("/kyc/{hotel_id}/reject")
async def reject_kyc(
    hotel_id: uuid.UUID,
    req: KycRejectRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="kyc_rejected",
        target_type="hotel",
        target_id=hotel_id,
        metadata_={"reason": req.reason}
    )
    db.add(audit_log)
    await db.commit()
    
    # Send rejection email (fails gracefully if Redis is down)
    if hotel:
        try:
            send_kyc_rejection_email.delay(hotel.email, hotel.name, req.reason)
        except Exception as e:
            print(f"Failed to queue rejection email: {e}")
        
    return {"status": "rejected"}

@router.post("/kyc/{hotel_id}/request-info")
async def request_kyc_info(
    hotel_id: uuid.UUID,
    req: KycRequestInfoRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="kyc_info_requested",
        target_type="hotel",
        target_id=hotel_id,
        metadata_={"message": req.message}
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "info_requested"}

@router.get("/hotels")
async def get_hotels(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(Hotel))
    hotels = result.scalars().all()
    return [{"id": str(h.id), "name": h.name, "status": h.status.value, "city": h.city} for h in hotels]

@router.get("/hotels/{hotel_id}")
async def get_hotel_details(
    hotel_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return {"id": str(hotel.id), "name": hotel.name, "status": hotel.status.value}

@router.post("/hotels/{hotel_id}/suspend")
async def suspend_hotel(
    hotel_id: uuid.UUID,
    req: SuspendRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    hotel.status = HotelStatus.SUSPENDED
    
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="hotel_suspended",
        target_type="hotel",
        target_id=hotel.id,
        metadata_={"reason": req.reason}
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "suspended"}

@router.post("/hotels/{hotel_id}/reinstate")
async def reinstate_hotel(
    hotel_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    hotel.status = HotelStatus.ACTIVE
    
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="hotel_reinstated",
        target_type="hotel",
        target_id=hotel.id
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "reinstated"}

@router.delete("/hotels/{hotel_id}/keys/{key_id}/revoke")
async def revoke_api_key(
    hotel_id: uuid.UUID,
    key_id: uuid.UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    api_key = await db.get(APIKey, key_id)
    if not api_key or str(api_key.hotel_id) != str(hotel_id):
        raise HTTPException(status_code=404, detail="API Key not found")
    
    api_key.is_active = False
    
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="api_key_revoked",
        target_type="api_key",
        target_id=key_id
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "revoked"}

@router.get("/plans")
async def get_plans(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(Plan))
    plans = result.scalars().all()
    return [{
        "id": str(p.id),
        "name": p.name,
        "display_name": p.display_name,
        "price_etb": p.price_etb,
        "is_active": p.is_active
    } for p in plans]

@router.post("/hotels/{id}/plan")
async def assign_plan(
    id: uuid.UUID,
    req: AssignPlanRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    hotel = await db.get(Hotel, id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    plan = await db.get(Plan, req.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    old_plan_id = hotel.plan_id
    hotel.plan_id = plan.id
    
    audit_log = AuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="plan_assigned",
        target_type="hotel",
        target_id=hotel.id,
        metadata_={"old_plan_id": str(old_plan_id) if old_plan_id else None, "new_plan_id": str(plan.id)}
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "plan_assigned"}

@router.get("/audit-log")
async def get_audit_log(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(50))
    logs = result.scalars().all()
    return [{
        "id": str(l.id),
        "action": l.action,
        "actor_email": l.actor_email,
        "target_type": l.target_type,
        "metadata": l.metadata_,
        "created_at": l.created_at.isoformat()
    } for l in logs]
