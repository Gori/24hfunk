# str

Hermetic, fully-local pipeline that generates AI music + beat-synced monospace-glyph
visuals. **Milestone 1: local preview** — runs on one Mac, plays to speakers, shows
visuals in a browser at `http://localhost:8080`. No network, no APIs, no streaming.

```
midi/  (canned OR MIDI-LLM)  ──OSC 57120──▶  synth/ (SuperCollider) ──audio──▶ speakers
      ▲ /midi/section (OSC 57121)                   │ /vis/* OSC 57130
director/ (Qwen3-8B, mlx-lm) ─OSC 57120 + HTTP 8080─▶ bridge/ (Node WS :8080) ──WS──▶ visualizer/ (browser)
```

- **Audio**: a MIDI source feeds SuperCollider's fixed SynthDef library
  (kick/snare/hat/bass/lead + reverb/delay bus). Two sources:
  - `canned` (**default**): deterministic generative lofi from the section's
    tempo/key/density. Always works.
  - `midillm` (opt-in): `slseanwu/MIDI-LLM_Llama-3.2-1B` (fp16/MPS, decoded via
    the `anticipation` lib). Auto-falls-back to canned on any failure.
- **Director**: local `mlx-community/Qwen3-8B-4bit` via `mlx-lm` picks a new
  `SectionState` (mood/bpm/key/palette/glyphs/params/text) every 5–8 min.
  Out-of-range values are clamped, never rejected.
- **Visuals**: Canvas2D monospace glyph field; note-ons spawn impulses, beats
  pulse brightness, palette slowly lerps, occasional centered text strings.

## Install (Phase A)

```bash
brew install --cask supercollider blackhole-16ch     # BlackHole unused until M2
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "mido==1.3.3" "git+https://github.com/jthickstun/anticipation.git"  # MIDI-LLM source only
python -c "from huggingface_hub import snapshot_download as d; d('mlx-community/Qwen3-8B-4bit'); d('slseanwu/MIDI-LLM_Llama-3.2-1B')"
npm install
```

> SuperCollider installs to `/Applications/SuperCollider.app`; the CLI is
> `/Applications/SuperCollider.app/Contents/MacOS/sclang` (override with `$SCLANG`).
> BlackHole 16ch needs an interactive `sudo` — install it manually when you
> reach Milestone 2; it is **not** used in Milestone 1.

## Run

```bash
./scripts/start-all.sh        # SC → bridge → director → midi worker
# open http://localhost:8080
./scripts/stop-all.sh         # also sweeps any orphan scsynth
```

Logs + pidfiles in `.run/`.

## Env knobs

| var | default | meaning |
|-----|---------|---------|
| `STR_MIDI_SOURCE` | `canned` | `canned` or `midillm` |
| `STR_SECTION_SEC` | (LLM-chosen 300–480) | override section length, e.g. `45` for testing |
| `STR_DIRECTOR_MODEL` | `mlx-community/Qwen3-8B-4bit` | director model id |
| `STR_MIDILLM_MODEL` | `slseanwu/MIDI-LLM_Llama-3.2-1B` | midi model id |
| `BRIDGE_HTTP_PORT` | `8080` | bridge HTTP/WS |
| `SC_OSC_PORT` | `57120` | SuperCollider router in |
| `VIS_OSC_PORT` | `57130` | SC → bridge |
| `MIDI_CTRL_OSC_PORT` | `57121` | director → midi worker |

## Smoke tests

```bash
/Applications/SuperCollider.app/Contents/MacOS/sclang scripts/smoke/sc-selftest.scd   # 6 synthdefs
/Applications/SuperCollider.app/Contents/MacOS/sclang scripts/smoke/sc-drone-test.scd # stuck-note safety
node scripts/smoke/send-test-note.js                                                  # bridge WS fanout
.venv/bin/python scripts/smoke/fire_osc.py seq 16 0.2                                  # OSC → SC
.venv/bin/python scripts/smoke/fake-section.py cycle 4 8                               # publish path
```

## Not in Milestone 1 (deferred)

OBS Browser Source, BlackHole routing, YouTube RTMP push, AI-content disclosure
flag, launchd watchdog / 24-7 reliability, recording. See the plan at
`~/.claude/plans/we-re-going-to-create-starry-coral.md`.
