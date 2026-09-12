"""
Email sender — transactional emails (OTP codes, etc.)
=====================================================================
Supports TWO delivery backends and picks whichever is configured:

  1. SendGrid HTTP API  (preferred — most reliable, no Gmail App Password)
       SENDGRID_API_KEY      your SendGrid API key (starts with "SG.")
       SENDGRID_FROM_EMAIL   a verified sender address

  2. SMTP  (fallback — e.g. Gmail)
       SMTP_HOST       default: smtp.gmail.com
       SMTP_PORT       default: 587 (STARTTLS)
       SMTP_USER       sending address, e.g. sachinnb534@gmail.com
       SMTP_PASSWORD   Gmail **App Password** (a 16-char code, NOT your normal
                       account password — a normal password always fails with
                       535 "Username and Password not accepted")
       SMTP_FROM_NAME  display name, default "CricShift"

If SENDGRID_API_KEY is present it is used; otherwise SMTP is used.
"""

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

# Load BOTH the project-root .env and backend/.env so email config is picked up
# regardless of which file the credentials live in or the current working dir.
_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / "backend" / ".env")

logger = logging.getLogger("backend.email")

# Placeholder that must never be treated as a real credential
_SMTP_PLACEHOLDER = "REPLACE_WITH_GMAIL_APP_PASSWORD"


class EmailError(Exception):
    """Raised when an email cannot be sent."""


def _smtp_cfg() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_name": os.getenv("SMTP_FROM_NAME", "CricShift"),
    }


def _sendgrid_key() -> str:
    return os.getenv("SENDGRID_API_KEY", "").strip()


def _sendgrid_from() -> str:
    # Prefer an explicit SendGrid sender, else fall back to the SMTP user
    return (os.getenv("SENDGRID_FROM_EMAIL") or os.getenv("SMTP_USER", "")).strip()


def _smtp_usable() -> bool:
    c = _smtp_cfg()
    return bool(c["user"] and c["password"] and c["password"] != _SMTP_PLACEHOLDER)


def is_configured() -> bool:
    """True if EITHER SendGrid or SMTP is properly configured."""
    return bool(_sendgrid_key()) or _smtp_usable()


# ── SendGrid backend ──────────────────────────────────────────────────────────

def _send_via_sendgrid(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    import requests

    api_key = _sendgrid_key()
    from_email = _sendgrid_from()
    if not from_email:
        raise EmailError("SENDGRID_FROM_EMAIL (or SMTP_USER) must be set as the sender address.")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email, "name": os.getenv("SMTP_FROM_NAME", "CricShift")},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body or " "},
            {"type": "text/html", "value": html_body},
        ],
    }
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
    except Exception as e:
        logger.error(f"SendGrid request failed: {e}")
        raise EmailError(f"Could not reach the email service: {e}")

    # SendGrid returns 202 Accepted on success
    if resp.status_code in (200, 201, 202):
        logger.info(f"OTP email sent to {to_email} via SendGrid")
        return

    detail = resp.text[:300]
    logger.error(f"SendGrid rejected send ({resp.status_code}): {detail}")
    if resp.status_code == 401:
        raise EmailError("SendGrid rejected the API key (401). Check SENDGRID_API_KEY.")
    if resp.status_code == 403:
        raise EmailError(
            "SendGrid refused the send (403). The 'from' address must be a verified "
            "sender in your SendGrid account (Settings → Sender Authentication)."
        )
    raise EmailError(f"Email service error ({resp.status_code}). Please try again.")


# ── SMTP backend ────────────────────────────────────────────────────────────

def _send_via_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    c = _smtp_cfg()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{c['from_name']} <{c['user']}>"
    msg["To"] = to_email
    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(c["host"], c["port"], timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(c["user"], c["password"])
            server.sendmail(c["user"], [to_email], msg.as_string())
        logger.info(f"OTP email sent to {to_email} via SMTP")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth failed: {e}")
        raise EmailError(
            "Email server rejected the credentials. For Gmail you must use a "
            "16-character App Password (Google Account → Security → App passwords), "
            "NOT your normal Google password."
        )
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        raise EmailError(f"Could not send email: {e}")


# ── Public entry point ─────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> None:
    """
    Send an HTML email using whichever backend is configured
    (SendGrid preferred, then SMTP). Raises EmailError on failure.
    """
    if _sendgrid_key():
        _send_via_sendgrid(to_email, subject, html_body, text_body)
    elif _smtp_usable():
        _send_via_smtp(to_email, subject, html_body, text_body)
    else:
        raise EmailError(
            "Email sending is not configured. Set SENDGRID_API_KEY (recommended) "
            "or a valid Gmail App Password in SMTP_PASSWORD, then restart the server."
        )


def build_otp_email(otp: str, minutes_valid: int) -> tuple[str, str]:
    """
    Return (html_body, text_body) for a password-reset OTP email.
    """
    text = (
        f"Your CricShift password reset code is: {otp}\n\n"
        f"This code is valid for {minutes_valid} minutes. "
        f"If you did not request a password reset, you can ignore this email."
    )

    html = f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#0b0b0b;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b0b0b;padding:32px 0;">
      <tr>
        <td align="center">
          <table width="440" cellpadding="0" cellspacing="0"
                 style="background:#141414;border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px 8px 32px;">
                <span style="display:inline-block;background:#c8f000;color:#000;font-weight:900;
                             font-size:14px;padding:4px 8px;border-radius:6px;">XI</span>
                <span style="color:#fff;font-weight:900;font-size:18px;letter-spacing:1px;
                             margin-left:8px;vertical-align:middle;">CRICSHIFT</span>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 32px 0 32px;">
                <h1 style="color:#fff;font-size:22px;margin:16px 0 4px 0;text-transform:uppercase;">
                  Password Reset
                </h1>
                <p style="color:rgba(255,255,255,0.55);font-size:14px;margin:0 0 20px 0;">
                  Use the verification code below to reset your CricShift password.
                </p>
              </td>
            </tr>
            <tr>
              <td align="center" style="padding:8px 32px 24px 32px;">
                <div style="background:#0d0d0d;border:1px solid #c8f000;border-radius:12px;
                            padding:18px 0;margin:0 0 16px 0;">
                  <span style="color:#c8f000;font-size:34px;font-weight:900;letter-spacing:10px;">
                    {otp}
                  </span>
                </div>
                <p style="color:rgba(255,255,255,0.45);font-size:12px;margin:0;">
                  This code expires in {minutes_valid} minutes. If you didn&apos;t request this,
                  ignore this email &mdash; your account is safe.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 28px 32px;border-top:1px solid rgba(255,255,255,0.06);">
                <p style="color:rgba(255,255,255,0.3);font-size:11px;margin:16px 0 0 0;">
                  &copy; CricShift &mdash; AI-Powered Cricket Analytics
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
    return html, text
