"""
Celery background tasks for asynchronous processing.
"""
import httpx
import logging
from datetime import datetime, timedelta, timezone

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=5)
def send_sms_task(self, phone_number: str, message: str) -> bool:
    """
    Send an SMS using Africa's Talking API (via httpx).
    Features exponential backoff on failure.
    """
    if not settings.AT_USERNAME or not settings.AT_API_KEY:
        logger.warning("[SMS_SERVICE]: API keys not found, skipping dispatch")
        return True

    # Africa's Talking SMS endpoint
    url = "https://api.africastalking.com/version1/messaging"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "apiKey": settings.AT_API_KEY
    }
    
    data = {
        "username": settings.AT_USERNAME,
        "to": phone_number,
        "message": message,
        "from": settings.AT_SENDER_ID
    }
    
    try:
        # We use a synchronous httpx client inside Celery
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, data=data)
            response.raise_for_status()
            logger.info("SMS sent successfully to %s", phone_number)
            return True
            
    except httpx.HTTPError as exc:
        logger.error("Failed to send SMS to %s: %s", phone_number, exc)
        # Exponential backoff: 5, 10, 20, 40, 80 seconds
        delay = self.default_retry_delay * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=delay)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def webhook_dispatcher_task(self, url: str, payload: dict) -> bool:
    """
    Dispatch a webhook to external hotel systems with exponential backoff.
    """
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook dispatched successfully to %s", url)
            return True
            
    except httpx.HTTPError as exc:
        logger.error("Failed to dispatch webhook to %s: %s", url, exc)
        delay = self.default_retry_delay * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=delay)


@celery_app.task(name="demo_notify_task")
def demo_notify_task(
    referral_id: str,
    session_id: str,
    guest_name: str,
    guest_phone: str,
    destination_hotel_name: str,
    handshake_code: str,
) -> bool:
    """
    Demo-mode notification task — logs the referral details to the console
    instead of sending a real SMS. Use this during presentations and testing.

    In production, replace the demo_notify_task.delay() call in fanout.py
    with send_sms_task.delay() targeting the hotel manager's phone.
    """
    logger.info(
        "\n"
        "┌─────────────────────────────────────────────────────┐\n"
        "│          🏨  LODGE-LINK REFERRAL NOTIFICATION        │\n"
        "├─────────────────────────────────────────────────────┤\n"
        "│  Session   : %s\n"
        "│  Referral  : %s\n"
        "│  Hotel     : %s\n"
        "│  Guest     : %s  (%s)\n"
        "│  Code      : *** %s ***  ← show at reception\n"
        "└─────────────────────────────────────────────────────┘",
        session_id,
        referral_id,
        destination_hotel_name,
        guest_name,
        guest_phone,
        handshake_code,
    )
    return True


@celery_app.task(name="expire_referrals_task")
def expire_referrals_task() -> int:
    """
    Periodic Celery task: expire PENDING referrals older than 5 minutes.

    This is designed to be called by Celery Beat on a schedule.
    Uses a synchronous DB session since Celery workers run sync.

    Returns: number of referrals marked EXPIRED.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.db.repositories.referral import ReferralRepository

    async def _run() -> int:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            repo = ReferralRepository(session)
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            count = await repo.expire_stale_referrals(older_than=cutoff)
            await session.commit()
            logger.info("expire_referrals_task: marked %d referral(s) as EXPIRED", count)
            return count
        await engine.dispose()

    return asyncio.run(_run())

