"""
Auth Routes — /api/auth/*
=========================
Handles user registration, login, logout, OTP-based password reset,
Google Sign-In, and Face Lock for the admin console.

Database backend (auto-detected at runtime)
-------------------------------------------
• LOCAL DEV  — DATABASE_URL is not set → uses SQLite at
               Cricshift-main/db/custom.db (same file the frontend Prisma
               client uses when running locally).
• PRODUCTION — DATABASE_URL is set (e.g. Render PostgreSQL) → uses
               psycopg2 to connect to the Postgres instance.  The schema
               is created by `prisma migrate deploy` as part of the
               frontend build step on Render.

Endpoints
---------
POST /api/auth/register/send-otp   — step 1 of signup: email a code
POST /api/auth/register/verify-otp — step 2: verify code, create account
POST /api/auth/login               — email/password login → session token
POST /api/auth/logout              — invalidate session
GET  /api/auth/me                  — return current user from session token
GET  /api/auth/config              — public auth config for the frontend
POST /api/auth/google              — Google Sign-In / sign-up
POST /api/auth/send-otp            — generate & email OTP for password reset
POST /api/auth/verify-otp          — check OTP; return a reset token
POST /api/auth/reset-password      — set new password using reset token
GET  /api/auth/face/status         — is a face registered for the admin?
POST /api/auth/face/enroll         — register a face (password-gated)
POST /api/auth/face/reset          — remove all faces (password-gated)
POST /api/auth/face/verify         — verify a captured face descriptor
"""

import json
import logging
import math
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

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

# ── Local SQLite path (used when DATABASE_URL is not set) ─────────────────────
_BASE = Path(__file__).resolve().parent.parent.parent
_SQLITE_PATH = _BASE / "Cricshift-main" / "db" / "custom.db"

# ── Database mode ─────────────────────────────────────────────────────────────

def _use_postgres() -> bool:
    """Return True when DATABASE_URL is configured (production / Render)."""
    return bool(os.getenv("DATABASE_URL", "").strip())


def _pg_url() -> str:
    """
    Return the PostgreSQL connection URL, rewriting postgres:// to
    postgresql:// as required by psycopg2.  Never logged or exposed.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


# ── Unified connection context manager ────────────────────────────────────────
#
# Both backends expose the same interface:
#   • rows behave like dicts  (sqlite3.Row  /  RealDictCursor)
#   • SQL uses  ?  (SQLite)  OR  %s  (PostgreSQL)  — handled by _ph() below
#   • commit() / rollback() behave the same
#

def _ph() -> str:
    """Return the parameter placeholder for the active database backend."""
    return "%s" if _use_postgres() else "?"


def _fix_sql(sql: str) -> str:
    """
    Translate SQL written with ? placeholders to %s for PostgreSQL, or
    keep ? for SQLite.  Always use ? in the source and call this helper.
    """
    if _use_postgres():
        return sql.replace("?", "%s")
    return sql


@contextmanager
def _conn() -> Generator:
    """
    Context manager that yields a database connection.

    SQLite path:   plain sqlite3 connection with WAL mode + Row factory.
    PostgreSQL path: psycopg2 RealDictCursor connection; commits on success,
                     rolls back on exception, always closes.
    """
    if _use_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(
            _pg_url(),
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(str(_SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _fetchone(conn, sql: str, params: tuple = ()) -> Optional[Dict]:
    """Execute a SELECT and return the first row as a plain dict, or None."""
    cur = conn.cursor() if _use_postgres() else conn
    if _use_postgres():
        cur.execute(_fix_sql(sql), params)
        row = cur.fetchone()
    else:
        row = conn.execute(_fix_sql(sql), params).fetchone()
    if row is None:
        return None
    return dict(row)


def _execute(conn, sql: str, params: tuple = ()):
    """Execute a DML/DDL statement and return the cursor."""
    if _use_postgres():
        cur = conn.cursor()
        cur.execute(_fix_sql(sql), params)
        return cur
    else:
        return conn.execute(_fix_sql(sql), params)


# ── Timestamp helpers ─────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_str() -> str:
    """ISO-8601 string — used for SQLite TEXT columns and as Postgres input."""
    return _now().isoformat()


def _parse_expiry(value) -> datetime:
    """
    Convert a DB expiry value to a timezone-aware datetime.
    SQLite stores datetimes as ISO strings; PostgreSQL returns real datetime
    objects.  Both are handled here.
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # SQLite string path
    try:
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot parse datetime: {value!r}")


