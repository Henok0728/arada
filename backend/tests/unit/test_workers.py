import pytest
from unittest.mock import patch, MagicMock
import httpx
from celery.exceptions import Retry

from app.workers.tasks import send_sms_task, webhook_dispatcher_task
from app.core.config import settings

def test_send_sms_task_success():
    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test with credentials mock
        with patch.object(settings, "AT_USERNAME", "test_user"), \
             patch.object(settings, "AT_API_KEY", "test_key"):
            result = send_sms_task(phone_number="+251911234567", message="Hello")
            
        assert result is True
        mock_post.assert_called_once()

def test_send_sms_task_missing_credentials():
    # When credentials are missing, it should mock send
    with patch.object(settings, "AT_USERNAME", ""), \
         patch.object(settings, "AT_API_KEY", ""):
        result = send_sms_task(phone_number="+251911234567", message="Hello")
        
    assert result is True

def test_send_sms_task_retry():
    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = httpx.HTTPError("Connection failed")
        
        with patch.object(settings, "AT_USERNAME", "test_user"), \
             patch.object(settings, "AT_API_KEY", "test_key"), \
             patch("app.workers.tasks.send_sms_task.retry") as mock_retry:
            
            mock_retry.side_effect = Retry("Retry exception")
            
            with pytest.raises(Retry):
                # By passing request with retries=0 we mock the celery request context
                send_sms_task.request.retries = 0
                send_sms_task(phone_number="+251911234567", message="Hello")
                
            mock_post.assert_called_once()
            mock_retry.assert_called_once()

def test_webhook_dispatcher_task_success():
    with patch("httpx.Client.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = webhook_dispatcher_task(url="http://example.com", payload={"test": "data"})
            
        assert result is True
        mock_post.assert_called_once()

def test_webhook_dispatcher_task_retry():
    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = httpx.HTTPError("Connection failed")
        
        with patch("app.workers.tasks.webhook_dispatcher_task.retry") as mock_retry:
            mock_retry.side_effect = Retry("Retry exception")
            
            with pytest.raises(Retry):
                webhook_dispatcher_task.request.retries = 0
                webhook_dispatcher_task(url="http://example.com", payload={"test": "data"})
                
            mock_post.assert_called_once()
            mock_retry.assert_called_once()
