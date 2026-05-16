#!/usr/bin/env bash
# Boot the full local pipeline: SuperCollider -> bridge -> director -> midi worker.
# Logs + pidfiles in .run/. Idempotent-ish: run stop-all.sh first if already up.
set -euo pipefail
cd "$(dirname "$0")/.."

RUN=.run
mkdir -p "$RUN"
SCLANG="${SCLANG:-/Applications/SuperCollider.app/Contents/MacOS/sclang}"
PY=.venv/bin/python
export PYTHONUNBUFFERED=1   # so .run/*.log is tail-able in real time

start() { # name, command...
  local name="$1"; shift
  echo "[start] $name"
  ( "$@" ) >"$RUN/$name.log" 2>&1 &
  echo $! >"$RUN/$name.pid"
}

wait_for() { # file, pattern, seconds
  local f="$1" pat="$2" max="$3" i=0
  until grep -q "$pat" "$f" 2>/dev/null; do
    i=$((i+1)); [ "$i" -ge "$max" ] && { echo "[start] timeout waiting for: $pat"; return 1; }
    sleep 1
  done
}

# 1) SuperCollider
start synth "$SCLANG" synth/boot.scd
wait_for "$RUN/synth.log" "str synth ready" 40 && echo "[start] synth ready"

# 2) bridge
start bridge node bridge/server.js
wait_for "$RUN/bridge.log" "http+ws on" 15 && echo "[start] bridge ready"

# 3) director (loads the LLM; takes a bit)
start director "$PY" -m director.director

# 4) midi worker (only if built — Phase H)
if [ -f midi/worker.py ]; then
  start midi "$PY" -m midi.worker
else
  echo "[start] midi/worker.py not present yet — skipping (Phase H)"
fi

# 5) scribe — LLM author of the demoscene scroller text. Run it in the macOS
# background scheduling tier (throttled CPU/IO) so its LLM bursts yield to the
# realtime audio + visuals; fall back to a low `nice`.
if [ -f director/scribe.py ]; then
  if command -v taskpolicy >/dev/null 2>&1; then
    start scribe taskpolicy -b "$PY" -m director.scribe
  else
    start scribe nice -n 19 "$PY" -m director.scribe
  fi
fi

echo
echo "  open  http://localhost:${BRIDGE_HTTP_PORT:-8080}"
echo "  logs  tail -f $RUN/*.log"
echo "  stop  ./scripts/stop-all.sh"
