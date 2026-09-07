"""Tests for email notification functionality."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.email_service import EmailService, get_email_service
from app.tools.handlers import escalate_emergency, flag_priority, mock_schedule
from app.tools.store import InMemoryStore


@pytest.fixture
def mock_email_service():
    """Create a mock email service for testing."""
    service = MagicMock(spec=EmailService)
    service.send_admin_booking_notification = AsyncMock(return_value=True)
    service.send_admin_priority_notification = AsyncMock(return_value=True)
    service.send_admin_escalation_notification = AsyncMock(return_value=True)
    return service


def test_email_service_initialization():
    """Test that email service can be initialized."""
    service = get_email_service()
    assert service is not None
    assert isinstance(service, EmailService)


@pytest.mark.asyncio
async def test_send_admin_booking_notification():
    """Test sending admin booking notification email."""
    service = EmailService()
    
    booking_data = {
        "confirmation_id": "SA-TEST123456",
        "call_id": "call_123",
        "name": "John Doe",
        "address": "123 Main St",
        "property_type": "residential",
        "availability": "Tomorrow 2-4pm",
        "urgency": "standard",
        "window": "Tomorrow 2-4pm",
    }
    
    # Test with email disabled (should return False)
    with patch("app.email_service.settings") as mock_settings:
        mock_settings.email_enabled = False
        result = await service.send_admin_booking_notification(
            "test@example.com",
            booking_data,
            "Sample call transcript",
        )
        assert result is False


@pytest.mark.asyncio
async def test_send_admin_priority_notification():
    """Test sending admin priority notification email."""
    service = EmailService()
    
    ticket_data = {
        "ticket_id": "PRI-ABCD1234",
        "call_id": "call_456",
        "priority": "high",
        "reason": "No heat, elderly resident",
        "address": "456 Oak Ave",
        "emergency_slot": "2026-09-07T10:00:00+00:00",
    }
    
    # Test with email disabled (should return False)
    with patch("app.email_service.settings") as mock_settings:
        mock_settings.email_enabled = False
        result = await service.send_admin_priority_notification(
            "test@example.com",
            ticket_data,
            "Sample emergency call transcript",
        )
        assert result is False


@pytest.mark.asyncio
async def test_send_admin_escalation_notification():
    """Test sending admin escalation notification email."""
    service = EmailService()
    
    escalation_data = {
        "call_id": "call_789",
        "action": "evacuate_and_call_911",
        "hazard_summary": "Gas leak reported",
        "caller_phone": "+1234567890",
        "escalated": True,
        "message": "Please evacuate immediately and call 911.",
    }
    
    # Test with email disabled (should return False)
    with patch("app.email_service.settings") as mock_settings:
        mock_settings.email_enabled = False
        result = await service.send_admin_escalation_notification(
            "test@example.com",
            escalation_data,
            "Sample safety escalation transcript",
        )
        assert result is False


def test_mock_schedule_triggers_email():
    """Test that mock_schedule triggers email notification."""
    store = InMemoryStore()
    
    with patch("app.tools.handlers.settings") as mock_settings, \
         patch("app.tools.handlers.asyncio.create_task") as mock_create_task:
        mock_settings.email_enabled = True
        mock_settings.admin_notification_email = "admin@example.com"
        
        result = mock_schedule(
            {
                "call_id": "call_123",
                "name": "Jane Smith",
                "address": "789 Elm St",
                "property_type": "commercial",
                "availability": "Next week",
                "urgency": "standard",
                "call_transcript": "Sample transcript",
            },
            store=store,
        )
        
        assert result["status"] == "scheduled"
        assert "confirmation_id" in result
        # Verify that email sending task was created
        mock_create_task.assert_called_once()


def test_flag_priority_triggers_email():
    """Test that flag_priority triggers email notification."""
    store = InMemoryStore()
    
    with patch("app.tools.handlers.settings") as mock_settings, \
         patch("app.tools.handlers.asyncio.create_task") as mock_create_task:
        mock_settings.email_enabled = True
        mock_settings.admin_notification_email = "admin@example.com"
        
        result = flag_priority(
            {
                "call_id": "call_456",
                "reason": "No AC, elderly resident in summer",
                "address": "321 Pine St",
                "call_transcript": "Emergency call transcript",
            },
            store=store,
        )
        
        assert result["priority"] == "high"
        assert "ticket_id" in result
        # Verify that email sending task was created
        mock_create_task.assert_called_once()


def test_escalate_emergency_triggers_email():
    """Test that escalate_emergency triggers email notification."""
    store = InMemoryStore()
    
    with patch("app.tools.handlers.settings") as mock_settings, \
         patch("app.tools.handlers.asyncio.create_task") as mock_create_task:
        mock_settings.email_enabled = True
        mock_settings.admin_notification_email = "admin@example.com"
        
        result = escalate_emergency(
            {
                "call_id": "call_789",
                "hazard_summary": "Strong gas smell near furnace",
                "caller_phone": "+1987654321",
                "call_transcript": "Gas leak emergency transcript",
            },
            store=store,
        )
        
        assert result["escalated"] is True
        assert result["action"] == "evacuate_and_call_911"
        # Verify that email sending task was created
        mock_create_task.assert_called_once()


def test_email_not_sent_when_disabled():
    """Test that emails are not sent when EMAIL_ENABLED is False."""
    store = InMemoryStore()
    
    with patch("app.tools.handlers.settings") as mock_settings, \
         patch("app.tools.handlers.asyncio.create_task") as mock_create_task:
        mock_settings.email_enabled = False
        mock_settings.admin_notification_email = "admin@example.com"
        
        mock_schedule(
            {
                "call_id": "call_123",
                "name": "Test User",
                "address": "123 Test St",
                "property_type": "residential",
                "availability": "Tomorrow",
                "urgency": "standard",
            },
            store=store,
        )
        
        # Email sending task should not be created
        mock_create_task.assert_not_called()


def test_email_gracefully_handles_missing_config():
    """Test that missing email config doesn't break booking flow."""
    store = InMemoryStore()
    
    with patch("app.tools.handlers.settings") as mock_settings:
        mock_settings.email_enabled = True
        mock_settings.admin_notification_email = None
        
        # Should still complete successfully even without email config
        result = mock_schedule(
            {
                "call_id": "call_123",
                "name": "Test User",
                "address": "123 Test St",
                "property_type": "residential",
                "availability": "Tomorrow",
                "urgency": "standard",
            },
            store=store,
        )
        
        assert result["status"] == "scheduled"
        assert "confirmation_id" in result
