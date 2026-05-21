"""Kokoro TTS — renders the song title (or a word) to a wav so the scratch
lead samples REAL speech instead of the procedural vowel. ONNX runtime
(kokoro-onnx), fully local once the model files are present. Falls back
silently (returns False) if the model/deps are missing — the SC boot keeps
its procedural 'ahh' buffer in that case.
"""
from __future__ import annotations

import os
import threading

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ROOT   = os.path.dirname(_HERE)
_MODEL  = os.path.join(_ROOT, "models", "kokoro", "kokoro-v1.0.onnx")
_VOICES = os.path.join(_ROOT, "models", "kokoro", "voices-v1.0.bin")
_VOICE  = os.environ.get("STR_TTS_VOICE", "af_heart")

_kokoro = None
_lock   = threading.Lock()


def available() -> bool:
    return os.path.exists(_MODEL) and os.path.exists(_VOICES)


def _get():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(_MODEL, _VOICES)
    return _kokoro


def render(text: str, path: str) -> bool:
    """Render `text` to a wav at `path`. Returns True on success."""
    text = (text or "").strip()
    if not text or not available():
        return False
    try:
        import soundfile as sf
        with _lock:
            k = _get()
            samples, sr = k.create(text, voice=_VOICE, speed=1.0, lang="en-us")
        sf.write(path, samples, sr)
        return True
    except Exception as e:                       # noqa: BLE001 — never crash the director
        print(f"[tts] render failed: {e}")
        return False
