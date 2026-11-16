#!/usr/bin/env bash
# Build agent APK + siapkan artefak prebuilt.
set -euo pipefail

R='\033[1;31m'; G='\033[1;32m'; A='\033[1;33m'; N='\033[0m'
say(){ echo -e "${R}[M4ZK1PLAY]${N} $*"; }
ok(){ echo -e "${G}[ OK ]${N} $*"; }
warn(){ echo -e "${A}[WARN]${N} $*"; }
err(){ echo -e "${R}[GAGAL]${N} $*" >&2; }

cd "$(dirname "$0")/.."
OUT="agent/app/build/outputs/apk/release/app-release.apk"

command -v java >/dev/null 2>&1 || { err "JDK tidak ada. Pasang openjdk-17."; exit 1; }

if command -v gradle >/dev/null 2>&1; then
  GRADLE_BIN="gradle"
elif [[ -x agent/gradlew ]]; then
  GRADLE_BIN="./gradlew"
elif [[ -x ./gradlew ]]; then
  GRADLE_BIN="./gradlew"
else
  err "gradle tidak ditemukan. Linux/macOS: pasang gradle + Android SDK. Termux: pkg install gradle"
  exit 1
fi

if [[ -z "${ANDROID_HOME:-}" && -z "${ANDROID_SDK_ROOT:-}" ]]; then
  warn "ANDROID_HOME / ANDROID_SDK_ROOT kosong — build kemungkinan gagal."
  echo "  Butuh platform-34 + build-tools 34."
fi

mkdir -p agent/prebuilt
say "Build agent release (bisa 2-5 menit)..."
( cd agent && "$GRADLE_BIN" --no-daemon assembleRelease ) || {
  err "gradle gagal. Cek log di atas."
  exit 1
}

[[ -f "$OUT" ]] || { err "APK tidak dihasilkan: $OUT"; exit 1; }

cp "$OUT" agent/prebuilt/agent.apk
ok "agent.apk siap ($(du -h agent/prebuilt/agent.apk | cut -f1))"

if [[ ! -f agent/prebuilt/template.apk ]]; then
  warn "template.apk belum ada → mode 'Build Baru' belum bisa."
  echo "  Buat sekali dari Android Studio (Empty Views Activity, package ai.m4zk1play.tpl),"
  echo "  build debug, lalu: cp app-debug.apk agent/prebuilt/template.apk"
else
  ok "template.apk tersedia"
fi

bash scripts/verify.sh || warn "struktur belum lengkap"
say "Selesai."
