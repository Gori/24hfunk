"""Per-song MIDI recorder.

A passive tap on the worker's note stream: every note the system actually
plays is mirrored here, buffered per *section* (= one song), and written to a
standalone Standard MIDI File when that song ends (next section, or shutdown).

RAW channel layout — exactly what the engine emits, no General-MIDI mapping:
  ch 0 bass · ch 1 lead · ch 2 keys · ch 3 perc-layer · ch 9 drum kit
  (drum kit keyed by pitch GM-style: 36 kick, 38 snare, 42 hat, 46 ohat, …)

Hermetic: a tiny pure-Python SMF (format-0) encoder, no external deps. The
recorder must NEVER disturb the audio path — every public method swallows its
own exceptions.

Disable by setting STR_RECORD_DIR="" ; otherwise songs land in ./songs/.
"""
from __future__ import annotations

import os
import re
import struct
import time

TPQN = 480                       # ticks per quarter note
_ONESHOT_CH = (2, 3, 9)          # keys / perc / drums: no real note-off comes
_ONESHOT_SEC = 0.15             # synthesised gate length for one-shot hits
_MIN_SONG_SEC = 20.0            # don't bother writing sub-20s stubs
_MIN_SONG_NOTES = 16


def _vlq(n: int) -> bytes:
    """MIDI variable-length quantity."""
    if n < 0:
        n = 0
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _safe_name(name: str) -> str:
    name = (name or "untitled").strip()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return (name or "untitled")[:48]


class SongRecorder:
    def __init__(self, out_dir: str | None = None) -> None:
        env = os.environ.get("STR_RECORD_DIR")
        # env unset -> default ./songs ; env set empty -> disabled
        self.dir = (out_dir if out_dir is not None
                    else ("songs" if env is None else env))
        self.enabled = bool(self.dir)
        self._idx = 0
        self._reset()
        if self.enabled:
            try:
                os.makedirs(self.dir, exist_ok=True)
            except OSError as e:
                print(f"[rec] disabled (mkdir failed: {e})")
                self.enabled = False

    # ---- lifecycle ----------------------------------------------------
    def _reset(self) -> None:
        self._t0 = 0.0
        self._bpm = 78.0
        self._name = ""
        self._genre = ""
        self._ev: list[tuple[float, int, int, int]] = []  # (sec, on?, ch, pitch, vel)

    def start(self, section: dict | None, t0: float | None = None) -> None:
        if not self.enabled:
            return
        try:
            self._reset()
            self._t0 = t0 if t0 is not None else time.monotonic()
            s = section or {}
            self._bpm = float(s.get("bpm") or s.get("tempo") or 78)
            self._genre = str(s.get("genre") or "")
            self._name = str(s.get("name") or s.get("mood") or "")
        except Exception as e:  # noqa: BLE001 — never break the stream
            print(f"[rec] start failed: {e}")

    def note_on(self, ch: int, pitch: int, vel: float, at: float) -> None:
        if not self.enabled:
            return
        try:
            t = at - self._t0
            if t < 0:
                t = 0.0
            v = max(1, min(127, int(round(vel * 127))))
            self._ev.append((t, 1, ch, pitch, v))
            if ch in _ONESHOT_CH:
                self._ev.append((t + _ONESHOT_SEC, 0, ch, pitch, 0))
        except Exception as e:  # noqa: BLE001
            print(f"[rec] note_on drop: {e}")

    def note_off(self, ch: int, pitch: int, at: float) -> None:
        if not self.enabled:
            return
        try:
            t = at - self._t0
            self._ev.append((t if t > 0 else 0.0, 0, ch, pitch, 0))
        except Exception as e:  # noqa: BLE001
            print(f"[rec] note_off drop: {e}")

    def flush(self) -> str | None:
        """Write the current song (if substantial) and reset."""
        if not self.enabled or not self._ev:
            self._reset()
            return None
        try:
            span = max(t for t, *_ in self._ev)
            n_on = sum(1 for _, on, *_ in self._ev if on)
            if span < _MIN_SONG_SEC or n_on < _MIN_SONG_NOTES:
                self._reset()
                return None
            path = self._write()
            self._reset()
            return path
        except Exception as e:  # noqa: BLE001
            print(f"[rec] flush failed: {e}")
            self._reset()
            return None

    # ---- SMF encoding -------------------------------------------------
    def _write(self) -> str:
        bpm = max(20.0, min(300.0, self._bpm))
        spt = (60.0 / bpm) / TPQN                       # seconds per tick
        # (tick, off-before-on@same-tick, on?, ch, pitch, vel)
        ev = sorted(
            ((int(round(t / spt)), 0 if on else 1, on, ch, p, v)
             for (t, on, ch, p, v) in self._ev),
            key=lambda e: (e[0], e[1]),
        )
        trk = bytearray()
        trk += _vlq(0) + b"\xFF\x51\x03" + struct.pack(
            ">I", int(round(60_000_000 / bpm)))[1:]      # tempo meta
        prev = 0
        for tick, _, on, ch, pitch, vel in ev:
            trk += _vlq(tick - prev)
            prev = tick
            ch &= 0x0F
            status = (0x90 if on else 0x80) | ch
            trk += bytes((status, pitch & 0x7F, vel & 0x7F))
        trk += _vlq(0) + b"\xFF\x2F\x00"                 # end of track

        hdr = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TPQN)
        body = hdr + b"MTrk" + struct.pack(">I", len(trk)) + bytes(trk)

        self._idx += 1
        stamp = time.strftime("%Y-%m-%d_%H%M%S")
        bits = [f"{self._idx:04d}", stamp]
        if self._genre:
            bits.append(_safe_name(self._genre))
        bits.append(_safe_name(self._name) if self._name else "untitled")
        path = os.path.join(self.dir, "_".join(bits) + ".mid")
        with open(path, "wb") as f:
            f.write(body)
        print(f"[rec] saved {path}  ({len(ev)} events, "
              f"{self._bpm:g}bpm, {self._genre or '?'})")
        return path
