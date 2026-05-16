"""Publish a SectionState to the three consumers:
  - SuperCollider router  (OSC 57120): /section/begin + /synth/param fan
  - MIDI worker control   (OSC 57121): /midi/section + /midi/tempo
  - bridge                (HTTP 8080): POST /section  -> WS to browser
"""
from __future__ import annotations

import json
import os

import requests
from pythonosc.udp_client import SimpleUDPClient

from director.schema import SectionState

SC_HOST = "127.0.0.1"
SC_PORT = int(os.environ.get("SC_OSC_PORT", "57120"))
MIDI_HOST = "127.0.0.1"
MIDI_PORT = int(os.environ.get("MIDI_CTRL_OSC_PORT", "57121"))
BRIDGE_URL = f"http://localhost:{os.environ.get('BRIDGE_HTTP_PORT', '8080')}/section"

_sc = SimpleUDPClient(SC_HOST, SC_PORT)
_midi = SimpleUDPClient(MIDI_HOST, MIDI_PORT)

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

    # 2) MIDI worker: re-prime hints
    enabled = {k: getattr(instr, k).enabled for k in _INSTR_PARAMS}
    _midi.send_message(
        "/midi/section",
        [json.dumps({
            "tempo": section.bpm,
            "key": section.key,
            "density": section.density,
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
