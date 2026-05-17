"""Funk groove engine — research-backed funk + a real music-theory harmony
layer (chords, voice-leading, walking bass, comping, motif leads).

SPACE is articulation/syncopation/dynamics/micro-timing, not just few notes.
Harmony: per-genre chord progressions with real qualities (maj7/min7/dom9/
dom7#9/min7b5/dim7/sus...), chord-aware bass (root/5/oct + chromatic approach;
jazz = walking quarters), comped voicings on off-beats, and a per-section
melodic MOTIF (guide tones, repeated with call-and-response variation).

Class stays `CannedSource` / name="canned" so the worker import is unchanged.
"""
from __future__ import annotations

import random

from midi.source import (CH_BASS, CH_LEAD, CH_KEYS, CH_PERC, CH_DRUMS,
                          Note, Phrase)

KICK, RIM, SNARE, CLAP, HAT, OHAT, PERC, RIDE = 36, 37, 38, 39, 42, 46, 75, 51

_PC = {
    "c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5,
    "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10,
    "b": 11,
}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
NAT_MINOR = [0, 2, 3, 5, 7, 8, 10]
DORIAN = [0, 2, 3, 5, 7, 9, 10]
PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]

# chord quality -> intervals from the chord root (chromatic)
CHORD = {
    "maj": [0, 4, 7], "min": [0, 3, 7], "dim": [0, 3, 6], "sus4": [0, 5, 7],
    "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "dom7": [0, 4, 7, 10],
    "min7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9], "min6": [0, 3, 7, 9],
    "maj9": [0, 4, 7, 11, 14], "min9": [0, 3, 7, 10, 14],
    "dom9": [0, 4, 7, 10, 14], "dom7#9": [0, 4, 7, 10, 15],
    "dom7b9": [0, 4, 7, 10, 13], "min11": [0, 3, 7, 10, 14, 17],
}

GENRES = ("electro_funk", "synthwave", "neon_dub", "broken_house",
          "lofi", "electro", "eighties_hiphop", "jazz", "funk",
          "minneapolis_funk", "minimal_techno", "detroit_techno",
          "dub", "steppers_dub", "dub_techno", "roots_reggae",
          "dub_garage", "uk_garage",
          "rnb", "afro_rnb", "indie_rnb")

# scale (for melody/passing) + chord progression as (scale_degree, quality)
# pairs + swing(0..0.5 of 16th) + snare_drag_s + kick_push_s + hat_jit_s +
# chaos_s + note cap
PROFILE = {
    "electro_funk": (DORIAN,
        [(0, "min9"), (0, "min9"), (3, "dom9"), (4, "dom7#9")],
        0.34, 0.026, -0.006, 0.006, 0.0, 70),
    "synthwave": (NAT_MINOR,
        [(0, "min9"), (5, "maj7"), (3, "maj7"), (4, "dom9")],
        0.07, 0.014, -0.003, 0.004, 0.0, 70),
    "neon_dub": (NAT_MINOR,
        [(0, "min9"), (0, "min9"), (3, "min7"), (3, "min7")],
        0.30, 0.040, 0.008, 0.006, 0.0, 36),
    "broken_house": (DORIAN,
        [(0, "min9"), (3, "maj7"), (4, "dom9"), (0, "min9")],
        0.42, 0.012, 0.0, 0.005, 0.0, 70),
    "lofi": (DORIAN,
        [(1, "min7"), (4, "dom9"), (0, "maj7"), (5, "min7")],
        0.42, 0.034, 0.004, 0.008, 0.0, 44),
    "electro": (PHRYGIAN,
        [(0, "min7"), (0, "min7"), (5, "maj7"), (6, "dom7")],
        0.06, 0.006, -0.004, 0.004, 0.0, 64),
    "eighties_hiphop": (DORIAN,
        [(0, "min9"), (0, "min9"), (3, "dom9"), (0, "min9")],
        0.30, 0.030, 0.0, 0.008, 0.0, 40),
    "jazz": (DORIAN,
        [(1, "min7"), (4, "dom9"), (0, "maj7"), (5, "dom7b9")],   # ii V I VI
        0.46, 0.030, 0.0, 0.006, 0.0, 60),
    "funk": (DORIAN,
        [(0, "dom7#9"), (0, "dom7#9"), (0, "min7"), (0, "dom7#9")],  # 1-chord vamp
        0.36, 0.024, -0.005, 0.006, 0.0, 72),
    "minneapolis_funk": (DORIAN,
        [(0, "min9"), (3, "maj9"), (4, "dom9"), (0, "min9")],
        0.30, 0.014, -0.004, 0.005, 0.0, 70),
    # minimal techno: hypnotic, mechanical, one-chord vamp, sparse
    "minimal_techno": (NAT_MINOR,
        [(0, "min9"), (0, "min9"), (0, "min7"), (0, "min9")],
        0.03, 0.003, -0.003, 0.004, 0.0, 32),
    # detroit techno: soulful/futurist, lush stab chords, driving
    "detroit_techno": (DORIAN,
        [(0, "min9"), (3, "maj9"), (5, "min7"), (4, "dom9")],
        0.06, 0.008, -0.004, 0.005, 0.0, 64),
    # Jamaican / UK lineage — bass + space heavy
    "dub": (NAT_MINOR,
        [(0, "min7"), (0, "min7"), (3, "maj7"), (0, "min7")],
        0.30, 0.030, 0.010, 0.006, 0.0, 30),
    "steppers_dub": (NAT_MINOR,
        [(0, "min7"), (0, "min7"), (5, "min7"), (0, "min7")],
        0.20, 0.024, 0.008, 0.006, 0.0, 34),
    "dub_techno": (NAT_MINOR,
        [(0, "min9"), (0, "min9"), (0, "min7"), (0, "min9")],
        0.05, 0.006, -0.003, 0.004, 0.0, 30),
    "roots_reggae": (NAT_MINOR,
        [(0, "min7"), (3, "maj7"), (4, "min7"), (0, "min7")],
        0.34, 0.028, 0.010, 0.007, 0.0, 36),
    "uk_garage": (DORIAN,
        [(0, "min9"), (3, "maj9"), (4, "dom9"), (0, "min9")],
        0.46, 0.010, 0.0, 0.005, 0.0, 60),
    "dub_garage": (DORIAN,
        [(0, "min9"), (0, "min9"), (3, "maj7"), (4, "dom9")],
        0.46, 0.012, 0.004, 0.005, 0.0, 56),
    # R&B family — lush extended harmony, laid-back pocket, lots of space
    "rnb": (DORIAN,
        [(0, "min9"), (3, "dom9"), (2, "maj9"), (4, "min7")],
        0.40, 0.030, 0.004, 0.007, 0.0, 44),
    "afro_rnb": (DORIAN,
        [(0, "min9"), (3, "maj9"), (4, "dom9"), (0, "min9")],
        0.26, 0.016, -0.002, 0.006, 0.0, 52),
    "indie_rnb": (NAT_MINOR,
        [(0, "min9"), (5, "maj7"), (3, "maj9"), (4, "min7")],
        0.44, 0.034, 0.006, 0.008, 0.0, 34),
}

