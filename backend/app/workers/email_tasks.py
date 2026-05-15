import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.email_tasks.send_welcome_email")
def send_welcome_email(email: str, hotel_name: str) -> None:
    logger.info(f"📧 [EMAIL SIMULATION] To: {email} | Subject: Welcome to Lodge-Link, {hotel_name}!")
    logger.info(f"Body: Thank you for registering. Please complete your KYC to go live.")

@celery_app.task(name="app.workers.email_tasks.send_kyc_submitted_email")
def send_kyc_submitted_email(email: str, hotel_name: str) -> None:
    logger.info(f"📧 [EMAIL SIMULATION] To: {email} | Subject: KYC Received for {hotel_name}")
    logger.info(f"Body: We have received your documents. Expect a review in ~3 days.")

@celery_app.task(name="app.workers.email_tasks.send_kyc_approval_email")
def send_kyc_approval_email(email: str, hotel_name: str) -> None:
    logger.info(f"📧 [EMAIL SIMULATION] To: {email} | Subject: KYC Approved - Welcome to Live!")
    logger.info(f"Body: Your KYC has been approved. Your live API key is ready in your dashboard.")

@celery_app.task(name="app.workers.email_tasks.send_kyc_rejection_email")
def send_kyc_rejection_email(email: str, hotel_name: str, reason: str) -> None:
    logger.info(f"📧 [EMAIL SIMULATION] To: {email} | Subject: Action Required: KYC Rejected")
    logger.info(f"Body: Unfortunately, your KYC was rejected. Reason: {reason}")
