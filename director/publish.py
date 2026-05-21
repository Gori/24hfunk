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
_SCRATCH_GENRES = {"eighties_hiphop", "boom_bap"}
# genres whose lead is the ROBOT VOCAL — render robot_phrase word-by-word so
# the leadVox synth chants it on the beat (reuses the scratch buffer slots).
_VOCODE_GENRES = {"electro"}
_VOX_MAX = 6                      # buffer slots available
_VOX_VOICE = "af_alloy"           # neutral source; robotization happens in SC
_SCRATCH_WAV = "/tmp/str_scratch.wav"

# classic one-word DJ-scratch vocab — the FIRST build phase scratches a
# rotating pair of these (Kokoro-rendered) instead of a teaser word. The
# emphatic spelling is intentional + honored: Kokoro elongates the vowels
# (Aaaaahhhhhh) and the caps/!!! add punch — it does NOT spell them out.
_CANON_SCRATCH = ("Aaaaahhhhhh", "FRESH!!!", "ROCK!", "AND!!", "HUHHHHH", "WIKKI-WIKKI")
_canon_i = 0

SC_HOST = "127.0.0.1"
SC_PORT = int(os.environ.get("SC_OSC_PORT", "57120"))
MIDI_HOST = "127.0.0.1"
MIDI_PORT = int(os.environ.get("MIDI_CTRL_OSC_PORT", "57121"))
BRIDGE_URL = f"http://localhost:{os.environ.get('BRIDGE_HTTP_PORT', '8080')}/section"

_sc = SimpleUDPClient(SC_HOST, SC_PORT)
_midi = SimpleUDPClient(MIDI_HOST, MIDI_PORT)


# articulation -> (TTS speed, scratch-synth drive, scratch-synth cutoff Hz)
_ARTIC = {
    "soft":       (0.92, 0.5, 2400),
    "neutral":    (1.00, 1.0, 3600),
    "aggressive": (1.12, 2.2, 5500),
}


def _phrase_words(phrase: str) -> list[str]:
    """A phrase -> exactly TWO word tokens (so each gets its own buffer; a
    1-word phrase fills both slots with the same word)."""
    words = [w for w in str(phrase).split() if w][:2]
    if not words:
        words = ["fresh"]
    if len(words) == 1:
        words = [words[0], words[0]]
    return words


def _render_scratch_set(phase_phrases: list[str], voice: str, speed: float) -> None:
    """Render each WORD of the 3 phase phrases into its own buffer slot, so
    multi-word phrases scratch word-by-word. Slots: phase1 words -> 0,1;
    phase2 -> 2,3; title -> 4,5. Daemon thread; silent no-op on failure."""
    for p, phrase in enumerate(phase_phrases[:3]):
        for w, word in enumerate(_phrase_words(phrase)):
            slot = p * 2 + w
            path = f"/tmp/str_scratch_{slot}.wav"
            if tts.render(word, path, voice=voice, speed=speed):
                _sc.send_message("/scratch/load", [slot, path])


def _render_vox_set(words: list[str]) -> None:
    """Render each WORD of the electro robot phrase into its own buffer slot
    (0..N-1), so the robot vocal chants them word-by-word. Daemon thread."""
    for i, word in enumerate(words[:_VOX_MAX]):
        path = f"/tmp/str_scratch_{i}.wav"
        if tts.render(word, path, voice=_VOX_VOICE, speed=1.0):
            _sc.send_message("/scratch/load", [i, path])

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
        global _canon_i
        words = list(section.scratch_words)[:2] or ["fresh", "go"]
        while len(words) < 2:
            words.append("go")
        # phase 1 = a rotating pair of CLASSIC scratch words (ahh/fresh/rock..),
        # phase 2 = the LLM teaser phrase, phase 3 = the two-word title.
        n = len(_CANON_SCRATCH)
        canon = f"{_CANON_SCRATCH[_canon_i % n]} {_CANON_SCRATCH[(_canon_i + 1) % n]}"
        _canon_i += 1
        phrases = [canon, words[0], section.scratch_title]
        speed, drive, cutoff = _ARTIC.get(section.scratch_articulation, _ARTIC["neutral"])
        # articulation -> scratch-synth drive + brightness (router applies to leadScratch)
        _sc.send_message("/scratch/artic", [float(drive), float(cutoff)])
        threading.Thread(target=_render_scratch_set,
                         args=(phrases, section.scratch_voice, speed), daemon=True).start()

    # electro robot vocal: render robot_phrase word-by-word into the buffer
    # slots; tell the worker how many words to cycle on the beat.
    vox_n = 0
    if section.genre in _VOCODE_GENRES:
        words = section.robot_phrase.split()[:_VOX_MAX] or ["machine"]
        vox_n = len(words)
        threading.Thread(target=_render_vox_set, args=(words,), daemon=True).start()

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
            "robot_words": vox_n,            # electro: # of robot words to cycle
            "duration_sec": section.duration_sec,  # rnb bell arp enters at halfway
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
