"""API hasil dump."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from . import config, db, security

router = APIRouter(prefix="/api/dumps", dependencies=[Depends(security.require_operator)])


def _safe(path: Path) -> Path:
    resolved = path.resolve()
    if not str(resolved).startswith(str(config.DUMP_DIR.resolve())):
        raise HTTPException(400, "Path tidak valid")
    return resolved


@router.get("")
async def listing(target: str = "", kind: str = "") -> dict:
    sql = "SELECT d.*, t.brand, t.model FROM dumps d LEFT JOIN targets t ON t.id=d.target_id WHERE 1=1"
    params: list = []
    if target:
        sql += " AND d.target_id=?"
        params.append(target)
    if kind:
        sql += " AND d.kind=?"
        params.append(kind)
    sql += " ORDER BY d.created DESC LIMIT 400"
    rows = [dict(r) for r in db.q(sql, params)]
    total = sum(int(r.get("size") or 0) for r in rows)
    return {"dumps": rows, "total_size": total}


@router.get("/{dump_id}/download")
async def download(dump_id: str) -> FileResponse:
    row = db.one("SELECT * FROM dumps WHERE id=?", (dump_id,))
    if row is None:
        raise HTTPException(404, "Dump tidak ditemukan")
    path = _safe(config.DUMP_DIR / row["target_id"] / row["filename"])
    if not path.exists():
        raise HTTPException(410, "File sudah dihapus dari disk")
    return FileResponse(path, filename=row["filename"], media_type="application/octet-stream")


@router.delete("/{dump_id}")
async def remove(dump_id: str) -> dict:
    row = db.one("SELECT * FROM dumps WHERE id=?", (dump_id,))
    if row is None:
        raise HTTPException(404, "Dump tidak ditemukan")
    path = config.DUMP_DIR / row["target_id"] / row["filename"]
    path.unlink(missing_ok=True)
    db.x("DELETE FROM dumps WHERE id=?", (dump_id,))
    return {"ok": True}


@router.get("/preview/{dump_id}")
async def preview(dump_id: str) -> FileResponse:
    row = db.one("SELECT * FROM dumps WHERE id=?", (dump_id,))
    if row is None:
        raise HTTPException(404, "Dump tidak ditemukan")
    path = _safe(config.DUMP_DIR / row["target_id"] / row["filename"])
    if not path.exists():
        raise HTTPException(410, "File hilang")
    suffix = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".txt": "text/plain; charset=utf-8",
        ".json": "application/json", ".mp4": "video/mp4", ".m4a": "audio/mp4",
    }.get(suffix, "application/octet-stream")
    return FileResponse(path, media_type=mime)
