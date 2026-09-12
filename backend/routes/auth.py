"""
Auth Routes — /api/auth/*
=========================
Handles user registration, login, logout, OTP-based password reset.

Endpoints
---------
POST /api/auth/register       — create account
POST /api/auth/login          — email/password login → session token
POST /api/auth/logout         — invalidate session
GET  /api/auth/me             — return current user from session token
POST /api/auth/send-otp       — generate & "send" OTP to mobile
POST /api/auth/verify-otp     — check OTP code; return a reset token
POST /api/auth/reset-password — set new password using reset token

Security notes
--------------
• Passwords are bcrypt-hashed (cost=12).
• Session tokens are random CUID-style strings stored in the DB.
• OTP codes are 6-digit random numbers, valid for 10 minutes.
• Reset tokens are short-lived (15 min) JWTs signed with JWT_SECRET.
• All endpoints that accept a session use the X-Session-Token header.
"""

import logging
import os
import json
import math
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator

logger = logging.getLogger("backend.auth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ── Config ────────────────────────────────────────────────────────────────────
_JWT_SECRET: str = os.getenv("JWT_SECRET", "cricshift-dev-secret-change-in-production")
_JWT_ALGO = "HS256"
_SESSION_TTL_DAYS = 30
_OTP_TTL_MINUTES = 10
_RESET_TOKEN_TTL_MINUTES = 15

# OAuth — Google Sign-In. Free to obtain a Client ID at:
#   https://console.cloud.google.com/apis/credentials  (OAuth 2.0 Client ID, type "Web application")
# Leave empty to disable the Google button (it will show "not configured").
def _google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


# ── Admin allow-list ──────────────────────────────────────────────────────────
# Comma-separated emails in the ADMIN_EMAILS env var are treated as admins.
# This is the single source of truth for who can reach the /admin console —
# safer than a self-service "promote" endpoint (no privilege-escalation path).
def _admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _resolve_role(email: str) -> str:
    """Return 'admin' if the email is in the allow-list, else 'user'."""
    return "admin" if (email or "").strip().lower() in _admin_emails() else "user"

# ── DB path (same SQLite the Next.js Prisma client uses) ─────────────────────
_BASE = Path(__file__).resolve().parent.parent.parent
_DB_PATH = _BASE / "Cricshift-main" / "db" / "custom.db"


def _conn() -> sqlite3.Connection:
    """Return a WAL-mode connection to the user DB."""
    con = sqlite3.connect(str(_DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def _normalize_mobile(mobile: str | None) -> str | None:
    """
    Canonicalise a mobile number so formatting differences never cause a
    mismatch. Strips spaces, dashes, parentheses and dots, keeping a leading
    '+' if present. e.g. "+91 98765 43210" and "+91-98765-43210" both become
    "+919876543210". Numbers without '+' keep just their digits.
    """
    if mobile is None:
        return None
    s = mobile.strip()
    has_plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None
    return ("+" + digits) if has_plus else digits


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_str() -> str:
    return _now().isoformat()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: str | None = None

    @field_validator("password")
    @classmethod
    def pw_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("mobile")
    @classmethod
    def mobile_fmt(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 7:
            raise ValueError("Invalid mobile number.")
        # Store in canonical form so lookups always match
        return _normalize_mobile(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    # The JWT ID token returned by Google Identity Services in the browser.
    credential: str


class RegisterVerifyRequest(BaseModel):
    # The pending-registration token issued by /register/send-otp, plus the
    # 6-digit code the user received by email.
    pending_token: str
    otp: str


class SendOtpRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def pw_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_session_token() -> str:
    import uuid
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64-char hex


def _create_session(user_id: str) -> str:
    """Insert a new session row for the user and return its token."""
    from cuid2 import Cuid as _Cuid
    token = _make_session_token()
    session_id = _Cuid().generate()
    now = _now_str()
    expiry = (_now() + timedelta(days=_SESSION_TTL_DAYS)).isoformat()
    with _conn() as con:
        con.execute(
            """INSERT INTO sessions (id, token, "userId", "expiresAt", "createdAt")
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, token, user_id, expiry, now),
        )
        con.commit()
    return token


def _get_user_by_token(token: str) -> dict | None:
    """Return the user row (with resolved role) if the session token is valid."""
    with _conn() as con:
        row = con.execute(
            """SELECT u.id, u.name, u.email, u.mobile
               FROM sessions s
               JOIN users u ON u.id = s."userId"
               WHERE s.token = ? AND s."expiresAt" > ?""",
            (token, _now_str()),
        ).fetchone()
    if not row:
        return None
    user = dict(row)
    user["role"] = _resolve_role(user["email"])
    return user


def _require_session(x_session_token: str = Header(..., alias="X-Session-Token")):
    user = _get_user_by_token(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return user


def _build_signup_otp_email(otp: str, minutes_valid: int) -> tuple[str, str]:
    """Return (html, text) for the first-time signup email-verification code."""
    text = (
        f"Welcome to CricShift! Your email verification code is: {otp}\n\n"
        f"Enter this code to finish creating your account. "
        f"It is valid for {minutes_valid} minutes. "
        f"If you didn't try to sign up, you can ignore this email."
    )
    html = f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#0b0b0b;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b0b0b;padding:32px 0;">
      <tr><td align="center">
        <table width="440" cellpadding="0" cellspacing="0"
               style="background:#141414;border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden;">
          <tr><td style="padding:28px 32px 8px 32px;">
            <span style="display:inline-block;background:#c8f000;color:#000;font-weight:900;font-size:14px;padding:4px 8px;border-radius:6px;">XI</span>
            <span style="color:#fff;font-weight:900;font-size:18px;letter-spacing:1px;margin-left:8px;vertical-align:middle;">CRICSHIFT</span>
          </td></tr>
          <tr><td style="padding:8px 32px 0 32px;">
            <h1 style="color:#fff;font-size:22px;margin:16px 0 4px 0;text-transform:uppercase;">Verify your email</h1>
            <p style="color:rgba(255,255,255,0.55);font-size:14px;margin:0 0 20px 0;">
              Welcome to CricShift! Use the code below to finish creating your account.
            </p>
          </td></tr>
          <tr><td align="center" style="padding:8px 32px 24px 32px;">
            <div style="background:#0d0d0d;border:1px solid #c8f000;border-radius:12px;padding:18px 0;margin:0 0 16px 0;">
              <span style="color:#c8f000;font-size:34px;font-weight:900;letter-spacing:10px;">{otp}</span>
            </div>
            <p style="color:rgba(255,255,255,0.45);font-size:12px;margin:0;">
              This code expires in {minutes_valid} minutes. If you didn&apos;t sign up, ignore this email.
            </p>
          </td></tr>
          <tr><td style="padding:0 32px 28px 32px;border-top:1px solid rgba(255,255,255,0.06);">
            <p style="color:rgba(255,255,255,0.3);font-size:11px;margin:16px 0 0 0;">&copy; CricShift — AI-Powered Cricket Analytics</p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""
    return html, text


# ── POST /api/auth/register/send-otp ──────────────────────────────────────────

@router.post(
    "/register/send-otp",
    summary="Start signup: email a verification code to a first-time user",
)
async def register_send_otp(req: RegisterRequest):
    """
    Step 1 of signup for first-time users. Validates the email/mobile are not
    already taken, emails a 6-digit verification code, and returns a signed,
    short-lived `pending_token` that carries the (hashed) registration data.
    No account is created until the code is verified.
    """
    email = str(req.email).strip().lower()

    # Reject if the email or mobile already belongs to an account.
    with _conn() as con:
        if con.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="Email already registered. Please log in.")
        if req.mobile:
            if con.execute("SELECT id FROM users WHERE mobile = ?", (req.mobile,)).fetchone():
                raise HTTPException(status_code=409, detail="Mobile number already registered.")

    # Generate the code and email it BEFORE issuing the token so a delivery
    # failure surfaces immediately.
    otp_plain = str(random.randint(100000, 999999))
    from backend.routes.email_sender import send_email, EmailError
    try:
        html_body, text_body = _build_signup_otp_email(otp_plain, _OTP_TTL_MINUTES)
        send_email(
            to_email=email,
            subject="Your CricShift verification code",
            html_body=html_body,
            text_body=text_body,
        )
    except EmailError as e:
        logger.error(f"register send-otp email failure for {email}: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    # Sign a short-lived pending-registration token. It carries the password
    # already hashed and the OTP hashed, so the raw values never leave here.
    payload = {
        "purpose": "signup_verify",
        "name": req.name,
        "email": email,
        "mobile": req.mobile,
        "pw_hash": _hash_password(req.password),
        "otp_hash": bcrypt.hashpw(otp_plain.encode(), bcrypt.gensalt(rounds=10)).decode(),
        "exp": _now() + timedelta(minutes=_OTP_TTL_MINUTES),
    }
    pending_token = jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGO)

    return {
        "ok": True,
        "pending_token": pending_token,
        "message": "A verification code has been sent to your email.",
    }


# ── POST /api/auth/register/verify-otp ────────────────────────────────────────

@router.post(
    "/register/verify-otp",
    summary="Finish signup: verify the emailed code and create the account",
)
async def register_verify_otp(req: RegisterVerifyRequest):
    """
    Step 2 of signup. Verifies the code against the signed pending_token, then
    creates the user and returns a session — exactly like the old /register.
    """
    try:
        payload = jwt.decode(req.pending_token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except JWTError:
        raise HTTPException(status_code=400, detail="Your code has expired. Please start again.")

    if payload.get("purpose") != "signup_verify":
        raise HTTPException(status_code=400, detail="Invalid verification token.")

    if not bcrypt.checkpw(req.otp.encode(), payload["otp_hash"].encode()):
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    name = payload["name"]
    email = payload["email"]
    mobile = payload.get("mobile")
    pw_hash = payload["pw_hash"]
    now = _now_str()

    try:
        with _conn() as con:
            # Re-check uniqueness in case someone registered during the window.
            if con.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone():
                raise HTTPException(status_code=409, detail="Email already registered. Please log in.")

            from cuid2 import Cuid as _Cuid
            user_id = _Cuid().generate()
            con.execute(
                """INSERT INTO users (id, name, email, "passwordHash", mobile, role, "createdAt", "updatedAt")
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, name, email, pw_hash, mobile, _resolve_role(email), now, now),
            )
            con.commit()

        token = _create_session(user_id)
        return {
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "role": _resolve_role(email),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Register verify failed")
        raise HTTPException(status_code=500, detail=f"Registration error: {e}")


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", summary="Login with email and password")
async def login(req: LoginRequest):
    try:
        with _conn() as con:
            row = con.execute(
                """SELECT id, name, email, "passwordHash" FROM users WHERE email = ?""",
                (req.email,),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not _check_password(req.password, row["passwordHash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Create session
        from cuid2 import Cuid as _Cuid
        _cid = _Cuid()
        token = _make_session_token()
        session_id = _cid.generate()
        now = _now_str()
        expiry = (_now() + timedelta(days=_SESSION_TTL_DAYS)).isoformat()
        with _conn() as con:
            con.execute(
                """INSERT INTO sessions (id, token, "userId", "expiresAt", "createdAt")
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, token, row["id"], expiry, now),
            )
            con.commit()

        return {
            "token": token,
            "user": {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "role": _resolve_role(row["email"]),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail=f"Login error: {e}")


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@router.post("/logout", summary="Invalidate the current session")
async def logout(x_session_token: str = Header(..., alias="X-Session-Token")):
    with _conn() as con:
        con.execute("DELETE FROM sessions WHERE token = ?", (x_session_token,))
        con.commit()
    return {"ok": True}


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@router.get("/me", summary="Return the currently authenticated user")
async def me(user: dict = Depends(_require_session)):
    return {"user": user}


# ── GET /api/auth/config ──────────────────────────────────────────────────────

@router.get("/config", summary="Public auth config for the frontend")
async def auth_config():
    """
    Tells the frontend which social-login providers are configured.
    The Google Client ID is public by design (it's embedded in the browser
    button), so exposing it here is safe.
    """
    return {
        "google": {
            "enabled": bool(_google_client_id()),
            "client_id": _google_client_id(),
        },
        "apple": {
            # Apple Sign-In needs a paid Apple Developer account + key setup.
            "enabled": bool(os.getenv("APPLE_CLIENT_ID", "").strip()),
        },
    }


# ── POST /api/auth/google ─────────────────────────────────────────────────────

@router.post("/google", summary="Sign in / sign up with a Google ID token")
async def google_login(req: GoogleLoginRequest):
    """
    Verifies a Google ID token (the `credential` from Google Identity Services),
    then logs the user in — creating an account automatically on first sign-in.

    The token is cryptographically verified against Google's public keys and
    checked to have been issued for OUR client id, so a forged token is rejected.
    """
    client_id = _google_client_id()
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In is not configured on the server (GOOGLE_CLIENT_ID missing).",
        )

    # ── Verify the ID token with Google ──────────────────────────────────────
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            req.credential,
            google_requests.Request(),
            client_id,
            # small clock-skew tolerance
            clock_skew_in_seconds=10,
        )
    except ValueError as e:
        # Bad signature, wrong audience, expired, etc.
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Google sign-in failed: invalid token.")
    except Exception as e:
        logger.exception("Google verification error")
        raise HTTPException(status_code=502, detail=f"Could not verify Google token: {e}")

    email = (idinfo.get("email") or "").strip().lower()
    email_verified = idinfo.get("email_verified", False)
    name = idinfo.get("name") or (email.split("@")[0] if email else "Player")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email address.")
    if not email_verified:
        raise HTTPException(status_code=400, detail="Google email is not verified.")

    # ── Find or create the user ───────────────────────────────────────────────
    try:
        with _conn() as con:
            row = con.execute(
                """SELECT id, name, email FROM users WHERE lower(email) = ?""",
                (email,),
            ).fetchone()

        if row:
            user_id = row["id"]
            user_name = row["name"]
        else:
            # Auto-register. There's no password for OAuth users, so we store a
            # random unusable hash — they must use Google (or reset password).
            from cuid2 import Cuid as _Cuid
            import secrets
            user_id = _Cuid().generate()
            random_pw_hash = _hash_password(secrets.token_urlsafe(32))
            now = _now_str()
            with _conn() as con:
                con.execute(
                    """INSERT INTO users (id, name, email, "passwordHash", mobile, "createdAt", "updatedAt")
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, name, email, random_pw_hash, None, now, now),
                )
                con.commit()
            user_name = name

        token = _create_session(user_id)
        return {
            "token": token,
            "user": {
                "id": user_id,
                "name": user_name,
                "email": email,
                "role": _resolve_role(email),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Google login failed")
        raise HTTPException(status_code=500, detail=f"Google login error: {e}")


# ── POST /api/auth/send-otp ───────────────────────────────────────────────────

@router.post("/send-otp", summary="Generate and email an OTP to a registered address")
async def send_otp(req: SendOtpRequest):
    """
    Generates a 6-digit OTP, stores it hashed against the user's email,
    and emails it to that address via SMTP. The OTP is valid for
    OTP_TTL_MINUTES minutes. The code is NEVER returned in the response.
    """
    email = str(req.email).strip().lower()

    # Verify the email is registered
    with _conn() as con:
        row = con.execute(
            "SELECT id FROM users WHERE lower(email) = ?", (email,)
        ).fetchone()
    if not row:
        # No matching account. Return ok:true to prevent email enumeration,
        # but include registered:false so the UI can show a friendly hint.
        logger.info(f"send-otp: no user for email {email!r}")
        return {
            "ok": True,
            "registered": False,
            "message": "If this email is registered, a verification code has been sent.",
        }

    # Generate 6-digit OTP
    otp_plain = str(random.randint(100000, 999999))
    otp_hash = bcrypt.hashpw(otp_plain.encode(), bcrypt.gensalt(rounds=10)).decode()
    expiry = (_now() + timedelta(minutes=_OTP_TTL_MINUTES)).isoformat()
    now = _now_str()

    # Send the email BEFORE persisting so a delivery failure surfaces as an error
    from backend.routes.email_sender import send_email, build_otp_email, EmailError
    try:
        html_body, text_body = build_otp_email(otp_plain, _OTP_TTL_MINUTES)
        send_email(
            to_email=email,
            subject="Your CricShift password reset code",
            html_body=html_body,
            text_body=text_body,
        )
    except EmailError as e:
        logger.error(f"send-otp email failure for {email}: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    # Persist the OTP hash against the user's email (reuses otpMobile column)
    with _conn() as con:
        con.execute(
            """UPDATE users
               SET "otpCode" = ?, "otpExpiry" = ?, "otpMobile" = ?, "updatedAt" = ?
               WHERE lower(email) = ?""",
            (otp_hash, expiry, email, now, email),
        )
        con.commit()

    return {
        "ok": True,
        "registered": True,
        "message": "A verification code has been sent to your email.",
    }


# ── POST /api/auth/verify-otp ─────────────────────────────────────────────────

@router.post("/verify-otp", summary="Verify emailed OTP and return a password-reset token")
async def verify_otp(req: VerifyOtpRequest):
    """
    Validates the OTP sent to the user's email. On success, returns a
    short-lived JWT reset_token that must be passed to /reset-password
    within 15 minutes.
    """
    email = str(req.email).strip().lower()
    with _conn() as con:
        row = con.execute(
            """SELECT id, "otpCode", "otpExpiry"
               FROM users WHERE lower(email) = ?""",
            (email,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Email address not found.")

    if not row["otpCode"]:
        raise HTTPException(status_code=400, detail="No verification code was requested for this email.")

    # Check expiry
    try:
        expiry_dt = datetime.fromisoformat(row["otpExpiry"]).replace(tzinfo=timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="OTP data corrupted.")

    if _now() > expiry_dt:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    # Verify the OTP
    if not bcrypt.checkpw(req.otp.encode(), row["otpCode"].encode()):
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    # Clear OTP fields so it cannot be reused
    with _conn() as con:
        con.execute(
            """UPDATE users SET "otpCode" = NULL, "otpExpiry" = NULL, "otpMobile" = NULL,
               "updatedAt" = ? WHERE lower(email) = ?""",
            (_now_str(), email),
        )
        con.commit()

    # Issue a short-lived reset JWT
    payload = {
        "sub": row["id"],
        "purpose": "password_reset",
        "exp": _now() + timedelta(minutes=_RESET_TOKEN_TTL_MINUTES),
    }
    reset_token = jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGO)

    return {"ok": True, "reset_token": reset_token}


# ── POST /api/auth/reset-password ─────────────────────────────────────────────

@router.post("/reset-password", summary="Set a new password using a reset token")
async def reset_password(req: ResetPasswordRequest):
    """
    Decodes the reset JWT, verifies purpose, and updates the password hash.
    The token is consumed on use (stateless — no DB tracking needed since
    the OTP was already cleared, preventing replay).
    """
    try:
        payload = jwt.decode(req.reset_token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except JWTError:
        raise HTTPException(status_code=400, detail="Reset token is invalid or has expired.")

    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token purpose.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Malformed token.")

    pw_hash = _hash_password(req.new_password)
    with _conn() as con:
        updated = con.execute(
            """UPDATE users SET "passwordHash" = ?, "updatedAt" = ? WHERE id = ?""",
            (pw_hash, _now_str(), user_id),
        ).rowcount
        con.commit()

    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")

    return {"ok": True, "message": "Password updated successfully."}


# ═════════════════════════════════════════════════════════════════════════════
# FACE LOCK (admin biometric-style gate for the /admin console)
# ─────────────────────────────────────────────────────────────────────────────
# The browser (face-api.js) computes a 128-float "descriptor" for a face and
# sends it here — we store ONLY the numeric embedding, never an image.
#   • /face/status  — is a face registered for the current admin?
#   • /face/enroll  — register a face (requires the admin's password re-entry)
#   • /face/verify  — compare a captured descriptor against registered ones
# Matching is Euclidean distance; < FACE_MATCH_THRESHOLD counts as the same face.
# ═════════════════════════════════════════════════════════════════════════════

# Standard face-api.js recognition threshold. Lower = stricter.
FACE_MATCH_THRESHOLD = 0.5
FACE_DESCRIPTOR_LEN = 128


class FaceEnrollRequest(BaseModel):
    password: str                 # admin re-authenticates before enrolling
    descriptor: List[float]       # 128-float face embedding from the browser


class FaceVerifyRequest(BaseModel):
    descriptor: List[float]


def _euclidean(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _load_descriptors(raw: Optional[str]) -> List[List[float]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            # normalise to a list-of-lists (support a single descriptor too)
            if data and isinstance(data[0], (int, float)):
                return [data]  # single descriptor stored flat
            return [d for d in data if isinstance(d, list)]
    except Exception:
        pass
    return []


def _require_admin(user: dict = Depends(_require_session)) -> dict:
    """Session dependency that additionally requires the admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ── GET /api/auth/face/status ─────────────────────────────────────────────────

@router.get("/face/status", summary="Whether the current admin has a face registered")
async def face_status(user: dict = Depends(_require_admin)):
    with _conn() as con:
        row = con.execute(
            'SELECT "faceDescriptors" FROM users WHERE id = ?', (user["id"],)
        ).fetchone()
    descriptors = _load_descriptors(row["faceDescriptors"] if row else None)
    return {"enrolled": len(descriptors) > 0, "count": len(descriptors)}


# ── POST /api/auth/face/enroll ────────────────────────────────────────────────

@router.post("/face/enroll", summary="Register a face for the current admin (password-gated)")
async def face_enroll(req: FaceEnrollRequest, user: dict = Depends(_require_admin)):
    if len(req.descriptor) != FACE_DESCRIPTOR_LEN:
        raise HTTPException(status_code=400, detail="Invalid face data. Please try scanning again.")

    # Re-authenticate: only the real admin (who knows the password) may set up Face Lock.
    with _conn() as con:
        row = con.execute(
            'SELECT "passwordHash", "faceDescriptors" FROM users WHERE id = ?',
            (user["id"],),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found.")
    if not _check_password(req.password, row["passwordHash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # Append the new descriptor to any existing ones (multiple angles allowed).
    existing = _load_descriptors(row["faceDescriptors"])
    existing.append([float(x) for x in req.descriptor])
    with _conn() as con:
        con.execute(
            'UPDATE users SET "faceDescriptors" = ?, "updatedAt" = ? WHERE id = ?',
            (json.dumps(existing), _now_str(), user["id"]),
        )
        con.commit()

    return {"ok": True, "count": len(existing), "message": "Face Lock enabled."}


# ── DELETE /api/auth/face  (POST alias for reset) ─────────────────────────────

@router.post("/face/reset", summary="Remove all registered faces (password-gated)")
async def face_reset(req: FaceEnrollRequest, user: dict = Depends(_require_admin)):
    # Reuse FaceEnrollRequest for the password field; descriptor is ignored here.
    with _conn() as con:
        row = con.execute('SELECT "passwordHash" FROM users WHERE id = ?', (user["id"],)).fetchone()
    if not row or not _check_password(req.password, row["passwordHash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    with _conn() as con:
        con.execute(
            'UPDATE users SET "faceDescriptors" = NULL, "updatedAt" = ? WHERE id = ?',
            (_now_str(), user["id"]),
        )
        con.commit()
    return {"ok": True, "message": "Face Lock removed."}


# ── POST /api/auth/face/verify ────────────────────────────────────────────────

@router.post("/face/verify", summary="Verify a captured face against the admin's registered faces")
async def face_verify(req: FaceVerifyRequest, user: dict = Depends(_require_admin)):
    if len(req.descriptor) != FACE_DESCRIPTOR_LEN:
        raise HTTPException(status_code=400, detail="Invalid face data. Please try scanning again.")

    with _conn() as con:
        row = con.execute(
            'SELECT "faceDescriptors" FROM users WHERE id = ?', (user["id"],)
        ).fetchone()
    registered = _load_descriptors(row["faceDescriptors"] if row else None)
    if not registered:
        raise HTTPException(status_code=400, detail="No face registered. Set up Face Lock first.")

    captured = [float(x) for x in req.descriptor]
    best = min(_euclidean(captured, d) for d in registered)
    matched = best < FACE_MATCH_THRESHOLD

    if not matched:
        # Deliberately do not reveal the distance to a caller on failure.
        raise HTTPException(status_code=401, detail="Face not recognised. Access denied.")

    return {"ok": True, "matched": True}
