# Visual Effects — Inventory, Analysis & Categorisation

A complete catalogue of every visual in the stream: the 4 rotating 3D
worlds + 1 fallback (`visualizer/worlds.js`) and the 89 demoscene effects
(`visualizer/demoscene.js`). **94 visuals total.**

## How the visual engine works (context for the analysis)

- **`a3d.js`** — a single ASCII framebuffer (char + packed-RGB + depth per
  cell, ~168 cols). Primitives: `plot` (depth-tested cell), `vspan`
  (vertical run), `hspan` (horizontal run — bypasses the symmetry wrapper),
  `line3` (3D Bresenham), `sprite`, `project`, and a colour-run-batched
  `flush()` (one `fillText` per same-colour run).
- **`render.js`** — owns the engine, a **shuffle-bag** rotation of the pool
  (every visual once, random order, no repeats until the bag empties),
  per-section palette cross-fade, the music-reactive `env`
  (`beat / energy / hit / bass / lead / drum / pitch / mv` — a composite of
  the *whole* music, not just the beat), the cinematic camera overlay, and
  a per-appearance variety wrapper (`fxSym`/`fxFlip`/`fxTime`) that can
  mirror/flip/retime a demo so a recurring mode never looks identical.
- **Performance classes** used below:
  - **point/line** — O(particles or vertices); inherently cheap.
  - **hspan/column** — drawn as horizontal/vertical runs; very cheap, and
    `hspan` skips the symmetry multiply.
  - **grid·2×** / **grid·4×** — full-field per-cell, but down-sampled
    (compute 1 of 4 / 1 of 16 cells, fill the block). The expensive
    transcendental maths is cut 4×/16×.
  - **CA-sim** — maintains a grid simulation each frame (often throttled);
    cost is the sim, not the draw.
  - **full-grid** — per-cell with no down-sample (the few remaining heavy
    ones, flagged).
- Every effect re-randomises its parameters on each appearance (`E()`
  factory) and reads the music `env`, so all of them are music-reactive.

---

## 3D Worlds (`worlds.js`)

| Title | Category | Technique | Perf |
|---|---|---|---|
| **E1M1** | 3D scene | Auto-walking DOOM raycaster — corridor-seeking maze, per-column wall cast + floor | column / moderate |
| **TERRAIN** | 3D scene | Voxel landscape flythrough — heightmap, painter's columns | column / moderate |
| **STAGE 1-1** | 3D scene | 2D side-scroller faked with a flat ortho cam — parallax `line3` layers + ASCII sprite hero | line / cheap |
| **SECTOR-7** | 3D scene | Battlezone wireframe cockpit — `line3` vectors + crosshair HUD | line / cheap |
| **FIELD** | 3D scene | Abstract glyph field (fallback world) | point / cheap |

---

## Demoscene effects (`demoscene.js`) — 89, by category

### Plasma & sinusoidal fields
| Title | Technique | Perf |
|---|---|---|
| PLASMA | Classic 4-sine + radial plasma | grid·2× |
| INTERFERENCE | Multi-sine + radial interference | grid·2× |
| PLASMA FRACTAL | Fractal-octave plasma, **separable** (x-term + y-term precomputed) | grid·2× (sep.) |
| BUMP PLASMA | Embossed/bump-lit plasma (gradient of a height field) | grid·2× |
| MOIRE | Two moving radial gratings multiplied | grid·2× |
| AURORA | Shimmering vertical curtains — iterates only the lit band | column / cheap |

### Tunnels, zoomers & warps
| Title | Technique | Perf |
|---|---|---|
| TUNNEL | Classic atan2/inv-radius tunnel | grid·4× |
| PLASMA TUNNEL | Tunnel × plasma hybrid | grid·2× |
| META TUNNEL | Tunnel modulated by metaballs | grid·2× |
| LIT TUNNEL | Shaded/textured lit tunnel | full-grid* |
| TUNNEL RINGS | Z-stacked parametric rings | line / cheap |
| ROTOZOOM | Rotating-zooming checkerboard texture | grid (int) |
| HEX ZOOM | Zooming hex-distance field | grid·2× |
| DEEP ZOOM | Infinite Mandelbrot zoom | grid·4× |
| WORMHOLE | Polar wormhole (atan2 + 1/r), hoisted | grid·4× |