SYNTH_PARAMS = {
    "electro_funk": {"kick": {"drive": 2.4, "click": 0.5, "decay": 0.28}, "snare": {"snap": 0.8, "tone": 0.5, "crush": 0.06}, "hat": {"metal": 0.6, "cutoff": 10000, "decay": 0.035}, "ohat": {"metal": 0.6, "cutoff": 9200, "decay": 0.24}, "clap": {"decay": 0.18, "tone": 1.05}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.3, "cutoff": 780, "res": 0.18, "fenv": 0.5, "sub": 0.85, "glide": 0.01}, "lead": {"detune": 0.1, "wave": 0.35, "cutoff": 5400, "drive": 1.4, "decay": 0.16}, "fx": {"reverb": 0.2, "delay": 0.18, "delayTime": 0.33, "width": 0.7}},
    "synthwave": {"kick": {"drive": 2.2, "click": 0.38, "decay": 0.3}, "snare": {"snap": 0.62, "tone": 0.52, "crush": 0.0}, "hat": {"metal": 0.4, "cutoff": 8400, "decay": 0.045}, "ohat": {"metal": 0.4, "cutoff": 7900, "decay": 0.28}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.045}, "perc": {"decay": 0.13}, "bass": {"drive": 1.2, "cutoff": 680, "res": 0.16, "fenv": 0.4, "sub": 0.78, "glide": 0.0}, "lead": {"detune": 0.2, "wave": 0.15, "cutoff": 6800, "drive": 1.1, "decay": 0.24}, "fx": {"reverb": 0.36, "delay": 0.25, "delayTime": 0.375, "width": 0.65}},
    "neon_dub": {"kick": {"drive": 2.0, "click": 0.28, "decay": 0.4}, "snare": {"snap": 0.42, "tone": 0.55, "crush": 0.08}, "hat": {"metal": 0.45, "cutoff": 7400, "decay": 0.055}, "ohat": {"metal": 0.45, "cutoff": 7000, "decay": 0.36}, "clap": {"decay": 0.28, "tone": 0.85}, "rim": {"decay": 0.055}, "perc": {"decay": 0.17}, "bass": {"drive": 1.1, "cutoff": 360, "res": 0.12, "fenv": 0.25, "sub": 0.97, "glide": 0.05}, "lead": {"detune": 0.12, "wave": 0.25, "cutoff": 4400, "drive": 0.9, "decay": 0.5}, "fx": {"reverb": 0.55, "delay": 0.44, "delayTime": 0.5, "width": 0.9}},
    "broken_house": {"kick": {"drive": 2.4, "click": 0.42, "decay": 0.28}, "snare": {"snap": 0.68, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.48, "cutoff": 9400, "decay": 0.04}, "ohat": {"metal": 0.48, "cutoff": 8800, "decay": 0.28}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.045}, "perc": {"decay": 0.12}, "bass": {"drive": 1.3, "cutoff": 740, "res": 0.2, "fenv": 0.5, "sub": 0.7, "glide": 0.0}, "lead": {"detune": 0.15, "wave": 0.3, "cutoff": 5800, "drive": 1.2, "decay": 0.2}, "fx": {"reverb": 0.26, "delay": 0.22, "delayTime": 0.353, "width": 0.7}},
    "lofi": {"kick": {"drive": 1.5, "click": 0.26, "decay": 0.34}, "snare": {"snap": 0.38, "tone": 0.44, "crush": 0.2}, "hat": {"metal": 0.32, "cutoff": 7000, "decay": 0.045}, "ohat": {"metal": 0.32, "cutoff": 6600, "decay": 0.24}, "clap": {"decay": 0.24, "tone": 0.8}, "rim": {"decay": 0.055}, "perc": {"decay": 0.15}, "bass": {"drive": 1.0, "cutoff": 460, "res": 0.14, "fenv": 0.35, "sub": 0.85, "glide": 0.0}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 4000, "drive": 0.85, "decay": 0.4}, "fx": {"reverb": 0.4, "delay": 0.3, "delayTime": 0.45, "width": 0.6}},
    "electro": {"kick": {"drive": 2.2, "click": 0.4, "decay": 0.42}, "snare": {"snap": 0.7, "tone": 0.4, "crush": 0.18}, "hat": {"metal": 0.7, "cutoff": 11000, "decay": 0.03}, "ohat": {"metal": 0.7, "cutoff": 10000, "decay": 0.2}, "clap": {"decay": 0.2, "tone": 1.15}, "rim": {"decay": 0.04}, "perc": {"decay": 0.1}, "bass": {"drive": 1.2, "cutoff": 900, "res": 0.22, "fenv": 0.55, "sub": 0.7, "glide": 0.0}, "lead": {"detune": 0.06, "wave": 0.6, "cutoff": 6500, "drive": 1.6, "decay": 0.14}, "fx": {"reverb": 0.26, "delay": 0.22, "delayTime": 0.1875, "width": 0.8}},
    "eighties_hiphop": {"kick": {"drive": 1.8, "click": 0.35, "decay": 0.46}, "snare": {"snap": 0.7, "tone": 0.55, "crush": 0.12}, "hat": {"metal": 0.4, "cutoff": 8500, "decay": 0.04}, "ohat": {"metal": 0.4, "cutoff": 8000, "decay": 0.26}, "clap": {"decay": 0.24, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.13}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.14, "fenv": 0.3, "sub": 0.9, "glide": 0.0}, "lead": {"detune": 0.1, "wave": 0.3, "cutoff": 4800, "drive": 1.0, "decay": 0.22}, "fx": {"reverb": 0.34, "delay": 0.28, "delayTime": 0.375, "width": 0.65}},
    "jazz": {"kick": {"drive": 1.2, "click": 0.2, "decay": 0.3}, "snare": {"snap": 0.4, "tone": 0.5, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9000, "decay": 0.05}, "ohat": {"metal": 0.5, "cutoff": 8500, "decay": 0.4}, "clap": {"decay": 0.18, "tone": 0.9}, "rim": {"decay": 0.05}, "perc": {"decay": 0.12}, "bass": {"drive": 0.8, "cutoff": 520, "res": 0.1, "fenv": 0.25, "sub": 0.8, "glide": 0.02}, "lead": {"detune": 0.06, "wave": 0.28, "cutoff": 3400, "drive": 0.45, "decay": 0.7}, "fx": {"reverb": 0.42, "delay": 0.18, "delayTime": 0.42, "width": 0.7}},
    "funk": {"kick": {"drive": 2.6, "click": 0.55, "decay": 0.26}, "snare": {"snap": 0.88, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.62, "cutoff": 10500, "decay": 0.03}, "ohat": {"metal": 0.62, "cutoff": 9500, "decay": 0.22}, "clap": {"decay": 0.17, "tone": 1.05}, "rim": {"decay": 0.038}, "perc": {"decay": 0.1}, "bass": {"drive": 0.6, "cutoff": 420, "res": 0.08, "fenv": 0.2, "sub": 0.92, "glide": 0.01}, "lead": {"detune": 0.08, "wave": 0.4, "cutoff": 5600, "drive": 1.5, "decay": 0.16}, "fx": {"reverb": 0.18, "delay": 0.16, "delayTime": 0.33, "width": 0.7}},
    "minneapolis_funk": {"kick": {"drive": 2.0, "click": 0.45, "decay": 0.3}, "snare": {"snap": 0.85, "tone": 0.55, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9800, "decay": 0.035}, "ohat": {"metal": 0.5, "cutoff": 9000, "decay": 0.26}, "clap": {"decay": 0.22, "tone": 1.0}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.4, "cutoff": 1000, "res": 0.3, "fenv": 0.6, "sub": 0.55, "glide": 0.0}, "lead": {"detune": 0.14, "wave": 0.45, "cutoff": 6200, "drive": 1.3, "decay": 0.18}, "fx": {"reverb": 0.28, "delay": 0.2, "delayTime": 0.1875, "width": 0.75}},
    "minimal_techno": {"kick": {"drive": 1.8, "click": 0.3, "decay": 0.34}, "snare": {"snap": 0.5, "tone": 0.4, "crush": 0.0}, "hat": {"metal": 0.55, "cutoff": 11000, "decay": 0.022}, "ohat": {"metal": 0.55, "cutoff": 9500, "decay": 0.16}, "clap": {"decay": 0.16, "tone": 1.1}, "rim": {"decay": 0.03}, "perc": {"decay": 0.08}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.12, "fenv": 0.3, "sub": 0.92, "glide": 0.02}, "lead": {"detune": 0.05, "wave": 0.5, "cutoff": 5200, "drive": 1.1, "decay": 0.12}, "fx": {"reverb": 0.34, "delay": 0.34, "delayTime": 0.5, "width": 0.7}},
    "detroit_techno": {"kick": {"drive": 2.2, "click": 0.4, "decay": 0.32}, "snare": {"snap": 0.6, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.48, "cutoff": 9600, "decay": 0.035}, "ohat": {"metal": 0.48, "cutoff": 8800, "decay": 0.3}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.045}, "perc": {"decay": 0.12}, "bass": {"drive": 0.7, "cutoff": 480, "res": 0.08, "fenv": 0.18, "sub": 0.85, "glide": 0.0}, "lead": {"detune": 0.16, "wave": 0.3, "cutoff": 5800, "drive": 1.2, "decay": 0.3}, "fx": {"reverb": 0.46, "delay": 0.32, "delayTime": 0.375, "width": 0.85}},
    "dub": {"kick": {"drive": 1.6, "click": 0.2, "decay": 0.5}, "snare": {"snap": 0.5, "tone": 0.55, "crush": 0.1}, "hat": {"metal": 0.35, "cutoff": 7200, "decay": 0.05}, "ohat": {"metal": 0.35, "cutoff": 6800, "decay": 0.4}, "clap": {"decay": 0.3, "tone": 0.8}, "rim": {"decay": 0.07}, "perc": {"decay": 0.18}, "bass": {"drive": 1.1, "cutoff": 320, "res": 0.1, "fenv": 0.25, "sub": 0.98, "glide": 0.06}, "lead": {"detune": 0.1, "wave": 0.2, "cutoff": 3600, "drive": 0.9, "decay": 0.5}, "fx": {"reverb": 0.6, "delay": 0.5, "delayTime": 0.5, "width": 0.9}},
    "steppers_dub": {"kick": {"drive": 1.8, "click": 0.25, "decay": 0.46}, "snare": {"snap": 0.55, "tone": 0.5, "crush": 0.08}, "hat": {"metal": 0.38, "cutoff": 7600, "decay": 0.045}, "ohat": {"metal": 0.38, "cutoff": 7000, "decay": 0.38}, "clap": {"decay": 0.28, "tone": 0.85}, "rim": {"decay": 0.06}, "perc": {"decay": 0.16}, "bass": {"drive": 1.2, "cutoff": 340, "res": 0.12, "fenv": 0.3, "sub": 0.97, "glide": 0.04}, "lead": {"detune": 0.1, "wave": 0.25, "cutoff": 3800, "drive": 1.0, "decay": 0.45}, "fx": {"reverb": 0.55, "delay": 0.46, "delayTime": 0.5, "width": 0.88}},
    "dub_techno": {"kick": {"drive": 1.8, "click": 0.28, "decay": 0.36}, "snare": {"snap": 0.45, "tone": 0.45, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9000, "decay": 0.03}, "ohat": {"metal": 0.5, "cutoff": 8200, "decay": 0.28}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.04}, "perc": {"decay": 0.1}, "bass": {"drive": 1.0, "cutoff": 380, "res": 0.1, "fenv": 0.25, "sub": 0.95, "glide": 0.03}, "lead": {"detune": 0.12, "wave": 0.35, "cutoff": 4200, "drive": 1.0, "decay": 0.4}, "fx": {"reverb": 0.6, "delay": 0.45, "delayTime": 0.5, "width": 0.85}},
    "roots_reggae": {"kick": {"drive": 1.5, "click": 0.22, "decay": 0.42}, "snare": {"snap": 0.5, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.34, "cutoff": 7000, "decay": 0.05}, "ohat": {"metal": 0.34, "cutoff": 6600, "decay": 0.34}, "clap": {"decay": 0.24, "tone": 0.85}, "rim": {"decay": 0.07}, "perc": {"decay": 0.16}, "bass": {"drive": 1.0, "cutoff": 380, "res": 0.1, "fenv": 0.3, "sub": 0.95, "glide": 0.05}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 3800, "drive": 0.85, "decay": 0.4}, "fx": {"reverb": 0.4, "delay": 0.28, "delayTime": 0.42, "width": 0.7}},
    "uk_garage": {"kick": {"drive": 2.2, "click": 0.42, "decay": 0.28}, "snare": {"snap": 0.7, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.5, "cutoff": 10000, "decay": 0.035}, "ohat": {"metal": 0.5, "cutoff": 9000, "decay": 0.26}, "clap": {"decay": 0.2, "tone": 1.05}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.4, "cutoff": 760, "res": 0.24, "fenv": 0.6, "sub": 0.78, "glide": 0.02}, "lead": {"detune": 0.14, "wave": 0.35, "cutoff": 5800, "drive": 1.3, "decay": 0.2}, "fx": {"reverb": 0.32, "delay": 0.24, "delayTime": 0.353, "width": 0.75}},
    "dub_garage": {"kick": {"drive": 2.0, "click": 0.38, "decay": 0.3}, "snare": {"snap": 0.65, "tone": 0.5, "crush": 0.06}, "hat": {"metal": 0.46, "cutoff": 9400, "decay": 0.035}, "ohat": {"metal": 0.46, "cutoff": 8600, "decay": 0.3}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.12}, "bass": {"drive": 1.3, "cutoff": 560, "res": 0.18, "fenv": 0.5, "sub": 0.88, "glide": 0.03}, "lead": {"detune": 0.12, "wave": 0.3, "cutoff": 5000, "drive": 1.1, "decay": 0.28}, "fx": {"reverb": 0.5, "delay": 0.42, "delayTime": 0.5, "width": 0.85}},
    "rnb": {"kick": {"drive": 1.4, "click": 0.25, "decay": 0.36}, "snare": {"snap": 0.5, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.4, "cutoff": 8200, "decay": 0.045}, "ohat": {"metal": 0.4, "cutoff": 7600, "decay": 0.26}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.13}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.12, "fenv": 0.35, "sub": 0.9, "glide": 0.03}, "lead": {"detune": 0.08, "wave": 0.28, "cutoff": 3000, "drive": 0.4, "decay": 0.62}, "fx": {"reverb": 0.4, "delay": 0.2, "delayTime": 0.375, "width": 0.7}},
    "afro_rnb": {"kick": {"drive": 1.8, "click": 0.35, "decay": 0.32}, "snare": {"snap": 0.6, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.42, "cutoff": 9200, "decay": 0.035}, "ohat": {"metal": 0.42, "cutoff": 8400, "decay": 0.24}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.045}, "perc": {"decay": 0.1}, "bass": {"drive": 1.3, "cutoff": 760, "res": 0.2, "fenv": 0.5, "sub": 0.75, "glide": 0.02}, "lead": {"detune": 0.12, "wave": 0.35, "cutoff": 5600, "drive": 1.1, "decay": 0.22}, "fx": {"reverb": 0.34, "delay": 0.22, "delayTime": 0.353, "width": 0.78}},
    "indie_rnb": {"kick": {"drive": 1.3, "click": 0.22, "decay": 0.4}, "snare": {"snap": 0.45, "tone": 0.5, "crush": 0.12}, "hat": {"metal": 0.35, "cutoff": 7400, "decay": 0.05}, "ohat": {"metal": 0.35, "cutoff": 6800, "decay": 0.34}, "clap": {"decay": 0.26, "tone": 0.85}, "rim": {"decay": 0.06}, "perc": {"decay": 0.16}, "bass": {"drive": 0.9, "cutoff": 420, "res": 0.1, "fenv": 0.3, "sub": 0.92, "glide": 0.05}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 3600, "drive": 0.75, "decay": 0.5}, "fx": {"reverb": 0.55, "delay": 0.34, "delayTime": 0.5, "width": 0.85}},
}


