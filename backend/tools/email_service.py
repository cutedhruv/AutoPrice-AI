"""SMTP email delivery with clear errors for common provider issues."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Dict, Optional, Tuple

import config

logger = logging.getLogger(__name__)


def _clean(s: Optional[str]) -> str:
    if not s:
        return ""
    return str(s).strip().replace("\ufeff", "")


def smtp_config_status() -> Dict[str, Any]:
    """Safe snapshot for debugging (no secrets)."""
    user = _clean(config.SMTP_USER)
    to = _clean(config.NOTIFICATION_EMAIL)
    return {
        "smtp_host": config.SMTP_HOST,
        "smtp_port": config.SMTP_PORT,
        "smtp_user_set": bool(user),
        "smtp_password_set": bool(_clean(config.SMTP_PASSWORD)),
        "notification_email_set": bool(to),
        "notification_email_domain": to.split("@")[-1] if "@" in to else None,
        "use_ssl": _use_ssl(),
        "ready_to_send": bool(user and _clean(config.SMTP_PASSWORD) and to),
    }


def _use_ssl() -> bool:
    if getattr(config, "SMTP_USE_SSL", False):
        return True
    return int(config.SMTP_PORT) == 465


def _use_starttls() -> bool:
    if _use_ssl():
        return False
    return str(getattr(config, "SMTP_STARTTLS", "true")).lower() in ("1", "true", "yes")


def _smtp_hint(exc: Exception) -> str:
    msg = str(exc).lower()
    if "535" in msg or "badcredentials" in msg or "username and password not accepted" in msg:
        return (
            "Auth rejected (often 535). For Gmail: enable 2FA and use a 16-char App Password "
            "(not your normal password). SMTP_USER must be the same Google account. "
            "For Microsoft 365: use smtp.office365.com:587 and an app password if required."
        )
    if "certificate" in msg or "ssl" in msg:
        return "TLS/SSL error: try SMTP_PORT=465 with SMTP_USE_SSL=true, or verify SMTP_HOST."
    return "Check SMTP_HOST, SMTP_PORT, firewall, and that the sender is allowed to relay."


def send_smtp_email(
    to_address: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Send email. Returns (success, error_message).
    """
    user = _clean(config.SMTP_USER)
    password = _clean(config.SMTP_PASSWORD)
    to_addr = _clean(to_address)

    if not user or not password or not to_addr:
        err = "Missing SMTP_USER, SMTP_PASSWORD, or recipient address"
        logger.warning("Email not sent: %s", err)
        return False, err

    from_name = _clean(getattr(config, "SMTP_FROM_NAME", "")) or "AutoPrice AI"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, user))
    msg["To"] = to_addr
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    host = _clean(config.SMTP_HOST) or "localhost"
    port = int(config.SMTP_PORT)

    try:
        if _use_ssl():
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=45, context=context) as server:
                server.login(user, password)
                server.sendmail(user, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=45) as server:
                server.ehlo()
                if _use_starttls():
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(user, password)
                server.sendmail(user, [to_addr], msg.as_string())
        logger.info("Email sent successfully to %s", to_addr)
        return True, None
    except Exception as exc:
        hint = _smtp_hint(exc)
        logger.error("SMTP send failed: %s | %s", exc, hint)
        return False, f"{exc!s}. {hint}"


def send_test_email() -> Dict[str, Any]:
    """Send a minimal test message to NOTIFICATION_EMAIL."""
    status = smtp_config_status()
    if not status["ready_to_send"]:
        return {
            "success": False,
            "error": "incomplete_config",
            "smtp_status": status,
            "hint": "Set SMTP_USER, SMTP_PASSWORD, and NOTIFICATION_EMAIL in backend/.env",
        }
    to_addr = _clean(config.NOTIFICATION_EMAIL)
    ok, err = send_smtp_email(
        to_addr,
        "AutoPrice AI — SMTP test",
        "If you received this message, SMTP is configured correctly.\n\n— AutoPrice AI",
        "<p>If you received this message, <strong>SMTP is configured correctly</strong>.</p>",
    )
    return {"success": ok, "error": err, "smtp_status": status}
