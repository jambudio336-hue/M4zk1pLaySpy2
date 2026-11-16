"""Konfigurasi global + path runtime."""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
STATIC_DIR = WEB_DIR / "static"
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
BUILD_DIR = DATA_DIR / "builds"
DUMP_DIR = DATA_DIR / "dumps"
KEYSTORE_DIR = DATA_DIR / "keys"
DB_PATH = DATA_DIR / "m4zk1play.db"
CONFIG_PATH = ROOT / "config.json"
AGENT_DIR = ROOT / "agent"
PREBUILT_DIR = AGENT_DIR / "prebuilt"

DEFAULTS: dict[str, Any] = {
    "license_key": "M4ZK1PL4Y",
    "host": "0.0.0.0",
    "port": 8777,
    "c2_public_url": "",
    "agent_token_secret": "",
    "session_hours": 24,
    "uninstall_pin": "211421",
    "contact_email": "jambudio336@gmail.com",
    "contact_team": "Cyber Team M4zk1pL4y",
    "keystore_pass": "",
    "theme_accent": "#ff2d55",
    "require_license": True,
    "max_upload_mb": 300,
}

_cache: dict[str, Any] | None = None


def ensure_dirs() -> None:
    for d in (DATA_DIR, UPLOAD_DIR, BUILD_DIR, DUMP_DIR, KEYSTORE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Muat config; buat dari default bila belum ada."""
    global _cache
    if _cache is not None:
        return _cache

    ensure_dirs()
    if not CONFIG_PATH.exists():
        data = dict(DEFAULTS)
        data["agent_token_secret"] = secrets.token_urlsafe(48)
        data["keystore_pass"] = secrets.token_urlsafe(24)
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = {}

    data = dict(DEFAULTS)
    data.update({k: v for k, v in raw.items() if k in DEFAULTS})
    if not data.get("agent_token_secret"):
        data["agent_token_secret"] = secrets.token_urlsafe(48)
        save(data)
    if not data.get("keystore_pass"):
        data["keystore_pass"] = secrets.token_urlsafe(24)
        save(data)

    _cache = data
    return data


def save(data: dict[str, Any]) -> None:
    global _cache
    _cache = data
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)


def update(**kwargs: Any) -> dict[str, Any]:
    data = load()
    for k, v in kwargs.items():
        if k in DEFAULTS and v is not None:
            data[k] = v
    save(data)
    return data


def reset_cache() -> None:
    global _cache
    _cache = None
