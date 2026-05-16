"""Publish hardcoded SectionStates (no LLM) to exercise the full publish path.

  python scripts/smoke/fake-section.py              # publish 1 (dark/slow)
  python scripts/smoke/fake-section.py bright        # publish 1 (bright/active)
  python scripts/smoke/fake-section.py cycle 4 8     # alternate every 8s, 4 times
"""
import sys
import time

from director.schema import SectionState
from director.publish import publish

DARK = SectionState(
    id="fake_dark",
    duration_sec=30,
    mood="rainy_dusk",
    bpm=72,
    key="F# minor",
    density=0.45,
    instruments={
        "kick": {"amp": 0.9, "fmIndex": 3.0, "decay": 0.4},
        "snare": {"amp": 0.5, "tone": 0.3},
        "hat": {"amp": 0.4, "cutoff": 6000, "decay": 0.05},
        "bass": {"amp": 0.8, "cutoff": 420, "res": 0.25},
        "lead": {"amp": 0.45, "fmRatio": 2.0, "fmIndex": 0.8, "wave": 0.2},
    },
    fx={"reverb": 0.45, "delay": 0.3, "delayTime": 0.5},
    palette={"bg": "#0a0c11", "fg": "#9fb0c8",
             "accent": ["#5a78c8", "#6f9e8a"], "transition_sec": 8},
    visuals={"font_size_px": 18, "glyph_set": "abstract_blocks",
             "motion": {"pacing": "slow_drift", "impulse_decay": 0.6, "trail": 0.25},
             "text_strings": ["a quiet station", "between two thoughts"]},
)

BRIGHT = SectionState(
    id="fake_bright",
    duration_sec=30,
    mood="neon_noon",
    bpm=84,
    key="A minor",
    density=0.7,
    instruments={
        "kick": {"amp": 0.95, "fmIndex": 4.5, "decay": 0.3},
        "snare": {"amp": 0.65, "tone": 0.55},
        "hat": {"amp": 0.55, "cutoff": 10500, "decay": 0.04},
        "bass": {"amp": 0.7, "cutoff": 900, "res": 0.4, "detune": 0.1},
        "lead": {"amp": 0.55, "fmRatio": 3.01, "fmIndex": 1.8, "wave": 0.6},
    },
    fx={"reverb": 0.25, "delay": 0.18, "delayTime": 0.28},
    palette={"bg": "#10131a", "fg": "#dfe6f0",
             "accent": ["#e0af68", "#9ece6a", "#7aa2f7"], "transition_sec": 6},
    visuals={"font_size_px": 16, "glyph_set": "mixed_unicode",
             "motion": {"pacing": "active", "impulse_decay": 0.35, "trail": 0.12},
             "text_strings": ["full daylight", "everything at once", "—— —— ——"]},
)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "dark"
    if arg == "cycle":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        gap = float(sys.argv[3]) if len(sys.argv) > 3 else 8
        for i in range(n):
            publish(DARK if i % 2 == 0 else BRIGHT)
            time.sleep(gap)
    else:
        publish(BRIGHT if arg == "bright" else DARK)


if __name__ == "__main__":
    main()
