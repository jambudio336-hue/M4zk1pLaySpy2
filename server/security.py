"""License gate, sesi operator, rate limit."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

from fastapi import HTTPException, Request

from . import config, db

COOKIE = "mzk_sess"
_tries: dict[str, list[float]] = {}


def _hash(token: str) -> str:
    secret = str(config.get("agent_token_secret", ""))
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def rate_ok(ip: str) -> bool:
    window = int(config.get("login_window", 300) or 300)
    limit = int(config.get("login_max_try", 6) or 6)
    now = time.time()
    hits = [t for t in _tries.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        _tries[ip] = hits
        return False
    hits.append(now)
    _tries[ip] = hits
    return True


def create_session(ip: str, ua: str) -> str:
    token = secrets.token_urlsafe(32)
    hours = int(config.get("session_hours", 24) or 24)
    now = time.time()
    db.x(
        "INSERT INTO sessions(token,ip,ua,created,expires) VALUES(?,?,?,?,?)",
        (_hash(token), ip, ua[:300], now, now + hours * 3600),
    )
    db.audit("login", f"{ip} :: {ua[:80]}")
    return token


def valid_session(token: str | None) -> bool:
    if not token:
        return False
    row = db.one("SELECT expires FROM sessions WHERE token=?", (_hash(token),))
    if row is None:
        return False
    if float(row["expires"]) < time.time():
        db.x("DELETE FROM sessions WHERE token=?", (_hash(token),))
        return False
    return True


def kill_session(token: str | None) -> None:
    if token:
        db.x("DELETE FROM sessions WHERE token=?", (_hash(token),))


def purge_sessions() -> None:
    db.x("DELETE FROM sessions WHERE expires < ?", (time.time(),))


def check_license(key: str) -> bool:
    expected = str(config.get("license_key", "M4ZK1PL4Y")).strip()
    return secrets.compare_digest(key.strip().upper(), expected.upper())


async def require_operator(request: Request) -> str:
    if not config.get("require_license", True):
        return "bypass"
    token = request.cookies.get(COOKIE)
    if not valid_session(token):
        raise HTTPException(status_code=401, detail="Sesi tidak valid")
    return token or ""


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("cf-connecting-ip", "")
    if real:
        return real.strip()
    return request.client.host if request.client else "0.0.0.0"


def client_ip_from_ws(ws: Any) -> str:
    try:
        headers = ws.headers
        for key in ("x-forwarded-for", "cf-connecting-ip", "x-real-ip"):
            val = headers.get(key, "")
            if val:
                return val.split(",")[0].strip()
        if ws.client is not None:
            return ws.client.host
    except (AttributeError, KeyError, TypeError):
        pass
    return "0.0.0.0"
