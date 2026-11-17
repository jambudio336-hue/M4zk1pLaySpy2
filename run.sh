#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
mkdir -p data/uploads data/builds data/dumps data/keys
exec uvicorn server.main:app --host 0.0.0.0 --port "${PORT:-8777}" --no-access-log
