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


def _render_scratch_title(text: str) -> None:
    """Render the title to a wav (Kokoro) and tell SC to load it as the
    scratch buffer. Runs in a daemon thread; silent no-op if TTS fails."""
    if tts.render(text, _SCRATCH_WAV):
        _sc.send_message("/scratch/load", [_SCRATCH_WAV])

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
        title = section.name if (section.name and section.name != "untitled") \
            else str(section.scratch_word)
        threading.Thread(target=_render_scratch_title, args=(title,), daemon=True).start()

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
