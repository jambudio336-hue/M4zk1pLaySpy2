#!/usr/bin/env bash
# M4zk1pLaySpy installer — Kali / Ubuntu / Parrot / macOS
set -euo pipefail

R='\033[1;31m'; A='\033[1;33m'; G='\033[1;32m'; N='\033[0m'
say(){ echo -e "${R}[M4ZK1PLAY]${N} $*"; }
ok(){ echo -e "${G}[ OK ]${N} $*"; }
warn(){ echo -e "${A}[WARN]${N} $*"; }

cd "$(dirname "$0")"
say "Memulai instalasi..."

OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
  command -v brew >/dev/null 2>&1 || { warn "Homebrew belum ada. Pasang dulu: https://brew.sh"; exit 1; }
  brew install python@3.11 apktool openjdk@17 android-commandlinetools 2>/dev/null || warn "sebagian paket gagal (lanjut)"
  PY="python3.11"
else
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-venv python3-pip apktool zipalign \
      openjdk-17-jdk-headless libxml2-utils android-sdk-build-tools 2>/dev/null \
      || warn "sebagian paket apt gagal (lanjut)"
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python apktool android-sdk-build-tools jdk17-openjdk 2>/dev/null || warn "pacman sebagian gagal"
  fi
  PY="python3"
fi

# verifikasi tool wajib
for t in java apktool zipalign apksigner keytool; do
  command -v "$t" >/dev/null 2>&1 && ok "$t" || warn "$t tidak ditemukan — build APK mungkin gagal"
done

say "Membuat virtualenv..."
"$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Dependensi Python terpasang"

mkdir -p data/uploads data/builds data/dumps data/keys
touch data/uploads/.keep data/builds/.keep data/dumps/.keep data/keys/.keep

if [[ ! -f config.json ]]; then
  cp config.example.json config.json
  SECRET="$("$PY" - <<'EOF'
import secrets; print(secrets.token_urlsafe(48))
EOF
)"
  "$PY" - "$SECRET" <<'EOF'
import json,sys
p="config.json"; d=json.load(open(p)); d["agent_token_secret"]=sys.argv[1]
json.dump(d,open(p,"w"),indent=2)
EOF
  ok "config.json dibuat + secret dirotasi"
else
  warn "config.json sudah ada, dilewati"
fi

chmod +x run.sh dev.sh 2>/dev/null || true
ok "Selesai. Jalankan: ./run.sh"
