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
          "dub_garage", "uk_garage", "boom_bap",
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
    # golden-age boom-bap (1992 Illmatic): dusty jazz-sampled minor, heavy
    # MPC swing, laid-back snare drag, DJ-scratch lead.
    "boom_bap": (DORIAN,
        [(1, "min7"), (4, "dom9"), (0, "min9"), (0, "min9")],   # jazzy ii-V-i vamp
        0.54, 0.040, -0.004, 0.010, 0.0, 45),
    "jazz": (DORIAN,
        [(1, "min7"), (4, "dom9"), (0, "min7"), (5, "min7")],   # minor ii-V-i-vi
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
    "electro_funk": {"kick": {"drive": 2.4, "click": 0.5, "decay": 0.28}, "snare": {"snap": 0.8, "tone": 0.5, "crush": 0.06}, "hat": {"metal": 0.6, "cutoff": 10000, "decay": 0.035}, "ohat": {"metal": 0.6, "cutoff": 9200, "decay": 0.24}, "clap": {"decay": 0.18, "tone": 1.05}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.3, "cutoff": 780, "res": 0.18, "fenv": 0.5, "sub": 0.85, "glide": 0.01, "level": 1.716}, "lead": {"detune": 0.1, "wave": 0.35, "cutoff": 5400, "drive": 1.4, "decay": 0.16}, "fx": {"reverb": 0.2, "delay": 0.18, "delayTime": 0.33, "width": 0.7}},
    "synthwave": {"kick": {"drive": 2.2, "click": 0.38, "decay": 0.3}, "snare": {"snap": 0.62, "tone": 0.52, "crush": 0.0}, "hat": {"metal": 0.4, "cutoff": 8400, "decay": 0.045}, "ohat": {"metal": 0.4, "cutoff": 7900, "decay": 0.28}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.045}, "perc": {"decay": 0.13}, "bass": {"drive": 1.2, "cutoff": 680, "res": 0.16, "fenv": 0.4, "sub": 0.78, "glide": 0.0, "level": 1.65}, "lead": {"detune": 0.2, "wave": 0.15, "cutoff": 6800, "drive": 1.1, "decay": 0.24}, "fx": {"reverb": 0.36, "delay": 0.25, "delayTime": 0.375, "width": 0.65}},
    "neon_dub": {"kick": {"drive": 2.0, "click": 0.28, "decay": 0.4}, "snare": {"snap": 0.42, "tone": 0.55, "crush": 0.08}, "hat": {"metal": 0.45, "cutoff": 7400, "decay": 0.055}, "ohat": {"metal": 0.45, "cutoff": 7000, "decay": 0.36}, "clap": {"decay": 0.28, "tone": 0.85}, "rim": {"decay": 0.055}, "perc": {"decay": 0.17}, "bass": {"drive": 1.1, "cutoff": 360, "res": 0.12, "fenv": 0.25, "sub": 0.97, "glide": 0.05, "level": 1.65}, "lead": {"detune": 0.12, "wave": 0.25, "cutoff": 4400, "drive": 0.9, "decay": 0.5}, "fx": {"reverb": 0.55, "delay": 0.44, "delayTime": 0.5, "width": 0.9}},
    "broken_house": {"kick": {"drive": 2.4, "click": 0.42, "decay": 0.28}, "snare": {"snap": 0.68, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.48, "cutoff": 9400, "decay": 0.04}, "ohat": {"metal": 0.48, "cutoff": 8800, "decay": 0.28}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.045}, "perc": {"decay": 0.12}, "bass": {"drive": 1.3, "cutoff": 740, "res": 0.2, "fenv": 0.5, "sub": 0.7, "glide": 0.0, "level": 2.112}, "lead": {"detune": 0.15, "wave": 0.3, "cutoff": 5800, "drive": 1.2, "decay": 0.2}, "fx": {"reverb": 0.26, "delay": 0.22, "delayTime": 0.353, "width": 0.7}},
    "lofi": {"kick": {"drive": 1.5, "click": 0.26, "decay": 0.34}, "snare": {"snap": 0.38, "tone": 0.44, "crush": 0.2}, "hat": {"metal": 0.32, "cutoff": 7000, "decay": 0.045}, "ohat": {"metal": 0.32, "cutoff": 6600, "decay": 0.24}, "clap": {"decay": 0.24, "tone": 0.8}, "rim": {"decay": 0.055}, "perc": {"decay": 0.15}, "bass": {"drive": 1.0, "cutoff": 460, "res": 0.14, "fenv": 0.35, "sub": 0.85, "glide": 0.0, "level": 1.65}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 4000, "drive": 0.85, "decay": 0.4}, "fx": {"reverb": 0.4, "delay": 0.3, "delayTime": 0.45, "width": 0.6}},
    "electro": {"kick": {"drive": 2.2, "click": 0.4, "decay": 0.42}, "snare": {"snap": 0.7, "tone": 0.4, "crush": 0.18}, "hat": {"metal": 0.7, "cutoff": 11000, "decay": 0.03}, "ohat": {"metal": 0.7, "cutoff": 10000, "decay": 0.2}, "clap": {"decay": 0.2, "tone": 1.15}, "rim": {"decay": 0.04}, "perc": {"decay": 0.1}, "bass": {"drive": 1.2, "cutoff": 900, "res": 0.22, "fenv": 0.55, "sub": 0.7, "glide": 0.0, "level": 1.65}, "lead": {"detune": 0.06, "wave": 0.6, "cutoff": 6500, "drive": 1.6, "decay": 0.14}, "fx": {"reverb": 0.26, "delay": 0.22, "delayTime": 0.1875, "width": 0.8}},
    "eighties_hiphop": {"kick": {"drive": 1.8, "click": 0.35, "decay": 0.46}, "snare": {"snap": 0.7, "tone": 0.55, "crush": 0.12}, "hat": {"metal": 0.4, "cutoff": 8500, "decay": 0.04}, "ohat": {"metal": 0.4, "cutoff": 8000, "decay": 0.26}, "clap": {"decay": 0.24, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.13}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.14, "fenv": 0.3, "sub": 0.9, "glide": 0.0, "level": 1.65}, "lead": {"detune": 0.1, "wave": 0.3, "cutoff": 4800, "drive": 1.0, "decay": 0.22}, "fx": {"reverb": 0.34, "delay": 0.28, "delayTime": 0.375, "width": 0.65}},
    "jazz": {"kick": {"drive": 1.2, "click": 0.2, "decay": 0.3}, "snare": {"snap": 0.4, "tone": 0.5, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9000, "decay": 0.05}, "ohat": {"metal": 0.5, "cutoff": 8500, "decay": 0.4}, "clap": {"decay": 0.18, "tone": 0.9}, "rim": {"decay": 0.05}, "perc": {"decay": 0.12}, "bass": {"drive": 0.8, "cutoff": 520, "res": 0.1, "fenv": 0.25, "sub": 0.8, "glide": 0.02, "level": 1.65}, "lead": {"detune": 0.06, "wave": 0.28, "cutoff": 3400, "drive": 0.45, "decay": 0.7}, "fx": {"reverb": 0.42, "delay": 0.18, "delayTime": 0.42, "width": 0.7}},
    "funk": {"kick": {"drive": 2.6, "click": 0.55, "decay": 0.26}, "snare": {"snap": 0.88, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.62, "cutoff": 10500, "decay": 0.03}, "ohat": {"metal": 0.62, "cutoff": 9500, "decay": 0.22}, "clap": {"decay": 0.17, "tone": 1.05}, "rim": {"decay": 0.038}, "perc": {"decay": 0.1}, "bass": {"drive": 0.95, "cutoff": 620, "res": 0.08, "fenv": 0.2, "sub": 0.88, "glide": 0.01, "level": 1.848}, "lead": {"detune": 0.08, "wave": 0.4, "cutoff": 5600, "drive": 1.5, "decay": 0.16}, "fx": {"reverb": 0.18, "delay": 0.16, "delayTime": 0.33, "width": 0.7}},
    "minneapolis_funk": {"kick": {"drive": 2.0, "click": 0.45, "decay": 0.3}, "snare": {"snap": 0.85, "tone": 0.55, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9800, "decay": 0.035}, "ohat": {"metal": 0.5, "cutoff": 9000, "decay": 0.26}, "clap": {"decay": 0.22, "tone": 1.0}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.4, "cutoff": 1000, "res": 0.3, "fenv": 0.6, "sub": 0.55, "glide": 0.0, "level": 2.4024}, "lead": {"detune": 0.14, "wave": 0.45, "cutoff": 6200, "drive": 1.3, "decay": 0.18}, "fx": {"reverb": 0.28, "delay": 0.2, "delayTime": 0.1875, "width": 0.75}},
    "minimal_techno": {"kick": {"drive": 1.8, "click": 0.3, "decay": 0.34}, "snare": {"snap": 0.5, "tone": 0.4, "crush": 0.0}, "hat": {"metal": 0.55, "cutoff": 11000, "decay": 0.022}, "ohat": {"metal": 0.55, "cutoff": 9500, "decay": 0.16}, "clap": {"decay": 0.16, "tone": 1.1}, "rim": {"decay": 0.03}, "perc": {"decay": 0.08}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.12, "fenv": 0.3, "sub": 0.92, "glide": 0.02, "level": 2.4024}, "lead": {"detune": 0.05, "wave": 0.5, "cutoff": 5200, "drive": 1.1, "decay": 0.12}, "fx": {"reverb": 0.34, "delay": 0.34, "delayTime": 0.5, "width": 0.7}},
    "detroit_techno": {"kick": {"drive": 2.2, "click": 0.4, "decay": 0.32}, "snare": {"snap": 0.6, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.48, "cutoff": 9600, "decay": 0.035}, "ohat": {"metal": 0.48, "cutoff": 8800, "decay": 0.3}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.045}, "perc": {"decay": 0.12}, "bass": {"drive": 0.7, "cutoff": 480, "res": 0.08, "fenv": 0.18, "sub": 0.85, "glide": 0.0, "level": 1.782}, "lead": {"detune": 0.16, "wave": 0.3, "cutoff": 5800, "drive": 1.2, "decay": 0.3}, "fx": {"reverb": 0.46, "delay": 0.32, "delayTime": 0.375, "width": 0.85}},
    "dub": {"kick": {"drive": 1.6, "click": 0.2, "decay": 0.5}, "snare": {"snap": 0.5, "tone": 0.55, "crush": 0.1}, "hat": {"metal": 0.35, "cutoff": 7200, "decay": 0.05}, "ohat": {"metal": 0.35, "cutoff": 6800, "decay": 0.4}, "clap": {"decay": 0.3, "tone": 0.8}, "rim": {"decay": 0.07}, "perc": {"decay": 0.18}, "bass": {"drive": 1.1, "cutoff": 320, "res": 0.1, "fenv": 0.25, "sub": 0.98, "glide": 0.06, "level": 1.65}, "lead": {"detune": 0.1, "wave": 0.2, "cutoff": 3600, "drive": 0.9, "decay": 0.5}, "fx": {"reverb": 0.6, "delay": 0.5, "delayTime": 0.5, "width": 0.9}},
    "steppers_dub": {"kick": {"drive": 1.8, "click": 0.25, "decay": 0.46}, "snare": {"snap": 0.55, "tone": 0.5, "crush": 0.08}, "hat": {"metal": 0.38, "cutoff": 7600, "decay": 0.045}, "ohat": {"metal": 0.38, "cutoff": 7000, "decay": 0.38}, "clap": {"decay": 0.28, "tone": 0.85}, "rim": {"decay": 0.06}, "perc": {"decay": 0.16}, "bass": {"drive": 1.2, "cutoff": 340, "res": 0.12, "fenv": 0.3, "sub": 0.97, "glide": 0.04, "level": 1.65}, "lead": {"detune": 0.1, "wave": 0.25, "cutoff": 3800, "drive": 1.0, "decay": 0.45}, "fx": {"reverb": 0.55, "delay": 0.46, "delayTime": 0.5, "width": 0.88}},
    "dub_techno": {"kick": {"drive": 1.8, "click": 0.28, "decay": 0.36}, "snare": {"snap": 0.45, "tone": 0.45, "crush": 0.0}, "hat": {"metal": 0.5, "cutoff": 9000, "decay": 0.03}, "ohat": {"metal": 0.5, "cutoff": 8200, "decay": 0.28}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.04}, "perc": {"decay": 0.1}, "bass": {"drive": 1.0, "cutoff": 380, "res": 0.1, "fenv": 0.25, "sub": 0.95, "glide": 0.03, "level": 1.65}, "lead": {"detune": 0.12, "wave": 0.35, "cutoff": 4200, "drive": 1.0, "decay": 0.4}, "fx": {"reverb": 0.6, "delay": 0.45, "delayTime": 0.5, "width": 0.85}},
    "roots_reggae": {"kick": {"drive": 1.5, "click": 0.22, "decay": 0.42}, "snare": {"snap": 0.5, "tone": 0.5, "crush": 0.05}, "hat": {"metal": 0.34, "cutoff": 7000, "decay": 0.05}, "ohat": {"metal": 0.34, "cutoff": 6600, "decay": 0.34}, "clap": {"decay": 0.24, "tone": 0.85}, "rim": {"decay": 0.07}, "perc": {"decay": 0.16}, "bass": {"drive": 1.0, "cutoff": 380, "res": 0.1, "fenv": 0.3, "sub": 0.95, "glide": 0.05, "level": 1.65}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 3800, "drive": 0.85, "decay": 0.4}, "fx": {"reverb": 0.4, "delay": 0.28, "delayTime": 0.42, "width": 0.7}},
    "uk_garage": {"kick": {"drive": 2.2, "click": 0.42, "decay": 0.28}, "snare": {"snap": 0.7, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.5, "cutoff": 10000, "decay": 0.035}, "ohat": {"metal": 0.5, "cutoff": 9000, "decay": 0.26}, "clap": {"decay": 0.2, "tone": 1.05}, "rim": {"decay": 0.04}, "perc": {"decay": 0.11}, "bass": {"drive": 1.4, "cutoff": 760, "res": 0.24, "fenv": 0.6, "sub": 0.78, "glide": 0.02, "level": 1.782}, "lead": {"detune": 0.14, "wave": 0.35, "cutoff": 5800, "drive": 1.3, "decay": 0.2}, "fx": {"reverb": 0.32, "delay": 0.24, "delayTime": 0.353, "width": 0.75}},
    "dub_garage": {"kick": {"drive": 2.0, "click": 0.38, "decay": 0.3}, "snare": {"snap": 0.65, "tone": 0.5, "crush": 0.06}, "hat": {"metal": 0.46, "cutoff": 9400, "decay": 0.035}, "ohat": {"metal": 0.46, "cutoff": 8600, "decay": 0.3}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.12}, "bass": {"drive": 1.3, "cutoff": 560, "res": 0.18, "fenv": 0.5, "sub": 0.88, "glide": 0.03, "level": 1.782}, "lead": {"detune": 0.12, "wave": 0.3, "cutoff": 5000, "drive": 1.1, "decay": 0.28}, "fx": {"reverb": 0.5, "delay": 0.42, "delayTime": 0.5, "width": 0.85}},
    "rnb": {"kick": {"drive": 1.4, "click": 0.25, "decay": 0.36}, "snare": {"snap": 0.5, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.4, "cutoff": 8200, "decay": 0.045}, "ohat": {"metal": 0.4, "cutoff": 7600, "decay": 0.26}, "clap": {"decay": 0.22, "tone": 0.95}, "rim": {"decay": 0.05}, "perc": {"decay": 0.13}, "bass": {"drive": 1.0, "cutoff": 520, "res": 0.12, "fenv": 0.35, "sub": 0.9, "glide": 0.03, "level": 1.6764}, "lead": {"detune": 0.08, "wave": 0.28, "cutoff": 3000, "drive": 0.4, "decay": 0.62}, "fx": {"reverb": 0.4, "delay": 0.2, "delayTime": 0.375, "width": 0.7}},
    "afro_rnb": {"kick": {"drive": 1.8, "click": 0.35, "decay": 0.32}, "snare": {"snap": 0.6, "tone": 0.5, "crush": 0.04}, "hat": {"metal": 0.42, "cutoff": 9200, "decay": 0.035}, "ohat": {"metal": 0.42, "cutoff": 8400, "decay": 0.24}, "clap": {"decay": 0.2, "tone": 1.0}, "rim": {"decay": 0.045}, "perc": {"decay": 0.1}, "bass": {"drive": 1.3, "cutoff": 760, "res": 0.2, "fenv": 0.5, "sub": 0.75, "glide": 0.02, "level": 1.782}, "lead": {"detune": 0.12, "wave": 0.35, "cutoff": 5600, "drive": 1.1, "decay": 0.22}, "fx": {"reverb": 0.34, "delay": 0.22, "delayTime": 0.353, "width": 0.78}},
    "indie_rnb": {"kick": {"drive": 1.3, "click": 0.22, "decay": 0.4}, "snare": {"snap": 0.45, "tone": 0.5, "crush": 0.12}, "hat": {"metal": 0.35, "cutoff": 7400, "decay": 0.05}, "ohat": {"metal": 0.35, "cutoff": 6800, "decay": 0.34}, "clap": {"decay": 0.26, "tone": 0.85}, "rim": {"decay": 0.06}, "perc": {"decay": 0.16}, "bass": {"drive": 0.9, "cutoff": 420, "res": 0.1, "fenv": 0.3, "sub": 0.92, "glide": 0.05, "level": 1.65}, "lead": {"detune": 0.08, "wave": 0.2, "cutoff": 3600, "drive": 0.75, "decay": 0.5}, "fx": {"reverb": 0.55, "delay": 0.34, "delayTime": 0.5, "width": 0.85}},
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
    "uk_garage": {"fxMel": {"reverb": 0.2, "delay": 0.18, "delayTime": 0.353}},  # organ stabs
    "boom_bap": {"fxMel": {"reverb": 0.1, "delay": 0.08}},      # dry — scratch needs to hit
    "eighties_hiphop": {"fxMel": {"reverb": 0.1, "delay": 0.06}},  # dry scratch
    "rnb": {"fxMel": {"reverb": 0.42, "delay": 0.2}, "fxBass": {"reverb": 0.04}},
    "afro_rnb": {"fxMel": {"reverb": 0.32, "delay": 0.22}},
    "indie_rnb": {"fxMel": {"reverb": 0.6, "delay": 0.4, "delayTime": 0.5},
                  "fxDrums": {"reverb": 0.22}},
}

