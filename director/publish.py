"""Publish a SectionState to the three consumers:
  - SuperCollider router  (OSC 57120): /section/begin + /synth/param fan
  - MIDI worker control   (OSC 57121): /midi/section + /midi/tempo
  - bridge                (HTTP 8080): POST /section  -> WS to browser
"""
from __future__ import annotations

import json
import os

import threading

import requests
from pythonosc.udp_client import SimpleUDPClient

from director import tts
from director.schema import SectionState

# genres whose lead is the DJ scratch — render their title via TTS so the
# scratch samples the actual song title.
_SCRATCH_GENRES = {"uk_garage", "eighties_hiphop"}
_SCRATCH_WAV = "/tmp/str_scratch.wav"

SC_HOST = "127.0.0.1"
SC_PORT = int(os.environ.get("SC_OSC_PORT", "57120"))
MIDI_HOST = "127.0.0.1"
MIDI_PORT = int(os.environ.get("MIDI_CTRL_OSC_PORT", "57121"))
BRIDGE_URL = f"http://localhost:{os.environ.get('BRIDGE_HTTP_PORT', '8080')}/section"

_sc = SimpleUDPClient(SC_HOST, SC_PORT)
_midi = SimpleUDPClient(MIDI_HOST, MIDI_PORT)


def _phrase_words(phrase: str) -> list[str]:
    """A phrase -> exactly TWO word tokens (so each gets its own buffer; a
    1-word phrase fills both slots with the same word)."""
    words = [w for w in str(phrase).split() if w][:2]
    if not words:
        words = ["fresh"]
    if len(words) == 1:
        words = [words[0], words[0]]
    return words


def _render_scratch_set(phase_phrases: list[str]) -> None:
    """Render each WORD of the 3 phase phrases into its own buffer slot, so
    multi-word phrases scratch word-by-word. Slots: phase1 words -> 0,1;
    phase2 -> 2,3; title -> 4,5. Daemon thread; silent no-op on failure."""
    for p, phrase in enumerate(phase_phrases[:3]):
        for w, word in enumerate(_phrase_words(phrase)):
            slot = p * 2 + w
            path = f"/tmp/str_scratch_{slot}.wav"
            if tts.render(word, path):
                _sc.send_message("/scratch/load", [slot, path])

# which numeric params of each instrument map to /synth/param
_INSTR_PARAMS = {
    "kick": ["amp", "fmRatio", "fmIndex", "decay"],
    "snare": ["amp", "tone", "decay"],
    "hat": ["amp", "cutoff", "decay"],
    "bass": ["amp", "cutoff", "res", "detune", "decay"],
    "lead": ["amp", "fmRatio", "fmIndex", "wave", "decay"],
}


def publish(section: SectionState) -> None:
    sid = section.id

    # 1) SuperCollider: section marker + tempo + per-synth params
    _sc.send_message("/section/begin", [sid])
    _sc.send_message("/midi/tempo", [float(section.bpm)])
    instr = section.instruments
    for name, params in _INSTR_PARAMS.items():
        inst = getattr(instr, name)
        for p in params:
            _sc.send_message("/synth/param", [name, p, float(getattr(inst, p))])
    for p in ("reverb", "delay", "delayTime"):
        _sc.send_message("/synth/param", ["fx", p, float(getattr(section.fx, p))])
    # scratch lead: re-render the vocal buffer with this section's word
    _sc.send_message("/scratch/word", [str(section.scratch_word)])
    # for scratch genres, render the SONG TITLE via Kokoro TTS (background
    # thread so it never blocks the director) and load it into the scratch
    # buffer. Falls back to the /scratch/word procedural vowel if TTS fails.
    if section.genre in _SCRATCH_GENRES:
        words = list(section.scratch_words)[:2] or ["fresh", "go"]
        while len(words) < 2:
            words.append("go")
        # phases 1 & 2 = the two teaser phrases; phase 3 = the two-word title
        phrases = [words[0], words[1], section.scratch_title]
        threading.Thread(target=_render_scratch_set, args=(phrases,), daemon=True).start()

    # 2) MIDI worker: re-prime hints
    enabled = {k: getattr(instr, k).enabled for k in _INSTR_PARAMS}
    _midi.send_message(
        "/midi/section",
        [json.dumps({
            "genre": section.genre,          # <-- the worker needs this!
            "tempo": section.bpm,
            "bpm": section.bpm,
            "key": section.key,
            "density": section.density,
            "harmony": section.harmony,      # LLM's chord-progression choice
            "structure": section.structure,  # LLM's arrangement archetype
            "name": section.name,
            "instruments": enabled,
        })],
    )
    _midi.send_message("/midi/tempo", [float(section.bpm)])

    # 3) bridge -> browser
    try:
        requests.post(BRIDGE_URL, json=section.model_dump(), timeout=2.0)
    except requests.RequestException as e:
        print(f"[publish] bridge POST failed (non-fatal): {e}")

    print(f"[publish] section '{sid}'  bpm={section.bpm}  mood={section.mood}")
