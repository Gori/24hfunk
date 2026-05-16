"""MIDI source abstraction. A source yields PHRASES of timed notes; the worker
schedules them in real time with a look-ahead buffer so generation latency
(especially the LLM source) is hidden and playback stays continuous.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Protocol, Tuple

# channel convention — must match synth/router.scd ~chanMap
CH_BASS = 0
CH_LEAD = 1
CH_KEYS = 2          # comp / pad harmonic voice (self-terminating synth)
CH_PERC = 3          # dedicated percussion layer (shaker / glitch / organic)
CH_DRUMS = 9
KICK, SNARE, HAT = 36, 38, 42


@dataclass
class Note:
    t: float        # onset in seconds, relative to phrase start
    dur: float      # seconds (note-off; drums ignore this)
    pitch: int
    vel: float      # 0..1
    ch: int


@dataclass
class Phrase:
    notes: List[Note] = field(default_factory=list)
    length: float = 2.0   # seconds this phrase occupies on the timeline


class MidiSource(Protocol):
    name: str

    def prime(self, section: dict) -> None:
        """Re-seed from a new SectionState dict (tempo/key/density/instruments)."""

    def next_phrase(self) -> Phrase:
        """Return the next phrase. Must never raise; degrade instead."""
