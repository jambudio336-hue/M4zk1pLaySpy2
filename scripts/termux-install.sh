#!/usr/bin/env bash
# Instalasi M4zk1pLaySpy di Termux. Tanpa sudo.
set -euo pipefail

R='\033[1;31m'; A='\033[1;33m'; G='\033[1;32m'; N='\033[0m'
say(){ echo -e "${R}[M4ZK1PLAY]${N} $*"; }
ok(){ echo -e "${G}[ OK ]${N} $*"; }
warn(){ echo -e "${A}[WARN]${N} $*"; }

cd "$(dirname "$0")/.."

if ! command -v pkg >/dev/null 2>&1; then
  warn "Ini bukan Termux. Pakai ./install.sh biasa."
  exit 1
fi

say "Update repo Termux..."
pkg update -y || warn "pkg update gagal (lanjut)"

say "Pasang paket dasar..."
pkg install -y python python-pip openssl libxml2 libxslt git unzip zip || warn "sebagian paket gagal"

say "Pasang paket build APK (opsional, bisa lama)..."
pkg install -y openjdk-17 apksigner zipalign android-tools gradle 2>/dev/null \
  || warn "sebagian paket build tidak tersedia — mode oprek APK mungkin terbatas"

say "Siapkan penyimpanan..."
termux-setup-storage 2>/dev/null || true

say "Buat virtualenv..."
python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip wheel
pip install --quiet -r requirements.txt
ok "Dependensi Python terpasang"

mkdir -p data/uploads data/builds data/dumps data/keys agent/prebuilt
for d in uploads builds dumps keys; do touch "data/$d/.keep"; done

if [[ ! -f config.json ]]; then
  cp config.example.json config.json
  python - <<'PYEOF'
import json, secrets
d = json.load(open("config.json"))
d["agent_token_secret"] = secrets.token_urlsafe(48)
d["keystore_pass"] = secrets.token_urlsafe(24)
json.dump(d, open("config.json", "w"), indent=2)
PYEOF
  chmod 600 config.json 2>/dev/null || true
  ok "config.json dibuat"
fi

chmod +x run.sh dev.sh scripts/*.sh 2>/dev/null || true

echo
ok "Selesai. Jalankan: ./run.sh"
echo "  Buka di browser Termux: http://127.0.0.1:8777"
echo "  Lisensi: M4ZK1PL4Y"
echo
warn "Untuk build APK, jalankan ./scripts/build-agent.sh"
warn "Kalau apktool/zipalign tidak tersedia, mode 'Oprek APK resmi' akan gagal."
