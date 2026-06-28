#!/usr/bin/env bash
#
# run_sweep.sh -- career sweep, with the fragile parts removed.
#
# The ONLY thing a model must decide is the board web_extract. Everything else
# (ATS scan, direct board pull, merge, email) is deterministic and lives here,
# so the email can never be skipped, the pipeline can never be "reinvented".
#
# THREE ways to call it:
#
#   ./run_sweep.sh prep    1) ATS scan + direct board pull, then prints the
#                             exact web_extract task + the 5 URLs to scrape.
#   ./run_sweep.sh send    3) merge everything in data/board-results-<today>.json
#                             and SEND the email. Reports email_sent.
#
#   ./run_sweep.sh         full autonomous run (prep + send, no web_extract).
#                          Always emails *something* -- use this for cron.
#
# Richest results = prep -> web_extract the 5 URLs into the board file -> send.
#
set -euo pipefail
cd /home/fihadmin/career-sweep
D=$(date +%F)
MODE="${1:-full}"
ATS="data/ats-$D.json"
BOARDS="data/board-results-$D.json"

do_prep() {
  echo "[1/2] ATS scan (31 companies)..."
  python3 sweep.py scan >/dev/null
  [[ -f "$ATS" ]] || ATS=$(ls -t data/ats-*.json | head -1)
  echo "[2/2] Direct board pull (no agent)..."
  python3 collect_boards.py
  [[ -f "$BOARDS" ]] || echo "[]" > "$BOARDS"
}

do_send() {
  [[ -f "$BOARDS" ]] || echo "[]" > "$BOARDS"
  [[ -f "$ATS" ]] || ATS=$(ls -t data/ats-*.json 2>/dev/null | head -1)
  echo "Merge + email..."
  OUT=$(python3 sweep.py merge --board-results "$BOARDS" --ats-results "$ATS" --json)
  echo "$OUT" | python3 -c "
import sys, json, re
m = re.search(r'\{.*\}', sys.stdin.read(), re.S)
d = json.loads(m.group(0)) if m else {}
print(f\"email_sent: {d.get('email_sent')} -- {d.get('total')} roles \"
      f\"(HIGH {d.get('high')}, MED {d.get('medium')}, LOW {d.get('low')})\")
"
}

case "$MODE" in
  prep)
    do_prep
    ROWS=$(python3 -c "import json;print(len(json.load(open('$BOARDS'))))")
    cat <<EOF

================ NEXT STEP (do this, then run: ./run_sweep.sh send) ===========
web_extract these 5 URLs and APPEND each IT/Sr IT Manager posting you find to
$BOARDS as JSON objects of the form:
  {"company":"","title":"","location":"","url":"","source":"glassdoor"}
Location MUST be "Remote, US" or a real US city (e.g. "Las Vegas, NV"); else the
row is dropped. ($ROWS row(s) already in the file from the direct pull.)

  https://www.glassdoor.com/Job/it-manager-jobs-SRCH_KO0,10.htm
  https://www.glassdoor.com/Job/las-vegas-it-manager-jobs-SRCH_IL.0,9_IC1139935_KO10,20.htm
  https://www.dice.com/jobs?q=IT+Manager+Las+Vegas
  https://builtin.com/jobs?search=IT+Manager&remote=true
  https://www.dice.com/jobs?q=Sr+IT+Manager+remote

Then: ./run_sweep.sh send
==============================================================================
EOF
    ;;
  send)
    do_send
    ;;
  full)
    do_prep
    do_send
    echo "(full autonomous run -- for richer results use: prep -> web_extract -> send)"
    ;;
  *)
    echo "usage: ./run_sweep.sh [prep|send|full]"; exit 2 ;;
esac
