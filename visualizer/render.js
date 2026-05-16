// render.js — SceneManager: owns the A3D engine, rotates a big pool of worlds
// (classic 3D + demoscene effects), lerps the palette, runs the cinematic
// camera overlay, and draws a PERSISTENT sine-scroller on top that continues
// across scene changes. window.Renderer keeps main.js's API.
(function () {
  // compact 5x7 uppercase bitmap font for the scroller
  const F = {
    A: ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    B: ['11110', '10001', '11110', '10001', '10001', '10001', '11110'],
    C: ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
    D: ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    E: ['11111', '10000', '11110', '10000', '10000', '10000', '11111'],
    F: ['11111', '10000', '11110', '10000', '10000', '10000', '10000'],
    G: ['01111', '10000', '10000', '10111', '10001', '10001', '01111'],
    H: ['10001', '10001', '11111', '10001', '10001', '10001', '10001'],
    I: ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
    J: ['00111', '00010', '00010', '00010', '10010', '10010', '01100'],
    K: ['10001', '10010', '11100', '10100', '11010', '10010', '10001'],
    L: ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    M: ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    N: ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    O: ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    P: ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    Q: ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
    R: ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    S: ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    T: ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    U: ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
    V: ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    W: ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
    X: ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    Y: ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    Z: ['11111', '00010', '00100', '01000', '10000', '10000', '11111'],
    0: ['01110', '10011', '10101', '10101', '10101', '11001', '01110'],
    1: ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    2: ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
    3: ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    4: ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    5: ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    6: ['01110', '10000', '11110', '10001', '10001', '10001', '01110'],
    7: ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    8: ['01110', '10001', '01110', '10001', '10001', '10001', '01110'],
    9: ['01110', '10001', '10001', '01111', '00001', '00001', '01110'],
    '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'],
    ',': ['00000', '00000', '00000', '00000', '01100', '01100', '11000'],
    '!': ['00100', '00100', '00100', '00100', '00100', '00000', '00100'],
    '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
    ':': ['00000', '01100', '01100', '00000', '01100', '01100', '00000'],
    '*': ['00000', '10101', '01110', '11111', '01110', '10101', '00000'],
    '/': ['00001', '00010', '00100', '00100', '01000', '10000', '10000'],
    "'": ['00100', '00100', '01000', '00000', '00000', '00000', '00000'],
    ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
  };
  const DEFAULT_MSG =
    'STR  //  ASCII DEMOSCENE AUDIOVISUAL  //  GENERATED LIVE  '
    + '//  GREETINGS TO ALL DEMO SCENERS  //  STAY FUNKY AS FUCK  ...  ';

  let eng, active, t0 = performance.now();
  let prevPal = window.Palette.normalize(null);
  let tgtPal = window.Palette.normalize(null);
  let curPal = window.Palette.normalize(null);
  let palT = 1, palDur = 4, beatEnv = 0, beatKick = 0, noteE = 0;
  // per-instrument musical energy so visuals move with the WHOLE music
  let bassE = 0, leadE = 0, drumE = 0, hitE = 0, lastPitch = 0.5, mv = 0;
  let pool = [], poolIdx = 0, sinceCut = 0, palIdx = 0;
  let scrollMsg = DEFAULT_MSG, scrollX = 0, llmScroll = null;

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
    const el = typeof document !== 'undefined' && document.getElementById('hud-effect');
    if (el && active) el.textContent = 'EFFECT · ' + (active.title || 'SCENE');
  }

  let demoSet = new Set();
  let fxSym = 0, fxFlip = false, fxTime = 1;
  function buildPool() {
    const W = window.Worlds || {};
    pool = [].concat(W.classics || [], W.demos || []);
    if (!pool.length) pool = [W.Glyph].filter(Boolean);
    demoSet = new Set(W.demos || []);
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
    const w = pool[poolIdx % pool.length];
    poolIdx++;
    return w;
  }

  // Amiga sine scroller: small rigid glyphs scrolling fast R->L; each char's
  // vertical position rides a sine that is fixed in SCREEN space (slow drift),
  // so the text visibly travels along a clean standing wave.
  function drawScroller(env) {
    const C = eng.cols, R = eng.rows;
    const PX = 1, GW = 6;                 // 5x7 glyph + 1 spacing
    const amp = Math.max(3, R * 0.20);
    const midRow = R * 0.5;
    const total = scrollMsg.length * GW;
    scrollX %= total;
    for (let i = 0; i < scrollMsg.length; i++) {
      const ch = scrollMsg[i].toUpperCase();
      const g = F[ch] || F[' '];
      const charX = (i * GW - scrollX) | 0;
      if (charX < -GW || charX > C) continue;
      // sine is a function of SCREEN x (+ slow drift) -> proper travelling wave
      const off = Math.sin(charX * 0.07 + env.t * 1.1) * amp;
      const top = (midRow + off - 3.5) | 0;
      const base = env.pal.accent[(i + ((env.t * 4) | 0)) % env.pal.accent.length];
      const col = [Math.min(255, base[0] + 55), Math.min(255, base[1] + 55), Math.min(255, base[2] + 55)];
      for (let ry = 0; ry < 7; ry++) for (let rx = 0; rx < 5; rx++) {
        if (g[ry][rx] === '1') eng.glyph2d(charX + rx, top + ry, '#', col);
      }
    }
  }

  window.Renderer = {
    init(canvas) {
      eng = new window.A3D(canvas);
      buildPool();
      window.addEventListener('resize', () => { eng.resize(); if (active && active.reset) active.reset(eng); });
      active = pool[0];
      if (active.reset) active.reset(eng);
      rerollFX(); announceEffect();
      announceEffect();
    },
    onSection(section) {
      prevPal = { bg: curPal.bg.slice(), fg: curPal.fg.slice(), accent: curPal.accent.map((x) => x.slice()) };
      // every new music style -> fade to the NEXT distinct curated palette
      palIdx = (palIdx + 1) % PALETTES.length;
      tgtPal = window.Palette.normalize(PALETTES[palIdx]);
      palDur = 4.0;                      // clearly visible crossfade
      palT = 0;
      // scroller precedence: live LLM scribe text > section.scrolltext >
      // section text_strings > default. The scribe (if running) wins.
      if (!llmScroll) {
        const sc = section && section.scrolltext;
        const ts = section && section.visuals && section.visuals.text_strings;
        if (typeof sc === 'string' && sc.trim().length > 20) {
          scrollMsg = '  ' + sc.trim().toUpperCase() + '   ***   ';
        } else if (ts && ts.length) {
          scrollMsg = '  ' + ts.join('   ***   ').toUpperCase()
            + '   ***   STR DEMOSCENE   ***   ';
        } else scrollMsg = DEFAULT_MSG;
      }
      // NOTE: a music-section change only fades the palette + swaps the
      // scroller. The visual EFFECT runs on its own independent 30s clock
      // (see frame()), so visuals and genre change at different rates.
    },
    setScroll(text) {
      if (typeof text !== 'string' || !text.trim()) return;
      llmScroll = text.trim();
      scrollMsg = '  ' + llmScroll.toUpperCase().replace(/\s+/g, ' ') + '   ***   ';
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
      const curT = (performance.now() - t0) / 1000;
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
      scrollX += dt * (34 + mv * 10);          // readable; only a gentle music lilt

      // visuals change on their OWN 30s clock, independent of the music genre
      sinceCut += dt;
      if (sinceCut > 30) {
        active = pool[poolIdx++ % pool.length];
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
      if (active.step) active.step(dt * (isDemo ? fxTime : 1), env);
      eng.clear(curPal.bg);
      drawActive(env);              // applies per-appearance symmetry/flip
      drawScroller(env);            // persists on top, every frame
      eng.flush();
    },
  };
})();
