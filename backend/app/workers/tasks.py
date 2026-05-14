"""
Celery background tasks for asynchronous processing.
"""
import httpx
import logging
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
        logger.warning("SMS credentials missing. Mocking SMS send to %s", phone_number)
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
