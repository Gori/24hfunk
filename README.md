# str — 24h generative funk audiovisual stream

A **hermetic, fully-local** machine that improvises endless funk/jazz/electro/dub
music *and* a matching ASCII demoscene visual, forever, with no network and no
APIs. Everything runs on one Mac: a groove engine drives SuperCollider synths,
a local LLM (Qwen via MLX) directs the sections, and a browser renders 103
music-reactive ASCII effects.

```
 midi/  groove engine ──OSC 57120─▶ synth/  SuperCollider ──audio──▶ speakers
   │  (21 genres, funk theory)        │  (per-track FX buses)
   │                                  └─ /vis/* OSC 57130 ─┐
 director/ Qwen ─ section state ─▶ bridge/ Node WS :8080 ◀─┘
                                   └── WS ──▶ visualizer/  browser  (103 ASCII FX)
```

## Screenshots

> The visuals run in your browser at `http://localhost:8080`. This agent can't
> capture browser screenshots — drop your own into `docs/screenshots/` (capture
> on macOS with **⌘⇧4**, or `screencapture -x docs/screenshots/raycaster.png`).

| | |
|---|---|
| ![DOOM raycaster](docs/screenshots/raycaster.png) | ![Plasma + HUD](docs/screenshots/plasma.png) |
| ![Voxel landscape](docs/screenshots/landscape.png) | ![Wireframe / tesseract](docs/screenshots/wireframe.png) |

Each shot should show the top **HUD** (`EFFECT · …` / `MUSIC · genre · mood
· bpm · key`).

## What's going on

### Music — a funk-first groove engine (`midi/canned.py`)
- **21 genres**: electro_funk, synthwave, neon_dub, broken_house, lofi,
  electro, eighties_hiphop, jazz, funk, minneapolis_funk, minimal_techno,
  detroit_techno, dub, steppers_dub, dub_techno, roots_reggae, uk_garage,
  dub_garage, rnb, afro_rnb, indie_rnb.
- **Research-backed funk**: space is articulation/syncopation/dynamics/
  micro-timing — *not* note count. "The one" lock, ghost-note tiers, per-genre
  swing, behind-the-beat pocket, 8-bar phrasing, and a per-section **energy
  roll** (mostly sparse, occasionally dense).
