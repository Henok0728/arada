import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from app.api.v1.handshake import generate_handshake_endpoint, verify_handshake_endpoint
from app.schemas.handshake import HandshakeGenerateRequest, HandshakeVerifyRequest
from app.services.handshake import generate_handshake, verify_handshake
from app.db.models.referral import Referral, ReferralStatus
from app.core.security import generate_handshake_code, hash_handshake_code

pytestmark = pytest.mark.asyncio

# --- Security tests ---

def test_generate_handshake_code():
    referral_id = uuid.uuid4()
    hotel_id = uuid.uuid4()
    secret = "test_secret"
    code = generate_handshake_code(referral_id, hotel_id, secret)
    assert len(code) == 6
    assert code.isdigit()
    
    # Deterministic check
    code2 = generate_handshake_code(referral_id, hotel_id, secret)
    assert code == code2

def test_hash_handshake_code():
    code = "123456"
    hashed = hash_handshake_code(code)
    assert len(hashed) == 64  # SHA-256 hex digest length

# --- Service tests ---

async def test_service_generate_handshake_success(mock_session):
    mock_redis = AsyncMock()
    referral_id = uuid.uuid4()
    hotel_id = uuid.uuid4()
    
    # Mock DB referral
    mock_referral = MagicMock(spec=Referral)
    mock_referral.id = referral_id
    mock_referral.status = ReferralStatus.ACCEPTED
    mock_referral.destination_hotel_id = hotel_id
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_referral
    mock_session.execute.return_value = mock_result
    
    with patch("app.services.handshake.send_sms_task.delay") as mock_sms:
        code = await generate_handshake(mock_session, mock_redis, referral_id, "+1234567890")
        
        assert len(code) == 6
        mock_session.commit.assert_called_once()
        mock_redis.setex.assert_called_once()
        mock_sms.assert_called_once()
        
async def test_service_generate_handshake_not_accepted(mock_session):
    mock_redis = AsyncMock()
    referral_id = uuid.uuid4()
    
    mock_referral = MagicMock(spec=Referral)
    mock_referral.id = referral_id
    mock_referral.status = ReferralStatus.PENDING
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_referral
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as excinfo:
        await generate_handshake(mock_session, mock_redis, referral_id)
    assert excinfo.value.status_code == 400

async def test_service_verify_handshake_redis_success(mock_session):
    mock_redis = AsyncMock()
    referral_id = uuid.uuid4()
    code = "123456"
    hashed_code = hash_handshake_code(code)
    
    # Redis cache hit
    mock_redis.get.return_value = hashed_code
    
    mock_referral = MagicMock(spec=Referral)
    mock_referral.status = ReferralStatus.ACCEPTED
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_referral
    mock_session.execute.return_value = mock_result
    
    is_valid = await verify_handshake(mock_session, mock_redis, referral_id, code)
    assert is_valid is True
    mock_session.commit.assert_called_once()
    assert mock_referral.status == ReferralStatus.COMPLETED
    assert mock_referral.is_handshake_verified is True
    mock_redis.delete.assert_called_once_with(f"handshake:{referral_id}")

async def test_service_verify_handshake_db_success(mock_session):
    mock_redis = AsyncMock()
    referral_id = uuid.uuid4()
    code = "123456"
    hashed_code = hash_handshake_code(code)
    
    # Redis cache miss
    mock_redis.get.return_value = None
    
    mock_referral = MagicMock(spec=Referral)
    mock_referral.status = ReferralStatus.ACCEPTED
    mock_referral.handshake_code = hashed_code
    mock_referral.handshake_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_referral
    mock_session.execute.return_value = mock_result
    
    is_valid = await verify_handshake(mock_session, mock_redis, referral_id, code)
    assert is_valid is True
    mock_session.commit.assert_called_once()

async def test_service_verify_handshake_expired(mock_session):
    mock_redis = AsyncMock()
    referral_id = uuid.uuid4()
    code = "123456"
    hashed_code = hash_handshake_code(code)
    
    # Redis cache miss
    mock_redis.get.return_value = None
    
    mock_referral = MagicMock(spec=Referral)
    mock_referral.status = ReferralStatus.ACCEPTED
    mock_referral.handshake_code = hashed_code
    mock_referral.handshake_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_referral
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as excinfo:
        await verify_handshake(mock_session, mock_redis, referral_id, code)
    assert excinfo.value.status_code == 400
    assert "expired" in excinfo.value.detail.lower()

# --- Endpoint tests ---

async def test_generate_endpoint_success(mock_session):
    req = HandshakeGenerateRequest(referral_id=uuid.uuid4())
    mock_redis = AsyncMock()
    
    with patch("app.api.v1.handshake.handshake_service.generate_handshake", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "123456"
        res = await generate_handshake_endpoint(req, db=mock_session, redis=mock_redis)
        assert res.success is True

async def test_verify_endpoint_success(mock_session):
    req = HandshakeVerifyRequest(referral_id=uuid.uuid4(), code="123456")
    mock_redis = AsyncMock()
    
    with patch("app.api.v1.handshake.handshake_service.verify_handshake", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = True
        res = await verify_handshake_endpoint(req, db=mock_session, redis=mock_redis)
        assert res.success is True