# per-genre per-track FX signatures (override the derived defaults)
_FX_SIG = {
    "neon_dub": {"fxMel": {"reverb": 0.6, "delay": 0.62, "delayTime": 0.5},
                 "fxDrums": {"delay": 0.3, "delayTime": 0.5}},
    "minimal_techno": {"fxMel": {"delay": 0.55, "delayTime": 0.5, "reverb": 0.4},
                       "fxDrums": {"reverb": 0.06, "delay": 0.18, "delayTime": 0.375}},
    "detroit_techno": {"fxMel": {"reverb": 0.55, "delay": 0.34, "delayTime": 0.375},
                       "fxBass": {"reverb": 0.05}},
    "jazz": {"fxMel": {"reverb": 0.5, "delay": 0.12}, "fxBass": {"reverb": 0.03}},
    "lofi": {"fxMel": {"reverb": 0.5, "delay": 0.3}, "fxDrums": {"reverb": 0.18}},
    "funk": {"fxMel": {"delay": 0.16}, "fxDrums": {"reverb": 0.05}},
    "dub": {"fxMel": {"reverb": 0.7, "delay": 0.68, "delayTime": 0.5},
            "fxDrums": {"delay": 0.45, "delayTime": 0.5, "reverb": 0.35},
            "fxBass": {"reverb": 0.1}},
    "steppers_dub": {"fxMel": {"reverb": 0.62, "delay": 0.6, "delayTime": 0.5},
                     "fxDrums": {"delay": 0.4, "delayTime": 0.375, "reverb": 0.3}},
    "dub_techno": {"fxMel": {"reverb": 0.7, "delay": 0.6, "delayTime": 0.5},
                   "fxDrums": {"reverb": 0.2, "delay": 0.25, "delayTime": 0.5}},
    "roots_reggae": {"fxMel": {"reverb": 0.42, "delay": 0.3, "delayTime": 0.42},
                     "fxDrums": {"reverb": 0.18, "delay": 0.2}},
    "dub_garage": {"fxMel": {"reverb": 0.5, "delay": 0.5, "delayTime": 0.5},
                   "fxDrums": {"delay": 0.28, "delayTime": 0.375}},
    "uk_garage": {"fxMel": {"reverb": 0.3, "delay": 0.22}},
    "rnb": {"fxMel": {"reverb": 0.42, "delay": 0.2}, "fxBass": {"reverb": 0.04}},
    "afro_rnb": {"fxMel": {"reverb": 0.32, "delay": 0.22}},
    "indie_rnb": {"fxMel": {"reverb": 0.6, "delay": 0.4, "delayTime": 0.5},
                  "fxDrums": {"reverb": 0.22}},
}

