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
