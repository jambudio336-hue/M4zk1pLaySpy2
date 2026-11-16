"""Resolusi geo/IP target via layanan publik."""
from __future__ import annotations

from typing import Any

import httpx


async def lookup(ip: str) -> dict[str, Any]:
    out: dict[str, Any] = {"ip": ip, "isp": "", "country": "", "city": "", "lat": None, "lon": None}
    if not ip or ip.startswith(("127.", "10.", "192.168.", "172.16.")):
        return out
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,city,lat,lon,isp,query"},
            )
            data = r.json()
            if data.get("status") == "success":
                out.update(
                    isp=data.get("isp", ""),
                    country=data.get("country", ""),
                    city=data.get("city", ""),
                    lat=data.get("lat"),
                    lon=data.get("lon"),
                )
    except (httpx.HTTPError, ValueError):
        pass
    return out
