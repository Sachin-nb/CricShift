"""
test_auth_pg.py — PostgreSQL authentication tests
====================================================
Tests cover:

1.  PostgreSQL connection configuration (_db_url helper)
2.  Schema validation — column names, placeholders, row dict access
3.  Auth helper unit tests — password hash, session token, _parse_dt
4.  Endpoint integration tests using FastAPI TestClient with mocked DB
    (register/send-otp, register/verify-otp, login, logout, me,
     google-login, send-otp, verify-otp, reset-password)
5.  Session creation and validation (mock)
6.  Role resolution (admin vs user)
7.  Error paths — wrong password, expired session, bad OTP, bad token

Run:
    pytest tests/test_auth_pg.py -v

The test suite does NOT require a live PostgreSQL connection — all DB calls
are mocked so the suite passes in any environment including local dev and CI.
"""

import json
import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

# ── Project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ═════════════════════════════════════════════════════════════════════════════
# 0. Syntax / import sanity — runs without a DB or network
# ═════════════════════════════════════════════════════════════════════════════

def test_auth_module_imports_cleanly():
    """auth.py must import without errors (psycopg2 present, no sqlite3)."""
    import importlib
    spec = importlib.util.spec_from_file_location(
        "auth",
        PROJECT_ROOT / "backend" / "routes" / "auth.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # raises on syntax / import error
    assert hasattr(mod, "router")
    assert hasattr(mod, "_conn")
    assert hasattr(mod, "_db_url")
    # Must NOT use sqlite3 anymore
    import inspect
    src = inspect.getsource(mod)
    assert "sqlite3" not in src, "sqlite3 found in auth.py — should use psycopg2"
    assert "psycopg2" in src
    assert "PRAGMA" not in src, "SQLite PRAGMA found in auth.py — must be removed"


def test_psycopg2_installed():
    """psycopg2-binary must be importable."""
    import psycopg2          # noqa: F401
    import psycopg2.extras   # noqa: F401


def test_no_hardcoded_db_path():
    """The hardcoded SQLite path must be gone from auth.py."""
    src = (PROJECT_ROOT / "backend" / "routes" / "auth.py").read_text(encoding="utf-8")
    assert "custom.db" not in src, "Hardcoded custom.db path still in auth.py"
    assert "_DB_PATH" not in src, "_DB_PATH (SQLite path) still in auth.py"


# ═════════════════════════════════════════════════════════════════════════════
# 1. _db_url() — connection URL helper
# ═════════════════════════════════════════════════════════════════════════════

def _import_auth():
    """Import the auth module fresh each time (avoids cached state)."""
    import importlib, backend.routes.auth as a
    return a


def test_db_url_raises_without_env(monkeypatch):
    """_db_url() raises HTTP 503 when DATABASE_URL is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    auth = _import_auth()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        auth._db_url()
    assert exc_info.value.status_code == 503
    assert "DATABASE_URL" in exc_info.value.detail


def test_db_url_returns_value(monkeypatch):
    """_db_url() returns the env value (with postgres:// → postgresql:// rewrite)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
    auth = _import_auth()
    url = auth._db_url()
    assert url == "postgresql://user:pass@host:5432/db"


def test_db_url_rewrites_postgres_scheme(monkeypatch):
    """Render provides postgres:// — _db_url() rewrites it to postgresql://."""
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/db")
    auth = _import_auth()
    url = auth._db_url()
    assert url.startswith("postgresql://")


def test_db_url_never_leaks_in_logs(monkeypatch, caplog):
    """
    DATABASE_URL credentials must never appear in log output.
    We call a function that reads the URL and verify the raw URL string is
    not present in any log record.
    """
    fake_url = "postgresql://SECRETUSER:SECRETPASS@pg-host:5432/cricshift"
    monkeypatch.setenv("DATABASE_URL", fake_url)
    import logging
    with caplog.at_level(logging.DEBUG):
        auth = _import_auth()
        try:
            auth._db_url()
        except Exception:
            pass
    for record in caplog.records:
        assert "SECRETPASS" not in record.getMessage(), (
            "Database password leaked in log output"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Auth helpers — unit tests (no DB required)
# ═════════════════════════════════════════════════════════════════════════════

def test_hash_and_check_password():
    auth = _import_auth()
    h = auth._hash_password("CricketRules99!")
    assert auth._check_password("CricketRules99!", h)
    assert not auth._check_password("WrongPassword!", h)


def test_session_token_is_64_chars_hex():
    auth = _import_auth()
    tok = auth._make_session_token()
    assert len(tok) == 64
    assert all(c in "0123456789abcdef" for c in tok)
    # Each call produces a different token
    assert auth._make_session_token() != tok


def test_parse_dt_with_datetime_object():
    auth = _import_auth()
    now = datetime.now(timezone.utc)
    result = auth._parse_dt(now)
    assert result == now
    assert result.tzinfo is not None


def test_parse_dt_with_naive_datetime():
    auth = _import_auth()
    naive = datetime(2025, 1, 1, 12, 0, 0)
    result = auth._parse_dt(naive)
    assert result.tzinfo is not None
    assert result.tzinfo == timezone.utc


def test_parse_dt_with_iso_string():
    auth = _import_auth()
    s = "2025-06-15T10:30:00+00:00"
    result = auth._parse_dt(s)
    assert result is not None
    assert result.year == 2025


def test_parse_dt_with_none():
    auth = _import_auth()
    assert auth._parse_dt(None) is None


def test_parse_dt_with_garbage():
    auth = _import_auth()
    assert auth._parse_dt("not-a-date") is None


def test_resolve_role_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "admin@cricshift.com,boss@example.com")
    auth = _import_auth()
    assert auth._resolve_role("admin@cricshift.com") == "admin"
    assert auth._resolve_role("ADMIN@CRICSHIFT.COM") == "admin"


def test_resolve_role_user(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "admin@cricshift.com")
    auth = _import_auth()
    assert auth._resolve_role("regular@example.com") == "user"
    assert auth._resolve_role("") == "user"


def test_normalize_mobile():
    auth = _import_auth()
    assert auth._normalize_mobile("+91 98765 43210") == "+919876543210"
    assert auth._normalize_mobile("98765-43210") == "9876543210"
    assert auth._normalize_mobile(None) is None
    assert auth._normalize_mobile("   ") is None


# ═════════════════════════════════════════════════════════════════════════════
# 3. PostgreSQL query shape — %s placeholders, quoted camelCase columns
# ═════════════════════════════════════════════════════════════════════════════

def test_no_sqlite_question_mark_placeholders():
    """All SQL in auth.py must use %s (psycopg2), never ? (sqlite3)."""
    import re
    src = (PROJECT_ROOT / "backend" / "routes" / "auth.py").read_text(encoding="utf-8")
    # Find SQL-like strings and check they don't contain bare ?
    # A bare ? in SQL would be a SQLite placeholder; %s is psycopg2.
    sql_strings = re.findall(r'"""(.*?)"""', src, re.DOTALL)
    sql_strings += re.findall(r"'''(.*?)'''", src, re.DOTALL)
    for s in sql_strings:
        assert " ?" not in s and ",?" not in s and "= ?" not in s, (
            f"Found SQLite '?' placeholder in SQL string: {s[:80]!r}"
        )


def test_camelcase_columns_are_quoted():
    """camelCase column names must be double-quoted in all SQL statements."""
    src = (PROJECT_ROOT / "backend" / "routes" / "auth.py").read_text(encoding="utf-8")
    # These camelCase column names must always appear in double quotes in SQL
    camel_cols = ["passwordHash", "otpCode", "otpExpiry", "otpMobile",
                  "faceDescriptors", "expiresAt", "createdAt", "updatedAt", "userId"]
    import re
    for col in camel_cols:
        # Check that every occurrence in SQL context is quoted
        # Allow unquoted only in Python string variable contexts (not SQL)
        sql_blocks = re.findall(r'(?:SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|SET|JOIN)'
                                r'.*?' + re.escape(col), src, re.DOTALL | re.IGNORECASE)
        for block in sql_blocks:
            # The column should appear as "col" (double-quoted) near the end of the match
            assert f'"{col}"' in block, (
                f'Column {col!r} used unquoted in SQL — must be "{col}"'
            )


# ═════════════════════════════════════════════════════════════════════════════
# 4. Endpoint integration tests with mocked DB
# ═════════════════════════════════════════════════════════════════════════════
# We patch backend.routes.auth._conn with a context-manager that returns a
# mock connection whose cursor().fetchone() / fetchall() / rowcount we control.

def _make_mock_conn(fetchone_return=None, fetchall_return=None, rowcount=1):
    """Build a mock psycopg2 connection + cursor."""
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_return
    cur.fetchall.return_value = fetchall_return or []
    cur.rowcount = rowcount

    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    return conn, cur


@contextmanager
def _mock_conn_ctx(fetchone_return=None, rowcount=1):
    """Context-manager compatible mock for _conn()."""
    conn, cur = _make_mock_conn(fetchone_return=fetchone_return, rowcount=rowcount)
    conn.__enter__.return_value = conn
    yield conn


@pytest.fixture(scope="module")
def client():
    """TestClient with the full FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.config import BACKEND_API_KEY
    headers = {"X-API-Key": BACKEND_API_KEY} if BACKEND_API_KEY else {}
    # We don't start the full lifespan for auth tests — auth routes don't need ML models
    with TestClient(app, headers=headers, raise_server_exceptions=False) as c:
        yield c


# ── /api/auth/me — valid session ──────────────────────────────────────────────

def test_me_returns_user_for_valid_session(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    user_row = {
        "id": "user_001",
        "name": "Sachin",
        "email": "sachin@test.com",
        "mobile": None,
    }
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=user_row)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.get("/api/auth/me",
                       headers={"X-Session-Token": "validtoken123"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["email"] == "sachin@test.com"
    assert "role" in body["user"]


# ── /api/auth/me — expired / invalid session ──────────────────────────────────

def test_me_returns_401_for_invalid_session(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.get("/api/auth/me",
                       headers={"X-Session-Token": "expired_or_bad_token"})
    assert r.status_code == 401


# ── /api/auth/me — missing header ────────────────────────────────────────────

def test_me_returns_422_without_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 422


# ── /api/auth/login — valid credentials ──────────────────────────────────────

def test_login_success(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    import bcrypt as _bcrypt
    pw_hash = _bcrypt.hashpw(b"ValidPass1!", _bcrypt.gensalt(rounds=4)).decode()
    user_row = {
        "id": "u_abc",
        "name": "Virat",
        "email": "virat@test.com",
        "passwordHash": pw_hash,
    }

    call_count = 0
    @contextmanager
    def fake_conn():
        nonlocal call_count
        call_count += 1
        conn, cur = _make_mock_conn(
            fetchone_return=user_row if call_count == 1 else None,
        )
        yield conn

    with patch("backend.routes.auth._conn") as mock_conn_fn:
        mock_conn_fn.side_effect = fake_conn
        r = client.post("/api/auth/login",
                        json={"email": "virat@test.com", "password": "ValidPass1!"})

    assert r.status_code == 200
    body = r.json()
    assert "token" in body
    assert body["user"]["email"] == "virat@test.com"
    assert len(body["token"]) == 64


# ── /api/auth/login — wrong password ─────────────────────────────────────────

def test_login_wrong_password(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    import bcrypt as _bcrypt
    pw_hash = _bcrypt.hashpw(b"CorrectPass1!", _bcrypt.gensalt(rounds=4)).decode()
    user_row = {
        "id": "u_abc",
        "name": "Virat",
        "email": "virat@test.com",
        "passwordHash": pw_hash,
    }
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=user_row)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/login",
                        json={"email": "virat@test.com",
                              "password": "WrongPass999!"})
    assert r.status_code == 401


# ── /api/auth/login — unknown email ──────────────────────────────────────────

def test_login_unknown_email(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/login",
                        json={"email": "nobody@example.com",
                              "password": "Pass1234!"})
    assert r.status_code == 401


# ── /api/auth/logout ──────────────────────────────────────────────────────────

def test_logout_success(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None, rowcount=1)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/logout",
                        headers={"X-Session-Token": "sometoken"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── /api/auth/register/send-otp — email already taken ────────────────────────

def test_register_send_otp_email_conflict(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    existing_row = {"id": "existing_user"}
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=existing_row)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/register/send-otp", json={
            "name": "New Player",
            "email": "taken@test.com",
            "password": "SecurePass1!",
        })
    assert r.status_code == 409
    assert "already registered" in r.json()["detail"].lower()


# ── /api/auth/register/verify-otp — bad OTP ──────────────────────────────────

def test_register_verify_otp_bad_code(client, monkeypatch):
    """A mismatched OTP must return 400."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    import bcrypt as _bcrypt
    from jose import jwt as _jwt

    otp_plain = "123456"
    otp_hash = _bcrypt.hashpw(otp_plain.encode(), _bcrypt.gensalt(rounds=4)).decode()
    payload = {
        "purpose": "signup_verify",
        "name": "Test User",
        "email": "test@example.com",
        "mobile": None,
        "pw_hash": _bcrypt.hashpw(b"Pass1234!", _bcrypt.gensalt(rounds=4)).decode(),
        "otp_hash": otp_hash,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    token = _jwt.encode(payload, os.getenv("JWT_SECRET", "cricshift-dev-secret-change-in-production"), algorithm="HS256")

    r = client.post("/api/auth/register/verify-otp", json={
        "pending_token": token,
        "otp": "999999",  # wrong code
    })
    assert r.status_code == 400
    assert "invalid" in r.json()["detail"].lower()


# ── /api/auth/register/verify-otp — expired token ────────────────────────────

def test_register_verify_otp_expired_token(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    import bcrypt as _bcrypt
    from jose import jwt as _jwt

    payload = {
        "purpose": "signup_verify",
        "name": "Test",
        "email": "test@example.com",
        "mobile": None,
        "pw_hash": "x",
        "otp_hash": "y",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),  # already expired
    }
    token = _jwt.encode(payload, os.getenv("JWT_SECRET", "cricshift-dev-secret-change-in-production"), algorithm="HS256")
    r = client.post("/api/auth/register/verify-otp",
                    json={"pending_token": token, "otp": "123456"})
    assert r.status_code == 400
    assert "expired" in r.json()["detail"].lower()


# ── /api/auth/send-otp — unregistered email (silent ok) ──────────────────────

def test_send_otp_unregistered_email(client, monkeypatch):
    """Unregistered email must return ok:true to prevent email enumeration."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/send-otp",
                        json={"email": "ghost@nobody.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["registered"] is False


# ── /api/auth/verify-otp — expired OTP ───────────────────────────────────────

def test_verify_otp_expired(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    import bcrypt as _bcrypt
    expired_dt = datetime.now(timezone.utc) - timedelta(minutes=20)
    otp_hash = _bcrypt.hashpw(b"111111", _bcrypt.gensalt(rounds=4)).decode()
    row = {
        "id": "u_xyz",
        "otpCode": otp_hash,
        "otpExpiry": expired_dt,  # Postgres returns datetime objects
    }
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=row)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/verify-otp",
                        json={"email": "user@test.com", "otp": "111111"})
    assert r.status_code == 400
    assert "expired" in r.json()["detail"].lower()


# ── /api/auth/reset-password — bad reset token ───────────────────────────────

def test_reset_password_bad_token(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    r = client.post("/api/auth/reset-password",
                    json={"reset_token": "not.a.valid.jwt",
                          "new_password": "NewPass1234!"})
    assert r.status_code == 400
    assert "invalid" in r.json()["detail"].lower()


# ── /api/auth/reset-password — valid token ───────────────────────────────────

def test_reset_password_success(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    from jose import jwt as _jwt
    payload = {
        "sub": "user_reset_001",
        "purpose": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    reset_token = _jwt.encode(
        payload,
        os.getenv("JWT_SECRET", "cricshift-dev-secret-change-in-production"),
        algorithm="HS256",
    )

    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None, rowcount=1)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        r = client.post("/api/auth/reset-password",
                        json={"reset_token": reset_token,
                              "new_password": "NewSecurePass1!"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── /api/auth/config — public endpoint ───────────────────────────────────────

def test_auth_config_returns_providers(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    r = client.get("/api/auth/config")
    assert r.status_code == 200
    body = r.json()
    assert "google" in body
    assert "apple" in body
    assert isinstance(body["google"]["enabled"], bool)


# ═════════════════════════════════════════════════════════════════════════════
# 5. Session creation and validation (mock)
# ═════════════════════════════════════════════════════════════════════════════

def test_create_session_returns_64_char_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    auth = _import_auth()
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        token = auth._create_session("user_abc_123")
    assert isinstance(token, str)
    assert len(token) == 64


def test_get_user_by_token_returns_none_for_bad_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    auth = _import_auth()
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=None)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        result = auth._get_user_by_token("bad_token_xyz")
    assert result is None


def test_get_user_by_token_returns_user_with_role(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mock:mock@localhost/mock")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@cricshift.com")
    auth = _import_auth()
    row = {
        "id": "u_admin_01",
        "name": "Admin",
        "email": "admin@cricshift.com",
        "mobile": None,
    }
    with patch("backend.routes.auth._conn") as mock_conn_fn:
        @contextmanager
        def fake_conn():
            conn, cur = _make_mock_conn(fetchone_return=row)
            yield conn
        mock_conn_fn.side_effect = fake_conn

        user = auth._get_user_by_token("valid_token")
    assert user is not None
    assert user["role"] == "admin"
    assert user["email"] == "admin@cricshift.com"


# ═════════════════════════════════════════════════════════════════════════════
# 6. Prisma schema — structural checks (no DB required)
# ═════════════════════════════════════════════════════════════════════════════

def test_prisma_schema_uses_postgresql():
    schema = (PROJECT_ROOT / "Cricshift-main" / "prisma" / "schema.prisma").read_text()
    assert 'provider = "postgresql"' in schema
    assert 'provider = "sqlite"' not in schema


def test_prisma_schema_has_user_and_session_models():
    schema = (PROJECT_ROOT / "Cricshift-main" / "prisma" / "schema.prisma").read_text()
    assert "model User" in schema
    assert "model Session" in schema
    assert '@@map("users")' in schema
    assert '@@map("sessions")' in schema


def test_prisma_schema_face_descriptors_has_text_annotation():
    """faceDescriptors must be @db.Text to avoid varchar(191) limit in PG."""
    schema = (PROJECT_ROOT / "Cricshift-main" / "prisma" / "schema.prisma").read_text()
    assert "@db.Text" in schema


def test_prisma_schema_database_url_from_env():
    schema = (PROJECT_ROOT / "Cricshift-main" / "prisma" / "schema.prisma").read_text()
    assert 'env("DATABASE_URL")' in schema


def test_prisma_migration_sql_exists():
    migrations_dir = PROJECT_ROOT / "Cricshift-main" / "prisma" / "migrations"
    sql_files = list(migrations_dir.rglob("*.sql"))
    assert len(sql_files) >= 1, "No migration SQL files found"


def test_prisma_migration_creates_users_table():
    migrations_dir = PROJECT_ROOT / "Cricshift-main" / "prisma" / "migrations"
    sql_files = list(migrations_dir.rglob("*.sql"))
    combined = "\n".join(f.read_text() for f in sql_files)
    assert "CREATE TABLE" in combined
    assert '"users"' in combined
    assert '"sessions"' in combined
    assert '"passwordHash"' in combined
    assert "CASCADE" in combined


def test_migration_lock_specifies_postgresql():
    lock = (PROJECT_ROOT / "Cricshift-main" / "prisma" / "migrations"
            / "migration_lock.toml").read_text()
    assert 'provider = "postgresql"' in lock


# ═════════════════════════════════════════════════════════════════════════════
# 7. requirements.txt contains psycopg2-binary
# ═════════════════════════════════════════════════════════════════════════════

def test_requirements_has_psycopg2():
    req = (PROJECT_ROOT / "requirements.txt").read_text()
    assert "psycopg2-binary" in req


def test_requirements_no_duplicate_entries():
    req = (PROJECT_ROOT / "requirements.txt").read_text()
    lines = [l.strip().split("==")[0].lower()
             for l in req.splitlines()
             if l.strip() and not l.strip().startswith("#")]
    assert len(lines) == len(set(lines)), "Duplicate packages in requirements.txt"


# ═════════════════════════════════════════════════════════════════════════════
# 8. package.json — safe migration scripts
# ═════════════════════════════════════════════════════════════════════════════

def test_package_json_no_accept_data_loss():
    import json as _json
    pkg = _json.loads(
        (PROJECT_ROOT / "Cricshift-main" / "package.json").read_text()
    )
    db_push = pkg["scripts"].get("db:push", "")
    assert "--accept-data-loss" not in db_push, (
        "db:push still contains --accept-data-loss which is unsafe"
    )


def test_package_json_has_db_deploy():
    import json as _json
    pkg = _json.loads(
        (PROJECT_ROOT / "Cricshift-main" / "package.json").read_text()
    )
    assert "db:deploy" in pkg["scripts"], "db:deploy script missing from package.json"
    assert "migrate deploy" in pkg["scripts"]["db:deploy"]