### Fractals
| Title | Technique | Perf |
|---|---|---|
| MANDELBROT | Escape-time, iteration-capped | grid·4× |
| JULIA | Escape-time Julia | grid·4× |
| BURNING SHIP | Burning-Ship escape-time | grid·4× |
| TRI FRACTAL | Sierpinski chaos game (IFS points) | point / cheap |

### Metaballs / blobs
| Title | Technique | Perf |
|---|---|---|
| METABALLS | 3-ball implicit field | grid·2× |
| META LIT | Metaballs with fake gradient lighting | grid·2× |

### Starfields, warps & galaxies
| Title | Technique | Perf |
|---|---|---|
| STARFIELD | Classic 3D starfield | point / cheap |
| STAR WARP | Hyperspace warp stars | point / cheap |
| WARP STARS | Warp stars with motion-blur streaks | point / cheap |
| STAR CYLINDER | Stars on a rotating cylinder | point / cheap |
| GALAXY | Logarithmic-spiral particle galaxy | point / cheap |

### Particle systems & fluids
| Title | Technique | Perf |
|---|---|---|
| DOT EXPLOSION | Beat-triggered particle burst (capped, in-place) | point / cheap |
| FIREWORKS | Gravity-fountain particles | point / cheap |
| INK FLOW | Flow-field advected ink particles | point / moderate |
| FALLING SAND | Falling-sand cellular automaton | CA-sim |
| SMOKE | Buoyant smoke advection grid | CA-sim |
| BALL PIT | Bouncing-ball physics (sprites) | point / cheap |

### 3D wireframe & solids
| Title | Technique | Perf |
|---|---|---|
| GLENZ | Rotating glenz vector solid | line / cheap |
| VECTOR CUBE | Rotating wireframe cube | line / cheap |
| CUBE FIELD | Flying field of wireframe cubes | line / cheap |
| WIRE SPHERE | Lat/long wireframe sphere | point / cheap |
| DOTSPHERE | Rotating point sphere | point / cheap |
| TORUS | Rotating shaded torus (param points) | point / cheap |
| TORUS KNOT | (p,q) torus-knot space curve | point / cheap |
| TESSERACT | 4D hypercube wireframe projection | line / cheap |
| LIT ICOSA | Back-face-culled flat-shaded icosahedron | moderate |
| BOING | Amiga Boing checkerboard ball | point / moderate |
| VECTOR BALL GRID | Grid of bouncing vector balls | point / cheap |

### Amiga raster / copper / bobs / bars
| Title | Technique | Perf |
|---|---|---|
| COPPER (classic) | Sine-moving copper bands | hspan / cheap |
| COPPER (bars) | Amiga copper bars | hspan / cheap |
| RASTER BARS | Thick shaded raster bars | hspan / cheap |
| KEFRENS BARS | Kefrens "bars" (per-row x history) | line / cheap |
| ROTO BARS | Rotating sine bars | column / cheap |
| TWISTER | Amiga 4-edge twister column | column / cheap |
| SHADEBOBS | Additive shade-bob accumulation buffer | grid (buf) |
| VECTOR BOBS | Sinusoidal bob sprites | point / cheap |
| BOBS | Lissajous bob cluster | point / cheap |
| SINE DOTS | Sine-scroller dot wave | point / cheap |
| SINE COLUMNS | Sine-driven vertical columns | column / cheap |

