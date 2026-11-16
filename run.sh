#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -d .venv ]] || { echo "Jalankan ./install.sh dulu"; exit 1; }
# shellcheck disable=SC1091
source .venv/bin/activate
PORT="$(python - <<'EOF'
import json,os
try: print(json.load(open("config.json"))["port"])
except Exception: print(os.environ.get("MZK_PORT","8777"))
EOF
)"
echo -e "\033[1;31m[M4ZK1PLAY]\033[0m http://127.0.0.1:${PORT}  — license: M4ZK1PL4Y"
exec uvicorn server.main:app --host 0.0.0.0 --port "$PORT" --reload
