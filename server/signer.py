"""Keystore + signing APK."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import config


def _tool(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for base in ("/usr/lib/android-sdk/build-tools", "/opt/android-sdk/build-tools"):
        p = Path(base)
        if p.is_dir():
            for sub in sorted(p.iterdir(), reverse=True):
                cand = sub / name
                if cand.exists():
                    return str(cand)
    return None


def ensure_keystore() -> Path:
    ks = config.KEYSTORE_DIR / "m4zk1play.jks"
    if ks.exists():
        return ks
    keytool = _tool("keytool") or "keytool"
    proc = subprocess.run(
        [
            keytool, "-genkeypair", "-v",
            "-keystore", str(ks),
            "-alias", "m4zk1play",
            "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000",
            "-storepass", str(config.get("keystore_pass")),
            "-keypass", str(config.get("keystore_pass")),
            "-dname", "CN=M4zk1pLaySpy, OU=CyberTeam, O=M4ZK1PL4Y, L=ID, C=ID",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or b"")[-800:].decode(errors="replace")
        raise RuntimeError(f"keytool gagal: {tail}")
    return ks


def zipalign(src: Path, dst: Path) -> None:
    tool = _tool("zipalign")
    if tool is None:
        shutil.copy2(src, dst)
        return
    proc = subprocess.run([tool, "-p", "4", str(src), str(dst)], capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or b"")[-800:].decode(errors="replace")
        raise RuntimeError(f"zipalign gagal: {tail}")


def sign(apk: Path) -> None:
    ks = ensure_keystore()
    tool = _tool("apksigner")

    if tool is None:
        jarsigner = _tool("jarsigner") or "jarsigner"
        proc = subprocess.run(
            [jarsigner, "-keystore", str(ks), "-storepass",
             str(config.get("keystore_pass")), str(apk), "m4zk1play"],
            capture_output=True,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or b"")[-800:].decode(errors="replace")
            raise RuntimeError(f"jarsigner gagal: {tail}")
        return

    base = [
        tool, "sign",
        "--ks", str(ks),
        "--ks-key-alias", "m4zk1play",
        "--ks-pass", f"pass:{config.get('keystore_pass')}",
        "--key-pass", f"pass:{config.get('keystore_pass')}",
        "--v1-signing-enabled", "true",
        "--v2-signing-enabled", "true",
    ]

    proc = subprocess.run(
        base + ["--v3-signing-enabled", "true", str(apk)], capture_output=True
    )
    if proc.returncode != 0:
        proc = subprocess.run(base + [str(apk)], capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or b"")[-800:].decode(errors="replace")
        raise RuntimeError(f"apksigner gagal: {tail}")
