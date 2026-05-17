#!/usr/bin/env bash
# Stop the full pipeline. Kills by pidfile, then sweeps stragglers.
set -u
cd "$(dirname "$0")/.."
RUN=.run

pids=()
for name in midi director bridge synth; do
  f="$RUN/$name.pid"
  if [ -f "$f" ]; then
    pid=$(cat "$f")
    if kill "$pid" 2>/dev/null; then echo "[stop] TERM $name (pid $pid)"; fi
    pids+=("$name:$pid")
    rm -f "$f"
  fi
done

# the director's graceful loop / an in-flight LLM gen can ignore TERM for a
# while — force-kill anything still alive after a short grace.
sleep 3
for np in "${pids[@]}"; do
  name="${np%%:*}"; pid="${np##*:}"
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null && echo "[stop] KILL $name (pid $pid)"
  fi
done

# sclang may leave an orphaned scsynth audio server holding the device
pkill -x scsynth 2>/dev/null && echo "[stop] swept orphan scsynth"
echo "[stop] done"
