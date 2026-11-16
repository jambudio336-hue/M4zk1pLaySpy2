#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -d .venv ]] || ./install.sh
# shellcheck disable=SC1091
source .venv/bin/activate
exec uvicorn server.main:app --host 127.0.0.1 --port 8777 --reload --log-level debug
