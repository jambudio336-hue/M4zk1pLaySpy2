"""Tunnel publik: cloudflared / ngrok / bore / localtunnel / ssh."""
from __future__ import annotations

import asyncio
import re
import shutil
import time
from typing import Any

from . import config, db

PATTERN = re.compile(
    r"https://[a-z0-9][a-z0-9.\-]*\."
    r"(?:trycloudflare\.com|ngrok(?:-free)?\.(?:app|io|dev)|loca\.lt|lhr\.life|bore\.pub|localhost\.run)"
)

BIN = {"cloudflared": "cloudflared", "ngrok": "ngrok", "bore": "bore",
       "localx": "npx", "ssh": "ssh"}
ORDER = ("cloudflared", "ngrok", "bore", "localx", "ssh")

ARGS = {
    "cloudflared": lambda p: ["cloudflared", "tunnel", "--no-autoupdate",
                              "--url", f"http://127.0.0.1:{p}"],
    "ngrok": lambda p: ["ngrok", "http", str(p), "--log=stdout"],
    "bore": lambda p: ["bore", "local", str(p), "--to", "bore.pub"],
    "localx": lambda p: ["npx", "--yes", "localtunnel", "--port", str(p)],
    "ssh": lambda p: ["ssh", "-o", "StrictHostKeyChecking=no",
                      "-o", "ServerAliveInterval=30",
                      "-R", f"80:127.0.0.1:{p}", "nokey@localhost.run"],
}

state: dict[str, Any] = {"proc": None, "kind": "", "url": "", "started": 0.0, "log": []}


def available() -> dict[str, bool]:
    return {k: bool(shutil.which(b)) for k, b in BIN.items()}


def _note(line: str) -> None:
    state["log"].append(line.rstrip()[:400])
    if len(state["log"]) > 220:
        del state["log"][:110]


async def _pump(proc: asyncio.subprocess.Process) -> None:
    if proc.stdout is None:
        return
    while True:
        raw = await proc.stdout.readline()
        if not raw:
            break
        line = raw.decode(errors="replace")
        _note(line)
        if not state["url"]:
            m = PATTERN.search(line)
            if m:
                state["url"] = m.group(0)


async def start(kind: str = "auto") -> dict:
    await stop()
    if kind == "auto":
        av = available()
        kind = next((k for k in ORDER if av.get(k)), "")
        if not kind:
            raise RuntimeError("tidak ada tunnel client (cloudflared/ngrok/bore/npx/ssh)")
    if kind not in ARGS:
        raise RuntimeError(f"engine '{kind}' tidak dikenal")
    if not shutil.which(BIN[kind]):
        raise RuntimeError(f"'{BIN[kind]}' belum terpasang")

    port = int(config.get("port", 8777))
    try:
        proc = await asyncio.create_subprocess_exec(
            *ARGS[kind](port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as exc:
        raise RuntimeError(str(exc)) from exc

    state.update(proc=proc, kind=kind, url="", started=time.time(), log=[])
    asyncio.create_task(_pump(proc))

    for _ in range(140):
        await asyncio.sleep(0.5)
        if state["url"] or proc.returncode is not None:
            break

    if not state["url"]:
        await stop()
        raise RuntimeError("gagal memperoleh URL publik")

    config.update(c2_public_url=state["url"])
    db.audit("tunnel", f"{kind} :: {state['url']}")
    return status()


async def stop() -> dict:
    proc = state.get("proc")
    if proc is not None and proc.returncode is None:
        try:
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=6)
        except (ProcessLookupError, asyncio.TimeoutError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass
    state.update(proc=None, url="", started=0.0)
    if config.get("c2_public_url"):
        config.update(c2_public_url="")
    return status()


def status() -> dict:
    return {
        "on": bool(state.get("proc")) and bool(state.get("url")),
        "kind": state.get("kind", ""),
        "url": state.get("url", ""),
        "uptime": int(time.time() - state["started"]) if state.get("started") else 0,
        "available": available(),
        "log": state.get("log", [])[-60:],
    }
