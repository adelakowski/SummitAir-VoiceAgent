"""Email service for sending booking confirmation and notification emails via Resend."""

from __future__ import annotations

import logging
from typing import Any, Optional

import resend

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self) -> None:
        self.api_key = settings.resend_api_key
        self.from_email = settings.email_from
        self.enabled = settings.email_enabled
        
        if self.api_key:
            resend.api_key = self.api_key

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Send an email via Resend API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email sending disabled. Would send to {to_email}: {subject}")
            return False

        if not self.api_key:
            logger.warning(
                "Resend API key not configured. Cannot send email. "
                "Set RESEND_API_KEY environment variable."
            )
            return False

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            
            resend.Emails.send(params)
            logger.info(f"Email sent successfully to {to_email} via Resend")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Resend: {e}")
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
            call_transcript: Optional call transcript text

        Returns:
            True if email was sent successfully, False otherwise
        """
        subject = f"New Booking: {booking_data.get('confirmation_id', 'N/A')} - {booking_data.get('name', 'Unknown')}"
        
        transcript_html = ""
        if call_transcript:
            transcript_html = f'<div class="transcript">{call_transcript}</div>'
        else:
            transcript_html = '<p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0066cc; color: white; padding: 20px; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; }}
        .section {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }}
        .transcript {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        td:first-child {{ font-weight: bold; width: 180px; }}
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
                    <tr><td>Confirmation ID:</td><td>{booking_data.get('confirmation_id', 'N/A')}</td></tr>
                    <tr><td>Call ID:</td><td>{booking_data.get('call_id', 'N/A')}</td></tr>
                    <tr><td>Customer Name:</td><td>{booking_data.get('name', 'N/A')}</td></tr>
                    <tr><td>Service Address:</td><td>{booking_data.get('address', 'N/A')}</td></tr>
                    <tr><td>Property Type:</td><td>{booking_data.get('property_type', 'N/A')}</td></tr>
                    <tr><td>Scheduled Window:</td><td>{booking_data.get('window', 'N/A')}</td></tr>
                    <tr><td>Priority Level:</td><td>{booking_data.get('urgency', 'N/A').title()}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Call Transcript</h2>
                {transcript_html}
            </div>
        </div>
    </div>
</body>
</html>
        """

        return await self.send_email(to_email, subject, html_content)

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

        transcript_html = ""
        if call_transcript:
            transcript_html = f'<div class="transcript">{call_transcript}</div>'
        else:
            transcript_html = '<p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #cc0000; color: white; padding: 20px; }}
        .content {{ background-color: #fff5f5; padding: 20px; margin-top: 20px; border: 2px solid #cc0000; }}
        .section {{ background-color: white; padding: 15px; margin: 15px 0; }}
        .transcript {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        td:first-child {{ font-weight: bold; width: 180px; }}
        .urgent {{ color: #cc0000; font-size: 20px; font-weight: bold; }}
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
                    <tr><td>Ticket ID:</td><td>{ticket_data.get('ticket_id', 'N/A')}</td></tr>
                    <tr><td>Call ID:</td><td>{ticket_data.get('call_id', 'N/A')}</td></tr>
                    <tr><td>Priority Level:</td><td><strong>HIGH</strong></td></tr>
                    <tr><td>Reason:</td><td>{ticket_data.get('reason', 'N/A')}</td></tr>
                    <tr><td>Address:</td><td>{ticket_data.get('address', 'N/A')}</td></tr>
                    <tr><td>Emergency Time Slot:</td><td>{ticket_data.get('emergency_slot', 'N/A')}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Call Transcript</h2>
                {transcript_html}
            </div>
            
            <p><strong>Action Required:</strong> Dispatch technician immediately within the emergency window.</p>
        </div>
    </div>
</body>
</html>
        """

        return await self.send_email(to_email, subject, html_content)

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

        transcript_html = ""
        if call_transcript:
            transcript_html = f'<div class="transcript">{call_transcript}</div>'
        else:
            transcript_html = '<p><em>Transcript not available. Configure Retell webhook to capture call transcripts.</em></p>'

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #990000; color: white; padding: 20px; }}
        .content {{ background-color: #fff0f0; padding: 20px; margin-top: 20px; border: 3px solid #990000; }}
        .section {{ background-color: white; padding: 15px; margin: 15px 0; }}
        .transcript {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border: 1px solid #ddd; font-family: monospace; white-space: pre-wrap; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        td:first-child {{ font-weight: bold; width: 180px; }}
        .critical {{ color: #990000; font-size: 22px; font-weight: bold; }}
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
                    <tr><td>Call ID:</td><td>{escalation_data.get('call_id', 'N/A')}</td></tr>
                    <tr><td>Action Taken:</td><td>{escalation_data.get('action', 'N/A')}</td></tr>
                    <tr><td>Hazard Summary:</td><td><strong>{escalation_data.get('hazard_summary', 'N/A')}</strong></td></tr>
                    <tr><td>Caller Phone:</td><td>{escalation_data.get('caller_phone', 'N/A')}</td></tr>
                    <tr><td>Escalated:</td><td>{escalation_data.get('escalated', False)}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Message to Caller</h2>
                <p>{escalation_data.get('message', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h2>Call Transcript</h2>
                {transcript_html}
            </div>
            
            <p><strong>Note:</strong> Caller was instructed to evacuate and call 911. No technician dispatch scheduled.</p>
        </div>
    </div>
</body>
</html>
        """

        return await self.send_email(to_email, subject, html_content)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global EmailService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
