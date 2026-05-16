"""scribe — LLM author of the demoscene SCROLLER text.

Watches what's currently playing (polls the bridge /state), and whenever the
genre/mood changes (debounced) asks the local Qwen for a long, moody,
Amiga-demoscene-flavoured scroll that's woven around the current music, then
POSTs it to the bridge /scroll. Decoupled from the director/audition so it
works whatever is driving the sections. Never crashes the stream.

Env: BRIDGE_HTTP_PORT (8080), STR_DIRECTOR_MODEL.
"""
from __future__ import annotations

import os
import re
import time

import requests

PORT = os.environ.get("BRIDGE_HTTP_PORT", "8080")
STATE_URL = f"http://localhost:{PORT}/state"
SCROLL_URL = f"http://localhost:{PORT}/scroll"
MODEL_ID = os.environ.get("STR_DIRECTOR_MODEL", "mlx-community/Qwen3-8B-4bit")
COOLDOWN = 38.0  # min seconds between regenerations

SYS = (
    "You write classic AMIGA DEMOSCENE SCROLLER text — the long hypnotic "
    "message that sine-waves across the screen. Style: moody, nocturnal, "
    "neon/chrome/void imagery, scene clichés woven in (greetings to the "
    "sceners, respect, stay tuned, the vibe, keep the faith, signing off into "
    "the night), ALL ONE FLOWING LINE, no line breaks, no quotes, no markdown, "
    "no preamble. 60-110 words. It must FEEL like the music."
)


def _fallback(genre, mood, key):
    g = (genre or "the groove").replace("_", " ")
    m = mood or "midnight"
    return (
        f"... welcome back to the endless stream ... tonight the machine "
        f"dreams in {g} ... a {m} haze over chrome and static ... greetings "
        f"to all the sceners still awake in the blue glow ... respect to the "
        f"ones who never sleep ... the bassline walks through {key or 'minor'} "
        f"shadows while the pixels breathe ... stay tuned, keep the faith, let "
        f"it ride ... we are signing off into the neon void ... and back "
        f"around again ............ "
    )


def _clean(txt: str) -> str:
    txt = re.split(r"</?think>", txt)[-1]
    txt = txt.strip().strip('"').strip("'")
    txt = re.sub(r"\s+", " ", txt.replace("\n", " "))
    return txt[:600]


def main():
    model = tok = gen = None
    sampler = None
    try:
        from mlx_lm import generate as _gen, load
        from mlx_lm.sample_utils import make_sampler
        print(f"[scribe] loading {MODEL_ID} …")
        model, tok = load(MODEL_ID)
        gen = _gen
        sampler = make_sampler(temp=0.95, top_p=0.95)
        print("[scribe] model ready")
    except Exception as e:  # noqa: BLE001
        print(f"[scribe] LLM unavailable ({e}); using templated fallbacks")

    last_key = None
    last_gen = 0.0
    while True:
        try:
            snap = requests.get(STATE_URL, timeout=3).json()
            sec = snap.get("section") or {}
            genre = sec.get("genre", "")
            mood = sec.get("mood", "")
            key = sec.get("key", "")
            sig = (genre, mood)
            now = time.time()
            if sig != last_key and (now - last_gen) > COOLDOWN and any(sig):
                text = None
                if model is not None:
                    try:
                        msgs = [
                            {"role": "system", "content": SYS},
                            {"role": "user", "content":
                                f"Music now: genre={genre or 'unknown'}, "
                                f"mood={mood or 'nocturnal'}, key={key or 'minor'}. "
                                f"Write the scroller."},
                        ]
                        try:
                            prompt = tok.apply_chat_template(
                                msgs, add_generation_prompt=True,
                                enable_thinking=False)
                        except TypeError:
                            prompt = tok.apply_chat_template(
                                msgs, add_generation_prompt=True)
                        out = gen(model, tok, prompt=prompt, max_tokens=320,
                                  sampler=sampler, verbose=False)
                        text = _clean(out)
                    except Exception as e:  # noqa: BLE001
                        print(f"[scribe] gen failed: {e}")
                if not text or len(text) < 60:
                    text = _fallback(genre, mood, key)
                try:
                    requests.post(SCROLL_URL, json={"text": text}, timeout=3)
                    print(f"[scribe] scroll updated for {genre}/{mood} "
                          f"({len(text)} chars)")
                except requests.RequestException as e:
                    print(f"[scribe] post failed: {e}")
                last_key = sig
                last_gen = now
        except requests.RequestException:
            pass  # bridge not up yet
        except Exception as e:  # noqa: BLE001
            print(f"[scribe] loop error: {e}")
        time.sleep(4)


if __name__ == "__main__":
    main()
