"""Audition every genre on demand — no LLM, no waiting. Publishes each genre
through the real publish path (groove engine + genre synth params + visuals)
for N seconds, looping. Run the director separately for autonomous behaviour.

  python scripts/smoke/genre_audition.py [secs_per_genre]   # default 25
"""
import sys
import time

from director.schema import SectionState
from director.publish import publish

SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0

GENRES = [
    ("electro_funk", 104, "G minor", 0.74, {"bg": "#140a16", "fg": "#f3d9a6",
        "accent": ["#ff5e7a", "#36e6c8", "#ffd166"]}),
    ("broken_house", 124, "A minor", 0.7, {"bg": "#0a1014", "fg": "#dfeaf2",
        "accent": ["#5ad1ff", "#ffae57", "#b988ff"]}),
    ("synthwave", 112, "E minor", 0.68, {"bg": "#150a22", "fg": "#ffe1f0",
        "accent": ["#ff43c8", "#43d9ff", "#ffd23f"]}),
    ("neon_dub", 84, "D minor", 0.42, {"bg": "#06121a", "fg": "#bfeaf0",
        "accent": ["#2ad6c0", "#7a6cff"]}),
    ("lofi", 78, "F# minor", 0.45, {"bg": "#100d0a", "fg": "#e6d6c0",
        "accent": ["#c8a06a", "#7a9e8a"]}),
    ("electro", 122, "C minor", 0.7, {"bg": "#04101a", "fg": "#cfeaff",
        "accent": ["#19e0ff", "#ff3df0", "#f8ff4d"]}),
    ("eighties_hiphop", 104, "G minor", 0.55, {"bg": "#16100a", "fg": "#ffe7c2",
        "accent": ["#ff8a3d", "#ffd23f", "#5ad1ff"]}),
    ("jazz", 132, "D minor", 0.5, {"bg": "#0a0c14", "fg": "#e8e0d0",
        "accent": ["#d4a25a", "#7a9ec8", "#c86a6a"]}),
    ("funk", 104, "E minor", 0.7, {"bg": "#140c04", "fg": "#ffe2b0",
        "accent": ["#ff6a2d", "#ffcf3f", "#3dd6c8"]}),
    ("minneapolis_funk", 114, "A minor", 0.65, {"bg": "#16061a", "fg": "#ffd6f5",
        "accent": ["#ff3df0", "#5af0ff", "#ffe14d"]}),
    ("minimal_techno", 127, "C minor", 0.42, {"bg": "#05080a", "fg": "#cdd6da",
        "accent": ["#5fb0c0", "#7a8a90", "#d0e0e0"]}),
    ("detroit_techno", 128, "F minor", 0.6, {"bg": "#0a0814", "fg": "#dfe0ff",
        "accent": ["#6c7bff", "#36d6c8", "#ffb35a"]}),
    ("dub", 76, "A minor", 0.4, {"bg": "#04100a", "fg": "#cfe8d6",
        "accent": ["#2ad67a", "#ffcf3f", "#ff6a4d"]}),
    ("steppers_dub", 80, "D minor", 0.5, {"bg": "#06120c", "fg": "#d6f0dc",
        "accent": ["#3ad68a", "#ffd23f", "#5ad1ff"]}),
    ("dub_techno", 122, "C minor", 0.42, {"bg": "#06100f", "fg": "#cfe0e0",
        "accent": ["#3ab0b8", "#7a8a90", "#d0e8e8"]}),
    ("roots_reggae", 78, "G minor", 0.5, {"bg": "#0a1006", "fg": "#e6f0c8",
        "accent": ["#ffd23f", "#3ad65a", "#ff5a4d"]}),
    ("uk_garage", 131, "E minor", 0.62, {"bg": "#100a16", "fg": "#e8d6ff",
        "accent": ["#b06cff", "#36e6c8", "#ffd23f"]}),
    ("dub_garage", 130, "F minor", 0.5, {"bg": "#0a0a16", "fg": "#d6dcf0",
        "accent": ["#6c7bff", "#3ad6b0", "#ffb35a"]}),
    ("rnb", 84, "D minor", 0.5, {"bg": "#140a12", "fg": "#f0d8e4",
        "accent": ["#e08ab0", "#7ab0c8", "#ffce6a"]}),
    ("afro_rnb", 108, "A minor", 0.6, {"bg": "#140e06", "fg": "#ffe8c8",
        "accent": ["#ff9b3d", "#3ad69e", "#ffd23f"]}),
    ("indie_rnb", 78, "C minor", 0.4, {"bg": "#0c0a14", "fg": "#dcd6ec",
        "accent": ["#8c7ad0", "#5ac8d6", "#e0a0c0"]}),
]


def main():
    print(f"[audition] {len(GENRES)} genres x {SECS:.0f}s, looping. Ctrl-C to stop.")
    i = 0
    while True:
        name, bpm, key, dens, pal = GENRES[i % len(GENRES)]
        s = SectionState(
            id=f"audition_{name}",
            duration_sec=300,
            mood=f"audition {name}",
            genre=name,
            bpm=bpm,
            key=key,
            density=dens,
            palette={**pal, "transition_sec": 3},
            visuals={"scene": "raycaster", "font_size_px": 13,
                     "glyph_set": "ascii_punct",
                     "motion": {"pacing": "active", "impulse_decay": 0.4, "trail": 0.2},
                     "text_strings": [name.replace("_", " "), key.lower()]},
        )
        publish(s)
        print(f"[audition] >>> {name}  {bpm}bpm {key}  density {dens}")
        time.sleep(SECS)
        i += 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[audition] stopped")
