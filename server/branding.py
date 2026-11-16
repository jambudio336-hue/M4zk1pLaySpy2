"""Branding APK: ikon, label, wallpaper, teks wizard."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

ICON_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

WALL_SIZES = {
    "drawable-mdpi": (320, 480),
    "drawable-hdpi": (480, 800),
    "drawable-xhdpi": (720, 1280),
    "drawable-xxhdpi": (1080, 1920),
}

# nama unik supaya tidak bentrok dengan resource APK target
ICON_NAME = "mzk_icon"
WALL_NAME = "mzk_wall"


def _square(raw: bytes, size: int) -> Image.Image:
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    side = min(img.size)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    return img.resize((size, size), Image.LANCZOS)


def write_icons(raw: bytes, res_dir: Path) -> None:
    """Tulis ikon dengan nama unik (mzk_icon) di semua densitas."""
    for folder, size in ICON_SIZES.items():
        out = res_dir / folder
        out.mkdir(parents=True, exist_ok=True)
        _square(raw, size).save(out / f"{ICON_NAME}.png", "PNG")


def write_wallpaper(raw: bytes, res_dir: Path) -> None:
    src = Image.open(io.BytesIO(raw)).convert("RGB")
    for folder, (w, h) in WALL_SIZES.items():
        out = res_dir / folder
        out.mkdir(parents=True, exist_ok=True)
        src.resize((w, h), Image.LANCZOS).save(out / f"{WALL_NAME}.jpg", "JPEG", quality=88)


def patch_strings(strings_file: Path, label: str, wizard: str, email: str, team: str) -> None:
    """Hanya key mzk_* — app_name milik target tidak disentuh."""
    def esc(s: str) -> str:
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <string name="mzk_label">{esc(label)}</string>\n'
        f'    <string name="mzk_wizard">{esc(wizard)}</string>\n'
        f'    <string name="mzk_email">{esc(email)}</string>\n'
        f'    <string name="mzk_team">{esc(team)}</string>\n'
        "</resources>\n"
    )
    strings_file.parent.mkdir(parents=True, exist_ok=True)
    strings_file.write_text(body, encoding="utf-8")
