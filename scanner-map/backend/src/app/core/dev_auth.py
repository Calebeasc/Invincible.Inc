import time
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.db.database import get_db

_ALGO = "HS256"
_TTL_S = 60 * 60 * 12
_hasher = PasswordHasher()


def _clean_email(email: str) -> str:
    return (email or "").strip().lower()


def get_operator(email: str):
    return get_db().execute(
        "SELECT email, password_hash, created_ms, last_login_ms FROM dev_operators WHERE email=?",
        (_clean_email(email),),
    ).fetchone()


def has_any_operator() -> bool:
    row = get_db().execute("SELECT email FROM dev_operators LIMIT 1").fetchone()
    return bool(row)


def create_operator(email: str, password: str):
    email = _clean_email(email)
    password_hash = _hasher.hash(password)
    now_ms = int(time.time() * 1000)
    conn = get_db()
    conn.execute(
        "INSERT INTO dev_operators (email, password_hash, created_ms, last_login_ms) VALUES (?, ?, ?, NULL)",
        (email, password_hash, now_ms),
    )
    conn.commit()
    return {"email": email, "created_ms": now_ms}


def verify_operator(email: str, password: str) -> bool:
    row = get_operator(email)
    if not row:
        return False
    try:
        ok = _hasher.verify(row["password_hash"], password)
    except VerifyMismatchError:
        return False

    if ok and _hasher.check_needs_rehash(row["password_hash"]):
        conn = get_db()
        conn.execute(
            "UPDATE dev_operators SET password_hash=? WHERE email=?",
            (_hasher.hash(password), _clean_email(email)),
        )
        conn.commit()
    return bool(ok)


def issue_token(email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": _clean_email(email),
        "iat": now,
        "exp": now + _TTL_S,
        "scope": "dev:elevation",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGO)
    conn = get_db()
    conn.execute(
        "UPDATE dev_operators SET last_login_ms=? WHERE email=?",
        (now * 1000, _clean_email(email)),
    )
    conn.commit()
    return token


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGO])
    except Exception:
        return None


# ── ADDED DURING LINUX SERVER SETUP (2026-06-12) ─────────────────────────────
# `require_developer` is imported by app/api/distribution.py but was missing
# from this module in every committed branch. Reconstructed to match its usage
# (`payload = require_developer(authorization)`): validate a Bearer token from
# the Authorization header and return its decoded payload, else 401.
# See scanner-map/SETUP_NOTES.md.
def require_developer(authorization: Optional[str]) -> dict:
    from fastapi import HTTPException

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split(" ", 1)[1].strip() if " " in authorization else authorization.strip()
    payload = decode_token(token)
    if not payload or payload.get("scope") != "dev:elevation":
        raise HTTPException(status_code=401, detail="Invalid or expired developer token")
    if not get_operator(payload.get("sub", "")):
        raise HTTPException(status_code=403, detail="Operator no longer exists")
    return payload