### Vector curves & scopes
| Title | Technique | Perf |
|---|---|---|
| LISSAJOUS | Lissajous figure | point / cheap |
| OSCILLOSCOPE | XY scope + ground waveform | point / cheap |
| HARMONOGRAPH | Damped harmonograph curve | point / cheap |
| ATTRACTOR | de Jong strange attractor (curated params) | point / cheap |
| PENDULUM WAVE | Phase-drifting pendulum wave | point / cheap |
| SPIROGRAPH-like → COLOR SPIRAL | Angular spiral field | grid·2× |
| POLAR SWIRL | Polar swirl field | grid·2× |
| MANDALA | Radial symmetric mandala | point / cheap |
| PULSE RINGS | Expanding parametric rings | line / cheap |
| STARBURST | Radial ray burst | line / cheap |
| RADAR | Sweep + decaying blips | line / cheap |
| DNA HELIX | Twin-strand helix with rungs | point / cheap |

### Cellular automata & generative grids
| Title | Technique | Perf |
|---|---|---|
| LIFE | Conway's Game of Life (throttled) | CA-sim |
| REACTION | Reaction-diffusion (sim full-res, draw 2×) | CA-sim |
| TURMITES | Multi-turmite Langton's ants | CA-sim |
| MAZE | Growing DFS maze + render | CA-sim |
| CRYSTAL | Diffusion-limited aggregation | CA-sim |
| VORONOI | Moving-site Voronoi (reused buffers) | grid·4× |
| TRUCHET | Animated Truchet tiling | tile / cheap |
| FIRE | Upward fire propagation buffer | CA-sim |

### Grids, landscapes & roads
| Title | Technique | Perf |
|---|---|---|
| WAVE GRID | 3D sine wave-grid points | point / cheap |
| DOT WAVE | Dense 3D dot wave | point / cheap |
| VOXEL HILLS | Voxel hill heightmap (columns) | column / moderate |
| NIGHT RIDGES | Layered parallax ridge silhouettes | vspan / cheap |
| CHECKER FLOOR | Perspective checker floor (hspan sky + 2× floor) | hspan / cheap |
| VECTOR ROAD | Outrun road via per-scanline `hspan` | hspan / cheap |

### Typographic
| Title | Technique | Perf |
|---|---|---|
| KINETIC TYPE | Jittering block-letter words | point / cheap |
| CODE | Scrolling pseudo-code wall | text / cheap |
| BOUNCE LOGO | DVD-style bouncing "OSKAR" bitmap | point / cheap |

### Glitch / digital / misc
| Title | Technique | Perf |
|---|---|---|
| DATAMOSH | XOR-band glitch shear | grid·2× |
| DIGITAL RAIN | Matrix code-rain columns | point / cheap |
| RIPPLE | Multi-source water ripple | grid·2× |
| LENS | Lens-distorted XOR texture | full-grid* |
| RAYMARCH | SDF sphere/torus ray-march (ST=3, capped) | grid·3× |
| BOIDS | Boids flocking (small-N O(n²)) | point / moderate |

`*` **LIT TUNNEL** and **LENS** are the only two remaining un-downsampled
full-grid effects (same per-cell profile as the others before the perf
sweep). They are candidates for the same 2× treatment if they ever feel
heavy.

---

## Performance summary

- **Cheap (point/line/hspan/column):** ~55 effects — bound by particle or
  vertex count, not screen area. The Amiga staples, starfields, particle
  systems, wireframes, vector curves, bars/copper, roads.
- **grid·2× / grid·4× (down-sampled fields):** ~22 effects — plasmas,
  tunnels, fractals, metaballs, voronoi, ripple, datamosh, hex/spiral.
  The transcendental cost is cut 4–16×; fractals & wormhole/voronoi are 4×.
- **CA-sim:** ~8 effects — Life, Reaction, Turmites, Maze, Crystal, Fire,
  Smoke, Falling Sand. Cost is the (often throttled) grid update.
- **full-grid (2 left):** LIT TUNNEL, LENS.
- **Worlds:** column/line raycasting & vector — moderate but bounded.

The render manager's symmetry wrapper can multiply `plot` calls ×2–4 on
demos; `hspan`/`vspan` deliberately bypass it, which is why the bar/road/
copper family is so cheap.

---

## Suggested 20 new demoscene-inspired effects (performant only)