# per-genre instrument variants (role -> SynthDef). Omitted roles = default.
_GENRE_INSTR = {
    "electro_funk":     {"bass": "bassFM",     "kick": "kickHard", "snare": "snare",    "lead": "lead"},
    "synthwave":        {"bass": "bass",       "kick": "kick",     "snare": "snare909", "lead": "lead"},
    "neon_dub":         {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadFM"},
    "broken_house":     {"bass": "bassSquare", "kick": "kickHard", "snare": "snare909", "lead": "leadPulse"},
    "lofi":             {"bass": "bass",       "kick": "kick",     "snare": "snareBrush", "lead": "leadFM"},
    "electro":          {"bass": "bassSquare", "kick": "kick808",  "snare": "snare909", "lead": "leadPulse"},
    "eighties_hiphop":  {"bass": "bass",       "kick": "kick808",  "snare": "snare909", "lead": "leadPulse"},
    "jazz":             {"bass": "bass",       "kick": "kick",     "snare": "snareBrush", "lead": "lead"},
    "funk":             {"bass": "bassFM",     "kick": "kickHard", "snare": "snare",    "lead": "lead"},
    "minneapolis_funk": {"bass": "bassSquare", "kick": "kickHard", "snare": "snare909", "lead": "leadPulse"},
    "minimal_techno":   {"bass": "bassSquare", "kick": "kick",     "snare": "snare909", "lead": "leadPulse"},
    "detroit_techno":   {"bass": "bassFM",     "kick": "kick",     "snare": "snare909", "lead": "leadFM"},
    "dub":              {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadFM"},
    "steppers_dub":     {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadFM"},
    "dub_techno":       {"bass": "bass",       "kick": "kick808",  "snare": "snare909", "lead": "leadFM"},
    "roots_reggae":     {"bass": "bass",       "kick": "kick",     "snare": "snare",    "lead": "leadFM"},
    "uk_garage":        {"bass": "bassFM",     "kick": "kickHard", "snare": "snare909", "lead": "leadPulse"},
    "dub_garage":       {"bass": "bassFM",     "kick": "kickHard", "snare": "snare909", "lead": "leadFM"},
    "rnb":              {"bass": "bass",       "kick": "kick",     "snare": "snare",    "lead": "lead"},
    "afro_rnb":         {"bass": "bassFM",     "kick": "kick",     "snare": "snare909", "lead": "leadFM"},
    "indie_rnb":        {"bass": "bass",       "kick": "kick808",  "snare": "snareBrush", "lead": "leadFM"},
}


def _key_pc(key: str) -> int:
    k = (key or "C minor").strip().lower().split()
    return _PC.get(k[0] if k else "c", 0)


# Repeating melodic contours (scale-step deltas from a chord-anchored note).
# A section picks one deterministically -> the lead phrase recurs (memorable),
# with a call-and-response variation on the "answer" bars.
_CONTOURS = (
    (0, 1, 2, 1, 0), (0, 2, 1, -1, -2), (0, -1, 1, 3, 2),
    (0, 1, -1, 2, 0, -2), (0, 3, 2, 0, -1), (0, -2, -1, 1, 0),
    (0, 1, 0, 2, 1, -1),
)
# Per-genre lead character. notes=fire prob mult (density), fill=prob of a
# stepwise scale pickup INTO the anchor, run=max pickup length, span=contour
# clamp (scale steps), harm=harmonised-interval prob. Sparse genres stay
# sparse (minimal aesthetic) — this changes note CHOICE, not density.
_LEAD_DEF = {"notes": 1.0, "fill": 0.45, "run": 2, "span": 6, "harm": 0.30}
_LEAD_STYLE = {
    "jazz":             {"notes": 1.25, "fill": 0.78, "run": 4, "span": 10, "harm": 0.22},
    "funk":             {"notes": 1.0,  "fill": 0.42, "run": 2, "span": 5,  "harm": 0.30},
    "minneapolis_funk": {"notes": 1.0,  "fill": 0.45, "run": 3, "span": 6,  "harm": 0.32},
    "electro_funk":     {"notes": 1.0,  "fill": 0.45, "run": 3, "span": 6,  "harm": 0.28},
    "neon_dub":         {"notes": 0.5,  "fill": 0.22, "run": 2, "span": 5,  "harm": 0.18},
    "dub":              {"notes": 0.5,  "fill": 0.22, "run": 2, "span": 5,  "harm": 0.18},
    "steppers_dub":     {"notes": 0.55, "fill": 0.25, "run": 2, "span": 5,  "harm": 0.18},
    "dub_techno":       {"notes": 0.55, "fill": 0.25, "run": 2, "span": 4,  "harm": 0.16},
    "dub_garage":       {"notes": 0.7,  "fill": 0.4,  "run": 3, "span": 6,  "harm": 0.22},
    "roots_reggae":     {"notes": 0.6,  "fill": 0.3,  "run": 2, "span": 5,  "harm": 0.22},
    "minimal_techno":   {"notes": 0.7,  "fill": 0.3,  "run": 2, "span": 4,  "harm": 0.14},
    "detroit_techno":   {"notes": 0.78, "fill": 0.4,  "run": 3, "span": 5,  "harm": 0.18},
    "rnb":              {"notes": 0.85, "fill": 0.62, "run": 3, "span": 7,  "harm": 0.36},
    "afro_rnb":         {"notes": 0.92, "fill": 0.6,  "run": 3, "span": 7,  "harm": 0.32},
    "indie_rnb":        {"notes": 0.78, "fill": 0.62, "run": 3, "span": 7,  "harm": 0.34},
    "lofi":             {"notes": 0.8,  "fill": 0.6,  "run": 3, "span": 6,  "harm": 0.34},
    "synthwave":        {"notes": 1.0,  "fill": 0.55, "run": 3, "span": 8,  "harm": 0.30},
    "electro":          {"notes": 1.0,  "fill": 0.42, "run": 2, "span": 6,  "harm": 0.24},
    "broken_house":     {"notes": 0.95, "fill": 0.5,  "run": 3, "span": 7,  "harm": 0.26},
    "uk_garage":        {"notes": 0.95, "fill": 0.5,  "run": 3, "span": 7,  "harm": 0.26},
    "eighties_hiphop":  {"notes": 0.85, "fill": 0.5,  "run": 3, "span": 6,  "harm": 0.28},
}

# Curated rhythmic motifs make the lead sound PLAYED, not random-sampled.
# A genre maps to a feel; each feel has a few hand-written figures of
# (degIdx, step16, dur16). degIdx is unused for pitch (the contour drives
# pitch) but kept so the tuple shape matches everything that reads motif.
_LEAD_FEEL = {
    "funk": "funk", "minneapolis_funk": "funk", "electro_funk": "funk",
    "jazz": "jazz",
    "broken_house": "stab", "uk_garage": "stab", "dub_garage": "stab",
    "electro": "stab", "synthwave": "stab",
    "minimal_techno": "hypno", "detroit_techno": "hypno", "dub_techno": "hypno",
    "rnb": "lyric", "afro_rnb": "lyric", "indie_rnb": "lyric",
    "lofi": "lyric", "eighties_hiphop": "lyric",
    "dub": "space", "neon_dub": "space", "steppers_dub": "space",
    "roots_reggae": "space",
}
_LEAD_RHYTHM = {
    "funk": [
        [(0, 0, 2), (1, 3, 1), (2, 6, 2), (1, 10, 1), (0, 11, 1)],
        [(0, 2, 1), (2, 5, 2), (1, 8, 1), (3, 11, 2), (0, 14, 1)],
        [(0, 0, 1), (1, 4, 1), (2, 7, 2), (0, 10, 1), (2, 13, 1)],
    ],
    "jazz": [
        [(0, 0, 2), (1, 4, 1), (2, 6, 1), (3, 8, 2), (1, 12, 2)],
        [(0, 2, 1), (1, 4, 1), (2, 6, 1), (3, 9, 1), (2, 12, 2), (0, 14, 1)],
    ],
    "stab": [
        [(0, 2, 2), (2, 6, 2), (1, 10, 2), (3, 14, 2)],
        [(0, 0, 1), (2, 6, 2), (0, 10, 1), (2, 14, 2)],
    ],
    "hypno": [
        [(0, 0, 3), (2, 8, 3)],
        [(0, 0, 2), (1, 6, 2), (0, 12, 2)],
    ],
    "lyric": [
        [(0, 0, 3), (2, 6, 2), (1, 10, 2), (0, 13, 2)],
        [(0, 2, 2), (1, 6, 2), (3, 10, 3)],
    ],
    "space": [
        [(0, 0, 6)],
        [(0, 4, 4), (0, 12, 3)],
    ],
}

# Dedicated percussion layer, per genre. Designed AGAINST each genre's
# existing kick/snare/hat groove so it fills gaps, never clashes.
#   mode : "none" (no perc at all) | "spice" (rare rhythmic seasoning,
#          often whole bars skipped) | "lots" (a real percussion part)
#   tone : perc2 character — ~0.1 glitch electronic, ~0.45 shaker,
#          ~0.9 organic African-ish drum
#   steps: 16th positions it MAY hit (chosen on the off-beats / gaps)
#   pitch: organic drum pitches it cycles (mostly matters when tone high)
#   syn  : perc2 synth params for the genre (decay/drive/crush)
_PERC = {
    # ---- LOTS: a real percussion part, but a SPARSE SYNCOPATED groove
    # (off-beat accents in the kick/snare gaps) — never a steady
    # subdivision, so it can't read as a second hi-hat.
    "afro_rnb":     {"mode": "lots", "tone": 0.9,  "prob": 0.88,
                     "steps": [3, 6, 10, 11, 14], "pitch": [50, 57, 45, 53],
                     "syn": {"decay": 0.17, "drive": 1.3, "crush": 0.2}},
    "roots_reggae": {"mode": "lots", "tone": 0.72, "prob": 0.82,
                     "steps": [3, 6, 10, 11, 14], "pitch": [48, 55, 52],
                     "syn": {"decay": 0.16, "drive": 1.0, "crush": 0.25}},
    "funk":         {"mode": "lots", "tone": 0.66, "prob": 0.8,
                     "steps": [2, 6, 7, 10, 14], "pitch": [53, 48, 57],
                     "syn": {"decay": 0.13, "drive": 1.3, "crush": 0.3}},
    "uk_garage":    {"mode": "lots", "tone": 0.5,  "prob": 0.75,
                     "steps": [2, 7, 10, 11, 14], "pitch": [60],
                     "syn": {"decay": 0.11, "drive": 0.9, "crush": 0.25}},
    "broken_house": {"mode": "lots", "tone": 0.46, "prob": 0.72,
                     "steps": [2, 3, 6, 11, 14], "pitch": [60],
                     "syn": {"decay": 0.12, "drive": 0.9, "crush": 0.25}},
    # ---- formerly NONE -> now sparse dubby/clicky SPICE seasoning ----
    "dub":            {"mode": "spice", "tone": 0.55, "prob": 0.28,
                       "steps": [6, 14], "pitch": [50, 45],
                       "syn": {"decay": 0.16, "drive": 0.9, "crush": 0.3}},
    "neon_dub":       {"mode": "spice", "tone": 0.5,  "prob": 0.26,
                       "steps": [6, 14], "pitch": [55, 48],
                       "syn": {"decay": 0.15, "drive": 0.9, "crush": 0.32}},
    "dub_techno":     {"mode": "spice", "tone": 0.42, "prob": 0.3,
                       "steps": [6, 10, 14], "pitch": [60],
                       "syn": {"decay": 0.1, "drive": 1.0, "crush": 0.4}},
    "minimal_techno": {"mode": "spice", "tone": 0.16, "prob": 0.32,
                       "steps": [6, 14, 10], "pitch": [60],
                       "syn": {"decay": 0.06, "drive": 1.1, "crush": 0.7}},
    # ---- SPICE: rare rhythmic seasoning (default for the rest) ----
    "minneapolis_funk": {"mode": "spice", "tone": 0.6,  "prob": 0.5,
                         "steps": [4, 12, 7], "pitch": [55, 50],
                         "syn": {"decay": 0.12, "drive": 1.1, "crush": 0.3}},
    "electro_funk":  {"mode": "spice", "tone": 0.18, "prob": 0.45,
                      "steps": [6, 14, 11], "pitch": [60],
                      "syn": {"decay": 0.07, "drive": 1.2, "crush": 0.6}},
    "electro":       {"mode": "spice", "tone": 0.1,  "prob": 0.4,
                      "steps": [6, 14], "pitch": [60],
                      "syn": {"decay": 0.06, "drive": 1.3, "crush": 0.75}},
    "detroit_techno": {"mode": "spice", "tone": 0.3, "prob": 0.4,
                       "steps": [6, 14, 10], "pitch": [60],
                       "syn": {"decay": 0.08, "drive": 1.1, "crush": 0.5}},
    "synthwave":     {"mode": "spice", "tone": 0.15, "prob": 0.35,
                      "steps": [14, 6], "pitch": [60],
                      "syn": {"decay": 0.07, "drive": 1.0, "crush": 0.55}},
    "eighties_hiphop": {"mode": "spice", "tone": 0.22, "prob": 0.4,
                        "steps": [10, 14], "pitch": [60],
                        "syn": {"decay": 0.08, "drive": 1.1, "crush": 0.5}},
    "jazz":          {"mode": "spice", "tone": 0.6,  "prob": 0.3,
                      "steps": [10, 6], "pitch": [64, 59],
                      "syn": {"decay": 0.12, "drive": 0.8, "crush": 0.2}},
    "lofi":          {"mode": "spice", "tone": 0.55, "prob": 0.35,
                      "steps": [6, 14], "pitch": [57, 52],
                      "syn": {"decay": 0.13, "drive": 0.9, "crush": 0.4}},
    "rnb":           {"mode": "spice", "tone": 0.65, "prob": 0.35,
                      "steps": [10, 6], "pitch": [55, 50],
                      "syn": {"decay": 0.13, "drive": 0.9, "crush": 0.25}},
    "indie_rnb":     {"mode": "spice", "tone": 0.7,  "prob": 0.28,
                      "steps": [14, 6], "pitch": [52, 57],
                      "syn": {"decay": 0.15, "drive": 0.8, "crush": 0.25}},
    "steppers_dub":  {"mode": "spice", "tone": 0.5,  "prob": 0.32,
                      "steps": [6, 14], "pitch": [55],
                      "syn": {"decay": 0.14, "drive": 1.0, "crush": 0.3}},
    "dub_garage":    {"mode": "spice", "tone": 0.4,  "prob": 0.4,
                      "steps": [6, 14, 10], "pitch": [72],
                      "syn": {"decay": 0.1, "drive": 1.0, "crush": 0.35}},
}
_PERC_DEF = {"mode": "spice", "tone": 0.45, "prob": 0.35, "steps": [6, 14],
             "pitch": [60], "syn": {"decay": 0.1, "drive": 1.0, "crush": 0.4}}

# Per-genre drum CHARACTER. New synthdef hooks: kick `punch` (boom<->snap,
# 0.5 neutral), snare `body`/`buzz` (shell weight / wire-tail, 0.5/0.35
# neutral), hat/ohat `loose` (openness, 0.0 = tight). Only deviations from
# neutral are listed; absent genres/keys keep the synthdef default sound.
_DRUM_CHAR = {
    "funk":             {"kick": {"punch": 0.74}, "snare": {"body": 0.34, "buzz": 0.26}},
    "minneapolis_funk": {"kick": {"punch": 0.64}, "snare": {"body": 0.42, "buzz": 0.28}},
    "electro_funk":     {"kick": {"punch": 0.70}, "snare": {"body": 0.32, "buzz": 0.24}, "hat": {"loose": 0.05}},
    "electro":          {"kick": {"punch": 0.68}, "snare": {"body": 0.30, "buzz": 0.22}, "hat": {"loose": 0.04}},
    "synthwave":        {"kick": {"punch": 0.44}, "snare": {"body": 0.60, "buzz": 0.42}, "hat": {"loose": 0.16}, "ohat": {"loose": 0.20}},
    "broken_house":     {"kick": {"punch": 0.62}, "snare": {"body": 0.40, "buzz": 0.30}, "hat": {"loose": 0.05}},
    "lofi":             {"kick": {"punch": 0.30}, "snare": {"body": 0.60, "buzz": 0.52}, "hat": {"loose": 0.22}, "ohat": {"loose": 0.26}},
    "eighties_hiphop":  {"kick": {"punch": 0.40}, "snare": {"body": 0.55, "buzz": 0.40}, "hat": {"loose": 0.10}},
    "jazz":             {"kick": {"punch": 0.28}, "snare": {"body": 0.70, "buzz": 0.62}, "hat": {"loose": 0.24}, "ohat": {"loose": 0.30}},
    "minimal_techno":   {"kick": {"punch": 0.56}, "snare": {"body": 0.40, "buzz": 0.24}},
    "detroit_techno":   {"kick": {"punch": 0.54}, "snare": {"body": 0.42, "buzz": 0.26}, "hat": {"loose": 0.04}},
    "neon_dub":         {"kick": {"punch": 0.30}, "snare": {"body": 0.56, "buzz": 0.50}, "hat": {"loose": 0.18}, "ohat": {"loose": 0.28}},
    "dub":              {"kick": {"punch": 0.26}, "snare": {"body": 0.58, "buzz": 0.54}, "hat": {"loose": 0.20}, "ohat": {"loose": 0.30}},
    "steppers_dub":     {"kick": {"punch": 0.30}, "snare": {"body": 0.56, "buzz": 0.50}, "hat": {"loose": 0.18}, "ohat": {"loose": 0.28}},
    "dub_techno":       {"kick": {"punch": 0.40}, "snare": {"body": 0.50, "buzz": 0.42}, "hat": {"loose": 0.12}, "ohat": {"loose": 0.22}},
    "roots_reggae":     {"kick": {"punch": 0.30}, "snare": {"body": 0.58, "buzz": 0.50}, "hat": {"loose": 0.18}, "ohat": {"loose": 0.26}},
    "uk_garage":        {"kick": {"punch": 0.64}, "snare": {"body": 0.40, "buzz": 0.30}, "hat": {"loose": 0.05}},
    "dub_garage":       {"kick": {"punch": 0.56}, "snare": {"body": 0.46, "buzz": 0.38}, "hat": {"loose": 0.10}, "ohat": {"loose": 0.18}},
    "rnb":              {"kick": {"punch": 0.42}, "snare": {"body": 0.55, "buzz": 0.40}, "hat": {"loose": 0.12}, "ohat": {"loose": 0.18}},
    "afro_rnb":         {"kick": {"punch": 0.48}, "snare": {"body": 0.50, "buzz": 0.36}, "hat": {"loose": 0.10}},
    "indie_rnb":        {"kick": {"punch": 0.36}, "snare": {"body": 0.58, "buzz": 0.46}, "hat": {"loose": 0.16}, "ohat": {"loose": 0.22}},
}

# Drums-bus glue (\fxdrum): (glue, punch). Punchy styles get more transient
# lift; spacious/soft styles a gentler, lower glue.
_DRUM_GLUE_DEF = (0.25, 0.20)
_DRUM_GLUE = {
    "funk": (0.32, 0.34), "minneapolis_funk": (0.30, 0.30),
    "electro_funk": (0.30, 0.32), "electro": (0.30, 0.30),
    "synthwave": (0.24, 0.16), "broken_house": (0.30, 0.28),
    "lofi": (0.20, 0.12), "eighties_hiphop": (0.26, 0.20),
    "jazz": (0.18, 0.12), "minimal_techno": (0.30, 0.26),
    "detroit_techno": (0.30, 0.26), "neon_dub": (0.20, 0.12),
    "dub": (0.18, 0.10), "steppers_dub": (0.20, 0.12),
    "dub_techno": (0.24, 0.16), "roots_reggae": (0.20, 0.12),
    "uk_garage": (0.32, 0.32), "dub_garage": (0.26, 0.22),
    "rnb": (0.24, 0.18), "afro_rnb": (0.28, 0.24),
    "indie_rnb": (0.22, 0.14),
}

# Per-genre LEAD output level (pure post-gain `level`, 1.0 = unchanged).
# Normalises the perceived lead loudness across genres: the 3 lead synths
# (saw-unison \lead / FM \leadFM / PWM \leadPulse) + each genre's cutoff/
# drive/decay give very different perceived levels for the same velocity.
# This trims output ONLY (not velocity) so tone and the visualizer's
# velocity-driven glyph brightness are unaffected. Tune by ear here.
_LEAD_LEVEL = {
    # leadPulse genres tend bright/loud -> trim
    "electro": 0.80, "uk_garage": 0.85, "minneapolis_funk": 0.86,
    "broken_house": 0.88, "minimal_techno": 0.90, "eighties_hiphop": 0.96,
    # \lead genres
    "funk": 0.95, "electro_funk": 0.95, "synthwave": 0.99, "jazz": 1.30,
    # leadFM genres tend dark/quiet -> lift
    "detroit_techno": 1.00, "afro_rnb": 1.02, "dub_garage": 1.06,
    "dub_techno": 1.10, "neon_dub": 1.12, "steppers_dub": 1.12,
    "lofi": 1.15, "rnb": 0.80, "roots_reggae": 1.20, "dub": 1.22,
    "indie_rnb": 1.22,
}


class CannedSource:
    name = "canned"

    def __init__(self):
        self.bpm = 100
        self.root = 0
        self.genre = "funk"
        self.energy = 0.5
        self.on = {"kick": True, "snare": True, "hat": True, "bass": True, "lead": True}
        self.bar = 0
        self.motif = []

    def prime(self, section: dict) -> None:
        self.bpm = float(section.get("tempo") or section.get("bpm") or 100)
        self.root = _key_pc(section.get("key", "C minor"))
        g = str(section.get("genre", "")).lower()
        self.genre = g if g in GENRES else "funk"
        instr = section.get("instruments") or {}
        for k in self.on:
            v = instr.get(k)
            self.on[k] = True if v is None else bool(
                v.get("enabled", True) if isinstance(v, dict) else v)
        d = section.get("density")
        r = random.random()
        if r < 0.15:
            self.energy = random.uniform(0.78, 0.95)
        elif r < 0.45:
            self.energy = random.uniform(0.5, 0.68)
        else:
            self.energy = random.uniform(0.3, 0.48)
        if isinstance(d, (int, float)):
            self.energy = max(0.22, min(0.95, 0.6 * self.energy + 0.4 * float(d)))
        # per-section lead motif: pick a curated rhythmic figure for the
        # genre's feel (intentional syncopation/space), stable across the
        # section so the phrase recurs and is recognisable.
        feel = _LEAD_FEEL.get(self.genre, "lyric")
        variants = _LEAD_RHYTHM.get(feel, _LEAD_RHYTHM["lyric"])
        rr = random.Random(int(self.root * 7 + len(self.genre)))
        self.motif = list(rr.choice(variants))
        self.bar = 0

    def synth_params(self) -> dict:
        # copy (do not mutate the module table) + inject the genre's perc2
        # character so the percussion synth is tuned per genre
        sp = dict(SYNTH_PARAMS.get(self.genre, SYNTH_PARAMS["funk"]))
        pf = _PERC.get(self.genre, _PERC_DEF)
        syn = dict(pf.get("syn", _PERC_DEF["syn"]))
        syn["tone"] = float(pf.get("tone", _PERC_DEF["tone"]))
        sp["perc2"] = syn
        # per-genre drum character — copy inner dicts so the module
        # SYNTH_PARAMS table is never mutated
        for role, extra in _DRUM_CHAR.get(self.genre, {}).items():
            merged = dict(sp.get(role, {}))
            merged.update(extra)
            sp[role] = merged
        # per-genre lead loudness normalisation (output-only trim)
        lv = _LEAD_LEVEL.get(self.genre)
        if lv is not None:
            ld = dict(sp.get("lead", {}))
            ld["level"] = lv
            sp["lead"] = ld
        return sp

    def instrument_map(self) -> dict:
        # per-genre instrument variants (roles omitted use the default def)
        return _GENRE_INSTR.get(self.genre, {})

    def fx_params(self) -> dict:
        """Per-track (drums / bass / lead+keys) FX, derived from the genre's
        base fx with role character + a few per-genre signatures. Drums tight,
        bass driest, melodic wettest — and e.g. dub/techno get huge lead delay.
        """
        base = SYNTH_PARAMS.get(self.genre, SYNTH_PARAMS["funk"]).get(
            "fx", {"reverb": 0.3, "delay": 0.2, "delayTime": 0.375, "width": 0.6})
        b = lambda k, d=0.0: float(base.get(k, d))
        out = {
            "fxDrums": {"reverb": b("reverb") * 0.30, "delay": b("delay") * 0.22,
                        "delayTime": b("delayTime") * 0.5, "width": b("width") * 0.8},
            "fxBass": {"reverb": b("reverb") * 0.12, "delay": b("delay") * 0.08,
                       "delayTime": b("delayTime"), "width": b("width") * 0.5},
            "fxMel": {"reverb": b("reverb") * 1.05, "delay": b("delay") * 1.1,
                      "delayTime": b("delayTime"), "width": b("width")},
            "fxPerc": {"reverb": b("reverb") * 0.55, "delay": b("delay") * 0.5,
                       "delayTime": b("delayTime"), "width": b("width") * 0.9},
        }
        gl, pu = _DRUM_GLUE.get(self.genre, _DRUM_GLUE_DEF)
        out["fxDrums"]["glue"] = gl
        out["fxDrums"]["punch"] = pu
        ov = _FX_SIG.get(self.genre)
        if ov:
            for bus, d in ov.items():
                out.setdefault(bus, {}).update(d)
        return out

    # ---- harmony ----
    def _scale(self):
        return PROFILE.get(self.genre, PROFILE["funk"])[0]

    def _chord(self, prog_idx, octave):
        """Return (root_midi, [chord tone midis]) for progression slot.
        Adds a secondary-dominant turnaround on the last bar (harmonic
        motion, no extra notes) — keeps the music interesting, not denser.
        """
        prog = PROFILE.get(self.genre, PROFILE["funk"])[1]
        sc = self._scale()
        if prog_idx % 4 == 3:
            rr = random.Random(prog_idx * 131 + self.root + len(self.genre))
            if rr.random() < 0.55:
                ndeg, _q = prog[(prog_idx + 1) % len(prog)]
                nroot_pc = (self.root + sc[ndeg % len(sc)]) % 12
                base = 12 * octave + ((nroot_pc + 7) % 12)     # V7 of next
                q = "dom7b9" if rr.random() < 0.5 else "dom9"
                return base, [base + iv for iv in CHORD[q]]
        deg, qual = prog[prog_idx % len(prog)]
        croot_pc = (self.root + sc[deg % len(sc)]) % 12
        base = 12 * octave + croot_pc
        tones = [base + iv for iv in CHORD.get(qual, CHORD["min7"])]
        return base, tones

    # ---- velocity tiers ----
    def _acc(self, r): return r.uniform(0.88, 1.0)
    def _main(self, r): return r.uniform(0.66, 0.82)
    def _ghost(self, r): return r.uniform(0.18, 0.36)

    def next_phrase(self) -> Phrase:
        try:
            return self._build()
        except Exception as e:
            beat = 60.0 / max(50.0, self.bpm)
            print(f"[canned] {self.genre} error: {e}")
            return Phrase(notes=[], length=4 * beat)

    def _build(self) -> Phrase:
        b = self.bar
        rnd = random.Random(b * 8419 + hash(self.genre) % 9973)
        beat = 60.0 / max(50.0, min(180.0, self.bpm))
        s16 = 0.25 * beat
        bar_len = 4 * beat
        sc, prog, swing, sdrag, kpush, hjit, chaos, cap = PROFILE.get(
            self.genre, PROFILE["funk"])
        ph = b % 8
        fill = ph == 7
        sparse = ph in (4, 5, 6)
        e = self.energy * (0.6 if sparse else 1.0)
        croot, ctones = self._chord(b, 2)
        nroot, _ = self._chord(b + 1, 2)

        def t(step, voice):
            base = step * s16 + (swing * s16 if step % 2 else 0.0)
            off = (sdrag if voice == "snare" else
                   kpush if voice == "kick" else
                   rnd.uniform(-hjit, hjit) if voice == "hat" else 0.0)
            if chaos:
                off += rnd.uniform(-chaos, chaos)
            return max(0.0, base + off)

        core, orn = [], []
        def D(st, du, pi, ve, ch, vo="", structural=False):
            (core if structural else orn).append(Note(t(st, vo), du, pi, ve, ch))

        getattr(self, f"_g_{self.genre}")(D, rnd, beat, sc, ctones, croot,
                                          nroot, e, fill, sparse)

        # soft sustained harmonic pad on the keys voice (energy-gated, not on
        # the spikier genres) — body without density, keeps the space.
        if self.on["lead"] and self.genre not in ("neon_dub", "electro"):
            self._pad(D, rnd, beat, ctones)

        # dedicated percussion layer (per-genre: none / rare spice / lots)
        self._perc(D, rnd, beat, e)

        # cap ONLY ornaments — the kick/snare backbone & bass "one" are core
        if len(orn) > max(0, cap - len(core)):
            orn.sort(key=lambda n: n.vel, reverse=True)
            orn = orn[:max(0, cap - len(core))]
        N = core + orn
        for n in N:
            n.t = max(0.0, n.t)
            n.vel = max(0.05, min(1.0, n.vel))
            n.pitch = max(0, min(127, int(n.pitch)))
        N.sort(key=lambda n: n.t)
        self.bar += 1
        return Phrase(notes=N, length=bar_len)

    # ---- shared layers ----
    def _hats(self, D, rnd, e, accents):
        for s in range(16):
            if s in (6, 14):
                continue
            p = 0.9 if s % 2 == 0 else 0.55 + 0.4 * e
            if rnd.random() < p:
                v = self._main(rnd) if s in accents else self._ghost(rnd) + (0.12 if s % 4 == 0 else 0)
                D(s, 0.04, HAT, v * 0.9, CH_DRUMS, "hat")
        for s in (6, 14):
            if rnd.random() < 0.6 + 0.3 * e:
                D(s, 0.16, OHAT, self._main(rnd) * 0.8, CH_DRUMS, "hat")

    def _ghost_sn(self, D, rnd, e):
        for s in (7, 9, 11, 13, 3):
            if rnd.random() < 0.2 + 0.5 * e:
                D(s, 0.05, SNARE, self._ghost(rnd), CH_DRUMS, "snare")

    def _backbeat(self, D, rnd, clap=True):
        for s in (4, 12):
            D(s, 0.18, SNARE, self._acc(rnd), CH_DRUMS, "snare", structural=True)
            if clap and rnd.random() < 0.6:
                D(s, 0.2, CLAP, 0.72, CH_DRUMS, "snare")

    def _funk_bass(self, D, rnd, beat, ctones, croot, nroot, e, steps):
        D(0, beat * 0.18, croot, self._acc(rnd), CH_BASS, "kick", structural=True)
        fifth = croot + 7
        for s in steps:
            if rnd.random() < 0.4 + 0.5 * e:
                if rnd.random() < 0.15:
                    D(s, beat * 0.1, croot, self._ghost(rnd), CH_BASS)  # dead
                else:
                    p = rnd.choice([croot, croot, croot + 12, fifth,
                                    rnd.choice(ctones)])
                    D(s, beat * rnd.choice([0.14, 0.18, 0.22]), p,
                      self._main(rnd), CH_BASS)
        # chromatic/diatonic approach into next chord's root
        if rnd.random() < 0.55 + 0.3 * e:
            ap = nroot - 1 if rnd.random() < 0.5 else nroot + 1
            D(15, beat * 0.16, ap, self._main(rnd) * 0.8, CH_BASS)

    def _walk_bass(self, D, rnd, beat, ctones, croot, nroot):
        # jazz: quarter-note walk root-3-5-approach toward next root
        line = [croot, ctones[1] if len(ctones) > 1 else croot + 3,
                ctones[2] if len(ctones) > 2 else croot + 7,
                (nroot - 1) if rnd.random() < 0.5 else (nroot + 1)]
        for i, p in enumerate(line):
            D(i * 4, beat * 0.9, p, self._main(rnd) + (0.12 if i == 0 else 0),
              CH_BASS, "kick" if i == 0 else "", structural=(i == 0))

    def _voicelead(self, tones, center=60):
        # move each chord tone to the octave nearest the previous voicing's
        # centre -> smooth, minimal-movement chord changes (better chords).
        c = getattr(self, "_vlc", center)
        out = []
        for p in tones:
            pc = p % 12
            best = pc + 12 * round((c - pc) / 12)
            out.append(int(best))
        out = sorted(set(out))
        self._vlc = sum(out) / len(out) if out else c
        return out

    def _comp(self, D, rnd, beat, ctones, steps, oct_shift=12):
        # voice-led top voicing on the KEYS voice (smooth chord motion, no
        # crowding the lead). Same hit count = harmony, not density.
        vc = self._voicelead(ctones, 48 + oct_shift)   # an octave lower
        if len(ctones) >= 4 and rnd.random() < 0.6:
            vc = vc + [vc[0] + 12]                       # colour tone on top
        for s in steps:
            if rnd.random() < 0.45 + 0.3 * self.energy:
                for p in vc:
                    D(s, beat * 0.26, p, 0.50 + rnd.uniform(-0.04, 0.07), CH_KEYS)

    def _pad(self, D, rnd, beat, ctones):
        # ONE soft sustained voice-led chord under the bar (keys self-
        # terminates). Harmonic body without notes-per-beat — keeps the space.
        if rnd.random() < 0.45 + 0.35 * self.energy:
            for p in self._voicelead(ctones[:4], 52):       # octave lower
                D(0, beat * 3.4, p, 0.37 + rnd.uniform(-0.03, 0.05), CH_KEYS)

    def _perc(self, D, rnd, beat, e):
        # Dedicated percussion layer, dropped into the groove's GAPS (its
        # steps are off-beats, chosen per genre vs the kick/snare pattern).
        # none -> nothing; spice -> rare seasoning (whole bars often skipped);
        # lots -> a real, characterful part.
        pf = _PERC.get(self.genre, _PERC_DEF)
        mode = pf.get("mode", "spice")
        if mode == "none":
            return
        steps = pf.get("steps", _PERC_DEF["steps"])
        pitches = pf.get("pitch", [60])
        if mode == "lots":
            if rnd.random() < 0.30:              # SPICE: it comes & goes
                return
            base_p = (0.50 + 0.20 * e) * pf.get("prob", 1.0)
            vlo, vhi = 0.32, 0.48
        else:                                    # spice: seasoning, not a part
            if rnd.random() > 0.5:               # skip whole bars often
                return
            base_p = (0.10 + 0.14 * e) * pf.get("prob", 1.0)
            vlo, vhi = 0.22, 0.34
        # per-hit variation -> creative, never two identical hits
        hits = 0
        for idx, s in enumerate(steps):
            if rnd.random() < base_p:
                D(s, beat * 0.12, pitches[idx % len(pitches)]
                  + rnd.choice([0, 0, 0, 12, -12, 7]),
                  rnd.uniform(vlo, vhi), CH_PERC, "perc")
                hits += 1
        if mode == "lots" and hits == 0 and steps:   # when it plays, >=1 hit
            idx = rnd.randrange(len(steps))
            D(steps[idx], beat * 0.12, pitches[idx % len(pitches)],
              rnd.uniform(vlo, vhi), CH_PERC, "perc")
        # occasional FAST roll/flourish — finer than 16ths (32nd = 0.5 step,
        # 64th = 0.25 step), as a crescendo fill into the bar end. Rare; the
        # steady spice above is left exactly as is.
        roll_p = (0.16 if mode == "lots" else 0.05) * (0.7 + e)
        if steps and rnd.random() < roll_p:
            sub = rnd.choice([0.5, 0.25, 0.25])       # 32nd or 64th roll
            n = rnd.choice([4, 5, 6, 8])
            start = max(9.0, 15.5 - ((n - 1) * sub))  # land at the bar end
            base = pitches[rnd.randrange(len(pitches))]
            for k in range(n):
                v = vlo + (vhi - vlo) * (k / max(1, n - 1)) * 0.9
                D(start + (k * sub), beat * 0.07,
                  base + rnd.choice([0, 0, 12, 7]),
                  min(0.6, v), CH_PERC, "perc")

    def _jazz_motif(self, D, rnd, beat, sc, ctones):
        # Jazz lead = a flowing bebop-ish line: CHORD tones on the strong
        # beats (so it outlines the ii-V-I changes) connected by SCALE
        # passing tones (Dorian) on the weak beats, with the occasional
        # enclosure approach. Legato (the jazz lead decay carries the
        # sustain) and soft/intimate, swung via the timing grid.
        cN = len(ctones)
        root = self.root
        scl = sorted({d % 12 for d in sc}) or [0, 2, 3, 5, 7, 9, 10]
        c0 = ctones[0] + 24                          # lead register (horn/vibe)
        ladder, o = [], (c0 // 12) - 2
        while (o * 12) + root <= c0 + 18:
            for d in scl:
                p = (o * 12) + root + d
                if (c0 - 7) <= p <= (c0 + 17):
                    ladder.append(p)
            o += 1
        ladder = sorted(set(ladder))
        if not ladder:
            return
        ct_oct = [c + 24 for c in ctones]
        near = lambda tgt: min(range(len(ladder)),
                               key=lambda k: abs(ladder[k] - tgt))
        seed = random.Random(root * 13 + (self.bar // 2) + 7)
        sct = seed.choice((0, 1, 2)) % cN
        pi = near(ct_oct[sct])
        for j, (ti, s, du) in enumerate(self.motif):
            strong = (s % 4) == 0
            if strong:
                pi = near(ct_oct[(sct + (j // 2)) % cN])    # land on a chord tone
            else:
                goal = near(ct_oct[(sct + (j // 2) + 1) % cN])
                pi = max(0, min(len(ladder) - 1,
                                pi + (1 if goal >= pi else -1)))  # scale step
            pit = ladder[pi]
            vel = 0.40 + (0.06 if strong else 0.0) + rnd.uniform(-0.03, 0.05)
            vel = max(0.22, min(0.80, vel))
            if strong and j > 0 and rnd.random() < 0.30:    # enclosure approach
                D(max(0.0, s - 0.5), beat * 0.12,
                  ladder[max(0, pi - 1)], vel * 0.65, CH_LEAD)
            D(s, beat * 0.30 * du, pit, vel, CH_LEAD)        # legato
            if rnd.random() < 0.16:                          # sparse 3rd below
                D(s, beat * 0.30 * du, pit - rnd.choice([3, 4]),
                  vel * 0.55, CH_LEAD)

    def _motif(self, D, rnd, beat, sc, ctones):
        # A "played" lead: the curated per-genre RHYTHMIC motif (self.motif —
        # intentional syncopation/space) carries a fixed per-section CONTOUR
        # over the CURRENT bar's CHORD TONES (always follows the changes), as
        # a 2-bar statement -> answer (the answer resolves to the root), with
        # a velocity arc toward the phrase peak and at most ONE diatonic
        # approach note into a strong beat. The phrase plays as written (no
        # random note-dropping) so it reads as a melody, not noise. Sparse.
        if not ctones or not self.motif:
            return
        if self.genre == "jazz":
            self._jazz_motif(D, rnd, beat, sc, ctones)
            return
        st = _LEAD_STYLE.get(self.genre, _LEAD_DEF)
        cN = len(ctones)
        cseed = random.Random(self.root * 17 + len(self.genre) * 5 + 3)
        shape = _CONTOURS[cseed.randrange(len(_CONTOURS))]
        base = cseed.choice((0, 0, 1, 2))
        nN = len(self.motif)
        answer = (self.bar % 2) == 1
        rot = 1 if answer else 0                    # answer = varied consequent
        degs = [(base + shape[(i + rot) % len(shape)]) % cN for i in range(nN)]
        peak = max(range(nN), key=lambda i: degs[i])
        scset = {(self.root + d) % 12 for d in sc}
        prev = None
        for i, (ti, s, du) in enumerate(self.motif):
            deg = degs[i]
            if answer and i == nN - 1:
                deg = 0                                # answer -> root
            elif answer and i == nN - 2 and cN > 1:
                deg = 1                                # ...approached via 3rd
            pit = ctones[deg] + 12
            if i == peak and not answer:
                pit += 12                          # melodic apex an octave up
            d2p = 1.0 - abs(i - peak) / max(1, nN - 1)
            vel = (0.42 + 0.20 * d2p + (0.05 if s % 4 == 0 else 0.0)
                   + rnd.uniform(-0.03, 0.04))
            if answer and i >= nN - 2:
                vel -= 0.06                            # softer resolution
            vel = max(0.20, min(0.86, vel))
            if (prev is not None and s in (0, 4, 8, 12)
                    and rnd.random() < 0.18 * st["notes"]):
                ap = pit - 1                           # one diatonic approach
                if (ap % 12) not in scset:
                    ap -= 1
                D(max(0.0, s - 0.5), beat * 0.09, ap, vel * 0.7, CH_LEAD)
            D(s, beat * 0.14 * du, pit, vel, CH_LEAD)  # short gate -> tight
            if rnd.random() < st["harm"] * 0.3:        # sparse soft harmony
                D(s, beat * 0.14 * du, pit - rnd.choice([3, 4, 7]),
                  vel * 0.6, CH_LEAD)
            prev = pit

    # ---- genre builders (drums = funk research; harmony via helpers) ----
    def _g_funk(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.2, KICK, self._acc(rnd), CH_DRUMS, "kick", structural=True)
            for s in (6, 7, 10, 14):
                if rnd.random() < 0.4 + 0.4 * e:
                    D(s, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            self._backbeat(D, rnd); self._ghost_sn(D, rnd, e)
            if fill:
                for s in (10, 12, 13, 14, 15):
                    D(s, 0.06, SNARE, 0.55 + 0.05 * s, CH_DRUMS, "snare")
        if self.on["hat"]:
            self._hats(D, rnd, e, (0, 4, 8, 12))
        if self.on["bass"]:
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [3, 6, 7, 10, 11, 14])
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)
            if rnd.random() < 0.3:
                self._comp(D, rnd, beat, ct, [6, 14])

    def _g_jazz(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["hat"]:
            for s in (0, 4, 6, 8, 12, 14):                 # swung jazz ride
                D(s, 0.5, RIDE,
                  self._main(rnd) if s in (4, 12) else self._ghost(rnd) + 0.2,
                  CH_DRUMS, "hat")
            if rnd.random() < 0.3:                          # occasional bell
                D(rnd.choice([6, 14]), 0.4, RIDE, self._main(rnd), CH_DRUMS, "hat")
            if rnd.random() < 0.35:
                D(10, 0.18, OHAT, 0.4, CH_DRUMS, "hat")
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.1, RIM, self._main(rnd), CH_DRUMS, "snare", True)
            self._ghost_sn(D, rnd, e * 0.7)
        if self.on["kick"]:
            D(0, 0.16, KICK, self._main(rnd) * 0.7, CH_DRUMS, "kick", True)
            if rnd.random() < 0.4:
                D(rnd.choice([6, 10, 14]), 0.14, KICK, self._ghost(rnd) + 0.2, CH_DRUMS, "kick")
        if self.on["bass"]:
            self._walk_bass(D, rnd, beat, ct, cr, nr)
        if self.on["lead"]:
            self._comp(D, rnd, beat, ct, [2, 7, 11], oct_shift=0)
            self._motif(D, rnd, beat, sc, ct)

    def _g_minneapolis_funk(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            for s in (0, 10):
                D(s, 0.2, KICK, self._acc(rnd) if s == 0 else self._main(rnd), CH_DRUMS, "kick", True)
            if rnd.random() < 0.4 + 0.4 * e:
                D(6, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):                                # big gated snare
                D(s, 0.22, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            self._ghost_sn(D, rnd, e * 0.6)
        if self.on["hat"]:
            self._hats(D, rnd, e, (0, 4, 8, 12))
        if self.on["bass"]:                                  # syncopated synth-bass
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [2, 3, 6, 10, 11, 14])
        if self.on["lead"]:
            self._comp(D, rnd, beat, ct, [2, 6, 10, 14])     # stabby synth chords
            if rnd.random() < 0.5:
                self._motif(D, rnd, beat, sc, ct)

    def _g_minimal_techno(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # hypnotic + sparse: steady 4-on-floor, off-beat hats, almost no melody
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.22, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["hat"]:
            for s in (2, 6, 10, 14):                          # off-beat ticks
                D(s, 0.035, HAT, self._main(rnd) * 0.7, CH_DRUMS, "hat")
            if rnd.random() < 0.4:
                D(rnd.choice([6, 14]), 0.12, OHAT, 0.4, CH_DRUMS, "hat")
            if rnd.random() < 0.3 + 0.3 * e:                  # rare ghost 16th
                D(rnd.choice([3, 7, 11, 15]), 0.03, HAT, self._ghost(rnd), CH_DRUMS, "hat")
        if self.on["snare"] and rnd.random() < 0.35:           # sparse rim/clap
            D(rnd.choice([4, 12]), 0.05, RIM, self._main(rnd) * 0.7, CH_DRUMS)
        if self.on["bass"]:                                    # deep, very spaced
            D(0, beat * 0.4, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            for s in (6, 10, 14):
                if rnd.random() < 0.3 + 0.35 * e:
                    D(s, beat * 0.35, cr if rnd.random() < 0.7 else cr + 12,
                      self._main(rnd), CH_BASS)
        if self.on["lead"]:
            if rnd.random() < 0.45:                            # faint pad only
                self._pad(D, rnd, beat, ct)
            if rnd.random() < 0.18 + 0.2 * e:                  # very rare blip
                D(rnd.choice([6, 11]), beat * 0.16,
                  ct[rnd.choice([0, 1, len(ct) - 1])] + 12, 0.4, CH_LEAD)

    def _g_detroit_techno(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # soulful/futurist: driving 4/4, lush stab chords + pad, rolling bass
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.22, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.18, CLAP, 0.7, CH_DRUMS, "snare", True)
            self._ghost_sn(D, rnd, e * 0.5)
        if self.on["hat"]:
            for s in range(16):
                if s % 2 == 1:
                    D(s, 0.04, HAT, self._main(rnd) if s % 4 == 1 else self._ghost(rnd) + 0.1, CH_DRUMS, "hat")
            for s in (6, 14):
                D(s, 0.18, OHAT, 0.5, CH_DRUMS, "hat")
        if self.on["bass"]:                                    # rolling octave bass
            root = cr
            for i in range(8):
                if i % 2 == 0 or rnd.random() < 0.5 + 0.3 * e:
                    D(i * 2, beat * 0.4, root + (12 if i % 4 == 3 else 0),
                      self._acc(rnd) if i == 0 else self._main(rnd), CH_BASS,
                      "kick", structural=(i == 0))
        if self.on["lead"]:                                    # the Detroit stabs
            self._comp(D, rnd, beat, ct, [3, 6, 10, 14], oct_shift=0)
            self._pad(D, rnd, beat, ct)
            if rnd.random() < 0.4:
                self._motif(D, rnd, beat, sc, ct)

    def _skank(self, D, rnd, beat, ct, steps, prob=0.7):
        # off-beat reggae/dub organ chord skank on the KEYS voice
        for s in steps:
            if rnd.random() < prob:
                for p in self._voicelead(ct[:3], 48):       # octave lower
                    D(s, beat * 0.18, p, 0.48 + rnd.uniform(-0.04, 0.05), CH_KEYS)

    def _g_dub(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # one-drop: the weight is on beat 3 (step 8); huge space + dub delay
        if self.on["kick"]:
            D(8, 0.3, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            if rnd.random() < 0.3:
                D(0, 0.26, KICK, self._main(rnd) * 0.7, CH_DRUMS, "kick")
        if self.on["snare"]:
            D(8, 0.16, RIM, self._acc(rnd), CH_DRUMS, "snare", True)  # cross-stick
            if rnd.random() < 0.3:
                D(rnd.choice([11, 14]), 0.05, RIM, self._ghost(rnd), CH_DRUMS)
        if self.on["hat"]:
            for s in (2, 6, 10, 14):
                if rnd.random() < 0.6:
                    D(s, 0.05, HAT, self._main(rnd) * 0.6, CH_DRUMS, "hat")
            if rnd.random() < 0.5:
                D(rnd.choice([6, 14]), 0.22, OHAT, 0.4, CH_DRUMS, "hat")
        if self.on["bass"]:                                       # deep, melodic, vast
            D(0, beat * 1.4, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            if rnd.random() < 0.5 + 0.3 * e:
                D(10, beat * 0.7, cr + rnd.choice([0, 3, 7, -5]),
                  self._main(rnd), CH_BASS)
        if self.on["lead"]:
            self._skank(D, rnd, beat, ct, [2, 6, 10, 14], 0.5)
            if rnd.random() < 0.4:
                self._pad(D, rnd, beat, ct)

    def _g_steppers_dub(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # "steppers": four-to-the-floor militant kick, still deeply dub
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.28, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["snare"]:
            D(8, 0.16, RIM, self._acc(rnd), CH_DRUMS, "snare", True)
            if rnd.random() < 0.4:
                D(12, 0.18, SNARE, self._main(rnd), CH_DRUMS, "snare")
        if self.on["hat"]:
            for s in (2, 6, 10, 14):
                D(s, 0.05, HAT, self._main(rnd) * 0.6, CH_DRUMS, "hat")
            if rnd.random() < 0.5:
                D(14, 0.22, OHAT, 0.42, CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 1.5, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            if rnd.random() < 0.5 + 0.3 * e:
                D(11, beat * 0.6, cr + rnd.choice([0, 7, 12]), self._main(rnd), CH_BASS)
        if self.on["lead"]:
            self._skank(D, rnd, beat, ct, [2, 6, 10, 14], 0.55)
            if rnd.random() < 0.4:
                self._pad(D, rnd, beat, ct)

    def _g_dub_techno(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # Basic-Channel hypnosis: tight 4/4, vast delayed chord, deep sub
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.22, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["snare"] and rnd.random() < 0.3:
            D(rnd.choice([4, 12]), 0.05, RIM, self._main(rnd) * 0.6, CH_DRUMS)
        if self.on["hat"]:
            for s in (2, 6, 10, 14):
                D(s, 0.035, HAT, self._main(rnd) * 0.55, CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 1.6, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            if rnd.random() < 0.35 + 0.3 * e:
                D(10, beat * 0.6, cr, self._main(rnd) * 0.8, CH_BASS)
        if self.on["lead"]:                                       # the dub chord
            for s in ([6] if rnd.random() < 0.6 else [10]):
                for p in self._voicelead(ct[:4], 48):       # octave lower
                    D(s, beat * 0.4, p, 0.43 + rnd.uniform(-0.03, 0.05), CH_KEYS)
            if rnd.random() < 0.5:
                self._pad(D, rnd, beat, ct)

    def _g_roots_reggae(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # classic one-drop + bubbling skank + prominent melodic bass
        if self.on["kick"]:
            D(8, 0.26, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            D(8, 0.2, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
        if self.on["hat"]:
            for s in (2, 6, 10, 14):
                D(s, 0.05, HAT, self._main(rnd) * 0.6, CH_DRUMS, "hat")
        if self.on["bass"]:                                       # reggae bass sings
            D(0, beat * 0.7, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            for s in (4, 8, 11):
                if rnd.random() < 0.55 + 0.3 * e:
                    D(s, beat * 0.55, cr + rnd.choice([0, 3, 5, 7, -5]),
                      self._main(rnd), CH_BASS)
        if self.on["lead"]:                                       # bubble organ
            self._skank(D, rnd, beat, ct, [2, 6, 10, 14], 0.8)

    def _g_uk_garage(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # CLASSIC 2-STEP, transcribed from the reference clip (deterministic
        # 2-bar loop; the synthdefs add the per-hit life). Per bar, 16ths:
        #   kick   : 1 and the "& of 3"            (steps 0, 10)
        #   snare  : 909 backbeat on 2 & 4         (steps 4, 12)
        #   606    : RIM ghosts a-of-2 / e-of-3    (steps 7, 9)
        #   open   : every offbeat "&"             (steps 2, 6, 10, 14)
        #   closed : the beat + its "e"            (steps 0,1,4,5,8,9,12,13)
        #   bar 2  : adds a RIM turnaround fill     (steps 14, 15)
        if self.on["kick"]:
            D(0,  0.2,  KICK, self._acc(rnd),  CH_DRUMS, "kick", True)     # the "one"
            D(10, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)     # & of 3
        if self.on["snare"]:
            for s in (4, 12):                                              # 909 backbeat
                D(s, 0.18, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            for s in (7, 9):                                               # 606 ghosts
                D(s, 0.06, RIM, self._ghost(rnd) + 0.12, CH_DRUMS, "snare")
            if self.bar % 2 == 1:                                          # 2-bar end fill
                for s in (14, 15):
                    D(s, 0.05, RIM, self._ghost(rnd) + 0.14, CH_DRUMS, "snare")
        if self.on["hat"]:
            for s in (0, 4, 8, 12):                                        # closed: the beat
                D(s, 0.035, HAT, self._main(rnd) * 0.7, CH_DRUMS, "hat")
            for s in (1, 5, 9, 13):                                        # closed: the "e"
                D(s, 0.03, HAT, self._ghost(rnd) + 0.08, CH_DRUMS, "hat")
            for s in (2, 6, 10, 14):                                       # open: every offbeat
                D(s, 0.14, OHAT, self._main(rnd) * 0.8, CH_DRUMS, "hat")
        if self.on["bass"]:                                                # syncopated garage sub
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [3, 6, 10, 11, 14, 15])
        if self.on["lead"]:
            self._comp(D, rnd, beat, ct, [3, 6, 10, 14])
            if rnd.random() < 0.35:
                self._motif(D, rnd, beat, sc, ct)

    def _g_dub_garage(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # 2-step skeleton, sparser + dubwise (huge delay via _FX_SIG)
        if self.on["kick"]:
            D(0, 0.22, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            if rnd.random() < 0.5 + 0.3 * e:
                D(10, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.18, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            if rnd.random() < 0.4:
                D(rnd.choice([7, 14]), 0.05, RIM, self._ghost(rnd), CH_DRUMS)
        if self.on["hat"]:
            for s in (2, 6, 10, 14):
                D(s, 0.045, HAT, self._main(rnd) * 0.6, CH_DRUMS, "hat")
            if rnd.random() < 0.5:
                D(6, 0.22, OHAT, 0.42, CH_DRUMS, "hat")
        if self.on["bass"]:
            self._funk_bass(D, rnd, beat, ct, cr, nr, e * 0.8, [3, 6, 10, 14])
        if self.on["lead"]:
            self._skank(D, rnd, beat, ct, [6, 14], 0.6)
            if rnd.random() < 0.4:
                self._pad(D, rnd, beat, ct)

    def _g_rnb(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # neo-soul: a LOCKED boom-bap pocket. Kick 1 + "&" of 2, snare hard on
        # 2 & 4, steady swung 16th hats (consistent pulse), Rhodes comp + pad.
        if self.on["kick"]:
            D(0, 0.24, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            D(7, 0.22, KICK, self._main(rnd), CH_DRUMS, "kick", True)   # & of 2
            if rnd.random() < 0.4:
                D(10, 0.2, KICK, self._main(rnd) * 0.8, CH_DRUMS, "kick")
        if self.on["snare"]:
            D(4, 0.2, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            D(12, 0.2, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            self._ghost_sn(D, rnd, e * 0.6)
        if self.on["hat"]:                                    # steady pulse
            for s in range(16):
                D(s, 0.045, HAT,
                  (self._main(rnd) * 0.7 if s % 4 == 0 else self._ghost(rnd) + 0.06),
                  CH_DRUMS, "hat")
            D(6, 0.16, OHAT, 0.36, CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 0.7, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            D(7, beat * 0.5, cr, self._main(rnd), CH_BASS)
            if rnd.random() < 0.5:
                D(11, beat * 0.45, cr + rnd.choice([3, 5, 7]), self._main(rnd), CH_BASS)
        if self.on["lead"]:
            self._comp(D, rnd, beat, ct, [2, 10], oct_shift=0)
            self._pad(D, rnd, beat, ct)
            if rnd.random() < 0.35:
                self._motif(D, rnd, beat, sc, ct)

    def _g_afro_rnb(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # afrobeats: a FIXED 3-3-2-ish kick (0, 3, 6, 10), clap on 2 & 4,
        # steady shaker 16ths, fixed log-drum perc — locked groove.
        if self.on["kick"]:
            for s in (0, 3, 6, 10):
                D(s, 0.2, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.18, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
                D(s, 0.18, CLAP, 0.6, CH_DRUMS, "snare")
            self._ghost_sn(D, rnd, e * 0.4)
        if self.on["hat"]:                                    # steady shaker
            for s in range(16):
                D(s, 0.03, HAT,
                  self._main(rnd) * 0.55 if s % 2 == 0 else self._ghost(rnd) + 0.05,
                  CH_DRUMS, "hat")
            for s in (7, 14):                                  # fixed log-drum
                D(s, 0.1, PERC, self._main(rnd) * 0.8, CH_DRUMS)
        if self.on["bass"]:                                   # lock to the kick
            for s in (0, 6, 10):
                D(s, beat * 0.34, cr + (12 if s == 10 else 0),
                  self._acc(rnd) if s == 0 else self._main(rnd), CH_BASS,
                  "kick", structural=(s == 0))
        if self.on["lead"]:
            self._comp(D, rnd, beat, ct, [2, 11])
            if rnd.random() < 0.5:
                self._motif(D, rnd, beat, sc, ct)

    def _g_indie_rnb(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # alt/indie R&B: slow, sparse but LOCKED. Kick 1 + "&" of 3, snare on
        # 2 & 4, soft steady off-beat hats, deep bass on the one. Dreamy.
        if self.on["kick"]:
            D(0, 0.28, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            D(10, 0.24, KICK, self._main(rnd) * 0.85, CH_DRUMS, "kick", True)
        if self.on["snare"]:
            D(4, 0.2, SNARE, self._main(rnd), CH_DRUMS, "snare", True)
            D(12, 0.2, SNARE, self._main(rnd), CH_DRUMS, "snare", True)
            if rnd.random() < 0.3:
                D(7, 0.05, RIM, self._ghost(rnd), CH_DRUMS)
        if self.on["hat"]:                                    # steady off-beats
            for s in (2, 6, 10, 14):
                D(s, 0.05, HAT, self._ghost(rnd) + 0.08, CH_DRUMS, "hat")
            if rnd.random() < 0.4:
                D(6, 0.2, OHAT, 0.32, CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 1.4, cr, self._main(rnd), CH_BASS, "kick", structural=True)
            if rnd.random() < 0.5:
                D(10, beat * 0.6, cr + rnd.choice([0, 3, 7]),
                  self._ghost(rnd) + 0.25, CH_BASS)
        if self.on["lead"]:                                    # hazy chords + pad
            self._comp(D, rnd, beat, ct, [6], oct_shift=0)
            self._pad(D, rnd, beat, ct)

    def _g_electro_funk(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.2, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            for s in (6, 7, 10, 11, 14):
                if rnd.random() < 0.35 + 0.45 * e:
                    D(s, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            self._backbeat(D, rnd); self._ghost_sn(D, rnd, e)
        if self.on["hat"]:
            self._hats(D, rnd, e, (0, 4, 8, 12))
        if self.on["bass"]:
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [3, 6, 7, 10, 11, 14])
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)

    def _g_broken_house(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.2, KICK, self._acc(rnd) if s == 0 else self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            self._backbeat(D, rnd); self._ghost_sn(D, rnd, e * 0.7)
        if self.on["hat"]:
            self._hats(D, rnd, e, (2, 6, 10, 14))
        if self.on["bass"]:
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [3, 6, 7, 10, 14, 15])
        if self.on["lead"] and rnd.random() < 0.5:
            self._comp(D, rnd, beat, ct, [10])

    def _g_synthwave(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            for s in (0, 4, 8, 12):
                D(s, 0.2, KICK, self._acc(rnd) if s == 0 else self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            self._backbeat(D, rnd, clap=False); self._ghost_sn(D, rnd, e * 0.5)
        if self.on["hat"]:
            for s in range(16):
                if s in (6, 14):
                    D(s, 0.15, OHAT, 0.5, CH_DRUMS, "hat")
                elif rnd.random() < 0.85:
                    D(s, 0.04, HAT, self._main(rnd) if s % 4 == 0 else self._ghost(rnd) + 0.12, CH_DRUMS, "hat")
        if self.on["bass"]:
            for i in range(8):
                D(i * 2, beat * 0.4, cr + (12 if i == 7 else 0),
                  self._acc(rnd) if i == 0 else self._main(rnd), CH_BASS,
                  "kick", structural=(i == 0))
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)
            self._comp(D, rnd, beat, ct, [0, 8])


    def _g_neon_dub(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.32, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            if self.bar % 2 == 1:
                D(8, 0.3, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            D(8, 0.2, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
            if rnd.random() < 0.5:
                D(8, 0.22, CLAP, 0.6, CH_DRUMS, "snare")
        if self.on["hat"]:
            for s in (6, 14):
                if rnd.random() < 0.7:
                    D(s, 0.22, OHAT, 0.42, CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 1.6, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            if rnd.random() < 0.4 + 0.3 * e:
                D(11, beat * 0.5, cr + 7, self._main(rnd) * 0.8, CH_BASS)
        if self.on["lead"] and rnd.random() < 0.5:
            self._comp(D, rnd, beat, ct, [6])

    def _g_lofi(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.25, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            if rnd.random() < 0.5:
                D(10, 0.22, KICK, self._main(rnd) * 0.8, CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.2, SNARE, self._main(rnd), CH_DRUMS, "snare", True)
            self._ghost_sn(D, rnd, e * 0.6)
        if self.on["hat"]:
            for s in range(0, 16, 2):
                if rnd.random() < 0.6 + 0.2 * e:
                    D(s, 0.05, HAT, self._main(rnd) if s % 4 == 0 else self._ghost(rnd), CH_DRUMS, "hat")
        if self.on["bass"]:
            self._funk_bass(D, rnd, beat, ct, cr, nr, e * 0.7, [6, 10])
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)

    def _g_electro(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.3, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            for s in (3, 6, 10, 11, 14):
                if rnd.random() < 0.4 + 0.4 * e:
                    D(s, 0.24, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            self._backbeat(D, rnd); self._ghost_sn(D, rnd, e * 0.6)
        if self.on["hat"]:
            self._hats(D, rnd, e, (0, 4, 8, 12))
            for s in (2, 7, 11):
                if rnd.random() < 0.4 + 0.4 * e:
                    D(s, 0.08, PERC, self._main(rnd) * 0.8, CH_DRUMS)
        if self.on["bass"]:                                  # robotic riff
            riff = [(0, cr), (3, cr + 12), (6, cr), (8, cr), (11, cr + 7), (14, cr + 12)]
            for s, p in riff:
                if s == 0 or rnd.random() < 0.55 + 0.4 * e:
                    D(s, beat * 0.16, p, self._acc(rnd) if s == 0 else self._main(rnd),
                      CH_BASS, "kick" if s == 0 else "", structural=(s == 0))
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)

    def _g_eighties_hiphop(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["kick"]:
            D(0, 0.28, KICK, self._acc(rnd), CH_DRUMS, "kick", True)
            for s in (6, 10):
                if rnd.random() < 0.35 + 0.4 * e:
                    D(s, 0.24, KICK, self._main(rnd), CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in (4, 12):
                D(s, 0.22, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
                if rnd.random() < 0.6:
                    D(s, 0.22, CLAP, 0.7, CH_DRUMS, "snare")
            if fill:
                for s in (12, 13, 14, 15):
                    D(s, 0.06, SNARE, 0.55 + 0.05 * s, CH_DRUMS, "snare")
        if self.on["hat"]:
            for s in range(0, 16, 2):
                if rnd.random() < 0.5 + 0.3 * e:
                    D(s, 0.05, HAT, self._main(rnd) if s % 4 == 0 else self._ghost(rnd), CH_DRUMS, "hat")
        if self.on["bass"]:
            D(0, beat * 0.5, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            for s in (6, 10, 14):
                if rnd.random() < 0.35 + 0.35 * e:
                    D(s, beat * 0.3, rnd.choice([cr, cr, cr + 12, cr + 7]),
                      self._main(rnd), CH_BASS)
        if self.on["lead"] and rnd.random() < 0.45:
            self._motif(D, rnd, beat, sc, ct)
