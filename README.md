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
**99 demoscene effects**. Every appearance re-randomises speed/phase/colour
and may mirror/flip, and all of them react to the music.

| Effect | What it is |
|---|---|
| `DOOM` *(world)* | Auto-walking corridor-seeking DOOM-style raycaster |
| `LAND` *(world)* | Voxel-landscape flythrough (Comanche-style heightmap) |
| `SIDE` *(world)* | Parallax 2D side-scroller |
| `WIRE` *(world)* | Wireframe Battlezone vector world |
| `RASTER BARS` | Classic copper/raster colour bars sweeping the screen |
| `KEFRENS BARS` | Kefrens "bar" recursion fanning down the screen |
| `SHADEBOBS` | Trailing additive blob sprites (shadebobs) |
| `MOIRE` | Interfering line grids producing moiré patterns |
| `VECTOR ROAD` | Outrun-style perspective road into the horizon |
| `MANDELBROT` | Animated Mandelbrot set zoom |
| `WORMHOLE` | Flight down a textured wormhole tunnel |
| `LIFE` | Conway's Game of Life cellular automaton |
| `AURORA` | Drifting aurora-curtain colour bands |
| `RIPPLE` | Concentric water-ripple interference |
| `DNA HELIX` | Rotating double-helix strand |
| `STARBURST` | Radial starburst rays pulsing on the beat |
| `DIGITAL RAIN` | Matrix-style falling glyph rain |
| `TORUS` | Rotating shaded 3D torus |
| `HEX ZOOM` | Infinitely zooming hex-grid tiling |
| `LISSAJOUS` | Lissajous-curve oscilloscope figures |
| `PLASMA TUNNEL` | Plasma-textured tunnel flythrough |
| `VECTOR BALL GRID` | Grid of bobbing vector balls |
| `COLOR SPIRAL` | Rotating multi-arm colour spiral |
| `CHECKER FLOOR` | Perspective checkerboard floor scroll |
| `DOT EXPLOSION` | Particle burst re-fired on the beat |
| `INTERFERENCE` | Two-source wave interference field |
| `WAVE GRID` | Oscillating 3D wireframe wave mesh |
| `ROTO BARS` | Rotating/zooming bar field (rotozoom bars) |
| `STAR CYLINDER` | Stars wrapped on a spinning cylinder |
| `PULSE RINGS` | Expanding rings pulsed by the music |
| `SPECTRUM` | Audio-spectrum analyser bars |
| `JULIA` | Animated Julia-set fractal |
| `BOUNCE LOGO` | The song title bounced DVD-logo style (bitmap font) |
| `POLAR SWIRL` | Polar-coordinate swirl warp |
| `TUNNEL RINGS` | Ring-segmented tunnel flythrough |
| `DOT WAVE` | Sine-driven dot wave surface |
| `WIRE SPHERE` | Rotating wireframe sphere |
| `DATAMOSH` | Horizontal glitch/datamosh displacement |
| `GALAXY` | Spiral-galaxy particle swirl |
| `FIREWORKS` | Beat-synced fireworks bursts |
| `META TUNNEL` | Metaball-walled tunnel |
| `CUBE FIELD` | Field of receding 3D cubes |
| `SINE DOTS` | Phased sine-scroll dot rows |
| `VOXEL HILLS` | Rolling voxel hill terrain |
| `PLASMA FRACTAL` | Fractal-noise plasma field |
| `LENS` | Magnifying-lens distortion over a pattern |
| `TRI FRACTAL` | Recursive triangle (Sierpinski-style) fractal |
| `LIT TUNNEL` | Shaded/lit tunnel with normals |
| `LIT ICOSA` | Lit rotating icosahedron |
| `ATTRACTOR` | Strange-attractor particle trace |
| `REACTION` | Reaction-diffusion (Gray-Scott) pattern |
| `META LIT` | Lit/shaded metaballs |
| `DEEP ZOOM` | Infinite Mandelbrot deep-zoom to set coordinates |
| `BUMP PLASMA` | Bump-mapped embossed plasma |
| `WARP STARS` | Accelerating warp-speed starfield |
| `TORUS KNOT` | Rotating 3D torus-knot curve |
| `INK FLOW` | Flowing ink-particle advection field |
| `KINETIC TYPE` | Big song-word typography, beat-pulsed reveal |
| `TURMITES` | Turmite / Langton's-ant cellular automaton |
| `MAZE` | Generated maze with a traversal sweep |
| `OSCILLOSCOPE` | Waveform oscilloscope trace |
| `FALLING SAND` | Falling-sand granular automaton |
| `RAYMARCH` | Raymarched SDF scene |
| `BOIDS` | Flocking-boids swarm |
| `HARMONOGRAPH` | Damped harmonograph pendulum curve |
| `MANDALA` | Symmetric rotating mandala |
| `JAVASCRIPT` | Scrolling source-code wall (syntax-tiered) |
| `HARDWARE REFERENCE MANUAL` | Scrolling reference-manual text wall |
| `NIGHT RIDGES` | Dotted night ridge-line silhouette |
| `BALL PIT` | Physics ball-pit pile-up |
| `CRYSTAL` | DLA crystal-growth accretion |
| `SMOKE` | Fluid smoke/plume simulation |
| `PENDULUM WAVE` | Phasing pendulum-wave array |
| `TESSERACT` | Rotating 4D hypercube projection |
| `RADAR` | Sweeping radar scope with blips |
| `TRUCHET` | Truchet-tile maze pattern |
| `VORONOI` | Animated Voronoi cell diagram |
| `BURNING SHIP` | Burning-Ship fractal zoom |
| `COPPER` | Amiga copperbar gradient stripes |
| `STAR WARP` | Star-warp speed tunnel |
| `SINE COLUMNS` | Sine-displaced vertical columns |
| `BOBS` | Classic bouncing sprite bobs |
| `VECTOR CUBE` | Rotating wireframe vector cube |
| `ROTOTEX` | Rotozoomer textured plane |
| `LUT PLASMA` | Look-up-table palette-cycled plasma |
| `FRACTAL TREE` | Recursive swaying fractal tree |
| `LIGHTNING` | Branching lightning bolts on hits |
| `HILBERT` | Hilbert space-filling curve draw |
| `RULE 30` | Rule-30 elementary cellular automaton |
| `BRIANS BRAIN` | Brian's Brain three-state automaton |
| `SPIROGRAPH` | Spirograph epicycloid curves |
| `VECTOR TUNNEL` | Wireframe polygon tunnel |
| `HYPERJUMP` | Star Wars-style hyperspace jump |
| `PHONG CUBE` | Phong-shaded rotating cube |
| `META DISCS` | Orbiting metaball discs |
| `ASCII DONUT` | The classic spinning ASCII donut |
| `WAVE TERRAIN` | Wireframe sine-terrain mesh |
| `PLASMA FIRE` | Plasma-fed fire effect |
| `SHUTTER` | Venetian-blind iris reveal of a colour wash |
| `GRAVITY WELL` | Particles pulled into a moving gravity well |
| `BOING SHADOW` | Amiga boing-ball with floor shadow |
| `TEXT RINGS` | Song word orbiting in concentric 3D rings |
| `ELITE` | Elite-style wireframe vector spacecraft |

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
