"""SectionState schema. Out-of-range numbers are CLAMPED (not rejected) so a
bad director output degrades gracefully instead of silencing the stream.
"""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

GLYPH_SETS = ("abstract_blocks", "ascii_punct", "mixed_unicode", "text_heavy")
PACINGS = ("still", "slow_drift", "active", "fast")
GENRES = ("electro_funk", "synthwave", "neon_dub", "broken_house",
          "lofi", "electro", "eighties_hiphop", "jazz", "funk",
          "minneapolis_funk", "minimal_techno", "detroit_techno",
          "dub", "steppers_dub", "dub_techno", "roots_reggae",
          "dub_garage", "uk_garage", "boom_bap",
          "rnb", "afro_rnb", "indie_rnb")
SCENES = ("raycaster", "glyphfield")
# vocal words the scratch lead can sample (synthesized formant recipes in
# router.scd ~scratchWords). Vowels/glides sound cleanest; consonant words
# (fresh/go/funk) are more synthetic but add DJ vocabulary.
SCRATCH_WORDS = ("ahh", "ohh", "eee", "uh", "yeah", "wow", "hey",
                 "fresh", "go", "funk")
# English Kokoro voices the scratch can use (af/am = US f/m, bf/bm = UK f/m)
SCRATCH_VOICES = (
    "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore",
    "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael",
    "am_onyx", "am_puck",
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis")
SCRATCH_ARTIC = ("soft", "neutral", "aggressive")


def _clamp(v, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, v))


class _Clamped(BaseModel):
    """Base that clamps every float/int field to its (ge, le) metadata."""

    @field_validator("*", mode="before")
    @classmethod
    def _clamp_numbers(cls, v, info):
        f = cls.model_fields.get(info.field_name)
        if f is None:
            return v
        lo = hi = None
        for m in f.metadata:
            lo = getattr(m, "ge", lo) if hasattr(m, "ge") else lo
            hi = getattr(m, "le", hi) if hasattr(m, "le") else hi
        if lo is not None and hi is not None and isinstance(v, (int, float)):
            return _clamp(v, lo, hi)
        return v


class Kick(_Clamped):
    enabled: bool = True
    amp: float = Field(0.9, ge=0.0, le=1.0)
    fmRatio: float = Field(1.0, ge=0.5, le=3.0)
    fmIndex: float = Field(3.2, ge=0.0, le=8.0)
    decay: float = Field(0.35, ge=0.1, le=0.8)


class Snare(_Clamped):
    enabled: bool = True
    amp: float = Field(0.6, ge=0.0, le=1.0)
    tone: float = Field(0.4, ge=0.0, le=1.0)
    decay: float = Field(0.18, ge=0.05, le=0.5)


class Hat(_Clamped):
    enabled: bool = True
    amp: float = Field(0.5, ge=0.0, le=1.0)
    cutoff: float = Field(7800, ge=3000, le=14000)
    decay: float = Field(0.06, ge=0.02, le=0.25)


class Bass(_Clamped):
    enabled: bool = True
    amp: float = Field(0.75, ge=0.0, le=1.0)
    cutoff: float = Field(600, ge=80, le=2000)
    res: float = Field(0.2, ge=0.0, le=0.9)
    detune: float = Field(0.06, ge=0.0, le=0.2)
    decay: float = Field(0.6, ge=0.1, le=1.5)


class Lead(_Clamped):
    enabled: bool = True
    amp: float = Field(0.5, ge=0.0, le=1.0)
    fmRatio: float = Field(2.01, ge=0.5, le=4.0)
    fmIndex: float = Field(1.1, ge=0.0, le=4.0)
    wave: float = Field(0.3, ge=0.0, le=1.0)
    decay: float = Field(0.5, ge=0.1, le=1.5)


class Instruments(BaseModel):
    kick: Kick = Kick()
    snare: Snare = Snare()
    hat: Hat = Hat()
    bass: Bass = Bass()
    lead: Lead = Lead()


class Fx(_Clamped):
    reverb: float = Field(0.35, ge=0.0, le=0.9)
    delay: float = Field(0.22, ge=0.0, le=0.7)
    delayTime: float = Field(0.375, ge=0.05, le=0.75)


class Palette(BaseModel):
    bg: str = "#0b0d12"
    fg: str = "#c9d2e3"
    accent: List[str] = Field(default_factory=lambda: ["#7aa2f7", "#9ece6a", "#e0af68"])
    transition_sec: float = Field(12, ge=1, le=60)

    @field_validator("bg", "fg")
    @classmethod
    def _hex_ok(cls, v):
        v = str(v).strip()
        if not v.startswith("#") or len(v) not in (4, 7):
            return "#101418"
        return v

    @field_validator("accent")
    @classmethod
    def _accent_ok(cls, v):
        v = [c for c in (v or []) if isinstance(c, str) and c.startswith("#")]
        return v or ["#7aa2f7", "#9ece6a", "#e0af68"]