# ── Helper utilities ──────────────────────────────────────────────────────────

def _google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def _admin_emails() -> set:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _resolve_role(email: str) -> str:
    return "admin" if (email or "").strip().lower() in _admin_emails() else "user"


def _normalize_mobile(mobile: Optional[str]) -> Optional[str]:
    if mobile is None:
        return None
    s = mobile.strip()
    has_plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None
    return ("+" + digits) if has_plus else digits


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_session_token() -> str:
    import uuid
    return uuid.uuid4().hex + uuid.uuid4().hex  # 64-char hex


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None

    @field_validator("password")
    @classmethod
    def pw_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("mobile")
    @classmethod
    def mobile_fmt(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 7:
            raise ValueError("Invalid mobile number.")
        return _normalize_mobile(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


class RegisterVerifyRequest(BaseModel):
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


# ── Session helpers ───────────────────────────────────────────────────────────

def _create_session(user_id: str) -> str:
    from cuid2 import Cuid as _Cuid
    token = _make_session_token()
    session_id = _Cuid().generate()
    expiry = (_now() + timedelta(days=_SESSION_TTL_DAYS)).isoformat()
    with _conn() as conn:
        _execute(
            conn,
            """INSERT INTO sessions (id, token, "userId", "expiresAt", "createdAt")
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, token, user_id, expiry, _now_str()),
        )
    return token


def _get_user_by_token(token: str) -> Optional[dict]:
    with _conn() as conn:
        row = _fetchone(
            conn,
            """SELECT u.id, u.name, u.email, u.mobile
               FROM sessions s
               JOIN users u ON u.id = s."userId"
               WHERE s.token = ? AND s."expiresAt" > ?""",
            (token, _now_str()),
        )
    if not row:
        return None
    row["role"] = _resolve_role(row["email"])
    return row


def _require_session(
    x_session_token: str = Header(..., alias="X-Session-Token"),
) -> dict:
    user = _get_user_by_token(x_session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return user


def _require_admin(user: dict = Depends(_require_session)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ── OTP email builders ────────────────────────────────────────────────────────

def _build_signup_otp_email(otp: str, minutes_valid: int):
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
            <span style="display:inline-block;background:#00c853;color:#000;font-weight:900;font-size:14px;padding:4px 10px;border-radius:6px;">&#127960;</span>
            <span style="color:#fff;font-weight:900;font-size:18px;letter-spacing:1px;margin-left:8px;vertical-align:middle;">CRICSHIFT</span>
          </td></tr>
          <tr><td style="padding:8px 32px 0 32px;">
            <h1 style="color:#fff;font-size:22px;margin:16px 0 4px 0;text-transform:uppercase;">Verify your email</h1>
            <p style="color:rgba(255,255,255,0.55);font-size:14px;margin:0 0 20px 0;">
              Welcome to CricShift! Use the code below to finish creating your account.
            </p>
          </td></tr>
          <tr><td align="center" style="padding:8px 32px 24px 32px;">
            <div style="background:#0d0d0d;border:1px solid #00c853;border-radius:12px;padding:18px 0;margin:0 0 16px 0;">
              <span style="color:#00c853;font-size:34px;font-weight:900;letter-spacing:10px;">{otp}</span>
            </div>
            <p style="color:rgba(255,255,255,0.45);font-size:12px;margin:0;">
              This code expires in {minutes_valid} minutes. If you didn&apos;t sign up, ignore this email.
            </p>
          </td></tr>
          <tr><td style="padding:0 32px 28px 32px;border-top:1px solid rgba(255,255,255,0.06);">
            <p style="color:rgba(255,255,255,0.3);font-size:11px;margin:16px 0 0 0;">&copy; CricShift &#8212; AI-Powered Cricket Analytics</p>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""
    return html, text


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

# ── POST /api/auth/register/send-otp ──────────────────────────────────────────

@router.post("/register/send-otp",
             summary="Start signup: email a verification code")
async def register_send_otp(req: RegisterRequest):
    email = str(req.email).strip().lower()

    with _conn() as conn:
        if _fetchone(conn, "SELECT id FROM users WHERE lower(email) = ?", (email,)):
            raise HTTPException(status_code=409,
                                detail="Email already registered. Please log in.")
        if req.mobile:
            if _fetchone(conn, "SELECT id FROM users WHERE mobile = ?", (req.mobile,)):
                raise HTTPException(status_code=409,
                                    detail="Mobile number already registered.")

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
        logger.error("register send-otp email failure for %s", email)
        raise HTTPException(status_code=502, detail=str(e))

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

@router.post("/register/verify-otp",
             summary="Finish signup: verify code, create account")
async def register_verify_otp(req: RegisterVerifyRequest):
    try:
        payload = jwt.decode(req.pending_token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except JWTError:
        raise HTTPException(status_code=400,
                            detail="Your code has expired. Please start again.")

    if payload.get("purpose") != "signup_verify":
        raise HTTPException(status_code=400, detail="Invalid verification token.")

    if not bcrypt.checkpw(req.otp.encode(), payload["otp_hash"].encode()):
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    name = payload["name"]
    email = payload["email"]
    mobile = payload.get("mobile")
    pw_hash = payload["pw_hash"]

    try:
        with _conn() as conn:
            if _fetchone(conn, "SELECT id FROM users WHERE lower(email) = ?", (email,)):
                raise HTTPException(status_code=409,
                                    detail="Email already registered. Please log in.")

            from cuid2 import Cuid as _Cuid
            user_id = _Cuid().generate()
            now = _now_str()
            _execute(
                conn,
                """INSERT INTO users
                   (id, name, email, "passwordHash", mobile, role,
                    "createdAt", "updatedAt")
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, name, email, pw_hash, mobile,
                 _resolve_role(email), now, now),
            )

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
    except Exception:
        logger.exception("Register verify failed")
        raise HTTPException(status_code=500, detail="Registration error.")


# ── POST /api/auth/login ──────────────────────────────────────────────────────

@router.post("/login", summary="Login with email and password")
async def login(req: LoginRequest):
    try:
        with _conn() as conn:
            row = _fetchone(
                conn,
                'SELECT id, name, email, "passwordHash" FROM users WHERE email = ?',
                (str(req.email),),
            )
        if not row:
            raise HTTPException(status_code=401,
                                detail="Invalid email or password.")
        if not _check_password(req.password, row["passwordHash"]):
            raise HTTPException(status_code=401,
                                detail="Invalid email or password.")

        token = _create_session(row["id"])
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
    except Exception:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail="Login error.")


