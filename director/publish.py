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
# genres whose lead is a TTS VOCAL CHANT — render each phrase as its own
# sample (NOT robotized) so leadChant plays them call-and-response.
_CHANT_GENRES = {"bounce"}
# distinct CALL (lead MC) vs RESPONSE (crowd) voices so the alternation reads
# as bounce call-and-response. Even-index phrases = calls, odd = responses.
_CHANT_VOICE_CALL = "af_bella"    # bright, hyped lead MC
_CHANT_VOICE_RESP = "am_adam"     # contrasting crowd "answer"
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


def _chant_layout(phrases: list[str]) -> tuple[list[str], list[str]]:
    """The bounce chant is built from SINGLE WORDS so the dance command can be
    chanted word-by-word. Slots 0..k-1 = the words of the COMMAND (phrase 0,
    e.g. "do the bayou wobble"); the rest = answer/hype single words from the
    other phrases. Returns (command_words, extra_words)."""
    cmd_words = (phrases[0].split() if phrases else ["do", "the", "dance"])[:4]
    low = {w.lower() for w in cmd_words}
    extras: list[str] = []
    for ph in phrases[1:]:
        for w in ph.split():
            wl = w.strip().lower()
            if wl and wl not in low and wl not in (e.lower() for e in extras):
                extras.append(w.strip())
    return cmd_words, extras[:max(0, _VOX_MAX - len(cmd_words))]


def _render_chant_set(phrases: list[str]) -> None:
    """Render each chant WORD into its own buffer slot (command words first,
    then answer/hype words), so the builder can chant the dance command word-by-
    word and shout single-word answers. Even slots = MC voice, odd = crowd."""
    cmd_words, extras = _chant_layout(phrases)
    for slot, w in enumerate((cmd_words + extras)[:_VOX_MAX]):
        voice = _CHANT_VOICE_CALL if (slot % 2 == 0) else _CHANT_VOICE_RESP
        path = f"/tmp/str_scratch_{slot}.wav"
        if tts.render(w, path, voice=voice, speed=1.05):
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

    # bounce chant: render the call-and-response phrases into buffer slots;
    # tell the worker how many to cycle.
    chant_cmd = 0
    chant_n = 0
    if section.genre in _CHANT_GENRES:
        phrases = list(section.chant_phrases) or ["do the dance"]
        cmd_words, extras = _chant_layout(phrases)
        chant_cmd = len(cmd_words)                       # # of command words (chanted in order)
        chant_n = min(_VOX_MAX, chant_cmd + len(extras))  # total word slots used
        print(f"[publish] bounce dance: command={cmd_words}  answers={extras}")
        threading.Thread(target=_render_chant_set, args=(phrases,), daemon=True).start()

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
            "chant_cmd": chant_cmd,          # bounce: # of command words (chanted in order)
            "chant_n": chant_n,              # bounce: total chant word slots
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
