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
from midi.recorder import SongRecorder
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
        self.rec = SongRecorder()
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
        # per-genre instrument variants — set chosen, reset the rest to default
        roles = ("kick", "snare", "hat", "ohat", "clap", "rim", "perc",
                 "bass", "lead", "keys")
        getm = getattr(self.source, "instrument_map", None)
        m = getm() if callable(getm) else {}
        try:
            for r in roles:
                self.sc.select(r, m.get(r, r))
        except Exception as e:  # noqa: BLE001
            print(f"[worker] instrument map push failed: {e}")
        # per-track genre-dependent FX (fxDrums / fxBass / fxMel)
        getfx = getattr(self.source, "fx_params", None)
        if callable(getfx):
            try:
                for bus, params in (getfx() or {}).items():
                    for name, value in params.items():
                        self.sc.param(bus, name, float(value))
            except Exception as e:  # noqa: BLE001
                print(f"[worker] fx params push failed: {e}")

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
        self.rec.start(_DEFAULT_SECTION, time.monotonic())

        heap = []  # (abs_time, seq, kind, ch, pitch, vel)
        seq = 0
        now = time.monotonic
        horizon = now() + 0.25
        pend_new = None      # genre queued behind a transition
        swap_at = 0.0        # when to actually drop the new genre

        while self._running:
            with self._lock:
                pend = self._pending_section
                self._pending_section = None

            # a new section arrived -> a CLEAN transition: let the last notes
            # ring out, a short breath of space, then the new genre drops on
            # a fresh downbeat. No fill/wash (that sounded weird).
            if pend is not None:
                if pend_new is None:
                    bpm = float(self.source.bpm or 100)
                    beatlen = 60.0 / max(50.0, min(180.0, bpm))
                    t0 = now()
                    tail = 0.32          # let notes already sounding ring out
                    # drop anything scheduled past the tail -> goes quiet
                    heap = [e for e in heap if e[0] <= t0 + tail]
                    heapq.heapify(heap)
                    # stop pulling old phrases (handled by the fill guard);
                    # new genre enters after the tail + ~1 beat of breath
                    swap_at = t0 + tail + max(0.45, beatlen)
                pend_new = pend     # always swap to the most recent request

            if pend_new is not None and now() >= swap_at:
                self.sc.panic()
                self.rec.flush()                 # finished song -> .mid
                self.source.prime(pend_new)
                self.sc.tempo(float(pend_new.get("bpm")
                                    or pend_new.get("tempo") or 78))
                self._push_synth_params()
                self.rec.start(pend_new, now())  # begin the next song
                heap.clear()
                horizon = now() + 0.10
                print(f"[worker] dropped: {pend_new.get('genre')} "
                      f"{pend_new.get('key')} "
                      f"{pend_new.get('bpm') or pend_new.get('tempo')}bpm")
                pend_new = None

            # keep the buffer full — but NOT while a transition is breathing
            while pend_new is None and horizon - now() < self.min_buffer:
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
                et, _, kind, ch, pitch, vel = heapq.heappop(heap)
                if kind == "on":
                    self.sc.note_on(ch, pitch, vel)
                    self.rec.note_on(ch, pitch, vel, et)
                else:
                    self.sc.note_off(ch, pitch)
                    self.rec.note_off(ch, pitch, et)

            time.sleep(0.004)

        self.rec.flush()                         # save the final song

    def stop(self):
        self._running = False


def main():
    import signal

    w = Worker()

    def _shutdown(_sig, _frm):
        w.stop()
        w.rec.flush()                            # save the in-progress song
        print("\n[worker] stopped")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    try:
        w.run()
    except KeyboardInterrupt:
        w.stop()
        w.rec.flush()
        print("\n[worker] stopped")


if __name__ == "__main__":
    main()
