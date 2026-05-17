#!/usr/bin/env bash
# 24/7 watchdog. Bootstraps the whole hybrid stream on first pass, then
# restarts ANY component that dies. Run this and leave it (e.g. in tmux /
# screen, or via the launchd plist in STREAMING.md). Ctrl-C stops watching;
# it does NOT stop the stream — use stop-all.sh for that.
cd "$(dirname "$0")/.."
RUN=.run; mkdir -p "$RUN"
SCLANG="${SCLANG:-/Applications/SuperCollider.app/Contents/MacOS/sclang}"
PY=.venv/bin/python
export PYTHONUNBUFFERED=1
export STR_SECTION_SEC="${STR_SECTION_SEC:-120}"   # ~2 min per song/section

alive() { local p; p=$(cat "$RUN/$1.pid" 2>/dev/null) || return 1; kill -0 "$p" 2>/dev/null; }
boot() { local n="$1"; shift; echo "[watch $(date +%T)] (re)start $n"; ( "$@" ) >>"$RUN/$n.log" 2>&1 & echo $! >"$RUN/$n.pid"; }

echo "[watch] supervising — Ctrl-C stops watching (stream keeps running)"
while true; do
  if ! alive synth; then
    pkill -x scsynth 2>/dev/null || true
    boot synth "$SCLANG" synth/boot.scd
    sleep 9                                  # let scsynth + defs come up
  fi
  alive bridge   || boot bridge node bridge/server.js
  alive midi     || boot midi "$PY" -m midi.worker
  alive director || boot director "$PY" -m director.director
  sleep 15
done
