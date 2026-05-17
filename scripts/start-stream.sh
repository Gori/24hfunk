#!/usr/bin/env bash
# Production stream stack — HYBRID: the local LLM director picks the vibe,
# sections rotate ~60s with the ring-out->breath->drop transition.
# 16 GB-lean (4B model). For 24/7 use supervise.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
RUN=.run; mkdir -p "$RUN"
SCLANG="${SCLANG:-/Applications/SuperCollider.app/Contents/MacOS/sclang}"
PY=.venv/bin/python
export PYTHONUNBUFFERED=1
export STR_SECTION_SEC="${STR_SECTION_SEC:-120}"    # ~2 min per song/section
# STR_AUDIO_DEVICE (optional): route SC to a capture device for streaming,
#   e.g.  export STR_AUDIO_DEVICE="BlackHole 16ch"   (see STREAMING.md)

start() { local n="$1"; shift; echo "[stream] $n"; ( "$@" ) >"$RUN/$n.log" 2>&1 & echo $! >"$RUN/$n.pid"; }
waitfor() { local f="$1" p="$2" m="$3" i=0; until grep -q "$p" "$f" 2>/dev/null; do i=$((i+1)); [ "$i" -ge "$m" ] && { echo "[stream] timeout: $p"; return 1; }; sleep 1; done; }

./scripts/stop-all.sh >/dev/null 2>&1 || true
sleep 1

start synth "$SCLANG" synth/boot.scd
waitfor "$RUN/synth.log" "str synth ready" 40 && echo "[stream] synth ready"
start bridge node bridge/server.js
waitfor "$RUN/bridge.log" "http+ws on" 15 && echo "[stream] bridge ready"
start midi "$PY" -m midi.worker
start director "$PY" -m director.director              # 4B, picks the vibe

echo
echo "  HYBRID stream live — director picks the vibe, ~${STR_SECTION_SEC}s rotation"
echo "  watch  http://localhost:${BRIDGE_HTTP_PORT:-8080}"
echo "  24/7   ./scripts/supervise.sh   (auto-restarts anything that dies)"
echo "  stream see STREAMING.md  (OBS + BlackHole + YouTube)"
echo "  stop   ./scripts/stop-all.sh"
