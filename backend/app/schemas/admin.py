from typing import List, Optional, Dict, Any
import uuid
from pydantic import BaseModel
from datetime import datetime

class HotelStats(BaseModel):
    total: int
    active: int
    pending_kyc: int
    suspended: int

class ReferralStats(BaseModel):
    total_all_time: int
    last_30_days: int
    last_7_days: int
    fulfillment_rate: float
    avg_response_time_seconds: float

class RevenueStats(BaseModel):
    commission_earned_etb_all_time: float
    commission_earned_etb_30d: float
    commission_earned_etb_7d: float

class TrustStats(BaseModel):
    avg_platform_trust_score: float
    hotels_with_score: int
    hotels_without_score: int

class ApiKeyStats(BaseModel):
    live_keys_issued: int
    sandbox_keys_active: int
    keys_revoked: int

class AdminStatsResponse(BaseModel):
    hotels: HotelStats
    referrals: ReferralStats
    revenue: RevenueStats
    trust: TrustStats
    api_keys: ApiKeyStats

class KycQueueItem(BaseModel):
    hotel_id: uuid.UUID
    slug: str
    display_name: str
    email: str
    phone: str
    city: str
    submitted_at: datetime
    documents: List[str]
    days_waiting: int

class KycApproveRequest(BaseModel):
    reviewer_notes: Optional[str] = None

class KycApproveResponse(BaseModel):
    live_api_key: str
    warning: str = "Show once. Not stored."

class KycRejectRequest(BaseModel):
    reason: str

class KycRequestInfoRequest(BaseModel):
    message: str

class SuspendRequest(BaseModel):
    reason: str

class PlanBase(BaseModel):
    name: str
    display_name: str
    price_etb: Optional[float] = None
    max_referrals_per_month: Optional[int] = None
    commission_rate: Optional[float] = None
    features: Optional[Dict[str, Any]] = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(PlanBase):
    pass

class PlanResponse(PlanBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

class AssignPlanRequest(BaseModel):
    plan_id: uuid.UUID
    effective_from: str  # ISO date

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID]
    actor_email: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[uuid.UUID]
    metadata: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime
