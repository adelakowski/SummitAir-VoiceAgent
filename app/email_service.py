"""Email service for sending booking confirmation and notification emails."""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import aiosmtplib
from jinja2 import Template

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email or settings.smtp_username
        self.from_name = settings.smtp_from_name
        self.enabled = settings.email_enabled

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email sending disabled. Would send to {to_email}: {subject}")
            return False

        if not self.from_email or not self.smtp_username or not self.smtp_password:
            logger.warning(
                "Email credentials not configured. Cannot send email. "
                "Set SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL."
            )
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_admin_booking_notification(
        self,
        to_email: str,
        booking_data: dict[str, Any],
        call_transcript: Optional[str] = None,
    ) -> bool:
        """Send admin notification with booking details and call transcript.

        Args:
            to_email: Admin email address
            booking_data: Dictionary containing booking details
                (confirmation_id, name, address, window, etc.)
            call_transcript: Optional call transcript text

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"New Booking: {booking_data.get('confirmation_id', 'N/A')} - {booking_data.get('name', 'Unknown')}"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background-color: #0066cc; color: white; padding: 20px; }
        .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
        .section { background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }
        .transcript { background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }
        .label { font-weight: bold; color: #0066cc; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        td:first-child { font-weight: bold; width: 180px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 New Summit Air Booking</h1>
            <p>Call completed and booking created</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>Booking Details</h2>
                <table>
                    <tr><td>Confirmation ID:</td><td>{{ confirmation_id }}</td></tr>
                    <tr><td>Call ID:</td><td>{{ call_id }}</td></tr>
                    <tr><td>Customer Name:</td><td>{{ name }}</td></tr>
                    <tr><td>Service Address:</td><td>{{ address }}</td></tr>
                    <tr><td>Property Type:</td><td>{{ property_type }}</td></tr>
                    <tr><td>Scheduled Window:</td><td>{{ window }}</td></tr>
                    <tr><td>Priority Level:</td><td>{{ urgency|title }}</td></tr>
                    {% if availability %}<tr><td>Requested Availability:</td><td>{{ availability }}</td></tr>{% endif %}
                </table>
            </div>
            
            {% if call_transcript %}
            <div class="section">
                <h2>Call Transcript</h2>
                <div class="transcript">{{ call_transcript }}</div>
            </div>
            {% else %}
            <div class="section">
                <h2>Call Transcript</h2>
                <p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """)

        text_template = Template("""
NEW SUMMIT AIR BOOKING
=====================

BOOKING DETAILS:
Confirmation ID: {{ confirmation_id }}
Call ID: {{ call_id }}
Customer Name: {{ name }}
Service Address: {{ address }}
Property Type: {{ property_type }}
Scheduled Window: {{ window }}
Priority Level: {{ urgency|title }}
{% if availability %}Requested Availability: {{ availability }}{% endif %}

{% if call_transcript %}
CALL TRANSCRIPT:
----------------
{{ call_transcript }}
{% else %}
CALL TRANSCRIPT:
----------------
Transcript not available. Configure Retell webhook to capture call transcripts.
{% endif %}
        """)

        template_data = {**booking_data, "call_transcript": call_transcript}
        html_content = html_template.render(**template_data)
        text_content = text_template.render(**template_data)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_booking_confirmation(
        self,
        to_email: str,
        booking_data: dict[str, Any],
    ) -> bool:
        """Send a booking confirmation email.

        Args:
            to_email: Customer email address
            booking_data: Dictionary containing booking details
                (confirmation_id, name, address, window, etc.)

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"Summit Air Booking Confirmation - {booking_data.get('confirmation_id', 'N/A')}"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #0066cc; color: white; padding: 20px; text-align: center; }
        .content { background-color: #f9f9f9; padding: 20px; margin-top: 20px; }
        .details { background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
        .confirmation-id { font-size: 24px; font-weight: bold; color: #0066cc; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Summit Air</h1>
            <p>Your HVAC Service Appointment is Confirmed</p>
        </div>
        <div class="content">
            <p>Hello {{ name }},</p>
            <p>Thank you for scheduling with Summit Air! Your appointment has been confirmed.</p>
            
            <div class="confirmation-id">Confirmation #: {{ confirmation_id }}</div>
            
            <div class="details">
                <h3>Appointment Details:</h3>
                <p><strong>Service Address:</strong> {{ address }}</p>
                <p><strong>Property Type:</strong> {{ property_type }}</p>
                <p><strong>Scheduled Window:</strong> {{ window }}</p>
                <p><strong>Priority:</strong> {{ urgency|title }}</p>
            </div>
            
            <p>Our technician will arrive during your scheduled window. Please ensure someone is available to provide access to your HVAC system.</p>
            
            <p>If you need to reschedule or have questions, please call us at <strong>1-800-SUMMIT-AIR</strong>.</p>
        </div>
        <div class="footer">
            <p>&copy; 2026 Summit Air. Professional HVAC Services.</p>
            <p>This is an automated confirmation email.</p>
        </div>
    </div>
</body>
</html>
        """)

        text_template = Template("""
SUMMIT AIR - Appointment Confirmation

Hello {{ name }},

Thank you for scheduling with Summit Air! Your appointment has been confirmed.

CONFIRMATION NUMBER: {{ confirmation_id }}

Appointment Details:
- Service Address: {{ address }}
- Property Type: {{ property_type }}
- Scheduled Window: {{ window }}
- Priority: {{ urgency|title }}

Our technician will arrive during your scheduled window. Please ensure someone is available to provide access to your HVAC system.

If you need to reschedule or have questions, please call us at 1-800-SUMMIT-AIR.

---
© 2026 Summit Air. Professional HVAC Services.
This is an automated confirmation email.
        """)

        html_content = html_template.render(**booking_data)
        text_content = text_template.render(**booking_data)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_admin_priority_notification(
        self,
        to_email: str,
        ticket_data: dict[str, Any],
        call_transcript: Optional[str] = None,
    ) -> bool:
        """Send admin notification for high-priority ticket.

        Args:
            to_email: Admin email address
            ticket_data: Dictionary containing priority ticket details
            call_transcript: Optional call transcript text

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"🚨 URGENT Priority Ticket: {ticket_data.get('ticket_id', 'N/A')}"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background-color: #cc0000; color: white; padding: 20px; }
        .content { background-color: #fff5f5; padding: 20px; margin-top: 20px; border: 2px solid #cc0000; }
        .section { background-color: white; padding: 15px; margin: 15px 0; }
        .transcript { background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        td:first-child { font-weight: bold; width: 180px; }
        .urgent { color: #cc0000; font-size: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 URGENT - High Priority Emergency</h1>
        </div>
        <div class="content">
            <p class="urgent">IMMEDIATE ACTION REQUIRED</p>
            
            <div class="section">
                <h2>Priority Ticket Details</h2>
                <table>
                    <tr><td>Ticket ID:</td><td>{{ ticket_id }}</td></tr>
                    <tr><td>Call ID:</td><td>{{ call_id }}</td></tr>
                    <tr><td>Priority Level:</td><td><strong>HIGH</strong></td></tr>
                    <tr><td>Reason:</td><td>{{ reason }}</td></tr>
                    {% if address %}<tr><td>Address:</td><td>{{ address }}</td></tr>{% endif %}
                    <tr><td>Emergency Time Slot:</td><td>{{ emergency_slot }}</td></tr>
                    {% if availability %}<tr><td>Requested Availability:</td><td>{{ availability }}</td></tr>{% endif %}
                </table>
            </div>
            
            {% if call_transcript %}
            <div class="section">
                <h2>Call Transcript</h2>
                <div class="transcript">{{ call_transcript }}</div>
            </div>
            {% else %}
            <div class="section">
                <h2>Call Transcript</h2>
                <p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>
            </div>
            {% endif %}
            
            <p><strong>Action Required:</strong> Dispatch technician immediately within the emergency window.</p>
        </div>
    </div>
</body>
</html>
        """)

        text_template = Template("""
🚨 URGENT - HIGH PRIORITY EMERGENCY 🚨
=====================================

IMMEDIATE ACTION REQUIRED

PRIORITY TICKET DETAILS:
Ticket ID: {{ ticket_id }}
Call ID: {{ call_id }}
Priority Level: HIGH
Reason: {{ reason }}
{% if address %}Address: {{ address }}{% endif %}
Emergency Time Slot: {{ emergency_slot }}
{% if availability %}Requested Availability: {{ availability }}{% endif %}

{% if call_transcript %}
CALL TRANSCRIPT:
----------------
{{ call_transcript }}
{% else %}
CALL TRANSCRIPT:
----------------
Transcript not available. Configure Retell webhook to capture call transcripts.
{% endif %}

Action Required: Dispatch technician immediately within the emergency window.
        """)

        template_data = {**ticket_data, "call_transcript": call_transcript}
        html_content = html_template.render(**template_data)
        text_content = text_template.render(**template_data)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_admin_escalation_notification(
        self,
        to_email: str,
        escalation_data: dict[str, Any],
        call_transcript: Optional[str] = None,
    ) -> bool:
        """Send admin notification for life-safety escalation.

        Args:
            to_email: Admin email address
            escalation_data: Dictionary containing escalation details
            call_transcript: Optional call transcript text

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"⚠️ LIFE SAFETY ESCALATION: {escalation_data.get('call_id', 'N/A')}"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background-color: #990000; color: white; padding: 20px; }
        .content { background-color: #fff0f0; padding: 20px; margin-top: 20px; border: 3px solid #990000; }
        .section { background-color: white; padding: 15px; margin: 15px 0; }
        .transcript { background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        td:first-child { font-weight: bold; width: 180px; }
        .critical { color: #990000; font-size: 22px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ LIFE SAFETY ESCALATION</h1>
        </div>
        <div class="content">
            <p class="critical">CRITICAL SAFETY EMERGENCY</p>
            
            <div class="section">
                <h2>Escalation Details</h2>
                <table>
                    <tr><td>Call ID:</td><td>{{ call_id }}</td></tr>
                    <tr><td>Action Taken:</td><td>{{ action }}</td></tr>
                    <tr><td>Hazard Summary:</td><td><strong>{{ hazard_summary }}</strong></td></tr>
                    {% if caller_phone %}<tr><td>Caller Phone:</td><td>{{ caller_phone }}</td></tr>{% endif %}
                    <tr><td>Escalated:</td><td>{{ escalated }}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Message to Caller</h2>
                <p>{{ message }}</p>
            </div>
            
            {% if call_transcript %}
            <div class="section">
                <h2>Call Transcript</h2>
                <div class="transcript">{{ call_transcript }}</div>
            </div>
            {% else %}
            <div class="section">
                <h2>Call Transcript</h2>
                <p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>
            </div>
            {% endif %}
            
            <p><strong>Note:</strong> Caller was instructed to evacuate and call 911. No technician dispatch scheduled.</p>
        </div>
    </div>
</body>
</html>
        """)

        text_template = Template("""
⚠️ LIFE SAFETY ESCALATION ⚠️
============================

CRITICAL SAFETY EMERGENCY

ESCALATION DETAILS:
Call ID: {{ call_id }}
Action Taken: {{ action }}
Hazard Summary: {{ hazard_summary }}
{% if caller_phone %}Caller Phone: {{ caller_phone }}{% endif %}
Escalated: {{ escalated }}

MESSAGE TO CALLER:
{{ message }}

{% if call_transcript %}
CALL TRANSCRIPT:
----------------
{{ call_transcript }}
{% else %}
CALL TRANSCRIPT:
----------------
Transcript not available. Configure Retell webhook to capture call transcripts.
{% endif %}

Note: Caller was instructed to evacuate and call 911. No technician dispatch scheduled.
        """)

        template_data = {**escalation_data, "call_transcript": call_transcript}
        html_content = html_template.render(**template_data)
        text_content = text_template.render(**template_data)

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_priority_notification(
        self,
        to_email: str,
        ticket_data: dict[str, Any],
    ) -> bool:
        """Send a high-priority ticket notification email.

        Args:
            to_email: Customer email address
            ticket_data: Dictionary containing priority ticket details

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"URGENT: Summit Air Emergency Service - {ticket_data.get('ticket_id', 'N/A')}"

        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #cc0000; color: white; padding: 20px; text-align: center; }
        .content { background-color: #fff5f5; padding: 20px; margin-top: 20px; border: 2px solid #cc0000; }
        .details { background-color: white; padding: 15px; margin: 15px 0; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
        .urgent { font-size: 24px; font-weight: bold; color: #cc0000; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ URGENT - Summit Air Emergency Service</h1>
        </div>
        <div class="content">
            <div class="urgent">PRIORITY EMERGENCY SERVICE</div>
            <div class="urgent">Ticket #: {{ ticket_id }}</div>
            
            <div class="details">
                <h3>Emergency Details:</h3>
                <p><strong>Reason:</strong> {{ reason }}</p>
                {% if address %}<p><strong>Address:</strong> {{ address }}</p>{% endif %}
                <p><strong>Emergency Time Slot:</strong> {{ emergency_slot }}</p>
            </div>
            
            <p><strong>We have flagged your case as high priority.</strong></p>
            <p>A technician will be dispatched to your location within the emergency window. We understand the urgency of your situation and will do everything we can to help.</p>
            
            <p>For immediate assistance, call <strong>1-800-SUMMIT-AIR</strong>.</p>
        </div>
        <div class="footer">
            <p>&copy; 2026 Summit Air. Professional HVAC Services.</p>
        </div>
    </div>
</body>
</html>
        """)

        text_template = Template("""
⚠️ URGENT - SUMMIT AIR EMERGENCY SERVICE ⚠️

PRIORITY EMERGENCY SERVICE
Ticket #: {{ ticket_id }}

Emergency Details:
- Reason: {{ reason }}
{% if address %}- Address: {{ address }}{% endif %}
- Emergency Time Slot: {{ emergency_slot }}

We have flagged your case as high priority.

A technician will be dispatched to your location within the emergency window. We understand the urgency of your situation and will do everything we can to help.

For immediate assistance, call 1-800-SUMMIT-AIR.

---
© 2026 Summit Air. Professional HVAC Services.
        """)

        html_content = html_template.render(**ticket_data)
        text_content = text_template.render(**ticket_data)

        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
