"""Director loop: every section, ask the local LLM for the next SectionState,
publish it, sleep for its duration. Resilient — never crashes the stream.

Env:
  STR_SECTION_SEC   override section length (seconds) for testing, e.g. 60
  STR_DIRECTOR_MODEL override the mlx model id
"""
from __future__ import annotations

import os
import signal
import time

from director.llm_client import Director, summarize
from director.publish import publish
from director.schema import SectionState

_running = True


def _stop(*_):
    global _running
    _running = False
    print("[director] stopping after current section…")


def main() -> None:
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    override = os.environ.get("STR_SECTION_SEC")
    override_sec = int(override) if override else None

    d = Director()
    d.load()

    # immediate warmup so the stream has state before the first LLM call
    warm = SectionState(id="warmup", duration_sec=20)
    publish(warm)

    history: list[str] = []
    n = 0
    while _running:
        n += 1
        section, lat = d.next_section(history)
        section.id = f"sec_{int(time.time())}_{n:03d}"
        dur = override_sec if override_sec else section.duration_sec

        publish(section)
        history.append(summarize(section))
        history = history[-8:]
        print(f"[director] #{n} {section.id} gen={lat:.1f}s hold={dur}s :: "
              f"{summarize(section)}")

        slept = 0
        while _running and slept < dur:
            time.sleep(min(1, dur - slept))
            slept += 1

    print("[director] exited cleanly")


if __name__ == "__main__":
    main()