class Motion(_Clamped):
    pacing: Literal["still", "slow_drift", "active", "fast"] = "slow_drift"
    impulse_decay: float = Field(0.45, ge=0.0, le=1.0)
    trail: float = Field(0.18, ge=0.0, le=1.0)

    @field_validator("pacing", mode="before")
    @classmethod
    def _pacing_ok(cls, v):
        return v if v in PACINGS else "slow_drift"


class Visuals(_Clamped):
    scene: Literal["raycaster", "glyphfield"] = "raycaster"
    font_size_px: int = Field(15, ge=8, le=48)
    glyph_set: Literal["abstract_blocks", "ascii_punct", "mixed_unicode", "text_heavy"] = "abstract_blocks"
    motion: Motion = Motion()
    text_strings: List[str] = Field(default_factory=list)

    @field_validator("scene", mode="before")
    @classmethod
    def _scene_ok(cls, v):
        return v if v in SCENES else "raycaster"

    @field_validator("glyph_set", mode="before")
    @classmethod
    def _glyph_ok(cls, v):
        return v if v in GLYPH_SETS else "abstract_blocks"

    @field_validator("text_strings")
    @classmethod
    def _strings_ok(cls, v):
        v = [str(s)[:64] for s in (v or []) if str(s).strip()]
        return v[:6]


class SectionState(_Clamped):
    id: str = "sec"
    duration_sec: int = Field(360, ge=20, le=600)
    mood: str = "neutral"
    genre: Literal["electro_funk", "synthwave", "neon_dub", "broken_house",
                   "lofi", "electro", "eighties_hiphop", "jazz", "funk",
                   "minneapolis_funk", "minimal_techno", "detroit_techno",
                   "dub", "steppers_dub", "dub_techno", "roots_reggae",
                   "dub_garage", "uk_garage", "boom_bap",
                   "rnb", "afro_rnb", "indie_rnb"] = "funk"
    bpm: int = Field(96, ge=70, le=150)
    key: str = "C minor"
    density: float = Field(0.6, ge=0.0, le=1.0)
    # composition choice: which of the genre's 4 researched chord
    # progressions to use (0=signature .. 3=alt/turnaround)
    harmony: int = Field(0, ge=0, le=3)
    # arrangement archetype: how instruments enter (staggered) + breaks
    # (0=classic build, 1=quick, 2=long/spacious, 3=DJ-tool/minimal)
    structure: int = Field(0, ge=0, le=3)
    # a short evocative track title — drives the HUD + text visuals
    name: str = "untitled"
    # the vocal word the scratch lead samples this section (uk_garage +
    # eighties_hiphop). Re-renders the scratch buffer on section change.
    scratch_word: str = "ahh"
    # DJ scratch build (TTS, scratch genres): two punchy standalone words for
    # the first two build phases, + a two-word version of the title for the
    # final phase. The LLM should pick words that are fun/punchy to scratch.
    scratch_words: List[str] = Field(default_factory=lambda: ["fresh", "go"])
    scratch_title: str = "the cut"
    # which Kokoro voice speaks the scratch words, + how it's articulated
    # (soft / neutral / aggressive -> TTS speed + scratch drive/brightness)
    scratch_voice: str = "af_heart"
    scratch_articulation: str = "neutral"

    @field_validator("genre", mode="before")
    @classmethod
    def _genre_ok(cls, v):
        return v if v in GENRES else "electro_funk"

    @field_validator("name", mode="before")
    @classmethod
    def _name_ok(cls, v):
        v = str(v or "").strip()
        return v[:40] if v else "untitled"

    @field_validator("scratch_word", mode="before")
    @classmethod
    def _scratch_word_ok(cls, v):
        v = str(v or "").strip().lower()
        return v if v in SCRATCH_WORDS else "ahh"

    @field_validator("scratch_words", mode="before")
    @classmethod
    def _scratch_words_ok(cls, v):
        v = [str(s).strip()[:24] for s in (v or []) if str(s).strip()]
        while len(v) < 2:
            v.append(["fresh", "go"][len(v)])
        return v[:2]

    @field_validator("scratch_title", mode="before")
    @classmethod
    def _scratch_title_ok(cls, v):
        v = str(v or "").strip()
        return v[:24] if v else "the cut"

    @field_validator("scratch_voice", mode="before")
    @classmethod
    def _scratch_voice_ok(cls, v):
        v = str(v or "").strip().lower()
        return v if v in SCRATCH_VOICES else "af_heart"

    @field_validator("scratch_articulation", mode="before")
    @classmethod
    def _scratch_artic_ok(cls, v):
        v = str(v or "").strip().lower()
        return v if v in SCRATCH_ARTIC else "neutral"
    instruments: Instruments = Instruments()
    fx: Fx = Fx()
    palette: Palette = Palette()
    visuals: Visuals = Visuals()
