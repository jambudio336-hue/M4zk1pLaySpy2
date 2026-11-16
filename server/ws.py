"""Hub WebSocket: agent (target) + operator (dashboard)."""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket

from . import db


class Hub:
    def __init__(self) -> None:
        self.agents: dict[str, WebSocket] = {}
        self.operators: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    # ---------- operator ----------
    async def add_operator(self, ws: WebSocket) -> None:
        async with self.lock:
            self.operators.add(ws)

    async def drop_operator(self, ws: WebSocket) -> None:
        async with self.lock:
            self.operators.discard(ws)

    async def to_operators(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        text = json.dumps(payload)
        for ws in list(self.operators):
            try:
                await ws.send_text(text)
            except RuntimeError:
                dead.append(ws)
        for ws in dead:
            await self.drop_operator(ws)

    # ---------- agent ----------
    async def add_agent(self, target_id: str, ws: WebSocket) -> None:
        async with self.lock:
            old = self.agents.get(target_id)
            self.agents[target_id] = ws
        if old is not None and old is not ws:
            try:
                await old.close()
            except RuntimeError:
                pass
        db.x("UPDATE targets SET online=1,last_seen=? WHERE id=?", (time.time(), target_id))
        await self.to_operators({"t": "presence", "id": target_id, "online": True})

    async def drop_agent(self, target_id: str, ws: WebSocket) -> None:
        async with self.lock:
            if self.agents.get(target_id) is ws:
                self.agents.pop(target_id, None)
        db.x("UPDATE targets SET online=0,last_seen=? WHERE id=?", (time.time(), target_id))
        await self.to_operators({"t": "presence", "id": target_id, "online": False})

    def is_online(self, target_id: str) -> bool:
        return target_id in self.agents

    async def send_to(self, target_id: str, payload: dict[str, Any]) -> bool:
        ws = self.agents.get(target_id)
        if ws is None:
            return False
        try:
            await ws.send_text(json.dumps(payload))
            return True
        except RuntimeError:
            await self.drop_agent(target_id, ws)
            return False

    async def command(self, target_id: str, ctype: str, args: dict[str, Any] | None = None) -> str:
        cid = f"{int(time.time()*1000):x}{target_id[:6]}"
        now = time.time()
        db.x(
            "INSERT INTO commands(id,target_id,type,args,status,created,updated)"
            " VALUES(?,?,?,?,'queued',?,?)",
            (cid, target_id, ctype, json.dumps(args or {}), now, now),
        )
        sent = await self.send_to(target_id, {"t": "cmd", "id": cid, "type": ctype, "args": args or {}})
        if sent:
            db.x("UPDATE commands SET status='sent',updated=? WHERE id=?", (time.time(), cid))
        await self.to_operators({"t": "cmd", "id": cid, "target": target_id, "type": ctype})
        return cid

    async def flush_queue(self, target_id: str) -> None:
        rows = db.q(
            "SELECT id,type,args FROM commands WHERE target_id=? AND status='queued'"
            " ORDER BY created LIMIT 40",
            (target_id,),
        )
        for r in rows:
            await self.send_to(
                target_id,
                {"t": "cmd", "id": r["id"], "type": r["type"], "args": json.loads(r["args"] or "{}")},
            )
            db.x("UPDATE commands SET status='sent',updated=? WHERE id=?", (time.time(), r["id"]))


hub = Hub()