- **Real harmony**: per-genre chord progressions with proper qualities
  (maj7/min9/dom7#9/…), secondary-dominant turnarounds, **voice-led** keys
  comping + a soft pad, and a melodic motif on chord guide-tones. The LLM
  picks 1 of **4 researched progression banks** per genre.
- **Song structure**: each section is a ~3-min *song* — the LLM picks an
  arrangement (staggered instrument entries + mid-song breaks) and **names
  it**; the title drives the HUD + text/sinus-scroller visuals.
- **Expressive, gliding, digital synths** (SuperCollider, `synth/synthdefs/`):
  25 SynthDefs incl. variants — bass is a **mono portamento** voice (real
  funk slides), velocity→filter/grit, fade-in vibrato, a warm FM e-piano.
  An **analogue console/tape pass** adds VCO drift, Moog-ladder filtering,
  multi-stage saturation and tape wow/flutter on the master.
- **Per-genre instruments**: every genre deliberately picks its kick / snare /
  bass / lead variant (e.g. funk = bassFM + kickHard; electro = bassSquare +
  kick808 + snare909 + leadPulse; dub = deep sub + kick808 + leadFM).
- **Per-track, genre-dependent FX**: drums / bass / lead+keys run through 3
  independent FX chains; dub gets huge delayed leads, jazz a room on the keys,
  techno tight dry drums, etc.
- **Director** (`director/director.py`, local Qwen3-4B via MLX): every few
  minutes picks the next section — genre/bpm/key/density, the progression
  bank + song structure + song name, and a curated **colour palette**
  (including whether to invert). The fast genre **audition**
  (`scripts/smoke/genre_audition.py`) cycles all 21 every ~20s for evaluation.

### Visuals — 103 ASCII effects (`visualizer/`)
- A shared ASCII 3D engine (`a3d.js`): depth-buffered framebuffer, projection,
  line raster, sprites, fog, fast colour-run flush.
- **4 worlds** (`worlds.js`): auto-walking DOOM raycaster (corridor-seeking),
  voxel landscape flythrough, 2D side-scroller, wireframe Battlezone.
- **99 demoscene effects** (`demoscene.js`): plasma, kefrens, shadebobs, moiré,
  Outrun road, mandelbrot/julia/burning-ship, fire, glenz, boing, tunnels,
  metaballs, raymarch, boids, harmonograph, mandala, DLA crystal, smoke,
  tesseract, radar, truchet, voronoi, life, turmites, … (Amiga/C64/Atari/PC).
- **Per-appearance variety**: every effect re-randomises speed/phase/colour/
  pattern + an occasional mirror/flip, so a recurring mode never looks the same.
- **Moves with the whole music** (not just the beat): per-instrument energy,
  note flashes and pitch drive every effect and the camera.
- **Palette** fades to a new curated scheme on every section.
- **HUD**: a big always-on top bar — `EFFECT · <name>` and
  `MUSIC · <genre · mood · bpm · key>`.

## Install (one-time)

```bash
brew install --cask supercollider blackhole-16ch     # BlackHole = future M2
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "mido==1.3.3" "git+https://github.com/jthickstun/anticipation.git"  # MIDI-LLM only
python -c "from huggingface_hub import snapshot_download as d; d('mlx-community/Qwen3-4B-Instruct-2507-4bit')"
npm install
```

> SuperCollider CLI: `/Applications/SuperCollider.app/Contents/MacOS/sclang`
> (override with `$SCLANG`). Apple Silicon required (MLX). BlackHole/RTMP are
> Milestone 2 — not used yet.

## Run

```bash
./scripts/start-all.sh        # SuperCollider → bridge → director → midi
open http://localhost:8080    # watch + listen
./scripts/stop-all.sh         # stops everything, sweeps orphans
```

Fast genre evaluation instead of the full director:

```bash
.venv/bin/python scripts/smoke/genre_audition.py 20   # cycle all 21, ~20s each
```

Logs + pidfiles land in `.run/`.

## Env knobs

| var | default | meaning |
|-----|---------|---------|
| `STR_MIDI_SOURCE` | `canned` | `canned` (groove engine) or `midillm` |
| `STR_SECTION_SEC` | LLM-chosen | override section length, e.g. `45` |
| `STR_DIRECTOR_MODEL` | `mlx-community/Qwen3-4B-Instruct-2507-4bit` | director model |
| `BRIDGE_HTTP_PORT` | `8080` | bridge HTTP/WS |
| `SC_OSC_PORT` | `57120` | SuperCollider router in |
| `VIS_OSC_PORT` | `57130` | SC → bridge |
| `MIDI_CTRL_OSC_PORT` | `57121` | director → midi worker |

## Smoke tests

```bash
$SCLANG scripts/smoke/sc-compile.scd                 # all 25 SynthDefs build
$SCLANG scripts/smoke/sc-drone-test.scd              # anti-stuck-note safety
node scripts/smoke/send-test-note.js                 # bridge WS fanout
.venv/bin/python scripts/smoke/fire_osc.py seq 16 .2 # OSC → SC
.venv/bin/python scripts/smoke/fake-section.py cycle 4 8
```

## Repo layout

```
midi/        groove engine + MIDI-LLM source + OSC out + worker
synth/       SuperCollider boot/router + 25 SynthDefs
director/    section director + schema/prompts
bridge/      Node HTTP+WS + OSC-in + state
visualizer/  a3d engine + 4 worlds + 99 demoscene effects + HUD
scripts/     start-all / stop-all / smoke tests
```

## Status

**Milestone 1 (local preview) — done.** The full creative pipeline runs
locally end-to-end. Deferred:

- **M2** — stream to YouTube: OBS/headless-Chromium capture + BlackHole audio
  routing + ffmpeg RTMP push. (On a Linux host the MLX LLM must be swapped for
  llama.cpp/vLLM — MLX is Apple-Silicon-only.)
- **M3** — 24/7 reliability: launchd/watchdog, auto-restart, soak hardening.

Lowest-friction deployment today: a spare/colocated Mac (runs as-is under
launchd). A Linux cloud box ≈ ~1 day (LLM backend swap); 24/7 YouTube
streaming is the bigger, deferred chunk.

## Credits / licenses

Qwen3 (Apache-2.0, via `mlx-community`), MIDI-LLM (`slseanwu`, Llama-3.2
Community License — optional source), `anticipation` (jthickstun),
SuperCollider (GPL). Generated with Claude Code.
