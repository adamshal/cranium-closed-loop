#!/bin/sh
cd "$(dirname "$0")" || exit 1
printf '\nCRANIUM — LIVE LOGIC ANALYZER DEMO\n\n'
printf 'Real Saleae capture: D0 = commands, D1 = board replies.\n'
printf 'Running five read-only GET_ID requests. Existing firmware is preserved.\n\n'
.venv/bin/python -c 'from workbench.launch import start_logic; start_logic()' || exit 1
.venv/bin/python tools/logic-demo.py --seconds 8 --uart-probe configured --read-only-demo --presentation --show
result=$?
for app in "$PWD/.local/logic2/Saleae Logic.app" /Applications/Logic.app '/Applications/Saleae Logic.app'; do
    if [ -d "$app" ]; then open -a "$app"; break; fi
done
printf '\nPress Enter to close this window.\n'
read -r response
exit "$result"