# ── POST /api/auth/logout ─────────────────────────────────────────────────────

@router.post("/logout", summary="Invalidate the current session")
async def logout(
    x_session_token: str = Header(..., alias="X-Session-Token"),
):
    with _conn() as conn:
        _execute(conn, "DELETE FROM sessions WHERE token = ?", (x_session_token,))
    return {"ok": True}


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

@router.get("/me", summary="Return the currently authenticated user")
async def me(user: dict = Depends(_require_session)):
    return {"user": user}


# ── GET /api/auth/config ──────────────────────────────────────────────────────

@router.get("/config", summary="Public auth config for the frontend")
async def auth_config():
    return {
        "google": {
            "enabled": bool(_google_client_id()),
            "client_id": _google_client_id(),
        },
        "apple": {
            "enabled": bool(os.getenv("APPLE_CLIENT_ID", "").strip()),
        },
    }


# ── POST /api/auth/google ─────────────────────────────────────────────────────

@router.post("/google", summary="Sign in / sign up with a Google ID token")
async def google_login(req: GoogleLoginRequest):
    client_id = _google_client_id()
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In is not configured on the server (GOOGLE_CLIENT_ID missing).",
        )

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            req.credential,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=60,
        )
    except ValueError as e:
        err_str = str(e).lower()
        logger.warning("Google token verification failed: %s", e)
        if "audience" in err_str or "client_id" in err_str:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Google sign-in failed: this app's origin is not authorised. "
                    "Add your deployed domain to Authorized JavaScript Origins "
                    "in Google Cloud Console → Credentials."
                ),
            )
        raise HTTPException(status_code=401, detail=f"Google sign-in failed: {e}")
    except Exception as e:
        logger.exception("Google verification error")
        raise HTTPException(status_code=502, detail=f"Could not verify Google token: {e}")

    email = (idinfo.get("email") or "").strip().lower()
    email_verified = idinfo.get("email_verified", False)
    name = idinfo.get("name") or (email.split("@")[0] if email else "Player")

    if not email:
        raise HTTPException(status_code=400,
                            detail="Google account has no email address.")
    if not email_verified:
        raise HTTPException(status_code=400,
                            detail="Google email is not verified.")

    try:
        with _conn() as conn:
            row = _fetchone(
                conn,
                "SELECT id, name, email FROM users WHERE lower(email) = ?",
                (email,),
            )

        if row:
            user_id = row["id"]
            user_name = row["name"]
        else:
            from cuid2 import Cuid as _Cuid
            import secrets
            user_id = _Cuid().generate()
            random_pw_hash = _hash_password(secrets.token_urlsafe(32))
            now = _now_str()
            with _conn() as conn:
                _execute(
                    conn,
                    """INSERT INTO users
                       (id, name, email, "passwordHash", mobile, role,
                        "createdAt", "updatedAt")
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, name, email, random_pw_hash, None,
                     _resolve_role(email), now, now),
                )
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
    except Exception:
        logger.exception("Google login failed")
        raise HTTPException(status_code=500, detail="Google login error.")


# ── POST /api/auth/send-otp ───────────────────────────────────────────────────

@router.post("/send-otp",
             summary="Generate and email an OTP for password reset")
async def send_otp(req: SendOtpRequest):
    email = str(req.email).strip().lower()

    with _conn() as conn:
        row = _fetchone(conn,
                        "SELECT id FROM users WHERE lower(email) = ?",
                        (email,))
    if not row:
        return {
            "ok": True,
            "registered": False,
            "message": "If this email is registered, a verification code has been sent.",
        }

    otp_plain = str(random.randint(100000, 999999))
    otp_hash = bcrypt.hashpw(otp_plain.encode(), bcrypt.gensalt(rounds=10)).decode()
    expiry = (_now() + timedelta(minutes=_OTP_TTL_MINUTES)).isoformat()

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
        logger.error("send-otp email failure for %s", email)
        raise HTTPException(status_code=502, detail=str(e))

    with _conn() as conn:
        _execute(
            conn,
            """UPDATE users
               SET "otpCode" = ?, "otpExpiry" = ?,
                   "otpMobile" = ?, "updatedAt" = ?
               WHERE lower(email) = ?""",
            (otp_hash, expiry, email, _now_str(), email),
        )
    return {
        "ok": True,
        "registered": True,
        "message": "A verification code has been sent to your email.",
    }


# ── POST /api/auth/verify-otp ─────────────────────────────────────────────────

@router.post("/verify-otp",
             summary="Verify emailed OTP; return a password-reset token")
async def verify_otp(req: VerifyOtpRequest):
    email = str(req.email).strip().lower()

    with _conn() as conn:
        row = _fetchone(
            conn,
            'SELECT id, "otpCode", "otpExpiry" FROM users WHERE lower(email) = ?',
            (email,),
        )
    if not row:
        raise HTTPException(status_code=400, detail="Email address not found.")
    if not row["otpCode"]:
        raise HTTPException(status_code=400,
                            detail="No verification code was requested for this email.")

    try:
        expiry_dt = _parse_expiry(row["otpExpiry"])
    except ValueError:
        raise HTTPException(status_code=400, detail="OTP data corrupted.")

    if _now() > expiry_dt:
        raise HTTPException(status_code=400,
                            detail="OTP has expired. Please request a new one.")

    if not bcrypt.checkpw(req.otp.encode(), row["otpCode"].encode()):
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    with _conn() as conn:
        _execute(
            conn,
            """UPDATE users
               SET "otpCode" = NULL, "otpExpiry" = NULL,
                   "otpMobile" = NULL, "updatedAt" = ?
               WHERE lower(email) = ?""",
            (_now_str(), email),
        )

    payload = {
        "sub": row["id"],
        "purpose": "password_reset",
        "exp": _now() + timedelta(minutes=_RESET_TOKEN_TTL_MINUTES),
    }
    reset_token = jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGO)
    return {"ok": True, "reset_token": reset_token}


# ── POST /api/auth/reset-password ─────────────────────────────────────────────

@router.post("/reset-password",
             summary="Set a new password using a reset token")
async def reset_password(req: ResetPasswordRequest):
    try:
        payload = jwt.decode(req.reset_token, _JWT_SECRET, algorithms=[_JWT_ALGO])
    except JWTError:
        raise HTTPException(status_code=400,
                            detail="Reset token is invalid or has expired.")

    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid token purpose.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Malformed token.")

    pw_hash = _hash_password(req.new_password)
    with _conn() as conn:
        cur = _execute(
            conn,
            'UPDATE users SET "passwordHash" = ?, "updatedAt" = ? WHERE id = ?',
            (pw_hash, _now_str(), user_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found.")

    return {"ok": True, "message": "Password updated successfully."}


# ═════════════════════════════════════════════════════════════════════════════
# FACE LOCK (admin biometric gate)
# ═════════════════════════════════════════════════════════════════════════════

FACE_MATCH_THRESHOLD = 0.5
FACE_DESCRIPTOR_LEN = 128


class FaceEnrollRequest(BaseModel):
    password: str
    descriptor: List[float]


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
            if data and isinstance(data[0], (int, float)):
                return [data]
            return [d for d in data if isinstance(d, list)]
    except Exception:
        pass
    return []


# ── GET /api/auth/face/status ─────────────────────────────────────────────────

@router.get("/face/status",
            summary="Whether the current admin has a face registered")
async def face_status(user: dict = Depends(_require_admin)):
    with _conn() as conn:
        row = _fetchone(conn,
                        'SELECT "faceDescriptors" FROM users WHERE id = ?',
                        (user["id"],))
    descriptors = _load_descriptors(row["faceDescriptors"] if row else None)
    return {"enrolled": len(descriptors) > 0, "count": len(descriptors)}


# ── POST /api/auth/face/enroll ────────────────────────────────────────────────

@router.post("/face/enroll",
             summary="Register a face for the current admin (password-gated)")
async def face_enroll(req: FaceEnrollRequest,
                      user: dict = Depends(_require_admin)):
    if len(req.descriptor) != FACE_DESCRIPTOR_LEN:
        raise HTTPException(status_code=400,
                            detail="Invalid face data. Please try scanning again.")

    with _conn() as conn:
        row = _fetchone(
            conn,
            'SELECT "passwordHash", "faceDescriptors" FROM users WHERE id = ?',
            (user["id"],),
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found.")
    if not _check_password(req.password, row["passwordHash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    existing = _load_descriptors(row["faceDescriptors"])
    existing.append([float(x) for x in req.descriptor])
    with _conn() as conn:
        _execute(
            conn,
            'UPDATE users SET "faceDescriptors" = ?, "updatedAt" = ? WHERE id = ?',
            (json.dumps(existing), _now_str(), user["id"]),
        )
    return {"ok": True, "count": len(existing), "message": "Face Lock enabled."}


# ── POST /api/auth/face/reset ─────────────────────────────────────────────────

@router.post("/face/reset",
             summary="Remove all registered faces (password-gated)")
async def face_reset(req: FaceEnrollRequest,
                     user: dict = Depends(_require_admin)):
    with _conn() as conn:
        row = _fetchone(conn,
                        'SELECT "passwordHash" FROM users WHERE id = ?',
                        (user["id"],))
    if not row or not _check_password(req.password, row["passwordHash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    with _conn() as conn:
        _execute(
            conn,
            'UPDATE users SET "faceDescriptors" = NULL, "updatedAt" = ? WHERE id = ?',
            (_now_str(), user["id"]),
        )
    return {"ok": True, "message": "Face Lock removed."}


# ── POST /api/auth/face/verify ────────────────────────────────────────────────

@router.post("/face/verify",
             summary="Verify a captured face against the admin's registered faces")
async def face_verify(req: FaceVerifyRequest,
                      user: dict = Depends(_require_admin)):
    if len(req.descriptor) != FACE_DESCRIPTOR_LEN:
        raise HTTPException(status_code=400,
                            detail="Invalid face data. Please try scanning again.")

    with _conn() as conn:
        row = _fetchone(conn,
                        'SELECT "faceDescriptors" FROM users WHERE id = ?',
                        (user["id"],))
    registered = _load_descriptors(row["faceDescriptors"] if row else None)
    if not registered:
        raise HTTPException(status_code=400,
                            detail="No face registered. Set up Face Lock first.")

    captured = [float(x) for x in req.descriptor]
    best = min(_euclidean(captured, d) for d in registered)
    if best >= FACE_MATCH_THRESHOLD:
        raise HTTPException(status_code=401,
                            detail="Face not recognised. Access denied.")

    return {"ok": True, "matched": True}
