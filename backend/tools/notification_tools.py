"""Notification tools - Email and logging"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime
from database.db import get_db_session
from database.models import Notification
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)

def _get_recipients() -> list[str]:
    """Parse comma-separated recipients from NOTIFICATION_EMAIL."""
    raw = (NOTIFICATION_EMAIL or "").strip()
    if not raw:
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


def _build_html_email(title: str, message: str, notification_type: str, product_id: int = None) -> str:
    """Build a clean HTML email with white theme."""
    type_colors = {
        "success": {"bg": "#ecfdf5", "border": "#10b981", "text": "#065f46", "badge_bg": "#d1fae5", "icon": "&#x2191;"},
        "info": {"bg": "#eff6ff", "border": "#3b82f6", "text": "#1e40af", "badge_bg": "#dbeafe", "icon": "&#x2193;"},
        "warning": {"bg": "#fffbeb", "border": "#f59e0b", "text": "#92400e", "badge_bg": "#fef3c7", "icon": "&#x26A0;"},
        "error": {"bg": "#fef2f2", "border": "#ef4444", "text": "#991b1b", "badge_bg": "#fee2e2", "icon": "&#x2716;"},
    }
    colors = type_colors.get(notification_type, type_colors["info"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f6f9;font-family:'Segoe UI',Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9;padding:40px 0;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
        
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1e1b4b,#312e81,#1e1b4b);padding:32px 40px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <div style="display:inline-block;background:rgba(255,255,255,0.15);border-radius:12px;padding:8px 12px;margin-bottom:12px;">
                    <span style="color:#ffffff;font-size:18px;font-weight:700;">&#x2197; AutoPrice AI</span>
                  </div>
                  <p style="color:rgba(199,210,254,0.8);font-size:12px;margin:0;text-transform:uppercase;letter-spacing:1.5px;">Autonomous Pricing Intelligence</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Alert Banner -->
        <tr>
          <td style="padding:0 40px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:32px;background-color:{colors['bg']};border-left:4px solid {colors['border']};border-radius:8px;">
              <tr>
                <td style="padding:16px 20px;">
                  <span style="display:inline-block;background-color:{colors['badge_bg']};color:{colors['text']};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:4px 10px;border-radius:20px;margin-bottom:8px;">
                    {colors['icon']} {notification_type.upper()}
                  </span>
                  <h2 style="color:#1e293b;font-size:20px;font-weight:700;margin:10px 0 0 0;">{title}</h2>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Message Body -->
        <tr>
          <td style="padding:24px 40px 0 40px;">
            <p style="color:#475569;font-size:15px;line-height:1.7;margin:0;">{message}</p>
          </td>
        </tr>

        <!-- Details Card -->
        <tr>
          <td style="padding:24px 40px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                        <span style="color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">Timestamp</span><br/>
                        <span style="color:#1e293b;font-size:14px;font-weight:600;">{datetime.utcnow().strftime('%b %d, %Y at %I:%M %p UTC')}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:8px 0;border-bottom:1px solid #e2e8f0;">
                        <span style="color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">Product ID</span><br/>
                        <span style="color:#1e293b;font-size:14px;font-weight:600;">#{product_id if product_id else 'N/A'}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:8px 0;">
                        <span style="color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;">Decision Source</span><br/>
                        <span style="color:#1e293b;font-size:14px;font-weight:600;">Market &#8594; Data &#8594; Pricing &#8594; Risk &#8594; Execution</span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:24px 40px 32px 40px;border-top:1px solid #f1f5f9;">
            <p style="color:#94a3b8;font-size:12px;margin:0;text-align:center;">
              This is an automated notification from <strong style="color:#6366f1;">AutoPrice AI</strong>.<br/>
              Autonomous Pricing Intelligence Platform
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send_email(title: str, message: str, notification_type: str, product_id: int = None):
    """Send an HTML email via SMTP (synchronous, called in background)."""
    recipients = _get_recipients()
    if not SMTP_USER or not SMTP_PASSWORD or not recipients:
        logger.warning("SMTP not configured — skipping email")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[AutoPrice AI] {title}"
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        # Plain-text fallback
        msg.attach(MIMEText(f"{title}\n\n{message}", "plain", "utf-8"))

        # HTML body
        html = _build_html_email(title, message, notification_type, product_id)
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        logger.info(f"Email sent to {', '.join(recipients)}: {title}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")


def send_notification(
    product_id: int,
    title: str,
    message: str,
    notification_type: str = "info"
) -> Dict:
    """
    Send a notification about a price change.
    Stores in DB and optionally sends email.
    
    Args:
        product_id: Related product ID
        title: Notification title
        message: Notification message
        notification_type: Type (info, warning, success, error)
    
    Returns:
        Notification confirmation
    """
    db = get_db_session()
    try:
        notification = Notification(
            product_id=product_id,
            title=title,
            message=message,
            notification_type=notification_type,
            timestamp=datetime.utcnow()
        )
        db.add(notification)
        db.commit()

        # Send HTML email notification
        try:
            _send_email(title, message, notification_type, product_id)
        except Exception as e:
            logger.error(f"Email send failed: {e}")

        return {
            "success": True,
            "notification_id": notification.id,
            "title": title,
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def send_rich_notification(
    product_id: int,
    short_msg: str,
    subject: str,
    plain_body: str,
    html_body: str,
    notification_type: str = "info",
) -> Dict:
    """
    Store a DB notification and send a fully-formed rich HTML email.

    Args:
        product_id: Related product ID
        short_msg: Short message stored in the DB notification
        subject: Email subject line
        plain_body: Plain-text email body
        html_body: Full HTML email body
        notification_type: Type (info, warning, success, error)

    Returns:
        Notification confirmation
    """
    db = get_db_session()
    try:
        notification = Notification(
            product_id=product_id,
            title=subject,
            message=short_msg,
            notification_type=notification_type,
            timestamp=datetime.utcnow(),
        )
        db.add(notification)
        db.commit()

        # Send the rich email
        try:
            _send_rich_email(subject, plain_body, html_body)
        except Exception as e:
            logger.error(f"Rich email send failed: {e}")

        return {
            "success": True,
            "notification_id": notification.id,
            "title": subject,
            "type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to send rich notification: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def _send_rich_email(subject: str, plain_body: str, html_body: str):
    """Send a pre-built HTML email via SMTP."""
    recipients = _get_recipients()
    if not SMTP_USER or not SMTP_PASSWORD or not recipients:
        logger.warning("SMTP not configured — skipping email")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        logger.info(f"Rich email sent to {', '.join(recipients)}: {subject}")
    except Exception as e:
        logger.error(f"Rich email send failed: {e}")


def get_notifications(limit: int = 20, unread_only: bool = False) -> list:
    """Get recent notifications"""
    db = get_db_session()
    try:
        query = db.query(Notification)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        notifications = query.order_by(
            Notification.timestamp.desc()
        ).limit(limit).all()

        return [{
            "id": n.id,
            "product_id": n.product_id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "is_read": n.is_read,
            "timestamp": n.timestamp.isoformat()
        } for n in notifications]
    finally:
        db.close()


def mark_notification_read(notification_id: int) -> Dict:
    """Mark a notification as read"""
    db = get_db_session()
    try:
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            db.commit()
            return {"success": True}
        return {"success": False, "error": "Notification not found"}
    finally:
        db.close()