# per-genre instrument variants (role -> SynthDef). Omitted roles = default.
_GENRE_INSTR = {
    "electro_funk":     {"bass": "bassFM",     "kick": "kickHard", "snare": "snare",    "lead": "leadMoog"},
    "synthwave":        {"bass": "bass",       "kick": "kick",     "snare": "snare909", "lead": "leadHyper"},
    "neon_dub":         {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadSiren"},
    "broken_house":     {"bass": "bassSquare", "kick": "kickHard", "snare": "snare909", "lead": "leadGlitch"},
    "lofi":             {"bass": "bass",       "kick": "kick",     "snare": "snareBrush", "lead": "leadPluck"},
    "electro":          {"bass": "bassSquare", "kick": "kick808",  "snare": "snare909", "lead": "leadVox", "keys": "keysElectro"},
    "eighties_hiphop":  {"bass": "bass",       "kick": "kick808",  "snare": "snare909", "lead": "leadScratch", "keys": "keysPad"},
    "jazz":             {"bass": "bass",       "kick": "kick",     "snare": "snareBrush", "lead": "leadJazz"},
    "funk":             {"bass": "bassFM",     "kick": "kickHard", "snare": "snare",    "lead": "leadMoog", "keys": "keys"},
    "minneapolis_funk": {"bass": "bassSquare", "kick": "kickHard", "snare": "snare909", "lead": "leadMoog", "keys": "keysOberheim"},
    "minimal_techno":   {"bass": "bassSquare", "kick": "kick",     "snare": "snare909", "lead": "leadGlitch"},
    "detroit_techno":   {"bass": "bassFM",     "kick": "kick",     "snare": "snare909", "lead": "leadHyper"},
    "dub":              {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadSiren"},
    "steppers_dub":     {"bass": "bass",       "kick": "kick808",  "snare": "snare",    "lead": "leadSiren"},
    "dub_techno":       {"bass": "bass",       "kick": "kick808",  "snare": "snare909", "lead": "leadSiren"},
    "roots_reggae":     {"bass": "bass",       "kick": "kick",     "snare": "snare",    "lead": "leadSiren"},
    "uk_garage":        {"bass": "bassFM",     "kick": "kickHard", "snare": "snare909", "lead": "leadBell"},
    "boom_bap":         {"bass": "bass",       "kick": "kickHard", "snare": "snare",    "lead": "leadScratch", "keys": "keysJazz"},
    "dub_garage":       {"bass": "bassFM",     "kick": "kickHard", "snare": "snare909", "lead": "leadBell"},
    "rnb":              {"bass": "bass",       "kick": "kick",     "snare": "snare",    "lead": "leadPluck"},
    "afro_rnb":         {"bass": "bassFM",     "kick": "kick",     "snare": "snare909", "lead": "leadPluck"},
    "indie_rnb":        {"bass": "bass",       "kick": "kick808",  "snare": "snareBrush", "lead": "leadPluck"},
}


# Four researched chord-progression variants per genre, as (scale_degree,
# quality) into the genre's PROFILE scale. Designed from genre harmony
# references (funk/jazz/neo-soul/house/techno/dub/garage/synthwave) and kept
# consonant with each genre's melodic scale (the lead/comp draw chord tones,
# so out-of-scale tones clash — see the rnb/jazz dissonance fix). A bluesy
# dominant tonic in funk is intentional genre signature, not a bug. One
# variant is chosen per section (LLM `harmony` 0..3, else rotated).
# Sources: pianowithjonny/guitarbased (funk), jazz-library/openmusictheory
# (jazz ii-V-I & turnarounds), orangecandymusic/pickupmusic (neo-soul),
# landr/richardpryn (lofi), attackmagazine/benrainey (deep house),
# musicradar/attackmagazine (Detroit/minimal techno), emastered/unison
# (synthwave), splice/orphiq (reggae/dub), futureproducers/loopmasters
# (UK garage), native-instruments (boom-bap), melodigging (electro-funk).
_PROGRESSIONS = {
    # ---- DORIAN genres (i=min, signature major IV=dom, bIII/bVII=maj) ----
    "electro_funk": [
        [(0, "min9"), (0, "min9"), (3, "dom9"), (4, "min7")],
        [(0, "min9"), (0, "min9"), (0, "min9"), (0, "min9")],
        [(0, "min7"), (6, "maj9"), (0, "min7"), (6, "maj9")],
        [(0, "min9"), (3, "dom9"), (0, "min9"), (3, "dom9")],
    ],
    "broken_house": [
        [(0, "min9"), (3, "dom9"), (4, "min7"), (0, "min9")],
        [(0, "min9"), (6, "maj9"), (2, "maj9"), (3, "dom9")],
        [(0, "min7"), (4, "min7"), (2, "maj7"), (0, "min7")],
        [(0, "min9"), (2, "maj9"), (0, "min9"), (2, "maj9")],
    ],
    "lofi": [
        [(1, "min7"), (3, "dom7"), (2, "maj7"), (0, "min7")],
        [(0, "min9"), (2, "maj9"), (3, "dom9"), (0, "min9")],
        [(0, "min7"), (6, "maj9"), (2, "maj7"), (3, "dom7")],
        [(1, "min7"), (4, "min7"), (2, "maj9"), (0, "min9")],
    ],
    "eighties_hiphop": [
        [(0, "min9"), (0, "min9"), (3, "dom9"), (0, "min9")],
        [(0, "min7"), (2, "maj7"), (3, "dom7"), (0, "min7")],
        [(1, "min7"), (3, "dom7"), (2, "maj7"), (0, "min7")],
        [(0, "min9"), (6, "maj9"), (0, "min9"), (6, "maj9")],
    ],
    "jazz": [
        [(1, "min7"), (4, "dom7"), (0, "min7"), (0, "min7")],
        [(0, "min9"), (0, "min9"), (2, "maj9"), (0, "min9")],
        [(0, "min9"), (0, "min9"), (3, "dom9"), (0, "min9")],
        [(0, "min7"), (6, "maj9"), (1, "min7"), (4, "dom7")],
    ],
    "funk": [
        [(0, "dom9"), (0, "dom9"), (0, "dom7#9"), (0, "dom9")],
        [(0, "min9"), (3, "dom9"), (0, "min9"), (3, "dom9")],
        [(0, "min7"), (6, "maj9"), (3, "dom9"), (0, "min7")],
        [(0, "min9"), (0, "min9"), (0, "min9"), (0, "min9")],
    ],
    "minneapolis_funk": [
        [(0, "min9"), (2, "maj9"), (3, "dom9"), (0, "min9")],
        [(0, "min9"), (0, "min9"), (3, "dom9"), (3, "dom9")],
        [(0, "min7"), (6, "maj9"), (0, "min7"), (6, "maj9")],
        [(0, "min9"), (3, "dom9"), (6, "maj9"), (0, "min9")],
    ],
    "detroit_techno": [
        [(0, "min9"), (2, "maj9"), (4, "min7"), (3, "dom9")],
        [(0, "min9"), (6, "maj9"), (2, "maj9"), (4, "min7")],
        [(0, "min7"), (0, "min7"), (2, "maj9"), (6, "maj9")],
        [(0, "min9"), (4, "min7"), (2, "maj9"), (0, "min9")],
    ],
    "uk_garage": [
        [(0, "min9"), (2, "maj9"), (3, "dom9"), (0, "min9")],
        [(1, "min7"), (3, "dom9"), (2, "maj9"), (0, "min9")],
        [(0, "min9"), (6, "maj9"), (4, "min7"), (0, "min9")],
        [(0, "min9"), (3, "dom9"), (2, "maj9"), (4, "min7")],
    ],
    "dub_garage": [
        [(0, "min9"), (0, "min9"), (3, "dom9"), (4, "min7")],
        [(0, "min7"), (6, "maj9"), (0, "min7"), (6, "maj9")],
        [(0, "min9"), (0, "min9"), (0, "min9"), (0, "min9")],
        [(0, "min9"), (3, "dom9"), (0, "min9"), (3, "dom9")],
    ],
    "rnb": [
        [(0, "min9"), (3, "dom9"), (2, "maj9"), (4, "min7")],
        [(0, "min9"), (6, "maj9"), (2, "maj9"), (4, "min7")],
        [(1, "min7"), (3, "dom9"), (0, "min9"), (0, "min9")],
        [(0, "min9"), (2, "maj9"), (3, "dom9"), (0, "min9")],
    ],
    "afro_rnb": [
        [(0, "min9"), (2, "maj9"), (3, "dom9"), (0, "min9")],
        [(0, "min9"), (3, "dom9"), (0, "min9"), (3, "dom9")],
        [(0, "min7"), (6, "maj9"), (2, "maj9"), (3, "dom9")],
        [(0, "min9"), (4, "min7"), (2, "maj9"), (0, "min9")],
    ],
    # ---- NAT_MINOR genres (i=min, bIII/bVI=maj, bVII=dom, iv/v=min) ----
    "synthwave": [
        [(0, "min9"), (5, "maj7"), (2, "maj7"), (6, "dom7")],
        [(0, "min9"), (6, "dom7"), (5, "maj7"), (6, "dom7")],
        [(0, "min9"), (2, "maj9"), (5, "maj7"), (6, "dom7")],
        [(0, "min7"), (3, "min7"), (5, "maj7"), (4, "min7")],
    ],
    "neon_dub": [
        [(0, "min9"), (0, "min9"), (3, "min7"), (0, "min9")],
        [(0, "min7"), (0, "min7"), (0, "min7"), (0, "min7")],
        [(0, "min9"), (5, "maj7"), (0, "min9"), (5, "maj7")],
        [(0, "min7"), (6, "dom7"), (0, "min7"), (6, "dom7")],
    ],
    "minimal_techno": [
        [(0, "min9"), (0, "min9"), (0, "min7"), (0, "min9")],
        [(0, "min9"), (0, "min9"), (0, "min9"), (0, "min9")],
        [(0, "min7"), (0, "min7"), (5, "maj7"), (0, "min7")],
        [(0, "min9"), (0, "min9"), (6, "dom7"), (0, "min9")],
    ],
    "dub": [
        [(0, "min7"), (0, "min7"), (3, "min7"), (0, "min7")],
        [(0, "min7"), (0, "min7"), (0, "min7"), (0, "min7")],
        [(0, "min9"), (5, "maj7"), (0, "min9"), (5, "maj7")],
        [(0, "min7"), (6, "dom7"), (5, "maj7"), (0, "min7")],
    ],
    "steppers_dub": [
        [(0, "min7"), (0, "min7"), (4, "min7"), (0, "min7")],
        [(0, "min9"), (0, "min9"), (3, "min7"), (0, "min9")],
        [(0, "min7"), (0, "min7"), (0, "min7"), (0, "min7")],
        [(0, "min7"), (6, "dom7"), (0, "min7"), (6, "dom7")],
    ],
    "dub_techno": [
        [(0, "min9"), (0, "min9"), (0, "min7"), (0, "min9")],
        [(0, "min9"), (0, "min9"), (0, "min9"), (0, "min9")],
        [(0, "min7"), (3, "min7"), (0, "min7"), (3, "min7")],
        [(0, "min9"), (5, "maj7"), (0, "min9"), (5, "maj7")],
    ],
    "roots_reggae": [
        [(0, "min7"), (3, "min7"), (4, "min7"), (0, "min7")],
        [(0, "min7"), (5, "maj7"), (6, "dom7"), (0, "min7")],
        [(0, "min9"), (3, "min9"), (0, "min9"), (3, "min9")],
        [(0, "min7"), (6, "dom7"), (5, "maj7"), (4, "min7")],
    ],
    "indie_rnb": [
        [(0, "min9"), (5, "maj7"), (3, "min9"), (4, "min7")],
        [(0, "min9"), (2, "maj9"), (5, "maj7"), (0, "min9")],
        [(0, "min7"), (6, "dom7"), (5, "maj7"), (2, "maj9")],
        [(0, "min9"), (3, "min7"), (2, "maj9"), (0, "min9")],
    ],
    # ---- PHRYGIAN genre (i=min, bII=maj signature, bIII=dom) ----
    "electro": [
        [(0, "min7"), (0, "min7"), (1, "maj7"), (0, "min7")],
        [(0, "min7"), (1, "maj9"), (0, "min7"), (1, "maj9")],
        [(0, "min7"), (6, "min7"), (5, "maj7"), (0, "min7")],
        [(0, "min7"), (0, "min7"), (0, "min7"), (0, "min7")],
    ],
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

# ── GROOVE-FIRST LEAD TUNING ──────────────────────────────────────────
# Per-genre kick "strong" positions (16th slots). The lead avoids these
# (hocket): a coincident lead hit is mostly dropped to leave the kick space.
_KICK_STRONG = {
    "funk": {0}, "minneapolis_funk": {0}, "electro_funk": {0, 8},
    "jazz": set(),
    "lofi": {0, 8}, "rnb": {0, 8}, "afro_rnb": {0, 8}, "indie_rnb": {0, 8},
    "eighties_hiphop": {0, 8}, "synthwave": {0, 4, 8, 12},
    "electro": {0, 4, 8, 12}, "broken_house": {0, 4, 8, 12},
    "minimal_techno": {0, 4, 8, 12}, "detroit_techno": {0, 4, 8, 12},
    "dub_techno": {0, 4, 8, 12}, "neon_dub": {0, 8},
    "dub": {0, 8}, "steppers_dub": {4, 12}, "roots_reggae": {8},
    "uk_garage": {0, 8}, "dub_garage": {0, 8},
}

# Per-feel rest probabilities: bar_p = whole-bar silence chance,
# note_p = individual-note drop chance. The groove lives in the gaps.
# per-feel note duration multiplier (the factor that scales beat * du into
# the actual gate length). Higher = longer-sustained notes.
_LEAD_NLEN = {
    "funk":  0.45,   # talkbox sings
    "solo":  0.5,    # expressive Moog solo notes ring/sing
    "mplslead": 0.4,  # mix of short stabs + long held notes (via du in the licks)
    "jazz":  0.30,   # bebop 8ths (also used by _jazz_motif)
    "stab":  0.16,   # true stabs
    "robotvox": 0.5,  # each word rings ~a beat (electro robot vocal)
    "hypno": 0.20,   # short repetitive
    "lyric": 0.42,   # singable, sustained
    "hook":  0.14,   # tight 16ths (80s hook)
    "scratch": 0.25, # du = rhythmic slot, so gate fills the slot exactly
    "space": 0.40,   # n/a (dub family uses skanks)
}

# per-feel per-note velocity multiplier (the SECOND loudness lever; the
# first being per-genre _LEAD_LEVEL above). User wanted funk-family leads
# +30% — bumped both knobs ~1.15 each (combined ~1.32x). Two-levers rule:
# synthdef level alone never quite shifts perceived loudness enough.
_LEAD_VEL_BOOST = {
    "funk":  1.15,   # leadMoog on funk / minneapolis_funk / electro_funk
    "stab":  0.95,   # electro / synthwave / broken_house / uk_garage / dub_garage
}

# per-GENRE octave offset applied AFTER the key-anchored pitch calc.
# Default 0; -1 = one octave down, +1 = one octave up.
_LEAD_OCT = {
    "electro": -1,
    "funk":    -1,
    "minneapolis_funk": -1,
}

# B-phrase FILL banks per feel — when use_b is True (1 in every 8 emitted
# phrases), pick a motif from here INSTEAD of the regular _LEAD_RHYTHM bank.
# These have MORE notes than the A motifs: chord-tone runs, busier
# answer-fills. The contrast (7 As locked in identical, then 1 busy B)
# is the song's "release valve."
_LEAD_FILL = {
    # funk: 2-bar busy answer-fill, 1-3-5-7 climb + descent
    "funk": [
        [(1,0,1), (3,1,1), (5,2,1), (7,4,2), (5,8,1), (3,9,1), (1,10,2),
         (5,16,1), (7,18,1), (5,20,1), (3,22,1), (1,24,4)],
        [(1,0,1), (3,1,1), (5,2,1), (7,3,1), (8,4,2),
         (8,16,1), (7,17,1), (5,18,1), (3,19,1), (1,20,4)],
    ],
    # lyric: 2-bar soul fill, more chord-tone movement
    "lyric": [
        [(3,0,2), (5,4,1), (7,6,1), (8,8,2),
         (8,16,1), (5,18,1), (3,20,1), (1,22,4)],
        [(1,0,1), (3,2,1), (5,4,1), (7,6,1), (8,8,4),
         (5,16,1), (3,18,1), (1,20,4)],
    ],
    # stab: 1-bar busy chord-tone run (8 notes vs typical 3-4)
    "stab": [
        [(1,0,1), (3,2,1), (5,4,1), (7,6,1), (8,8,1), (5,10,1), (3,12,1), (1,14,2)],
        [(5,0,1), (7,2,1), (8,4,1), (5,6,1), (3,8,1), (1,10,1), (5,12,1), (1,14,2)],
    ],
    # hypno: a touch busier than minimal A (still sparse)
    "hypno": [
        [(1,0,1), (3,4,1), (5,8,2), (3,12,2)],
        [(5,0,2), (3,4,1), (1,8,1), (3,12,2)],
    ],
    # hook: 8 16th-notes (vs typical 3-5) — full bar of chord-tone run
    "hook": [
        [(1,0,1), (3,1,1), (5,2,1), (7,3,1), (8,4,1), (5,5,1), (3,6,1), (1,7,1)],
        [(5,0,1), (3,1,1), (1,2,1), (3,3,1), (5,4,1), (7,5,1), (8,6,1), (5,7,1)],
    ],
    # scratch B-fill: rapid 16th "scribble" run (continuous chops)
    "scratch": [
        [(1,0,1),(5,1,1),(1,2,1),(5,3,1),(1,4,1),(5,5,1),(1,6,1),(5,7,1),
         (1,8,1),(5,9,1),(1,10,1),(5,11,1),(1,12,1),(5,13,1),(1,14,1),(5,15,1)],
    ],
}

# per-feel bar interval between emitted phrases. 4 = "one phrase per 4
# bars" (the phrase plays in bar 0 of the group, bars 1-3 are silent).
# Jazz is unchanged (uses _jazz_motif, emits continuously). Space = n/a.
_LEAD_EVERY = {
    "funk":  4,
    "solo":  8,    # a featured Moog solo every 8 bars (funk only)
    "mplslead": 2,  # mpls Moog hook comes often (every 2 bars)
    "lyric": 4,
    "stab":  2,   # stab feel emits twice as often (electro/synthwave/etc)
    "robotvox": 2,   # 2-bar robot-vocal phrase (electro)
    "hypno": 4,
    "hook":  4,
    "scratch": 2, # scratch is rhythmic — present every other bar
}

# Phrase LENGTH in bars per feel — a phrase spans this many bars, notes
# in the motif have s up to (16 * len - 1). Combined with _LEAD_EVERY:
# a new phrase STARTS every "_LEAD_EVERY" bars and plays for "_PHRASE_LEN"
# bars; the remainder is silent breath. Designed for HORN-SECTION feel:
# tight chord-tone stabs, NOT sustained melodies. 1 bar = single riff;
# 2 bars allows a call-response within the phrase.
_PHRASE_LEN = {
    "funk":  2,    # 2-bar horn riff w/ call-response, then 2 bars breath
    "solo":  2,    # 2-bar Moog solo statement
    "mplslead": 1,  # 1-bar hook + 1 bar breath (repeats often)
    "lyric": 2,    # 2-bar soul-horn line, then 2 bars breath
    "stab":  1,    # 1-bar stab riff, 1 bar breath
    "robotvox": 2,  # 2-bar robot-vocal phrase (electro)
    "hypno": 1,    # 1-bar minimal hit, 3 bars breath
    "hook":  1,    # 1-bar 16th burst, 3 bars breath
    "scratch": 2,  # 2-bar scratch patterns (main repeated + turnaround)
}

_LEAD_REST = {
    "hook":  (0.0,  0.05),   # silence handled deterministically by the hook branch
    "scratch": (0.0, 0.0),   # NO drops -> a repeated pattern is byte-identical
    "robotvox": (0.0, 0.0),  # mechanical: every word lands, identical repeats
    "solo": (0.0, 0.05),     # the solo statement lands fully (it's featured)
    "mplslead": (0.05, 0.1),  # mostly lands; a little space
    "funk":  (0.06, 0.14),
    "jazz":  (0.04, 0.06),
    "stab":  (0.06, 0.10),
    "hypno": (0.10, 0.15),
    "lyric": (0.08, 0.15),
    "space": (0.22, 0.16),
}

# Per-genre lead micro-timing (in 16th-step units). Negative = push (on
# top of the beat), positive = lay back behind it.
_LEAD_PUSH = {
    "funk": -0.10, "minneapolis_funk": -0.10, "electro_funk": -0.08,
    "jazz": 0.05,
    "lofi": 0.20, "rnb": 0.20, "afro_rnb": 0.18, "indie_rnb": 0.18,
    "eighties_hiphop": 0.06,
    "dub": 0.22, "neon_dub": 0.22, "steppers_dub": 0.20, "dub_techno": 0.18,
    "roots_reggae": 0.22, "dub_garage": 0.08,
    "synthwave": 0.0, "electro": -0.05, "broken_house": -0.05,
    "minimal_techno": -0.04, "detroit_techno": -0.04, "uk_garage": -0.02,
}

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
    "eighties_hiphop":  {"notes": 0.5,  "fill": 0.35, "run": 2, "span": 4,  "harm": 0.18},
}

# Curated rhythmic motifs make the lead sound PLAYED, not random-sampled.
# A genre maps to a feel; each feel has a few hand-written figures of
# (degIdx, step16, dur16). degIdx is unused for pitch (the contour drives
# pitch) but kept so the tuple shape matches everything that reads motif.
_LEAD_FEEL = {
    "funk": "solo", "minneapolis_funk": "mplslead", "electro_funk": "funk",
    "jazz": "jazz",
    "broken_house": "stab", "uk_garage": "stab", "dub_garage": "stab",
    "boom_bap": "scratch",
    "electro": "robotvox", "synthwave": "stab",
    "minimal_techno": "hypno", "detroit_techno": "hypno", "dub_techno": "hypno",
    "rnb": "lyric", "afro_rnb": "lyric", "indie_rnb": "lyric",
    "lofi": "lyric", "eighties_hiphop": "scratch",
    "dub": "space", "neon_dub": "space", "steppers_dub": "space",
    "roots_reggae": "space",
}
# Per-section melodies. Each tuple is (deg, s, du):
#   deg : scale degree relative to the CURRENT CHORD ROOT, mapped through
#         the chord's mode (minor scale for minor chords, major scale for
#         major, mixolydian for dom7, locrian for half-dim). Deg 1..7 plus
#         deg 8 (octave) supported; chord-aware transposition is handled
#         in _motif via _scale_deg_pit().
#   s   : 16th-step position within the bar (0..15)
#   du  : duration in 16th-step units
# A section locks ONE melody (its A motif) + one variation (B motif), then
# replays the A/A/A/B pattern across emit-bars (every bar for funk/jazz,
# every 2 bars for hook/lyric/stab/hypno).
_LEAD_RHYTHM = {
    # funk (horn section): 2-bar phrases. EACH A motif has INTERNAL
    # REPETITION + follows the BASS — deg -6 (one octave below default
    # lead reg = bass-doubling register) on the 'one' of each bar, echoing
    # the bass kick rhythm. Small repeating figures (5-3, 1-3) hook the ear.
    # Bernie Worrell / Junie Morrison Mini-Moog SOLO — expressive 2-bar
    # statements: scale runs, repeated wails, octave leaps, held bends. The
    # leadMoog glide ties the notes so it SINGS. Appears every 16 bars.
    # mpls funk Moog HOOK — 1-bar repeating phrases that mix SHORT stabs (du 1)
    # with LONG held notes (du 4-8). Recurs (AAAAAAAB) every 2 bars.
    "mplslead": [
        [(5, 0, 1), (3, 1, 1), (1, 2, 1), (5, 4, 8)],            # 3 short stabs -> long hold
        [(1, 0, 1), (3, 2, 1), (5, 4, 6), (8, 12, 1), (5, 14, 1)], # pickup -> hold -> short tag
        [(5, 0, 1), (5, 2, 1), (3, 4, 1), (1, 6, 1), (5, 8, 8)],   # repeated short hook -> long
        [(8, 0, 6), (5, 8, 1), (3, 10, 1), (1, 12, 4)],           # long note -> short answer
    ],
    "solo": [
        # ascending run -> wail at the top -> descend home
        [(1,0,1), (3,2,1), (4,4,1), (5,6,2), (7,10,1), (8,12,3), (7,18,1),
         (5,20,1), (4,22,1), (3,24,1), (1,26,4)],
        # repeated-note funk stab -> leap up -> held wail -> turn
        [(5,0,1), (5,2,1), (4,4,1), (5,6,1), (8,8,4), (7,14,1), (5,16,2),
         (3,20,1), (1,22,1), (5,24,4)],
        # call (high held) -> response run down -> resolve
        [(8,0,4), (7,6,1), (5,8,1), (4,10,1), (3,12,2), (1,16,2), (3,20,1),
         (5,22,1), (7,24,2), (8,28,3)],
        # sparse, vocal — leave space, big bends
        [(5,0,2), (7,4,1), (8,6,3), (5,12,2), (4,16,1), (3,18,2), (1,22,5)],
    ],
    "funk": [
        # Bass-octave on each 'one' (echoing bass) + chord-tone fills
        [(-6,0,1), (1,2,1), (3,4,1), (-6,8,1), (5,12,1), (-6,16,1), (1,18,1), (3,20,1), (5,22,2)],
        # Bass-doubling HELD over bar 1 + repeated 5-stab answer
        [(-6,0,7), (5,16,1), (5,18,1), (5,20,1), (1,22,4)],
        # Bass-octave call x2 + held 5 response (lead mirrors bass-then-replies)
        [(-6,0,2), (1,4,1), (-6,8,2), (1,12,1), (5,16,4), (5,22,2)],
        # 5-3 figure x3 + bass-anchor hold on bar 2
        [(5,0,1), (3,2,1), (5,4,1), (3,6,1), (5,8,1), (3,10,1), (-6,20,4)],
        # 1-3 alternating x4 + bass anchor hold
        [(1,0,1), (3,2,1), (1,4,1), (3,6,1), (1,8,1), (3,10,1), (1,12,1), (3,14,1), (-6,16,7)],
        # Bass-dip + held 5 + bass-dip + repeated 5-stab
        [(-6,0,2), (5,4,5), (-6,16,2), (5,20,1), (5,22,2)],
        # Bass-octave-then-chord-tone pattern repeated in both bars
        [(-6,0,2), (5,4,1), (3,6,1), (1,8,2), (-6,16,2), (5,20,1), (3,22,1), (1,24,2)],
        # Long bass-octave + brief chord-tone climb answer
        [(-6,0,5), (1,16,1), (3,17,1), (5,18,1), (1,20,4)],
    ],
    # jazz (bebop): _jazz_motif uses a CHROMATIC ladder (chord tones on
    # strong beats, semitone passing tones between) -> the deg field here
    # is unused by _jazz_motif. Kept as 0 to preserve tuple shape.
    "jazz": [
        [(0,0,1), (0,2,1), (0,4,1), (0,6,1), (0,8,1), (0,10,1), (0,12,1), (0,14,1)],
        [(0,0,1), (0,2,1), (0,4,1), (0,8,1), (0,10,1), (0,12,1), (0,14,1)],
        [(0,2,1), (0,4,1), (0,6,1), (0,8,1), (0,10,1), (0,12,1), (0,14,1)],
        [(0,0,1), (0,2,1), (0,4,1), (0,6,1), (0,8,2), (0,12,2)],
        [(0,0,1), (0,1,1), (0,2,1), (0,3,1), (0,6,1), (0,8,1), (0,10,1), (0,12,2)],
    ],
    # stab (synthwave/electro horn-stab): 1-bar phrases. INTERNAL REPETITION
    # of 2-3 note figures + bass-echo on beat 1 (deg -6 = bass-doubling reg).
    "stab": [
        [(-6,0,1), (5,4,1), (3,6,1), (1,8,4)],                          # bass-echo + stabs-HOLD
        [(5,0,1), (5,4,1), (5,8,1), (1,12,3)],                          # repeated 5 stabs + HOLD
        [(1,0,1), (5,4,1), (1,8,1), (5,12,1)],                          # 1-5 alternating
        [(-6,0,1), (3,2,1), (1,4,1), (-6,8,1), (3,10,1), (1,12,4)],     # bass-echo x2 + repeated 3-1 + held
        [(3,0,1), (5,2,1), (3,4,1), (5,6,1), (1,8,4)],                  # 3-5 alternating + HOLD
    ],
    # hypno (techno): minimal — long held + sparse hit. Single voice
    # sustained over the loop.
    "hypno": [
        [(1,0,3), (5,8,5)],                                             # 1 stab + 5 HELD
        [(5,0,7)],                                                       # one long held 5
        [(1,4,2), (5,8,5)],                                             # 1 + held 5
        [(5,2,1), (3,4,1), (1,8,5)],                                    # 5-3-1 + held 1
    ],
    # lyric (rnb/lofi soul-horn): 2-bar phrases. INTERNAL REPETITION +
    # bass-echo on beat 1 of each bar (lead follows the bass anchor).
    "lyric": [
        # Bass-anchor held + repeated soul stabs
        [(-6,0,7), (5,16,1), (3,18,1), (5,20,1), (3,22,2)],
        # Bass-echo + 5-3 figure x2 + held
        [(-6,0,1), (5,4,1), (3,6,1), (5,8,1), (3,10,1), (-6,16,1), (1,20,4)],
        # 3-5 alternating x3 + bass anchor on bar 2
        [(3,0,1), (5,2,1), (3,4,1), (5,6,1), (3,8,1), (5,10,1), (-6,16,7)],
        # Long held 5 + bass-echo + stab answer
        [(5,0,7), (-6,16,2), (5,20,1), (3,22,2)],
        # Bass-anchor x2 (one per bar) + soul-stab fills between
        [(-6,0,2), (5,4,1), (3,6,1), (1,8,1), (-6,16,2), (5,20,1), (3,22,1), (1,24,1)],
    ],
    "space": [
        [(1,0,6)],
        [(1,4,4), (1,12,3)],
        [(1,6,7)],
        [(1,2,2), (2,11,5)],
    ],
    # hook (80s hiphop horn-stab): tight 16th chord-tone bursts.
    "hook": [
        [(1,0,1), (3,1,1), (5,2,1)],                                    # 1-3-5 stab
        [(5,0,1), (3,1,1), (1,2,1)],                                    # 5-3-1 descending
        [(1,8,1), (3,9,1), (5,10,1)],                                   # 1-3-5 late stab
        [(5,4,1), (1,5,1), (5,6,1), (3,7,1)],                           # 5-1-5-3 mid-bar
        [(1,0,1), (5,2,1), (3,4,1)],                                    # 1-5-3 punch
    ],
    # scratch (turntablist): 1-bar patterns, VARIED per phrase. The KEY is
    # MIXED subdivisions within a pattern — NOT a stiff even grid. s is in
    # 16th-steps but FRACTIONAL is allowed: gap 2 = 8th, gap 1 = 16th,
    # gap 0.5 = 32nd. Cluster the 0.5-gaps for fast scratch bursts. A LONG
    # note (du=10) = the DJ "lets the record go" so the word plays out.
    # MOST phrases are pure scratching; the played-out word is the payoff.
    "scratch": [
        # 8th 8th | 16th 16th | 8th | 32nd 32nd 32nd 32nd | 8th
        [(1,0,1),(1,2,1),(1,4,1),(1,5,1),(1,6,1),(1,8,1),(1,8.5,1),(1,9,1),(1,9.5,1),(1,12,1)],
        # 16th 16th | 32nd 32nd 32nd | 8th | 32nd 32nd 16th
        [(1,0,1),(1,1,1),(1,2,1),(1,2.5,1),(1,3,1),(1,6,1),(1,8,1),(1,8.5,1),(1,9,1)],
        # 32nd cluster | 8th | 8th | 32nd cluster | 8th
        [(1,0,1),(1,0.5,1),(1,1,1),(1,4,1),(1,6,1),(1,6.5,1),(1,7,1),(1,10,1),(1,12,1),(1,12.5,1),(1,13,1)],
        # syncopated: 8th | 32nd 32nd | 8th | 32nd cluster | 8th
        [(1,2,1),(1,3,1),(1,3.5,1),(1,4,1),(1,8,1),(1,10,1),(1,10.5,1),(1,11,1),(1,11.5,1),(1,14,1)],
        # rapid 32nd bursts on beats 1 & 3
        [(1,0,1),(1,0.5,1),(1,1,1),(1,1.5,1),(1,8,1),(1,8.5,1),(1,9,1),(1,9.5,1)],
        # fifth accents + 32nd clusters
        [(5,0,1),(5,0.5,1),(1,2,1),(1,4,1),(1,4.5,1),(1,5,1),(5,8,1),(1,10,1),(1,10.5,1),(1,11,1)],
        # --- scratch THEN word (payoff) ---
        [(1,0,1),(1,0.5,1),(1,1,1),(1,1.5,1),(1,4,1),(1,8,10)],   # 32nd flurry -> word
        [(1,0,1),(1,2,1),(1,2.5,1),(1,3,1),(1,8,10)],             # mixed -> word
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
    "boom_bap":         {"kick": {"punch": 0.70}, "snare": {"body": 0.66, "buzz": 0.30}, "hat": {"loose": 0.16}},
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
    "boom_bap": (0.36, 0.38),
    "rnb": (0.24, 0.18), "afro_rnb": (0.28, 0.24),
    "indie_rnb": (0.22, 0.14),
}

# Per-genre LEAD output level (pure post-gain `level`, 1.0 = unchanged).
# Normalises the perceived lead loudness across genres: the 3 lead synths
# (saw-unison \lead / FM \leadFM / PWM \leadPulse) + each genre's cutoff/
# drive/decay give very different perceived levels for the same velocity.
# This trims output ONLY (not velocity) so tone and the visualizer's
# velocity-driven glyph brightness are unaffected. Tune by ear here.
# global mix balance (per-channel velocity scale): drums sit back 10%, the
# melodic/bass instruments come up 10%. Applied centrally in _build's D().
_CH_GAIN = {CH_DRUMS: 0.69, CH_PERC: 0.69, CH_BASS: 1.21, CH_LEAD: 1.21, CH_KEYS: 1.21}

# global lead-volume multiplier applied to BOTH levers (level + velocity)
# so the combined effect is one global trim. 0.84 x 0.84 = 0.706 ~= -30%.
_LEAD_GLOBAL = 0.84

_LEAD_LEVEL = {
    # leadPulse genres tend bright/loud -> trim
    "electro": 0.4788, "uk_garage": 0.55, "minneapolis_funk": 0.218,
    "broken_house": 0.5267, "minimal_techno": 0.567, "eighties_hiphop": 0.60,
    "boom_bap": 0.60,
    # \lead genres
    "funk": 0.118, "electro_funk": 0.8332, "synthwave": 0.5925, "jazz": 0.5292,
    # leadFM genres tend dark/quiet -> lift
    "detroit_techno": 0.63, "afro_rnb": 0.315, "dub_garage": 0.6344,
    "dub_techno": 0.8489, "neon_dub": 0.8644, "steppers_dub": 0.8644,
    "lofi": 0.7245, "rnb": 0.9198, "roots_reggae": 0.9261, "dub": 0.9416,
    "indie_rnb": 0.7686,
}

# Per-genre CHORD (CH_KEYS) loudness multiplier. keys is not in the
# SYNTH_PARAMS plumbing, so this is applied to the chord note velocity
# in _comp/_pad/_skank (default 1.0 = unchanged).
# Genres you explicitly set keep their value; every other genre's chords
# sit at 0.8. dub stays at 1.2 (a deliberate chord *raise*), rnb at 0.64.
_KEYS_LEVEL = {
    "dub": 0.96,
    "rnb": 0.512,
    "minimal_techno": 0.64,
    "roots_reggae": 0.64,
    "afro_rnb": 0.64,
    "broken_house": 0.64,
    "detroit_techno": 0.64,
    "dub_garage": 0.64,
    "dub_techno": 0.64,
    "eighties_hiphop": 0.64,
    "electro": 1.035,
    "electro_funk": 0.64,
    "funk": 0.64,
    "indie_rnb": 0.64,
    "jazz": 0.64,
    "lofi": 0.64,
    "minneapolis_funk": 0.64,
    "neon_dub": 0.64,
    "steppers_dub": 0.64,
    "synthwave": 0.64,
    "uk_garage": 0.64,
}


# Song STRUCTURE: instruments enter staggered, then periodic breaks. Entry
# offsets are in "units" (U bars); U is larger for spacious genres so their
# builds are longer. One archetype per section — chosen by the LLM
# `structure` 0..3 (else seeded rotation), same pattern as `harmony`.
_STRUCT = [
    # 0 classic build: bass+drums, keys +1U, lead +2U; breakdown every 8U
    {"in": {"bass": 0, "drums": 0, "keys": 1, "lead": 2},
     "brk": {"every": 8, "len": 2, "drop": ["drums", "lead"]}},
    # 1 quick: in fast, lead +1U; rare lead drop
    {"in": {"bass": 0, "drums": 0, "keys": 0, "lead": 1},
     "brk": {"every": 16, "len": 2, "drop": ["lead"]}},
    # 2 long / spacious: slow staggered build, dubby breakdowns
    {"in": {"bass": 0, "drums": 1, "keys": 2, "lead": 3},
     "brk": {"every": 12, "len": 4, "drop": ["drums", "lead"]}},
    # 3 DJ-tool / minimal: tight, frequent 2-bar drum drops, lead late
    {"in": {"bass": 0, "drums": 0, "keys": 1, "lead": 4},
     "brk": {"every": 4, "len": 2, "drop": ["drums"]}},
]
_SPACIOUS = {"dub", "steppers_dub", "dub_techno", "neon_dub", "roots_reggae",
             "minimal_techno", "lofi", "indie_rnb"}


class CannedSource:
    name = "canned"

    def __init__(self):
        self.bpm = 100
        self.root = 0
        self.genre = "funk"
        self.energy = 0.5
        self.on = {"kick": True, "snare": True, "hat": True, "bass": True,
                   "lead": True, "keys": True}
        self.bar = 0
        self.motif = []
        # arrangement defaults — no-op (everything on) until prime() sets them
        self.base_on = dict(self.on)
        self._in = {}
        self._bk_start = 10 ** 9
        self._bk_every = 16
        self._bk_len = 0
        self._bk_drop = []
        self._keys_lvl = 1.0

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
        # electro robot vocal: how many word buffers to cycle on the beat
        try:
            self._vox_n = max(1, min(6, int(section.get("robot_words") or 4)))
        except (TypeError, ValueError):
            self._vox_n = 4
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
        self._motif_bank = [list(v) for v in variants]
        self.motif = self._motif_bank[0]                  # _jazz_motif reads self.motif
        self.bar = 0
        # which of the 4 researched progressions this section uses: the LLM's
        # composition choice (`harmony` 0..3); absent -> rotate so all four
        # are heard over a run.
        self._sec = getattr(self, "_sec", -1) + 1
        banks = _PROGRESSIONS.get(self.genre)
        n = len(banks) if banks else 1
        h = section.get("harmony")
        try:
            self.prog_sel = int(h) % n if h is not None else self._sec % n
        except (TypeError, ValueError):
            self.prog_sel = self._sec % n
        # SONG STRUCTURE: pick an arrangement archetype (LLM `structure`
        # 0..3, else seeded rotation) and materialise it into absolute
        # bars. U (intro unit) is longer for spacious genres.
        ns = len(_STRUCT)
        sx = section.get("structure")
        try:
            self.struct_sel = int(sx) % ns if sx is not None else self._sec % ns
        except (TypeError, ValueError):
            self.struct_sel = self._sec % ns
        u = 8 if self.genre in _SPACIOUS else 4
        st = _STRUCT[self.struct_sel]
        self._in = {r: st["in"][r] * u for r in st["in"]}
        bk = st["brk"]
        self._bk_every = max(4, bk["every"] * u)
        self._bk_len = bk["len"]
        self._bk_drop = bk["drop"]
        # never break until the whole arrangement is in + a bar of groove
        self._bk_start = max(self._in.values()) + max(4, u)
        self.base_on = dict(self.on)
        self._keys_lvl = _KEYS_LEVEL.get(self.genre, 1.0)   # per-genre chord level

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
            ld["level"] = lv * _LEAD_GLOBAL
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
        banks = _PROGRESSIONS.get(self.genre)
        if banks:
            prog = banks[getattr(self, "prog_sel", 0) % len(banks)]
        else:
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

    def _arr_on(self, role, b):
        """Is `role` allowed this bar (staggered entry + periodic breaks)?"""
        if b < self._in.get(role, 0):
            return False
        if b >= self._bk_start:
            pos = (b - self._bk_start) % self._bk_every
            if pos < self._bk_len and role in self._bk_drop:
                return False
        return True

    def _apply_arrangement(self, b):
        """Per-bar instrument gate = section base enables AND the
        arrangement (drums = kick/snare/hat as one group)."""
        base = self.base_on
        dr = self._arr_on("drums", b)
        self.on = {
            "kick":  base["kick"] and dr,
            "snare": base["snare"] and dr,
            "hat":   base["hat"] and dr,
            "bass":  base["bass"] and self._arr_on("bass", b),
            "lead":  base["lead"] and self._arr_on("lead", b),
            "keys":  base.get("keys", True) and self._arr_on("keys", b),
        }

    def _build(self) -> Phrase:
        b = self.bar
        self._apply_arrangement(b)
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
            ve = ve * _CH_GAIN.get(ch, 1.0)         # global mix: drums -10%, rest +10%
            (core if structural else orn).append(Note(t(st, vo), du, pi, ve, ch))

        getattr(self, f"_g_{self.genre}")(D, rnd, beat, sc, ctones, croot,
                                          nroot, e, fill, sparse)

        # soft sustained harmonic pad on the keys voice (energy-gated, not on
        # the spikier genres) — body without density, keeps the space.
        if self.on.get("keys", True) and self.genre not in ("neon_dub", "electro", "funk", "minneapolis_funk"):
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
        if not self.on.get("keys", True):
            return                                  # keys not in yet / break
        # voice-led top voicing on the KEYS voice (smooth chord motion, no
        # crowding the lead). Same hit count = harmony, not density.
        vc = self._voicelead(ctones, 48 + oct_shift)   # an octave lower
        if len(ctones) >= 4 and rnd.random() < 0.6:
            vc = vc + [vc[0] + 12]                       # colour tone on top
        for s in steps:
            if rnd.random() < 0.45 + 0.3 * self.energy:
                for p in vc:
                    D(s, beat * 0.26, p, (0.575 + rnd.uniform(-0.04, 0.07)) * self._keys_lvl, CH_KEYS)

    def _pad(self, D, rnd, beat, ctones):
        if not self.on.get("keys", True):
            return                                  # keys not in yet / break
        # ONE soft sustained voice-led chord under the bar (keys self-
        # terminates). Harmonic body without notes-per-beat — keeps the space.
        if rnd.random() < 0.45 + 0.35 * self.energy:
            for p in self._voicelead(ctones[:4], 52):       # octave lower
                D(0, beat * 3.4, p, (0.425 + rnd.uniform(-0.03, 0.05)) * self._keys_lvl, CH_KEYS)

    def _funk_comp(self, D, rnd, beat, ctones):
        # 70s funk keys comp (Bernie/Junie) with VARYING note lengths: a HELD
        # chord on the 'one' (loud -> rings long on keysFunk) + shorter
        # syncopated answer-stabs on the & of 2 and & of 4 + an occasional
        # ghost chank. keysFunk maps velocity->length, so loud=long, quiet=short.
        if not self.on.get("keys", True):
            return
        # drop the 9th/#9 tension tone — voiced low it formed a muddy/dissonant
        # cluster next to the root. A clean dom7 shell (root/3/5/b7) is clear.
        vc = self._voicelead(ctones[:4], 50)
        kl = self._keys_lvl
        if rnd.random() < 0.85:                              # the 'one' — held, rings
            for p in vc:
                D(0, beat * 1.2, p, (0.72 + rnd.uniform(-0.03, 0.05)) * kl, CH_KEYS)
        for s in (6, 14):                                    # & of 2 / & of 4 answer
            if rnd.random() < 0.6:
                for p in vc:
                    D(s, beat * 0.35, p, (0.54 + rnd.uniform(-0.04, 0.05)) * kl, CH_KEYS)
        if rnd.random() < 0.4:                               # syncopated ghost chank
            s = rnd.choice([3, 10, 11])
            for p in vc:
                D(s, beat * 0.2, p, (0.42 + rnd.uniform(-0.04, 0.04)) * kl, CH_KEYS)

    def _mpls_comp(self, D, rnd, beat, ctones):
        # Oberheim stabs with MIXED lengths: an occasional HELD chord (loud ->
        # rings long on keysOberheim) + the loved short off-beat STABS (quieter
        # -> short). Simple triad only.
        if not self.on.get("keys", True):
            return
        vc = self._voicelead(ctones[:3], 50)
        kl = self._keys_lvl
        # SAME velocity (= same volume) for all; LENGTH is set by note duration
        # (keysOberheim is gated). So a held chord + short stabs sit equal-loud.
        vel = 0.62 * kl
        if rnd.random() < 0.6:                               # a HELD chord (long du)
            for p in vc:
                D(0, beat * 1.5, p, vel + rnd.uniform(-0.03, 0.03), CH_KEYS)
        for s in (2, 6, 10, 14):                             # off-beat STABS (short du)
            if rnd.random() < 0.5 + (0.25 * self.energy):
                for p in vc:
                    D(s, beat * 0.18, p, vel + rnd.uniform(-0.03, 0.03), CH_KEYS)

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
        c0 = ctones[0] + 36                          # lead register (horn/vibe) — +1 octave
        # BEBOP: chromatic ladder so weak-beat passing tones are semitone
        # neighbours connecting chord-tone landings (chord tones still land
        # on strong beats via near(ct_oct[...]) below).
        ladder = list(range(c0 - 7, c0 + 18))
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
            if rnd.random() < 0.08:                          # rare 3rd below
                D(s, beat * 0.30 * du, pit - 3,
                  vel * 0.5, CH_LEAD)

    def _maybe_siren(self, D, rnd, beat, ct, cr):
        # Dub siren — fires at section start (bar 0) AND at each major
        # instrument drop-in moment within the song (when lead/bass/keys
        # structurally enter). Typically 2-3 sirens per song. NOT gated by
        # self.on["lead"] — siren IS the announcement, fires regardless.
        if not ct:
            return
        triggers = {0}
        for role in ("lead", "bass", "keys"):
            v = self._in.get(role)
            if v is not None and v > 0:
                triggers.add(v)
        if self.bar not in triggers:
            return
        pit = (ct[0] + 24) + rnd.choice([0, 5, 7, 12])
        dur = beat * 4.4
        D(0, dur, pit, 0.857 * _LEAD_GLOBAL, CH_LEAD)   # global lead trim applied

    def _chord_mode(self, ct, cr):
        # Infer a 7-degree mode for the CURRENT CHORD by reading its quality
        # from the chord-tone intervals. The melody's scale degrees (1..7+)
        # are then interpreted in this mode so the same melodic SHAPE works
        # against any chord (transposed to that chord's root + quality).
        if not ct:
            return [0, 2, 4, 5, 7, 9, 10]
        iv = {(p - cr) % 12 for p in ct}
        if 3 in iv and 6 in iv:
            return [0, 2, 3, 5, 6, 8, 10]   # locrian (half-dim)
        if 3 in iv:
            return [0, 2, 3, 5, 7, 8, 10]   # aeolian / natural minor
        if 4 in iv and 11 in iv:
            return [0, 2, 4, 5, 7, 9, 11]   # ionian / major
        if 4 in iv and 10 in iv:
            return [0, 2, 4, 5, 7, 9, 10]   # mixolydian (dom7)
        if 4 in iv:
            return [0, 2, 4, 5, 7, 9, 11]   # default major
        return [0, 2, 4, 5, 7, 9, 10]

    def _scale_deg_pit(self, deg, cr, mode, base_oct=24):
        # deg: 1..7 (with 8 = root+oct, 0 / negative supported). Mapped via
        # the chord's mode and offset from chord root + octave register.
        o, i = divmod(deg - 1, 7)
        return cr + mode[i] + 12 * o + base_oct

    def _scale_deg_pit_in_key(self, deg, sc, base_oct=24):
        # KEY-ANCHORED variant — pitch is computed from the SECTION'S scale
        # at the SECTION'S root, NOT from the current chord. Same actual
        # MIDI pitch for the same deg every emit. Chord progression moves
        # underneath; melody hits chord tones / color tones as it does.
        # deg = scale degree of the section. deg > 7 = octave up; deg < 1
        # = octave below (deg=-6 = tonic one octave below default reg,
        # i.e. bass-doubling register).
        scale = sorted({d % 12 for d in sc})[:7]
        while len(scale) < 7:
            scale.append((scale[-1] + 2) % 12)
        o, i = divmod(deg - 1, 7)
        # Anchor at MIDI ~C3 (36) + section root pitch class + base_oct (24).
        # Default (deg=1) lands at MIDI 60-ish = C4 area = lead register.
        return 36 + (self.root % 12) + scale[i] + 12 * o + base_oct

    # beat-aligned rhythmic CELLS (positions within one beat = 4 16th-steps).
    # Generating from these keeps every note ON THE GRID -> rhythmical, not a
    # random gap-walk. Mix of subdivisions incl. fast 32nd bursts.
    _SCR_CELLS = {
        "q":       [0.0],                                       # quarter
        "8":       [0.0, 2.0],                                  # two 8ths
        "8.":      [0.0, 1.5],                                  # dotted-8th + 16th
        "16":      [0.0, 1.0, 2.0, 3.0],                        # four 16ths
        "8_16":    [0.0, 2.0, 3.0],                             # 8th + two 16ths
        "16_8":    [0.0, 1.0, 2.0],                             # two 16ths + 8th
        "gallop":  [0.0, 1.5, 2.0],                             # gallop (long-short-)
        "rgallop": [0.0, 0.5, 2.0],                             # reverse gallop
        "burst":   [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],    # full 32nd scribble
        "hburst":  [0.0, 0.5, 1.0, 1.5],                        # 32nd burst, 1st half
        "hburst2": [2.0, 2.5, 3.0, 3.5],                        # 32nd burst, 2nd half
        "off":     [1.0, 2.0, 3.0],                             # off-start 16ths
        "off2":    [1.5, 2.5, 3.5],                             # syncopated offbeats
        "rest":    [],                                          # silent beat (groove space)
    }
    # per-genre groove anchors (16th-steps) — the scratch LOCKS to the snare.
    # (Mirrors the kick/snare positions in each _g_<genre> drum builder.)
    _SCR_GROOVE = {
        "uk_garage":       {"kick": [0, 10],    "snare": [4, 12]},
        "eighties_hiphop": {"kick": [0, 6, 10], "snare": [4, 12]},
        "boom_bap":        {"kick": [0, 6, 10], "snare": [4, 12]},
    }
    _SCR_NAMES   = ("16", "8", "8.", "8_16", "16_8", "gallop", "rgallop",
                    "burst", "hburst", "hburst2", "off", "off2", "q", "rest")
    # SPARSE/punchy: quarter + rest dominate (a few well-placed scratches +
    # space), 8ths next; multi-note cells rare; no 32nd burst. ~3-4 notes/bar.
    _SCR_WEIGHTS = (1,    14,  4,    2,      2,      3,        2,
                    0,      1,        0,         3,     1,      30,   26)

    def _scratch_bar(self, rnd, intensity=1.0):
        # one bar of scratch onsets (0..15) LOCKED TO THE BACKBEAT: hits land
        # ON the genre's snare positions and just around them ('e'/'a' grace),
        # so the scratch sits in the pocket with the drums. `intensity` scales
        # the grace + downbeat-anchor hits.
        snares = self._SCR_GROOVE.get(self.genre, {}).get("snare", [4, 12])
        onsets = []
        for sn in snares:
            onsets.append(float(sn))                          # the backbeat hit
            if rnd.random() < 0.45 * intensity:               # grace just around the snare
                onsets.append(sn + rnd.choice([-0.5, 0.5, 1.0]))
        if rnd.random() < 0.30 * intensity:                   # occasional downbeat anchor
            onsets.append(0.0)
        return sorted(set(round(o, 3) for o in onsets if 0.0 <= o < 16.0))

    def _scr_notes(self, rnd, onsets, end, word_at=None, bufslot=None):
        # turn onsets into (code, s, du, bufslot): du = gap to next onset;
        # gesture code = speed(0..3, slow-weighted) + dir*4, baked here so a
        # REPEATED pattern scratches identically. bufslot = which word buffer
        # this note scratches (None -> the phase's current word, set at emit).
        onsets = sorted(set(onsets))
        notes = []
        for i, s in enumerate(onsets):
            nxt = onsets[i + 1] if i + 1 < len(onsets) else end
            if word_at is not None and s < word_at <= nxt:
                nxt = word_at
            du     = max(0.5, min(4.0, round(nxt - s, 3)))
            divIdx = rnd.choices((0, 1, 2, 3), weights=(28, 38, 22, 12))[0]
            code   = divIdx + rnd.randint(0, 1) * 4
            notes.append((code, s, du, bufslot))
        if word_at is not None:
            notes.append((1, word_at, 10, bufslot))
        return notes

    def _scratch_pattern(self, rnd, kind="main", intensity=1.0, bufslot=None):
        # GENERATE a 2-bar scratch pattern (notes s in 0..31). "main" = pure
        # scratch (bar 2 often echoes bar 1) that gets REPEATED; "turn" =
        # scratch then the WORD plays out. `intensity` scales the density.
        bar1 = self._scratch_bar(rnd, intensity)
        if kind == "turn":
            # word in bar 2: usually beat 3 (s=24), seldom middle (s=20)
            word_at = 16.0 + rnd.choices([8.0, 4.0], weights=[75, 25])[0]
            b2 = [16.0 + o for o in self._scratch_bar(rnd, intensity) if 16.0 + o < word_at]
            return self._scr_notes(rnd, bar1 + b2, 32.0, word_at=word_at, bufslot=bufslot)
        bar2 = bar1 if rnd.random() < 0.6 else self._scratch_bar(rnd, intensity)
        return self._scr_notes(rnd, bar1 + [16.0 + o for o in bar2], 32.0, bufslot=bufslot)

    def _scratch_twoword(self, rnd, slot_a, slot_b, intensity=1.0):
        # 2-bar routine that scratches + PLAYS two words SEPARATELY: bar 1 =
        # scratch + play the word in buffer slot_a; bar 2 = scratch + play the
        # word in slot_b. Used when a phrase has >1 word, or to reveal both
        # teaser words in one routine.
        b1 = [o for o in self._scratch_bar(rnd, intensity) if o < 8.0]
        n1 = self._scr_notes(rnd, b1, 16.0, word_at=8.0, bufslot=slot_a)
        b2 = [16.0 + o for o in self._scratch_bar(rnd, intensity) if 16.0 + o < 24.0]
        n2 = self._scr_notes(rnd, b2, 32.0, word_at=24.0, bufslot=slot_b)
        return n1 + n2

    def _motif(self, D, rnd, beat, sc, ctones):
        # SCALE-DEGREE MELODIES — one melody locked per section, replayed
        # verbatim across emit-bars. Each motif tuple is (deg, s, du):
        # deg is a scale degree (1..7+) interpreted via the CURRENT CHORD's
        # mode, so the same melodic SHAPE follows the chord progression
        # underneath (user picked the chord-aware transpose option).
        # AABA across 4 emit-bars (A-A-A-B). Strict mono — no harmony
        # stacks, no overlapping note slots. Per-feel note length.
        if not ctones:
            return
        if self.genre == "jazz":
            self._jazz_motif(D, rnd, beat, sc, ctones)
            return
        bank = getattr(self, "_motif_bank", None) or ([self.motif] if self.motif else [])
        if not bank:
            return
        feel = _LEAD_FEEL.get(self.genre, "lyric")
        # Per-feel emit cadence + phrase-length: a phrase plays for
        # _PHRASE_LEN bars starting every _LEAD_EVERY bars. Bars
        # 0..phrase_len-1 of the group emit; phrase_len..every-1 are silent.
        every = _LEAD_EVERY.get(feel, 1)
        phrase_len = _PHRASE_LEN.get(feel, 1)
        bar_in_group = self.bar % every
        if bar_in_group >= phrase_len:
            return
        # Repetition: 7 A-phrases then 1 B variant (AAAAAAAB cycle = every 8
        # emitted phrases). Pure-locked A on the other 7 -> strong recurrence.
        # B picks from a dedicated FILL bank (more notes than the A motifs).
        phrase_idx = self.bar // every
        if feel == "scratch":
            # BUILD across the song: 4 phases that SCALE UP, monotonic (never
            # cycles back). Each phase = 16 bars.
            #   phase 0 : no scratches (intro)
            #   phase 1 : a SMALL scratch every 4th bar
            #   phase 2 : MORE scratch, still every 4th bar
            #   phase 3 : full density, every bar (the routine + word)
            phase = min(3, self.bar // 16)
            if phase == 0:
                return
            if getattr(self, "_scr_sec", None) != self._sec:
                sr = random.Random(self._sec * 97 + 41)
                # phase 1: a SINGLE small scratch. phase 2: a full one-bar
                # scratch. phase 3: 2-bar main + a two-word title reveal turn.
                self._scr_p1   = self._scr_notes(sr, [4.0], 16.0)   # single hit ON the backbeat
                self._scr_p2   = self._scr_notes(sr, self._scratch_bar(sr, 0.35), 16.0)
                self._scr_main = self._scratch_pattern(sr, "main", 0.45, bufslot=4)
                # turn = scratch+PLAY title word 1 (slot 4) then word 2 (slot 5)
                self._scr_turn = self._scratch_twoword(sr, 4, 5, 0.45)
                self._scr_sec  = self._sec
            # Each phase owns 2 word-buffer slots: phase p -> [(p-1)*2, +1]
            # (its phrase's two words). Teaser phases alternate the two words
            # across emissions; phase 3 main scratches title word 1.
            base = (phase - 1) * 2
            if phase < 3:
                # ONE bar per 4-bar group gets the scratch (bar "1" or "4").
                grp = self.bar // 4
                tgt = 3 if ((self._sec + grp) % 2) else 0
                if (self.bar % 4) != tgt:
                    return
                scr_slot = base + (grp % 2)     # alternate this phase's 2 words
                motif = self._scr_p1 if phase == 1 else self._scr_p2
                bar_in_group = 0                # 1-bar pattern emits this bar
            else:
                ph_i   = self.bar // every      # 2-bar phrase index
                within = ph_i % 4               # 0..3 -> AAAB w/ word turnaround
                motif  = self._scr_turn if within == 3 else self._scr_main
                scr_slot = 4                    # title word 1 (turn overrides per-note)
            use_b = False
        elif feel == "robotvox":
            # ELECTRO robot vocal: chant the phrase word-by-word ON THE BEAT,
            # repeating across the section. Words cycle through the loaded
            # buffer slots (0..vox_n-1). Build: silent intro, then half the
            # phrase, then the full phrase. Mechanical in-key carrier line.
            vox_n = max(1, min(6, getattr(self, "_vox_n", 4)))
            phase = self.bar // 12              # ~12-bar phases
            if phase == 0:
                return                          # intro: vocal enters after ~12 bars
            if getattr(self, "_vox_sec", None) != self._sec:
                degs  = [sc[0], sc[0], sc[min(4, len(sc) - 1)], sc[min(2, len(sc) - 1)],
                         sc[0], sc[min(4, len(sc) - 1)]]
                steps = [0, 8, 16, 24, 4, 20]   # one word per half-note over 2 bars
                self._vox_full = [(degs[i % len(degs)], steps[i], 2.0, i % vox_n)
                                  for i in range(min(vox_n, 6))]
                # sparser early phase: first two words, one per bar
                self._vox_half = [(degs[0], 0, 2.0, 0),
                                  (degs[1], 16, 2.0, 1 % vox_n)]
                self._vox_sec  = self._sec
            motif    = self._vox_half if phase == 1 else self._vox_full
            scr_slot = 0
            use_b    = False
        else:
            # Repetition: 7 A-phrases then 1 B variant (AAAAAAAB cycle = every
            # 8 emitted phrases). Pure-locked A on the other 7 -> recurrence.
            use_b = (phrase_idx % 8) == 7
            sec_rnd = random.Random(self._sec * 53 + len(self.genre))
            a_idx = sec_rnd.randrange(len(bank))
            if use_b:
                fill = _LEAD_FILL.get(feel)
                if fill:
                    b_idx = sec_rnd.randrange(len(fill))
                    motif = fill[b_idx]
                else:
                    b_idx = (a_idx + 1 + sec_rnd.randrange(max(1, len(bank) - 1))) % len(bank)
                    motif = bank[b_idx]
            else:
                motif = bank[a_idx]
        if not motif:
            return
        bar_p, note_p = _LEAD_REST.get(feel, (0.10, 0.18))
        kicks = set() if feel in ("hook", "scratch", "robotvox", "solo") else _KICK_STRONG.get(self.genre, set())
        lpush = _LEAD_PUSH.get(self.genre, 0.0)
        nlen = _LEAD_NLEN.get(feel, 0.20)
        boost = _LEAD_VEL_BOOST.get(feel, 1.0)
        rrr = random.Random(self._sec * 31 + self.bar * 7 + 11)
        if rrr.random() < bar_p:
            return
        nN = len(motif)
        for i, note in enumerate(motif):
            deg, s, du = note[0], note[1], note[2]
            nbuf = note[3] if len(note) > 3 else None     # per-note buffer slot (scratch)
            # Multi-bar phrase: s in 0..(16*phrase_len-1). Filter to current bar.
            if s // 16 != bar_in_group:
                continue
            local_s = s % 16
            if local_s in kicks and rrr.random() < 0.45:
                continue
            if rrr.random() < note_p:
                continue
            if feel == "scratch":
                # pitch encodes the WORD BUFFER SLOT (octave: slot 0..5 ->
                # +0/12/.../60) AND the gesture code 0..7 (mod 12, decoded by
                # the synth). Per-note bufslot wins (two-word reveal); else the
                # phase's current word slot. Repeats -> scratches identically.
                buf_slot = nbuf if nbuf is not None else scr_slot
                pit = 60 + buf_slot * 12 + int(deg)
                vel = 0.37 * _LEAD_GLOBAL          # scratch volume (+20%; level lever also up)
            elif feel == "robotvox":
                # octave = word buffer slot, pitch-class = sung carrier tone
                buf_slot = nbuf if nbuf is not None else scr_slot
                pit = 60 + buf_slot * 12 + int(deg)
                vel = 1.0 * _LEAD_GLOBAL           # robot vocal volume (electro lead)
            else:
                d = deg
                if use_b and i == nN - 1:                     # B-phrase resolves to root
                    d = 1
                # KEY-ANCHORED pitch — same MIDI note for same deg every emit
                pit = self._scale_deg_pit_in_key(d, sc, 36) + 12 * _LEAD_OCT.get(self.genre, 0)
                mid = nN / 2.0
                d2p = 1.0 - abs(i - mid) / max(1.0, nN - 1)
                vel = 0.46 + 0.18 * d2p + (0.05 if local_s % 4 == 0 else 0.0) + rnd.uniform(-0.03, 0.04)
                if use_b and i >= nN - 2:
                    vel -= 0.05
                vel *= boost * _LEAD_GLOBAL
                vel = max(0.22 * _LEAD_GLOBAL, min(0.95, vel))
            if feel == "scratch":
                # Align the scratch's micro-timing to the DRUM it locks to:
                # a snare-position hit uses the "snare" voice (same sdrag), a
                # kick-position hit the "kick" voice (same kpush) -> it lands
                # EXACTLY with the drum, not just near it. No lead lpush.
                g = self._SCR_GROOVE.get(self.genre, {})
                scr_vo = ("snare" if local_s in g.get("snare", [])
                          else "kick" if local_s in g.get("kick", []) else "")
                D(local_s, beat * nlen * du, pit, vel, CH_LEAD, scr_vo)
            elif feel == "robotvox":
                D(local_s, beat * nlen * du, pit, vel, CH_LEAD)   # on the grid, mechanical
            else:
                D(local_s + lpush, beat * nlen * du, pit, vel, CH_LEAD)

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
        if self.on.get("keys", True):
            # Bernie/Junie warm analog comp — held 'one' + funk answer-stabs,
            # with VARYING note lengths (velocity->length on keysFunk).
            self._funk_comp(D, rnd, beat, ct)
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)              # Moog SOLO (feel=solo)

    def _g_jazz(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        if self.on["hat"]:
            # swung "spang-a-lang" ride — soft bed under the kit; the
            # accents on the beat, the skip notes quiet (no extra bell hit
            # — that hammered the old cowbell tone).
            for s in (0, 4, 6, 8, 12, 14):
                on_beat = s in (0, 4, 8, 12)
                D(s, 0.5, RIDE,
                  (self._main(rnd) * 0.55) if on_beat else (self._ghost(rnd) + 0.04),
                  CH_DRUMS, "hat")
            if rnd.random() < 0.28:
                D(10, 0.16, OHAT, 0.34, CH_DRUMS, "hat")
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
        # Prince / LinnDrum: punchy SYNCOPATED kick, BIG gated snare LAYERED
        # with a clap on the backbeat, crisp machine 16th hats + open hat, a
        # little tambourine sizzle. Bright Oberheim stabs + syncopated synth bass.
        if self.on["kick"]:
            D(0, 0.2, KICK, self._acc(rnd), CH_DRUMS, "kick", True)         # the boom
            if rnd.random() < 0.55 + 0.3 * e:
                D(10, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick", True)  # & of 3
            if rnd.random() < 0.35 + 0.3 * e:
                D(6, 0.18, KICK, self._main(rnd), CH_DRUMS, "kick")         # & of 2
            if rnd.random() < 0.2:
                D(3, 0.16, KICK, self._main(rnd) * 0.85, CH_DRUMS, "kick")  # e-of-1 push
        if self.on["snare"]:
            for s in (4, 12):                                # gated snare + CLAP (Prince/Linn)
                D(s, 0.22, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
                D(s, 0.2, CLAP, 0.82, CH_DRUMS, "snare")
            self._ghost_sn(D, rnd, e * 0.5)
            if fill:                                         # machine tom-ish fill
                for s in (13, 14, 15):
                    D(s, 0.08, SNARE, 0.55 + 0.06 * s, CH_DRUMS, "snare")
        if self.on["hat"]:
            for s in range(16):                              # crisp machine 16ths
                if rnd.random() < 0.85:
                    v = (self._main(rnd) if (s % 4 == 0)
                         else self._ghost(rnd) + (0.1 if s % 2 == 0 else 0.0))
                    D(s, 0.04, HAT, v * 0.85, CH_DRUMS, "hat")
            if rnd.random() < 0.4:
                D(rnd.choice([6, 14]), 0.16, OHAT, 0.4, CH_DRUMS, "hat")
            for s in (2, 10):                                # tambourine sizzle (LinnDrum)
                if rnd.random() < 0.3:
                    D(s, 0.05, PERC, self._ghost(rnd) * 0.8, CH_DRUMS)
        if self.on["bass"]:                                  # syncopated synth-bass
            self._funk_bass(D, rnd, beat, ct, cr, nr, e, [2, 3, 6, 10, 11, 14])
        if self.on.get("keys", True):
            self._mpls_comp(D, rnd, beat, ct)                # Oberheim stabs, mixed lengths
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)                # Moog hook (feel=mplslead)

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
            if rnd.random() < 0.45:                            # faint pad
                self._pad(D, rnd, beat, ct)
            self._motif(D, rnd, beat, sc, ct)                  # hypno-feel melody

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
        if not self.on.get("keys", True):
            return                                  # keys not in yet / break
        # off-beat reggae/dub organ chord skank on the KEYS voice
        for s in steps:
            if rnd.random() < prob:
                for p in self._voicelead(ct[:3], 48):       # octave lower
                    D(s, beat * 0.18, p, (0.55 + rnd.uniform(-0.04, 0.05)) * self._keys_lvl, CH_KEYS)

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
        self._maybe_siren(D, rnd, beat, ct, cr)

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
        self._maybe_siren(D, rnd, beat, ct, cr)

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
                    D(s, beat * 0.4, p, 0.49 + rnd.uniform(-0.03, 0.05), CH_KEYS)
            if rnd.random() < 0.5:
                self._pad(D, rnd, beat, ct)
        self._maybe_siren(D, rnd, beat, ct, cr)

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
        self._maybe_siren(D, rnd, beat, ct, cr)

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
            for s in (7, 9):                                               # 606 snare — a real hit, not a ghost
                D(s, 0.06, RIM, self._acc(rnd), CH_DRUMS, "snare", True)
            if self.bar % 2 == 1:                                          # 2-bar end fill
                for s in (14, 15):
                    D(s, 0.05, RIM, self._main(rnd), CH_DRUMS, "snare")
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
            self._motif(D, rnd, beat, sc, ct)              # scratch (always)

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
            self._motif(D, rnd, beat, sc, ct)                  # stab-feel melody

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
        # afrobeats: 3 transcribed kick/snare variations, rotating every
        # 4-bar phrase. Shaker 16ths + fixed log-drum + clap on the snare
        # keep the locked afro feel; bass locks to the core.
        kp, sp = (
            ((0, 3, 10), (6, 12)),       # pattern 01
            ((0, 5, 10), (3, 12)),       # pattern 02
            ((0, 3),     (6, 9, 12)),    # pattern 03 — sparse kick, busy snare
        )[(self.bar // 4) % 3]
        if self.on["kick"]:
            for s in kp:
                D(s, 0.2, KICK, self._acc(rnd) if s == 0 else self._main(rnd),
                  CH_DRUMS, "kick", True)
        if self.on["snare"]:
            for s in sp:
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
        if self.on["lead"]:                                    # hazy chords + pad + sung lead
            self._comp(D, rnd, beat, ct, [6], oct_shift=0)
            self._pad(D, rnd, beat, ct)
            self._motif(D, rnd, beat, sc, ct)                  # lyric-feel melody

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
        if self.on["lead"]:
            if rnd.random() < 0.5:
                self._comp(D, rnd, beat, ct, [10])
            self._motif(D, rnd, beat, sc, ct)                  # stab-feel melody

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
        self._maybe_siren(D, rnd, beat, ct, cr)

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
        if self.on.get("keys", True):
            # electro: a driving 16th-note ARP up through the chord tones,
            # wrapping two octaves (soft digital synth, quiet). Recurs per bar.
            tones = self._voicelead(ct, 48)
            if tones:
                ext = tones + [t + 12 for t in tones]      # two octaves
                for s in range(0, 16):                     # 16th notes
                    if rnd.random() < 0.92:
                        p = ext[s % len(ext)]
                        vel = (0.5 + (0.06 if s % 4 == 0 else 0.0)) * self._keys_lvl
                        D(s, beat * 0.22, p, vel, CH_KEYS)

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
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)              # scratch (always)

    def _g_boom_bap(self, D, rnd, beat, sc, ct, cr, nr, e, fill, sparse):
        # golden-age boom-bap (Premier / Pete Rock / Large Pro). NOT a 1-bar
        # loop — it breathes over a 2-BAR phrase: bar A states the groove,
        # bar B answers with a shifted syncopation + a 16th DOUBLE-kick (the
        # "b-boom") and a pickup into the turnaround. The backbeat snare on
        # 2 & 4 is the only fixed anchor; the kick dances around it. Dusty
        # ghost snares + a 4-bar turnaround give the human, sampled feel.
        # Heavy MPC swing + snare drag come from PROFILE.
        barB = (self.bar % 2 == 1)            # answer bar
        turn = (self.bar % 4 == 3) or fill    # 4-bar turnaround
        if self.on["snare"]:
            for s in (4, 12):                                              # the BAP — fat, layered (anchor)
                D(s, 0.26, SNARE, self._acc(rnd), CH_DRUMS, "snare", True)
                D(s, 0.24, CLAP, 0.78, CH_DRUMS, "snare")
            # dusty ghost snares — the texture between the backbeats
            for s, p in ((3, 0.3), (10, 0.25), (15, 0.45 if barB else 0.2)):
                if rnd.random() < p:
                    D(s, 0.10, SNARE, self._ghost(rnd), CH_DRUMS, "snare")
            if turn:                                                       # snare-roll turnaround
                for s in (13, 14, 15):
                    D(s, 0.08, SNARE, 0.55 + 0.07 * s, CH_DRUMS, "snare")
        if self.on["kick"]:
            D(0, 0.36, KICK, 1.0, CH_DRUMS, "kick", True)                  # the BOOM (1)
            if not barB:
                # CALL bar — classic "boom ... boom" with an & of 2 push
                D(10, 0.32, KICK, self._acc(rnd), CH_DRUMS, "kick", True)  # & of 3
                if rnd.random() < 0.6:
                    D(6, 0.28, KICK, self._main(rnd), CH_DRUMS, "kick")    # a of 2
            else:
                # ANSWER bar — shifted, syncopated, with the 16th double-kick
                D(7, 0.28, KICK, self._main(rnd), CH_DRUMS, "kick")        # a of 2
                D(10, 0.30, KICK, self._acc(rnd), CH_DRUMS, "kick", True)  # & of 3
                D(11, 0.24, KICK, self._main(rnd) * 0.85, CH_DRUMS, "kick")  # the b-BOOM (double)
                if not turn and rnd.random() < 0.55:
                    D(14, 0.26, KICK, self._main(rnd) * 0.8, CH_DRUMS, "kick")  # pickup into next bar
        if self.on["hat"]:
            for s in range(0, 16, 2):                                      # swung dusty 8ths, dynamic
                if rnd.random() < 0.82:
                    D(s, 0.05, HAT, self._main(rnd) if s % 4 == 0 else self._ghost(rnd),
                      CH_DRUMS, "hat")
            if rnd.random() < 0.3:                                         # 16th roll lick
                r = rnd.choice([6, 7, 14])
                D(r, 0.04, HAT, self._ghost(rnd), CH_DRUMS, "hat")
                D(r + 1, 0.04, HAT, self._ghost(rnd), CH_DRUMS, "hat")
            if rnd.random() < 0.28:
                D(rnd.choice([6, 14]), 0.2, OHAT, 0.42, CH_DRUMS, "hat")
        if self.on["bass"]:                                                # sampled-soul, walks
            D(0, beat * 0.9, cr, self._acc(rnd), CH_BASS, "kick", structural=True)
            for s in (6, 10, 14):
                if rnd.random() < 0.45 + 0.3 * e:
                    D(s, beat * 0.45, cr + rnd.choice([0, 0, 7, 12, -5]),
                      self._main(rnd), CH_BASS)
        if self.on["lead"]:
            self._motif(D, rnd, beat, sc, ct)              # scratch (always)