All chosen to fit an existing cheap perf class (point/line/hspan/column or
a down-sampled separable field) — no unbounded per-pixel work.

1. **Rotozoom Texture** — rotozoom over a procedural XOR/argyle pattern
   drawn as `hspan` rows per scanline (the *real* Amiga technique). hspan.
2. **LUT Plasma** — classic Amiga plasma: two precomputed 1-D gradient
   LUTs scrolled and summed (no per-cell `sin`). grid·2×, near-free maths.
3. **Fractal Tree** — recursive L-system tree, depth-capped (~6), branches
   sway with `mv`/beat. line, O(2^depth) bounded.
4. **Lightning** — beat-triggered recursive jagged bolt + a few forks,
   short-lived. line, only on hits.
5. **Hilbert / Space-Filling Path** — animated Hilbert curve drawn/erased
   progressively. line, one path.
6. **Elementary CA (Rule 30/110)** — 1-D automaton, one new row per frame
   scrolling up. O(width)/frame — extremely cheap.
7. **Brian's Brain / WireWorld** — 3-state CA in the existing LIFE cost
   class; visually very different. CA-sim.
8. **Spirograph** — epicycloid/hypotrochoid traced as points, radii
   morphing with the music. point.
9. **Concentric Moiré Rings** — two sets of offset circles (line draw, not
   per-pixel) beating against each other. line.
10. **Vector Tunnel (polygon rings)** — z-stacked rotating N-gon outlines
    receding to a vanishing point. line.
11. **Starfield Hyperjump** — radial streak starfield with a charge-up then
    "jump" on a strong beat. point.
12. **Phong Cube** — rotating cube, 12 triangles flat-shaded by face
    normal at low cell resolution. line + small bounded fill.
13. **Metaball Discs** — 3–4 additive filled discs at half-res (bounded
    circle rasters, not a full implicit field). bounded.
14. **ASCII Donut** — the classic `donut.c` torus with lambert shading,
    angular step (no per-pixel). point/grid-small.
15. **Voxel Wave Terrain** — `line3` 3-D grid mesh undulating (a true 3-D
    cousin of NIGHT RIDGES). line.
16. **Plasma Fire 2.0** — palette-cycled upward fire using a 1-column
    propagate + `hspan` rows. hspan/CA-cheap.
17. **Shutter Wipes / Venetian Blinds** — horizontal bands opening/closing
    revealing a second pattern. hspan.
18. **Particle Gravity Well** — particles orbiting/falling into a moving
    attractor (Verlet, capped count). point.
19. **Boing Shadow Ball** — Amiga Boing ball + a skewed floor shadow and
    grid (bounded sphere raster, like BOING but with the classic shadow).
    point / bounded.
20. **Text Ring Tunnel** — a word/phrase wrapped on receding rings
    rotating toward the viewer (à la classic credits tunnels). point/line.

Honourable extras if more are wanted: **Conway glider-gun showcase**,
**XY audio-scope bloom**, **recursive Pythagoras tree**, **droplet
caustics** (1-D ripple LUT), **starfield "warp gate"** ring.

---

## Implemented (status)

All 20 above were implemented (cheap perf classes, per-appearance `this.P`
variety + music-reactive), plus user-requested additions:

- **ELITE** — black space, wireframe Cobra ship + planet, starfield, the
  classic scanner/dashboard. (line/point + `hspan` bg)
- **HARDWARE REFERENCE MANUAL** — Amiga-assembly code wall (`move.l`,
  `lea`, `$DFFxxx`, copper/blit comments). The old **CODE** effect was
  renamed **JAVASCRIPT**.
- **WORKBENCH 1.3** (insert-disk hand+floppy) was attempted and **removed**
  — an ASCII/Bresenham rendering can't be a faithful replica of that
  pixel-art, so it was cut rather than ship a poor version.

Effect total is now **115** (4 worlds + 111 demoscene). E1M1 also gained
a roaming enemy imp; STAGE 1-1's music sway was reduced to ~30%.
