#!/usr/bin/env bash
# Build agent APK + siapkan artefak prebuilt. Jalan di Linux, macOS, Termux.
set -euo pipefail

R='\033[1;31m'; G='\033[1;32m'; A='\033[1;33m'; N='\033[0m'
say(){ echo -e "${R}[M4ZK1PLAY]${N} $*"; }
ok(){ echo -e "${G}[ OK ]${N} $*"; }
warn(){ echo -e "${A}[WARN]${N} $*"; }
err(){ echo -e "${R}[GAGAL]${N} $*" >&2; }

cd "$(dirname "$0")/.."

OUT="agent/app/build/outputs/apk/release/app-release.apk"

command -v java >/dev/null 2>&1 || { err "JDK tidak ada. Pasang openjdk-17 dulu."; exit 1; }

if command -v gradle >/dev/null 2>&1; then
  GRADLE="gradle --no-daemon"
elif [[ -x ./gradlew ]]; then
  GRADLE="./gradlew --no-daemon"
elif [[ -x agent/gradlew ]]; then
  GRADLE="(cd agent && ./gradlew --no-daemon)"
else
  err "gradle tidak ditemukan."
  echo "  Linux/macOS : pasang Android SDK + gradle"
  echo "  Termux      : pkg install gradle"
  exit 1
fi

if [[ -z "${ANDROID_HOME:-}" && -z "${ANDROID_SDK_ROOT:-}" ]]; then
  warn "ANDROID_HOME / ANDROID_SDK_ROOT kosong."
  echo "  Build butuh Android SDK platform-34 + build-tools."
  echo "  Termux: pkg install android-sdk && sdkmanager 'platforms;android-34' 'build-tools;34.0.0'"
fi

mkdir -p agent/prebuilt

say "Build agent release..."
if [[ "$GRADLE" == "gradle --no-daemon" || "$GRADLE" == "./gradlew --no-daemon" ]]; then
  ( cd agent && eval "$GRADLE assembleRelease" )
else
  eval "$GRADLE assembleRelease"
fi

if [[ ! -f "$OUT" ]]; then
  err "APK tidak dihasilkan: $OUT"
  echo "  Cek log di atas. Sering karena SDK/build-tools belum lengkap."
  exit 1
fi

cp "$OUT" agent/prebuilt/agent.apk
ok "agent.apk siap ($(du -h agent/prebuilt/agent.apk | cut -f1))"

if [[ ! -f agent/prebuilt/template.apk ]]; then
  warn "template.apk belum ada → mode 'Build Baru' belum bisa dipakai."
  cat <<'EOF'
  Cara membuat (sekali saja):
    1. Android Studio → New Project → Empty Views Activity
    2. package: ai.m4zk1play.tpl · minSdk 21
    3. Build > Build APK(s) (debug)
    4. cp app-debug.apk agent/prebuilt/template.apk
  Mode 'Oprek APK resmi' sudah bisa dipakai tanpa template.
EOF
else
  ok "template.apk tersedia"
fi

say "Selesai."
