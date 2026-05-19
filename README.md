# str — 24h generative funk audiovisual stream

A **hermetic, fully-local** machine that improvises endless funk/jazz/electro/dub
music *and* a matching ASCII demoscene visual, forever, with no network and no
APIs. Everything runs on one Mac: a groove engine drives SuperCollider synths,
a local LLM (Qwen via MLX) directs the sections, and a browser renders 130
music-reactive ASCII effects.

```
 midi/  groove engine ──OSC 57120─▶ synth/  SuperCollider ──audio──▶ speakers
   │  (21 genres, funk theory)        │  (per-track FX buses)
   │                                  └─ /vis/* OSC 57130 ─┐
 director/ Qwen ─ section state ─▶ bridge/ Node WS :8080 ◀─┘
                                   └── WS ──▶ visualizer/  browser  (130 ASCII FX)
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

### Visuals — 130 ASCII effects (`visualizer/`)
- A shared ASCII 3D engine (`a3d.js`): depth-buffered framebuffer, projection,
  line raster, sprites, fog, fast colour-run flush.
- **4 worlds** (`worlds.js`) + **126 demoscene effects** (`demoscene.js`),
  spanning classic demoscene, fractals/math, cellular sims, typographic,
  and fine-art-inspired. See the **Effect reference** section below for the
  category breakdown (no full enumeration — the registry is the source of
  truth).
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
visualizer/  a3d engine + 4 worlds + 126 demoscene effects + HUD
scripts/     start-all / stop-all / smoke tests
```

## Genre reference

All 21 genres the director can pick. *Scale* is the mode the melody/harmony
draw from; *groove* is the swing/pocket feel; *voices* are the per-genre
kick·snare·bass·lead SynthDef picks (the LLM still tunes their params,
progression bank, structure and palette per song).

| Genre | Character | Scale · groove | Voices (kick·snare·bass·lead) |
|---|---|---|---|
| `funk` | Hard one-chord vamp on a dom7#9 — the canonical "the one" funk | Dorian · swung | kickHard · snare · bassFM · lead |
| `electro_funk` | Min9→dom electro-funk with an FM pluck bass and crisp backbeat | Dorian · swung | kickHard · snare · bassFM · lead |
| `minneapolis_funk` | Prince-style synth-funk: punchy square bass, bright pulse lead | Dorian · swung | kickHard · snare909 · bassSquare · leadPulse |
| `synthwave` | Wistful 80s neon: maj7 lifts, straight pulse, clean lead | Aeolian · straight | kick · snare909 · bass · lead |
| `eighties_hiphop` | Boom-bap min9 vamp, 808 kick, 909 snare, pulse lead | Dorian · swung | kick808 · snare909 · bass · leadPulse |
| `electro` | Cold Phrygian electro: 808 kick, 909 snare, square bass | Phrygian · straight | kick808 · snare909 · bassSquare · leadPulse |
| `broken_house` | Shuffled broken-beat house, maj7/dom9 lift, square bass | Dorian · heavily shuffled | kickHard · snare909 · bassSquare · leadPulse |
| `minimal_techno` | Stripped hypnotic min9 loop, dry tight kit, square sub | Aeolian · straight | kick · snare909 · bassSquare · leadPulse |
| `detroit_techno` | Soulful machine-funk: maj9 colour, FM bass + FM lead | Dorian · straight | kick · snare909 · bassFM · leadFM |
| `dub_techno` | Deep chord-stab techno, long FM lead, sub bass | Aeolian · straight | kick808 · snare909 · bass · leadFM |
| `jazz` | Brush-kit ii–V–I swing, vibraphone-mallet lead, room keys | Dorian · heavy triplet swing | kick · snareBrush · bass · leadJazz |
| `lofi` | Lazy late-night ii–V, brushed snare, mellow FM lead | Dorian · swung (laid back) | kick · snareBrush · bass · leadFM |
| `rnb` | Smooth modern R&B, min9→dom9 changes, warm subtle lead | Dorian · swung | kick · snare · bass · lead |
| `afro_rnb` | Afro-R&B lilt, maj9/dom9 colour, FM bass + FM lead | Dorian · swung | kick · snare909 · bassFM · leadFM |
| `indie_rnb` | Hazy indie-R&B: maj7/maj9, 808 kick, brushed snare | Aeolian · swung | kick808 · snareBrush · bass · leadFM |
| `neon_dub` | Neon-lit dub: min9/min7, 808 kick, long FM lead | Aeolian · swung | kick808 · snare · bass · leadFM |
| `dub` | Heavy roots dub, sub bass, sparse 808 kick, echoing lead | Aeolian · swung | kick808 · snare · bass · leadFM |
| `steppers_dub` | Four-on-the-floor steppers dub, driving sub | Aeolian · light swing | kick808 · snare · bass · leadFM |
| `roots_reggae` | One-drop roots reggae, maj7 lift, off-beat feel | Aeolian · swung (one-drop) | kick · snare · bass · leadFM |
| `uk_garage` | Skippy 2-step garage, swung hats, FM bass, pulse lead | Dorian · heavy 2-step swing | kickHard · snare909 · bassFM · leadPulse |
| `dub_garage` | Dubwise garage: 2-step swing meets deep FM lead | Dorian · heavy 2-step swing | kickHard · snare909 · bassFM · leadFM |

## Effect reference

The visual pool the engine shuffles through: **4 worlds** (3D scenes) +
**126 demoscene effects** = **130 total**, rotated continuously. Every
appearance re-randomises speed/phase/colour and may mirror/flip, and all
of them react to the music. The HUD shows the current effect's number +
name live; the authoritative list is the registry in `visualizer/
demoscene.js` (`window.Worlds.demos`) + `worlds.js` (`classics`).

Roughly by category:

- **3D worlds (4):** auto-walking DOOM raycaster (E1M1), voxel-landscape
  flythrough, the STAGE 1-1 parallax side-scroller, wireframe Battlezone.
- **Classic demoscene:** plasma, copper/raster bars, tunnels, rotozoom,
  twister, glenz/vector solids, boing, kefrens, shadebobs, metaballs,
  fire, starfields, kaleidoscope, feedback zoom, …
- **Fractals & math:** mandelbrot/julia/burning-ship/buddhabrot,
  raymarched menger/mandelbulb, attractors (lorenz/clifford), flow
  fields, chladni, phyllotaxis, domain warp, apollonian, harmonograph, …
- **Cellular / simulation:** life, brian's brain, rule 30, turmites,
  reaction-diffusion, smoke, boids, gravity well, falling sand, DLA, …
- **Text / typographic:** kinetic type, text rings, scrollers,
  code/manual walls, teletext.
- **Fine-art inspired:** Riley waves, Vasarely bulge, Penrose stairs,
  Mondrian, Pollock drip, Rothko fields, Hokusai great wave, Kusama
  dots, Joy-Division "Unknown Pleasures".

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
