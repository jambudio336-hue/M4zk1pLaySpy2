#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "[*] deps python"
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "[*] dir runtime"
mkdir -p data/uploads data/builds data/dumps data/keys
echo "[*] tunnel client (opsional)"
if ! command -v cloudflared >/dev/null 2>&1; then
  curl -fsSL -o /tmp/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 || true
  [ -s /tmp/cloudflared ] && sudo install -m755 /tmp/cloudflared /usr/local/bin/cloudflared || true
fi
echo "[+] selesai. jalankan: ./run.sh"
