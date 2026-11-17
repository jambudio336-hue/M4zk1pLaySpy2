"""Lookup geo IP ringan (offline-safe)."""
from __future__ import annotations

import httpx

_cache: dict[str, dict] = {}

EMPTY = {"isp": "", "country": "", "city": "", "lat": None, "lon": None}


def _private(ip: str) -> bool:
    return (
        ip.startswith(("10.", "127.", "192.168.", "0.", "172.16.", "172.17.",
                       "172.18.", "172.19.", "172.2", "172.30.", "172.31."))
        or ip in ("", "::1")
    )


async def lookup(ip: str) -> dict:
    if _private(ip):
        return dict(EMPTY)
    if ip in _cache:
        return _cache[ip]
    try:
        async with httpx.AsyncClient(timeout=6.0) as c:
            r = await c.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,city,lat,lon,isp"},
            )
            d = r.json()
        if d.get("status") == "success":
            out = {
                "isp": d.get("isp", ""), "country": d.get("country", ""),
                "city": d.get("city", ""), "lat": d.get("lat"), "lon": d.get("lon"),
            }
            _cache[ip] = out
            return out
    except (httpx.HTTPError, ValueError):
        pass
    _cache[ip] = dict(EMPTY)
    return dict(EMPTY)
