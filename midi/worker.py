"""MIDI worker: pull phrases from a source, schedule them in real time with a
look-ahead buffer, emit OSC note-on/off to SuperCollider. Listens on a control
port for /midi/section (re-prime) and /midi/tempo from the director.

Env:
  STR_MIDI_SOURCE   "canned" (default, guaranteed) | "midillm" (model, falls back)
  MIDI_CTRL_OSC_PORT  default 57121
"""
from __future__ import annotations

import heapq
import json
import os
import threading
import time

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

from midi.osc_out import ScSender
from midi.canned import CannedSource
from midi.source import CH_BASS, CH_LEAD

CTRL_PORT = int(os.environ.get("MIDI_CTRL_OSC_PORT", "57121"))
SOURCE_NAME = os.environ.get("STR_MIDI_SOURCE", "canned").lower()

# default section until the director sends one
_DEFAULT_SECTION = {
    "tempo": 78, "bpm": 78, "key": "C minor", "density": 0.5,
    "instruments": {k: {"enabled": True} for k in
                    ("kick", "snare", "hat", "bass", "lead")},
}


def make_source():
    if SOURCE_NAME == "midillm":
        try:
            from midi.midillm import MidiLLMSource
            src = MidiLLMSource()
            src.load()
            print("[worker] using MIDI-LLM source")
            return src
        except Exception as e:  # noqa: BLE001 — must never block the stream
            print(f"[worker] MIDI-LLM unavailable ({e}); falling back to canned")
    print("[worker] using canned source")
    return CannedSource()


class Worker:
    def __init__(self):
        self.sc = ScSender()
        self.source = make_source()
        self.min_buffer = getattr(self.source, "min_buffer", 2.5)
        self._pending_section = None
        self._lock = threading.Lock()
        self._running = True

    # ---- control OSC (from director/publish.py) ----
    def _on_section(self, _addr, *args):
        try:
            data = json.loads(args[0]) if args else {}
            with self._lock:
                self._pending_section = data
        except (ValueError, IndexError) as e:
            print(f"[worker] bad /midi/section: {e}")

    def _on_tempo(self, _addr, *args):
        if args:
            self.sc.tempo(float(args[0]))

    def _push_synth_params(self):
        """Send the source's genre-tuned SynthDef params to SuperCollider."""
        getp = getattr(self.source, "synth_params", None)
        if not callable(getp):
            return
        try:
            for synth, params in (getp() or {}).items():
                for name, value in params.items():
                    self.sc.param(synth, name, float(value))
        except Exception as e:  # noqa: BLE001
            print(f"[worker] synth_params push failed: {e}")

    def _serve_ctrl(self):
        disp = Dispatcher()
        disp.map("/midi/section", self._on_section)
        disp.map("/midi/tempo", self._on_tempo)
        srv = BlockingOSCUDPServer(("127.0.0.1", CTRL_PORT), disp)
        print(f"[worker] control OSC on udp {CTRL_PORT}")
        srv.serve_forever()

    # ---- main scheduling loop ----
    def run(self):
        threading.Thread(target=self._serve_ctrl, daemon=True).start()

        self.source.prime(_DEFAULT_SECTION)
        self.sc.tempo(float(_DEFAULT_SECTION["bpm"]))
        self._push_synth_params()

        heap = []  # (abs_time, seq, kind, ch, pitch, vel)
        seq = 0
        now = time.monotonic
        horizon = now() + 0.25

        while self._running:
            # section change -> panic + re-prime + reset timeline
            with self._lock:
                pend = self._pending_section
                self._pending_section = None
            if pend is not None:
                self.sc.panic()
                self.source.prime(pend)
                self.sc.tempo(float(pend.get("bpm") or pend.get("tempo") or 78))
                self._push_synth_params()
                heap.clear()
                horizon = now() + 0.15
                print(f"[worker] re-primed: {pend.get('key')} "
                      f"{pend.get('bpm') or pend.get('tempo')}bpm")

            # keep the buffer full
            while horizon - now() < self.min_buffer:
                ph = self.source.next_phrase()
                for n in ph.notes:
                    t0 = horizon + n.t
                    seq += 1
                    heapq.heappush(heap, (t0, seq, "on", n.ch, n.pitch, n.vel))
                    if n.ch in (CH_BASS, CH_LEAD):
                        seq += 1
                        heapq.heappush(
                            heap, (t0 + max(0.05, n.dur), seq, "off",
                                   n.ch, n.pitch, 0.0))
                horizon += ph.length

            # emit everything due
            t = now()
            while heap and heap[0][0] <= t:
                _, _, kind, ch, pitch, vel = heapq.heappop(heap)
                if kind == "on":
                    self.sc.note_on(ch, pitch, vel)
                else:
                    self.sc.note_off(ch, pitch)

            time.sleep(0.004)

    def stop(self):
        self._running = False


def main():
    w = Worker()
    try:
        w.run()
    except KeyboardInterrupt:
        w.stop()
        print("\n[worker] stopped")


if __name__ == "__main__":
    main()
