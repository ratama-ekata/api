"""
Email notification service: manages dispatching official citizen confirmation emails
with generated report IDs, incident details, and confidentiality assurances.
"""

import os
import smtplib
import logging
import asyncio
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("ratamaekata_api.email_service")


class EmailService:
    """Service class for dispatching notifications and confirmation emails."""

    @staticmethod
    def _build_html_template(
        fullname: str,
        report_id: str,
        police_station: str,
        type_of_activity: str,
        submitted_at: Optional[datetime] = None,
    ) -> str:
        """Construct a responsive, government-branded HTML email."""
        date_str = (
            submitted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if submitted_at
            else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Incident Report Confirmation - {report_id}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1E293B;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #F8FAFC; padding: 30px 15px;">
    <tr>
      <td align="center">
        <!-- Main Container Card -->
        <table role="presentation" width="100%" max-width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; background-color: #FFFFFF; border-radius: 16px; border: 2px solid #882637; box-shadow: 0 10px 25px rgba(136, 38, 55, 0.08); overflow: hidden;">
          
          <!-- Header Bar -->
          <tr>
            <td style="background-color: #882637; padding: 24px 30px; text-align: center;">
              <h1 style="margin: 0; color: #FFFFFF; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">
                රටම එකට &bull; Ratamaekata.gov.lk
              </h1>
              <p style="margin: 6px 0 0 0; color: #F29EAA; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                National Operation for Drug Prevention & Enforcement
              </p>
            </td>
          </tr>

          <!-- Body Content -->
          <tr>
            <td style="padding: 35px 35px 25px 35px;">
              <p style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: #0F172A;">
                Dear {fullname},
              </p>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                Thank you for your civic contribution. Your report concerning suspected drug activity has been successfully received and registered into the National Operation incident tracking system.
              </p>

              <!-- Highlighted Report ID Card -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #FFF1BF; border: 2px solid #882637; border-radius: 12px; margin: 25px 0; text-align: center;">
                <tr>
                  <td style="padding: 20px;">
                    <span style="display: block; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: #882637;">
                      Official Incident Report ID
                    </span>
                    <span style="display: block; font-size: 32px; font-weight: 900; letter-spacing: 1px; color: #882637; font-family: monospace; margin: 8px 0;">
                      {report_id}
                    </span>
                    <span style="display: block; font-size: 12px; color: #511B25; font-weight: 600;">
                      Please retain this reference ID for all future follow-ups.
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Incident Summary Breakdown -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 25px;">
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #E2E8F0; font-size: 13px; font-weight: 600; color: #64748B; width: 40%;">
                    Designated Police Station:
                  </td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #E2E8F0; font-size: 13px; font-weight: 700; color: #1E293B;">
                    {police_station}
                  </td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #E2E8F0; font-size: 13px; font-weight: 600; color: #64748B;">
                    Type of Activity:
                  </td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #E2E8F0; font-size: 13px; font-weight: 700; color: #1E293B;">
                    {type_of_activity}
                  </td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B;">
                    Recorded Timestamp:
                  </td>
                  <td style="padding: 12px 16px; font-size: 13px; font-weight: 700; color: #1E293B;">
                    {date_str}
                  </td>
                </tr>
              </table>

              <!-- Strict Confidentiality Notice -->
              <div style="background-color: #F0FDF4; border-left: 4px solid #16A34A; padding: 14px 16px; border-radius: 4px; margin-bottom: 25px;">
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #166534; font-weight: 600;">
                  <strong>Confidentiality Guaranteed:</strong> Your report is handled under strict government information security protocols. Your personal contact details will only be accessible to authorized investigative officers.
                </p>
              </div>

              <!-- Emergency Hotlines Strip -->
              <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: 700; color: #1E293B;">
                Need Immediate Assistance or Additional Information?
              </p>
              <ul style="margin: 0 0 25px 0; padding-left: 20px; font-size: 13px; color: #475569; line-height: 1.7;">
                <li><strong>Hotline 1818</strong> &mdash; 24/7 Toll-Free Drug Reporting & Enforcement</li>
                <li><strong>Hotline 1927</strong> &mdash; Confidential Rehabilitation & Counseling Support</li>
              </ul>

              <p style="margin: 0; font-size: 13px; color: #64748B;">
                Sincerely,<br>
                <strong style="color: #1E293B;">National Coordination Unit</strong><br>
                Presidential Secretariat of Sri Lanka
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #0F172A; padding: 20px 30px; text-align: center;">
              <p style="margin: 0 0 6px 0; color: #94A3B8; font-size: 11px;">
                This is an automated confirmation sent from <a href="https://ratamaekata.gov.lk" style="color: #38BDF8; text-decoration: none;">ratamaekata.gov.lk</a>. Please do not reply directly to this email.
              </p>
              <p style="margin: 0; color: #64748B; font-size: 11px;">
                &copy; 2026 Presidential Secretariat of Sri Lanka. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    @staticmethod
    def _build_text_template(
        fullname: str,
        report_id: str,
        police_station: str,
        type_of_activity: str,
        submitted_at: Optional[datetime] = None,
    ) -> str:
        """Construct a plain text fallback message."""
        date_str = (
            submitted_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if submitted_at
            else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        return f"""RATAMAEKATA.GOV.LK - INCIDENT REPORT CONFIRMATION
National Operation for Drug Prevention & Enforcement
Presidential Secretariat of Sri Lanka

Dear {fullname},

Thank you for your civic contribution. Your report concerning suspected drug activity has been successfully received and registered into the National Operation incident tracking system.

------------------------------------------------------------
YOUR OFFICIAL REPORT ID: {report_id}
------------------------------------------------------------
Please retain this reference ID for all future follow-ups.

INCIDENT SUMMARY:
- Designated Police Station: {police_station}
- Type of Activity: {type_of_activity}
- Recorded Timestamp: {date_str}

CONFIDENTIALITY GUARANTEED:
Your report is handled under strict government confidentiality protocols.
Your personal details are accessible solely to authorized investigative officers.

NATIONAL HOTLINES:
- 1818 : 24/7 Toll-Free Drug Reporting & Enforcement
- 1927 : Confidential Rehabilitation & Counseling Support

Sincerely,
National Coordination Unit
Presidential Secretariat of Sri Lanka
https://ratamaekata.gov.lk
"""

    @classmethod
    def _send_smtp_sync(
        cls,
        recipient_email: str,
        fullname: str,
        report_id: str,
        police_station: str,
        type_of_activity: str,
        submitted_at: Optional[datetime] = None,
    ) -> bool:
        """Synchronous SMTP email delivery intended to be run in a background worker."""
        if not recipient_email or "@" not in recipient_email:
            logger.warning("Skipping email dispatch: Invalid recipient email '%s'", recipient_email)
            return False

        # In dev or unconfigured SMTP mode, log and succeed gracefully
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info(
                "[EMAIL DISPATCH - LOCAL/DEMO] Confirmation email prepared for '%s' (User: %s) with Report ID '%s' at station '%s'.",
                recipient_email,
                fullname,
                report_id,
                police_station,
            )
            return True

        try:
            subject = f"[Ratamaekata.gov.lk] Incident Report Confirmation - Report ID: {report_id}"
            from_addr = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = recipient_email

            text_body = cls._build_text_template(
                fullname=fullname,
                report_id=report_id,
                police_station=police_station,
                type_of_activity=type_of_activity,
                submitted_at=submitted_at,
            )
            html_body = cls._build_html_template(
                fullname=fullname,
                report_id=report_id,
                police_station=police_station,
                type_of_activity=type_of_activity,
                submitted_at=submitted_at,
            )

            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            logger.info("Connecting to SMTP server %s:%d to send report ID %s...", settings.SMTP_HOST, settings.SMTP_PORT, report_id)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Confirmation email for Report ID '%s' successfully delivered to '%s'", report_id, recipient_email)
            return True

        except Exception as exc:
            logger.error("Failed to send confirmation email for Report ID '%s' to '%s': %s", report_id, recipient_email, exc)
            return False

    @classmethod
    async def send_report_confirmation_email(
        cls,
        recipient_email: str,
        fullname: str,
        report_id: str,
        police_station: str,
        type_of_activity: str,
        submitted_at: Optional[datetime] = None,
    ) -> bool:
        """
        Asynchronously dispatch citizen confirmation email without blocking
        the API request thread.
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                cls._send_smtp_sync,
                recipient_email,
                fullname,
                report_id,
                police_station,
                type_of_activity,
                submitted_at,
            )
        except Exception as exc:
            logger.error("Unexpected error in async email dispatcher: %s", exc)
            return False

