// render.js — SceneManager: owns the A3D engine, rotates a big pool of worlds
// (classic 3D + demoscene effects), lerps the palette, and runs the
// cinematic camera overlay. window.Renderer keeps main.js's API.
(function () {

  // GLOBAL movement speed for ALL visual effects. 1.0 = original; 0.7 =
  // 30% slower. Scales autonomous motion only (effect time, env.t, the
  // camera swim) — NOT music-synced motion (beat jumps, mv/energy/decays,
  // palette fade, the scene-rotation clock). One knob, tune freely.
  let SPEED = 0.7;
  // per-effect motion trim (multiplies SPEED for that title only). 1 = use
  // the global. >1 faster, <1 slower. Easy to tune per effect.
  const FXSPEED = {
    'PLASMA': 1.6, 'ROTOZOOM': 1.6, 'COPPER': 1.6, 'SINE COLUMNS': 1.6,
    'POLAR SWIRL': 1.6, 'DOT WAVE': 1.6,
    'GLENZ': 0.55, 'FIREWORKS': 0.55, 'WARP STARS': 0.55,
    'E1M1': 1.7,
  };
  let eng, active, vT = 0;
  let prevPal = window.Palette.normalize(null);
  let tgtPal = window.Palette.normalize(null);
  let curPal = window.Palette.normalize(null);
  let palT = 1, palDur = 4, beatEnv = 0, beatKick = 0, noteE = 0;
  // per-instrument musical energy so visuals move with the WHOLE music
  let bassE = 0, leadE = 0, drumE = 0, hitE = 0, lastPitch = 0.5, mv = 0;
  let pool = [], bag = [], sinceCut = 0, palIdx = 0;
  // HUD is drawn THROUGH the ascii engine (glyph2d) so it is literally the
  // same font/size and snapped to the same cell grid as the effect behind it.
  let hudEffect = '', hudMusic = '';
  const HUD_COL = [240, 240, 248];

  // curated, deliberately DISTINCT palettes — we fade to the next one on every
  // new music style so the colour world visibly changes each section.
  const PALETTES = [
    { bg: '#0a0612', fg: '#e9d8ff', accent: ['#ff3d81', '#36e6ff', '#ffe14d'] },
    { bg: '#04121a', fg: '#cdeaf2', accent: ['#19e0ff', '#7affc0', '#ff8a3d'] },
    { bg: '#140a06', fg: '#ffe6c2', accent: ['#ff7a2d', '#ffd23f', '#ff4d6d'] },
    { bg: '#0a1206', fg: '#e3ffce', accent: ['#9dff3d', '#3dff9e', '#f6ff5c'] },
    { bg: '#100614', fg: '#f4d5ff', accent: ['#c14dff', '#ff4dd2', '#6c7bff'] },
    { bg: '#06080f', fg: '#cfd6ff', accent: ['#5a78ff', '#36e6ff', '#b0c4ff'] },
    { bg: '#160c04', fg: '#ffdfae', accent: ['#ff9b2f', '#ffcf3f', '#7ad6ff'] },
    { bg: '#020a08', fg: '#bff5e4', accent: ['#1fe0b0', '#7affd1', '#ffe66d'] },
    { bg: '#120410', fg: '#ffd6ef', accent: ['#ff2e88', '#ff6f3c', '#ffd23f'] },
    { bg: '#0c0c12', fg: '#dfe4f0', accent: ['#8892ff', '#ff79c6', '#50fa7b'] },
  ];

  // Push the current effect name into the always-on HUD.
  function announceEffect() {
    if (active) hudEffect = (active.title || 'SCENE').toUpperCase();
  }
  function setNowPlaying(section) {
    if (!section) return;
    const up = (s) => String(s || '').replace(/_/g, ' ').trim().toUpperCase();
    const parts = [up(section.genre)];
    if (section.mood) parts.push(up(section.mood));
    if (section.bpm) parts.push(`${section.bpm | 0} BPM`);
    if (section.key) parts.push(up(section.key));
    hudMusic = parts.filter(Boolean).join('  ·  ');
  }
  // draw a string through the engine grid, centred, skipping spaces so the
  // effect shows between words and only the glyphs are opaque (always on top).
  function drawHudLine(str, row) {
    if (!str || !eng) return;
    const C = eng.cols, R = eng.rows;
    if (row < 0 || row >= R) return;
    const sx = Math.max(0, (C - str.length) >> 1);
    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      if (ch === ' ' || sx + i >= C) continue;
      eng.glyph2d(sx + i, row, ch, HUD_COL);
    }
  }
  function drawHud() {
    drawHudLine(hudEffect, 1);
    drawHudLine(hudMusic, eng.rows - 2);
  }

  let demoSet = new Set();
  let fxSym = 0, fxFlip = false, fxTime = 1;
  function buildPool() {
    const W = window.Worlds || {};
    pool = [].concat(W.classics || [], W.demos || []);
    if (!pool.length) pool = [W.Glyph].filter(Boolean);
    demoSet = new Set(W.demos || []);
    bag = [];
  }
  // shuffle-bag: every scene plays once (random order) before any repeats;
  // reshuffle on exhaustion, never repeating the just-shown one back-to-back.
  function nextActive() {
    if (!bag.length) {
      bag = pool.map((_, i) => i);
      for (let i = bag.length - 1; i > 0; i--) {
        const j = (Math.random() * (i + 1)) | 0;
        const tmp = bag[i]; bag[i] = bag[j]; bag[j] = tmp;
      }
      if (active && pool.length > 1 && pool[bag[0]] === active) {
        const tmp = bag[0]; bag[0] = bag[1]; bag[1] = tmp;
      }
    }
    return pool[bag.shift()];
  }
  // re-roll universal variety knobs whenever the active scene changes, so a
  // recurring demoscene mode is mirrored/flipped/timed differently each time
  function rerollFX() {
    // weighted: mostly NONE, sometimes a single cheap mirror (2x draw),
    // quad (4x) rare, kaleido removed — symmetry was tanking the framerate
    // across every effect.
    const r = Math.random();
    fxSym = r < 0.55 ? 0 : r < 0.80 ? 1 : r < 0.93 ? 2 : 3;
    fxFlip = Math.random() < 0.25;
    fxTime = 0.92 + Math.random() * 0.22;     // ~1x: gentle vary, no crawl/runaway
  }
  function drawActive(env) {
    const isDemo = demoSet.has(active);
    if (!isDemo || fxSym === 0 && !fxFlip) { active.draw(eng, env); return; }
    const C = eng.cols, R = eng.rows, op = eng.plot.bind(eng);
    eng.plot = (x, y, g, c, z) => {
      x |= 0; y |= 0;
      if (fxFlip) y = R - 1 - y;
      op(x, y, g, c, z);
      if (fxSym === 1 || fxSym >= 3) op(C - 1 - x, y, g, c, z);
      if (fxSym === 2 || fxSym >= 3) op(x, R - 1 - y, g, c, z);
      if (fxSym >= 3) op(C - 1 - x, R - 1 - y, g, c, z);
      if (fxSym === 4) { op(y * (C / R) | 0, x * (R / C) | 0, g, c, z); }
    };
    try { active.draw(eng, env); } finally { eng.plot = op; }
  }
  function mix(a, b, k) {
    const L = window.Palette.lerpRgb;
    const n = Math.max(a.accent.length, b.accent.length), ac = [];
    for (let i = 0; i < n; i++)
      ac.push(L(a.accent[i % a.accent.length], b.accent[i % b.accent.length], k));
    return { bg: L(a.bg, b.bg, k), fg: L(a.fg, b.fg, k), accent: ac };
  }
  const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

  function nextWorld(section) {
    const sc = section && section.visuals && section.visuals.scene;
    if (sc === 'glyphfield' && window.Worlds.Glyph) return window.Worlds.Glyph;
    return nextActive();
  }

  window.Renderer = {
    init(canvas) {
      eng = new window.A3D(canvas);
      buildPool();
      window.addEventListener('resize', () => { eng.resize(); if (active && active.reset) active.reset(eng); });
      // LOCAL TESTING: each browser refresh steps to the NEXT effect in the
      // pool (deterministic walk via localStorage), so you can review them
      // one by one. In-session rotation still uses the shuffle-bag.
      let idx = 0;
      try {
        idx = (parseInt(window.localStorage.getItem('str_fx_idx'), 10) || 0);
        if (!(idx >= 0) || idx >= pool.length) idx = 0;
        window.localStorage.setItem('str_fx_idx', String((idx + 1) % pool.length));
      } catch (e) { idx = 0; }
      active = pool[idx] || nextActive();
      if (active.reset) active.reset(eng);
      rerollFX(); announceEffect();
      announceEffect();
    },
    onSection(section) {
      setNowPlaying(section);
      prevPal = { bg: curPal.bg.slice(), fg: curPal.fg.slice(), accent: curPal.accent.map((x) => x.slice()) };
      // every new music style -> fade to the NEXT distinct curated palette
      palIdx = (palIdx + 1) % PALETTES.length;
      tgtPal = window.Palette.normalize(PALETTES[palIdx]);
      palDur = 4.0;                      // clearly visible crossfade
      palT = 0;
      // NOTE: a music-section change only fades the palette. The visual
      // EFFECT runs on its own independent 30s clock (see frame()), so
      // visuals and genre change at different rates.
    },
    onNoteOn(n) {
      const v = (n && n.vel) ? n.vel : 0.7, ch = n ? n.ch : 1;
      noteE = Math.min(1.5, noteE + 0.14 + v * 0.14);
      hitE = 1;
      if (typeof n.pitch === 'number') lastPitch = ((n.pitch % 24) / 24);
      if (ch === 0) bassE = Math.min(1.5, bassE + 0.35 + v * 0.3);
      else if (ch === 9) drumE = Math.min(1.5, drumE + 0.3 + v * 0.3);
      else leadE = Math.min(1.5, leadE + 0.3 + v * 0.35);
      if (active && active.note) active.note(n);
    },
    onBeat() { beatEnv = 1; beatKick = 1; if (active && active.beat) active.beat(); },
    frame(dt) {
      if (!eng) return;
      vT += dt * SPEED;                 // slowed autonomous clock
      const curT = vT;
      if (palT < 1) palT = Math.min(1, palT + dt / palDur);
      curPal = mix(prevPal, tgtPal, ease(palT));
      beatEnv = Math.max(0, beatEnv - dt / 0.26);
      beatKick = Math.max(0, beatKick - dt / 0.13);
      noteE = Math.max(0, noteE - dt * 1.6);
      bassE = Math.max(0, bassE - dt * 2.4);
      leadE = Math.max(0, leadE - dt * 2.2);
      drumE = Math.max(0, drumE - dt * 3.0);
      hitE = Math.max(0, hitE - dt * 6);
      // composite musical motion — beat AND notes AND per-instrument energy
      mv = Math.min(1.6, beatEnv * 0.7 + noteE * 0.7 + drumE * 0.5
        + hitE * 0.4 + bassE * 0.3);

      // visuals change on their OWN 30s clock, independent of the music genre
      sinceCut += dt;
      if (sinceCut > 30) {
        active = nextActive();
        if (active.reset) active.reset(eng);
        rerollFX(); announceEffect();
        sinceCut = 0;
      }
      // camera SWIMS with the music (energy/bass/drums/pitch), not just beat
      eng.fx.dyaw = Math.sin(curT * 0.7) * 0.02 + (lastPitch - 0.5) * 0.35 * mv
        + Math.sin(curT * 3.1) * 0.03 * leadE;
      eng.fx.dpitch = Math.sin(curT * 0.9) * 0.015 + bassE * 0.05;
      eng.fx.droll = Math.sin(curT * 0.5) * 0.02 + (beatKick + drumE * 0.5) * 0.10;
      eng.fx.dfov = -mv * 0.22;                 // strong musical zoom
      eng.fx.dy = (beatKick + bassE * 0.6) * 0.18;
      eng.fx.dz = mv * 0.22 + bassE * 0.2;

      const env = {
        pal: curPal, t: curT,
        beat: Math.min(1.4, beatEnv * 0.9 + noteE * 0.6 + hitE * 0.5),  // = music motion
        energy: Math.min(1.4, noteE + drumE * 0.4),
        hit: hitE, bass: bassE, lead: leadE, drum: drumE, pitch: lastPitch,
        mv: mv,
      };
      const isDemo = demoSet.has(active);
      if (active.step) active.step(dt * SPEED * (FXSPEED[active.title] || 1) * (isDemo ? fxTime : 1), env);
      eng.clear(curPal.bg);
      drawActive(env);              // applies per-appearance symmetry/flip
      drawHud();                    // grid-aligned HUD, top-most
      eng.flush();
    },
  };
})();
