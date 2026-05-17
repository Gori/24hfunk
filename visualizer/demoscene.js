// demoscene.js — Amiga-demo inspired ASCII effects. Each: title, reset(eng,
// section), note(n), beat(), step(dt,env), draw(eng,env). Registered into
// window.Worlds.demos and rotated by the manager. env={pal,beat,t}.
(function () {
  const acc = (e, i) => {
    const A = e.pal.accent, n = A.length;
    const k = (((Math.floor(i) % n) + n) % n) | 0;
    return A[k] || A[0];
  };
  const mul = (c, k) => [Math.min(255, c[0] * k) | 0, Math.min(255, c[1] * k) | 0, Math.min(255, c[2] * k) | 0];
  const lerpC = (a, b, k) => [a[0] + (b[0] - a[0]) * k | 0, a[1] + (b[1] - a[1]) * k | 0, a[2] + (b[2] - a[2]) * k | 0];
  const RMP = ' .:-=+*o%#@█';
  const gly = (b) => RMP[Math.max(0, Math.min(RMP.length - 1, (b * (RMP.length - 1)) | 0))];
  // current song name (set by render.js from the LLM section.name), sanitised
  // to the A-Z/space the bitmap font supports. Text effects render THIS.
  const _song = () => String((window.Worlds && window.Worlds.song) || '')
    .toUpperCase().replace(/[^A-Z ]+/g, ' ').replace(/\s+/g, ' ').trim();
  const SONG_FULL = () => _song() || 'STR FUNK';
  const SONG_WORD = () => {
    const p = _song().split(' ').filter(Boolean);
    return p.length ? p[(Math.random() * p.length) | 0] : 'STR';
  };

  // ---- 1. PLASMA ----
  const Plasma = {
    title: 'PLASMA', t: 0, reset() { this.t = 0; }, note() {}, beat() { this.t += 0.4; },
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, t = this.t;
      for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
        const v = Math.sin(x * 0.16 + t) + Math.sin(y * 0.22 - t * 1.3)
          + Math.sin((x + y) * 0.12 + t * 0.7) + Math.sin(Math.hypot(x - C / 2, y - R / 2) * 0.18 - t * 2);
        const k = (v + 4) / 8;
        const col = lerpC(acc(env, 0), acc(env, 1), (Math.sin(v + t) + 1) / 2);
        const g = gly(0.2 + k * 0.8), c = mul(col, 0.5 + env.beat * 0.5 + k * 0.5);
        eng.plot(x, y, g, c, 500); eng.plot(x + 1, y, g, c, 500);
        eng.plot(x, y + 1, g, c, 500); eng.plot(x + 1, y + 1, g, c, 500);
      }
    },
  };

  // ---- 2. ROTOZOOMER ----
  const Roto = {
    title: 'ROTOZOOM', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, a = this.t * 0.6;
      const z = 0.5 + Math.sin(this.t * 0.4) * 0.35, ca = Math.cos(a) * z, sa = Math.sin(a) * z;
      for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
        const u = ((x - C / 2) * ca - (y - R / 2) * sa) | 0;
        const v = ((x - C / 2) * sa + (y - R / 2) * ca) | 0;
        const chk = ((u >> 2) + (v >> 2)) & 1;
        const col = chk ? acc(env, 0) : acc(env, 1);
        eng.plot(x, y, chk ? '#' : '+', mul(col, 0.7 + env.beat * 0.3), 500);
      }
    },
  };

  // ---- 3. STARFIELD ----
  const Stars = {
    title: 'STARFIELD',
    reset(eng) { this.s = []; for (let i = 0; i < 260; i++) this.s.push(this._n()); },
    _n() { return { x: (Math.random() - 0.5) * 2, y: (Math.random() - 0.5) * 2, z: Math.random() * 1 + 0.1 }; },
    note() { this.warp = 1; }, beat() {},
    step(dt) { this.warp = Math.max(1, (this.warp || 1) - dt * 2); for (const p of this.s) { p.z -= dt * 0.55 * this.warp; if (p.z < 0.05) Object.assign(p, this._n(), { z: 1 }); } },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows;
      for (const p of this.s) {
        const sx = (C / 2 + (p.x / p.z) * C * 0.5) | 0, sy = (R / 2 + (p.y / p.z) * R * 0.5) | 0;
        const b = 1 - p.z;
        eng.plot(sx, sy, b > 0.7 ? '@' : b > 0.4 ? '*' : '.', mul(acc(env, b > 0.6 ? 2 : 0), 0.4 + b), 500);
      }
    },
  };

  // ---- 4. COPPER BARS ----
  const Copper = {
    title: 'COPPER', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows;
      for (let y = 0; y < R; y++) {
        for (let b = 0; b < 3; b++) {
          const cy = R / 2 + Math.sin(this.t * (0.7 + b * 0.3) + b * 2) * R * 0.42;
          const d = Math.abs(y - cy);
          if (d < 5) {
            const k = 1 - d / 5;
            const col = mul(acc(env, b), 0.3 + k * (0.8 + env.beat * 0.4));
            for (let x = 0; x < C; x++) eng.plot(x, y, gly(0.4 + k * 0.6), col, 600);
          }
        }
      }
    },
  };

  // ---- 5. VECTOR BOBS ----
  const Bobs = {
    title: 'VECTOR BOBS', reset() { this.t = 0; }, note() { this.t += 0.3; }, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows;
      for (let i = 0; i < 24; i++) {
        const p = i / 24 * 6.283 + this.t;
        const x = C / 2 + Math.sin(p * 1.0 + this.t) * C * 0.4;
        const y = R / 2 + Math.sin(p * 1.4 + this.t * 0.8) * R * 0.4;
        const col = acc(env, i % env.pal.accent.length);
        for (let dy = -2; dy <= 2; dy++) for (let dx = -3; dx <= 3; dx++)
          if (dx * dx / 9 + dy * dy / 4 <= 1)
            eng.plot((x + dx) | 0, (y + dy) | 0, dx === 0 && dy === 0 ? '@' : 'o',
              mul(col, 0.6 + env.beat * 0.4), 300 - i);
      }
    },
  };

  // ---- 6. TUNNEL ----
  const Tunnel = {
    title: 'TUNNEL', t: 0, reset() { this.t = 0; }, note() {}, beat() { this.t += 0.5; },
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows;
      const cx = C / 2, cy = R / 2, ix = 1 / cx, iy = 1 / cy, t2 = this.t * 2;
      for (let y = 0; y < R; y += 4) for (let x = 0; x < C; x += 4) {
        const dx = (x - cx) * ix, dy = (y - cy) * iy;
        const d = Math.sqrt(dx * dx + dy * dy) + 0.0001;
        const u = (1 / d * 1.4 + t2);
        const v = Math.atan2(dy, dx) / 6.283 * 16;
        const chk = ((u | 0) + (v | 0)) & 1;
        const sh = Math.min(1, d * 1.3);
        const g = chk ? gly(sh) : gly(sh * 0.5), c = mul(acc(env, chk ? 0 : 1), 0.15 + sh);
        for (let yy = 0; yy < 4; yy++) for (let xx = 0; xx < 4; xx++)
          eng.plot(x + xx, y + yy, g, c, 500);
      }
    },
  };

  // ---- 7. TWISTER ----
  const Twister = {
    title: 'TWISTER', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, cx = C / 2;
      for (let y = 0; y < R; y++) {
        const a = this.t * 1.5 + y * 0.12;
        for (let e = 0; e < 4; e++) {
          const ang = a + e * 1.5708;
          const x = cx + Math.sin(ang) * (C * 0.22);
          const front = Math.cos(ang) > 0;
          const col = mul(acc(env, e % 3), front ? 1 : 0.4);
          for (let w = -1; w <= 1; w++) eng.plot((x + w) | 0, y, front ? '#' : ':', col, 500 - (front ? 10 : 0));
        }
      }
    },
  };

  // ---- 8. FIRE ----
  const Fire = {
    title: 'FIRE',
    reset(eng) { this.w = eng.cols; this.h = eng.rows; this.b = new Float32Array(this.w * this.h); },
    note() {}, beat() { this.boost = 1; },
    step(dt) {
      const w = this.w, h = this.h, b = this.b;
      for (let x = 0; x < w; x++) b[(h - 1) * w + x] = Math.random() < 0.85 ? 1 : 0.5;
      for (let y = 0; y < h - 1; y++) for (let x = 0; x < w; x++) {
        const s = (b[(y + 1) * w + ((x - 1 + w) % w)] + b[(y + 1) * w + x] * 2
          + b[(y + 1) * w + ((x + 1) % w)] + b[Math.min(h - 1, y + 2) * w + x]) / 4.08;
        b[y * w + x] = s;
      }
      this.boost = Math.max(0, (this.boost || 0) - dt * 2);
    },
    draw(eng, env) {
      const w = this.w, h = this.h, b = this.b;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const v = Math.min(1, b[y * w + x] + this.boost * 0.2);
        if (v < 0.08) continue;
        const col = v > 0.75 ? acc(env, 2) : v > 0.4 ? acc(env, 0) : acc(env, 1);
        eng.plot(x, y, gly(v), mul(col, 0.4 + v * 0.8), 500);
      }
    },
  };

  // ---- 9. GLENZ VECTOR (rotating solid wireframe) ----
  const Glenz = {
    title: 'GLENZ', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.22;
      const v = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]];
      const E = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
      const a = this.t, b = this.t * 0.7;
      const P = v.map(([x, y, z]) => {
        let y1 = y * Math.cos(a) - z * Math.sin(a), z1 = y * Math.sin(a) + z * Math.cos(a);
        let x1 = x * Math.cos(b) - z1 * Math.sin(b); z1 = x * Math.sin(b) + z1 * Math.cos(b);
        const p = 3 / (3 + z1);
        return [C / 2 + x1 * s * p, R / 2 - y1 * s * p];
      });
      const drawL = (p0, p1, col) => {
        let [x0, y0] = p0, [x1, y1] = p1; x0 |= 0; y0 |= 0; x1 |= 0; y1 |= 0;
        const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
        let er = dx - dy, n = dx + dy + 1;
        while (n-- > 0) { eng.plot(x0, y0, '#', col, 400); if (x0 === x1 && y0 === y1) break; const e2 = 2 * er; if (e2 > -dy) { er -= dy; x0 += sx; } if (e2 < dx) { er += dx; y0 += sy; } }
      };
      E.forEach(([i, j], k) => drawL(P[i], P[j], mul(acc(env, k % 3), 0.7 + env.beat * 0.3)));
    },
  };

  // ---- 10. BOING BALL ----
  const Boing = {
    title: 'BOING', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows;
      for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 3)
        eng.plot(x, y, '+', mul(acc(env, 1), 0.18), 700);              // floor grid
      const cx = C / 2 + Math.sin(this.t * 1.3) * C * 0.32;
      const cy = R * 0.30 + Math.abs(Math.sin(this.t * 2.2)) * R * 0.34;
      const rr = Math.min(C * 0.13, R * 0.32), sp = this.t * 3;
      for (let yy = -rr; yy <= rr; yy++) for (let xx = -rr * 2; xx <= rr * 2; xx++) {
        const nx = xx / (rr * 2), ny = yy / rr;
        if (nx * nx + ny * ny > 1) continue;
        const lon = Math.atan2(nx, Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny))) + sp;
        const lat = Math.asin(ny);
        const chk = ((((lon / 0.5) | 0) + ((lat / 0.4) | 0)) & 1);
        eng.plot((cx + xx) | 0, (cy + yy) | 0, chk ? '@' : ' ',
          chk ? mul(acc(env, 0), 0.7 + env.beat * 0.3) : env.pal.bg,
          chk ? 300 : 9e8);
      }
    },
  };

  // ---- 11. METABALLS ----
  const Meta = {
    title: 'METABALLS', t: 0, reset() { this.t = 0; }, note() {}, beat() {},
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, t = this.t;
      const b = [[C / 2 + Math.sin(t) * C * 0.3, R / 2 + Math.cos(t * 1.3) * R * 0.3],
      [C / 2 + Math.sin(t * 1.7 + 2) * C * 0.32, R / 2 + Math.sin(t * 0.9) * R * 0.32],
      [C / 2 + Math.cos(t * 0.8) * C * 0.28, R / 2 + Math.cos(t * 1.5 + 1) * R * 0.3]];
      for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
        let s = 0;
        for (const [bx, by] of b) s += 30 / (Math.hypot(x - bx, (y - by) * 2) + 1);
        if (s > 1.0) {
          const g = gly(Math.min(1, (s - 1) * 0.6)), c = mul(acc(env, s > 2.4 ? 2 : 0), 0.4 + Math.min(0.9, s * 0.25));
          eng.plot(x, y, g, c, 500); eng.plot(x + 1, y, g, c, 500);
          eng.plot(x, y + 1, g, c, 500); eng.plot(x + 1, y + 1, g, c, 500);
        }
      }
    },
  };

  // ---- 12. DOT SPHERE ----
  const DotSphere = {
    title: 'DOTSPHERE', t: 0, reset() { this.t = 0; }, note() {}, beat() { this.t += 0.25; },
    step(dt) { this.t += dt; },
    draw(eng, env) {
      const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.34, a = this.t, b = this.t * 0.6;
      for (let i = 0; i < 360; i += 7) for (let j = 0; j < 180; j += 11) {
        const th = i * 0.0174, ph = j * 0.0174;
        let x = Math.sin(ph) * Math.cos(th), y = Math.cos(ph), z = Math.sin(ph) * Math.sin(th);
        let y1 = y * Math.cos(a) - z * Math.sin(a), z1 = y * Math.sin(a) + z * Math.cos(a);
        let x1 = x * Math.cos(b) - z1 * Math.sin(b); z1 = x * Math.sin(b) + z1 * Math.cos(b);
        if (z1 < 0) continue;
        const p = 2.4 / (2.4 + z1);
        eng.plot((C / 2 + x1 * s * p) | 0, (R / 2 - y1 * s * p) | 0,
          z1 > 0.6 ? '@' : 'o', mul(acc(env, (j / 30) % 3 | 0), 0.4 + z1), 300);
      }
    },
  };

  // ===== big batch: Amiga / C64 / Atari / PC scene classics, beat-reactive =====
  // Every effect gets a fresh randomized parameter set on each reset, so a
  // recurring mode never looks the same twice -> effectively an endless demo.
  // this.P = { spd, amp, dens, dir, cj, ph, glyph } — effects read these.
  const E = (title, init, drawf) => ({
    title, t: 0,
    reset(eng, s) {
      const r = Math.random;
      this.P = {
        spd: 0.85 + r() * 0.45,       // time speed (tight: ~normal, gentle vary)
        amp: 0.65 + r() * 0.9,        // spatial amplitude
        dens: 0.5 + r() * 0.95,       // density / threshold
        dir: r() < 0.5 ? -1 : 1,      // rotation / scroll direction
        cj: (r() * 4) | 0,            // accent-colour offset
        ph: r() * 100,                // phase offset
        zoom: 0.7 + r() * 0.9,
        variant: (r() * 4) | 0,       // sub-mode (effects branch on this)
        warp: 0.6 + r() * 1.3,        // distortion amount
        rx: r() * 6.28, ry: r() * 6.28,  // random rotation axis seeds
        k1: 0.5 + r() * 2.5, k2: 0.5 + r() * 2.5,  // pattern constants
      };
      this.t = this.P.ph;
      this.bt = 0; this.nt = 0;
      if (init) init.call(this, eng, s);
    },
    note() { this.nt = 1; },
    beat() { this.bt = 1; this.t += 0.12 * this.P.spd; },
    step(dt) {
      this.t += dt * this.P.spd;
      this.bt = Math.max(0, (this.bt || 0) - dt * 4);
      this.nt = Math.max(0, (this.nt || 0) - dt * 3);
    },
    draw(eng, env) {
      // tint accent lookups with this effect's colour offset for variety
      const base = env.pal, P = this.P;
      // forward the WHOLE env (mv/bass/lead/drum/pitch + future fields) and
      // only override the palette with this effect's accent offset. Dropping
      // mv here made env.mv undefined -> NaN sizes -> black effects.
      // perf: reuse persistent env/pal/accent objects (this ran Object.assign
      // + accent.map every frame for the active demo -> constant GC churn).
      let e2 = env;
      if (base && base.accent) {
        const A = base.accent, n = A.length;
        let ac = this._ac;
        if (!ac || ac.length !== n) ac = this._ac = new Array(n);
        for (let i = 0; i < n; i++) ac[i] = A[(i + P.cj) % n];
        const pal = this._pal || (this._pal = {});
        pal.bg = base.bg; pal.fg = base.fg; pal.accent = ac;
        const o = this._e2 || (this._e2 = {});
        for (const k in env) o[k] = env[k];
        o.pal = pal;
        e2 = o;
      }
      drawf.call(this, eng, e2);
    },
  });
  const px = (eng, x, y, g, c, z) => eng.plot(x | 0, y | 0, g, c, z || 500);

  const Raster = E('RASTER BARS', null, function (eng, env) {
    // authentic copper/raster bars: a few THICK shaded bands over empty bg,
    // drawn with the fast hspan (no per-cell plot, no symmetry multiply).
    const C = eng.cols, R = eng.rows, N = 6, half = 4;
    for (let b = 0; b < N; b++) {
      const cy = R / 2 + Math.sin(this.t * (0.5 + b * 0.22) + b * 1.6 * this.P.dir)
        * R * 0.42 * this.P.amp;
      const base = acc(env, (b + (this.t | 0)) % env.pal.accent.length);
      for (let d = -half; d <= half; d++) {
        const k = (1 - Math.abs(d) / half);                 // bright core
        eng.hspan(cy + d, 0, C - 1, gly(0.4 + k * 0.6),
          mul(base, 0.22 + k * (0.75 + env.beat * 0.45)), 200 + b);
      }
    }
  });
  const Kefrens = E('KEFRENS BARS', function () { this.h = []; }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const x = (C / 2 + Math.sin(this.t * 1.7) * C * 0.42) | 0;
    this.h.unshift(x); if (this.h.length > R) this.h.pop();
    for (let y = 0; y < this.h.length; y++) {
      const bx = this.h[y];
      for (let w = -6; w <= 6; w++) {
        const k = 1 - Math.abs(w) / 6;
        px(eng, bx + w, y, gly(k), mul(acc(env, y % 3), 0.3 + k * (0.7 + env.beat * 0.4)), 400 + y);
      }
    }
  });
  const Shadebobs = E('SHADEBOBS', function (eng) { this.b = new Float32Array(eng.cols * eng.rows); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, b = this.b;
    for (let i = 0; i < b.length; i++) b[i] *= 0.86;
    for (let k = 0; k < 5; k++) {
      const cx = C / 2 + Math.sin(this.t * (1 + k * 0.3) + k) * C * 0.4;
      const cy = R / 2 + Math.cos(this.t * (1.3 + k * 0.2) + k * 2) * R * 0.4;
      for (let yy = -4; yy <= 4; yy++) for (let xx = -6; xx <= 6; xx++) {
        const X = (cx + xx) | 0, Y = (cy + yy) | 0;
        if (X < 0 || Y < 0 || X >= C || Y >= R) continue;
        b[Y * C + X] += (1 - (xx * xx / 36 + yy * yy / 16)) * 0.5;
      }
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
      const v = b[y * C + x]; if (v > 0.06) px(eng, x, y, gly(Math.min(1, v)), mul(acc(env, v > 1 ? 2 : 0), 0.4 + Math.min(0.9, v)));
    }
  });
  const Moire = E('MOIRE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const ax = C / 2 + Math.sin(this.t) * C * 0.3, ay = R / 2 + Math.cos(this.t * 1.2) * R * 0.3;
    const bx = C / 2 - Math.sin(this.t * 0.8) * C * 0.3, by = R / 2 - Math.cos(this.t) * R * 0.3;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const d1 = Math.hypot(x - ax, (y - ay) * 2), d2 = Math.hypot(x - bx, (y - by) * 2);
      const v = (Math.sin(d1 * 0.5) * Math.sin(d2 * 0.5));
      if (v > 0.2) {
        const g = v > 0.6 ? '#' : '+', c = mul(acc(env, v > 0.6 ? 0 : 1), 0.4 + v * (0.6 + env.beat * 0.4));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Road = E('VECTOR ROAD', null, function (eng, env) {
    // Outrun road via hspan per scanline (grass band + road band), no
    // per-cell loop, not symmetry-multiplied -> cheap.
    const C = eng.cols, R = eng.rows, hor = R * 0.42 | 0;
    const sky = acc(env, 2), grass = acc(env, 1);
    for (let y = 0; y < hor; y += 2)                 // faint sky bands
      eng.hspan(y, 0, C - 1, '`', mul(sky, 0.10 + (1 - y / hor) * 0.16), 800);
    for (let y = hor; y < R; y++) {
      const p = (y - hor) / (R - hor) + 0.05;
      const z = 1 / p, curve = Math.sin(this.t * 0.8 + z * 0.05) * 18;
      const w = (C * 0.06 + (1 - p) * C * 0.7) | 0;
      const cx = (C / 2 + curve / p) | 0;
      const seg = ((z * 1.5 + this.t * 12) | 0) & 1;
      const rd = seg ? acc(env, 0) : env.pal.fg;
      eng.hspan(y, 0, C - 1, ':', mul(grass, 0.16 + (seg ? 0.05 : 0)), 620);
      eng.hspan(y, cx - w, cx + w, gly(0.5 + (seg ? 0.4 : 0)),
        mul(rd, 0.5 + env.beat * 0.4), 600);
      if (seg) eng.hspan(y, cx - 1, cx + 1, '|',
        mul(env.pal.fg, 0.8), 590);                  // centre line
    }
  });
  const Mandel = E('MANDELBROT', null, function (eng, env) {
    // 2x downsample (compute 1/4 cells, fill 2x2) + lower cap -> ~5x faster
    const C = eng.cols, R = eng.rows, M = 20;
    const zoom = 0.6 + Math.sin(this.t * 0.2) * 0.5, ox = -0.745, oy = 0.113;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const cr = ox + (x / C - 0.5) * 3 / zoom, ci = oy + (y / R - 0.5) * 2.4 / zoom;
      let zr = 0, zi = 0, n = 0;
      while (n < M && zr * zr + zi * zi < 4) { const t = zr * zr - zi * zi + cr; zi = 2 * zr * zi + ci; zr = t; n++; }
      if (n < M) {
        const g = gly(n / M), c = mul(acc(env, n % 3), 0.3 + n / M + env.beat * 0.3);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Worm = E('WORMHOLE', null, function (eng, env) {
    // 4x downsample + hoisted consts/reciprocals, sqrt over hypot
    const C = eng.cols, R = eng.rows;
    const cx = C / 2, cy = R / 2, ix = 1 / cx, iy = 1 / cy;
    const t3 = this.t * 3, t2 = this.t * 2, bk = 0.7 + env.beat * 0.4;
    for (let y = 0; y < R; y += 4) for (let x = 0; x < C; x += 4) {
      const dx = (x - cx) * ix, dy = (y - cy) * iy;
      const a = Math.atan2(dy, dx), d = Math.sqrt(dx * dx + dy * dy) + 1e-3;
      const v = Math.sin(8 / d + t3) + Math.sin(a * 6 + t2);
      const k = (v + 2) / 4;
      const g = gly(k * (1 - d * 0.4));
      const c = mul(acc(env, (a * 3 | 0) % 3), 0.2 + k * bk);
      for (let yy = 0; yy < 4; yy++) for (let xx = 0; xx < 4; xx++)
        px(eng, x + xx, y + yy, g, c);
    }
  });
  const Life = E('LIFE', function (eng) {
    const C = eng.cols, R = eng.rows; this.g = new Uint8Array(C * R);
    for (let i = 0; i < this.g.length; i++) this.g[i] = Math.random() < 0.32 ? 1 : 0;
    this.acc = 0;
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g;
    this.acc = (this.acc || 0) + 1;
    if (this.acc % 4 === 0 || this.bt > 0.5) {
      const n = (this._n && this._n.length === C * R) ? this._n : (this._n = new Uint8Array(C * R)); n.fill(0);
      for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
        let s = 0;
        for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) {
          if (!i && !j) continue;
          s += g[((y + j + R) % R) * C + ((x + i + C) % C)];
        }
        const a = g[y * C + x];
        n[y * C + x] = (a && (s === 2 || s === 3)) || (!a && s === 3) ? 1 : 0;
      }
      if (this.bt > 0.5) for (let k = 0; k < 30; k++) n[(Math.random() * n.length) | 0] = 1;
      this.g = n; this._n = g;          // ping-pong: old field -> next scratch
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++)
      if (this.g[y * C + x]) px(eng, x, y, env.beat > 0.4 ? '#' : 'o', mul(acc(env, 0), 0.6 + env.beat * 0.4));
  });
  const XOR = E('AURORA', null, function (eng, env) {
    // shimmering vertical aurora curtains — flowing, music-reactive
    const C = eng.cols, R = eng.rows, t = this.t, P = this.P;
    for (let x = 0; x < C; x++) {
      const fx = x * 0.05 * P.k1;
      const base = R * 0.5
        + Math.sin(fx + t * 1.1) * R * 0.22 * P.amp
        + Math.sin(fx * 2.3 - t * 0.7) * R * 0.12;
      const h = R * (0.16 + 0.14 * (0.5 + 0.5 * Math.sin(fx * 1.7 + t * 1.6)))
        * (1 + env.mv * 0.6);
      const ci = (x * 0.04 + t * 0.5 | 0);
      const c0 = acc(env, ci), c1 = acc(env, ci + 1);   // per-column, hoisted
      // iterate ONLY the lit band, not every row
      const y0 = Math.max(0, (base - h) | 0);
      const y1 = Math.min(R - 1, (base + h) | 0);
      for (let y = y0; y <= y1; y++) {
        const d = Math.abs(y - base);
        const k = (1 - d / h) * (0.55 + 0.45 * Math.sin(fx + y * 0.12 - t * 3))
          + env.beat * 0.4;
        if (k < 0.12) continue;
        const yr = y / R;
        const c = [c0[0] + (c1[0] - c0[0]) * yr | 0, c0[1] + (c1[1] - c0[1]) * yr | 0,
          c0[2] + (c1[2] - c0[2]) * yr | 0];
        px(eng, x, y, gly(Math.min(1, k)), mul(c, 0.3 + Math.min(0.95, k)));
      }
      if (Math.random() < 0.04 + env.hit * 0.1)        // sparkle
        px(eng, x, (base + (Math.random() - 0.5) * h * 2) | 0, '*',
          mul(acc(env, ci + 2), 0.7 + env.beat * 0.3), 200);
    }
  });
  const Ripple = E('RIPPLE', function () { this.src = []; }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    if (this.nt > 0.6 && (this.src.length === 0 || this.src[this.src.length - 1].a > 0.5))
      this.src.push({ x: Math.random() * C, y: Math.random() * R, a: 0 });
    if (this.src.length === 0) this.src.push({ x: C / 2, y: R / 2, a: 0 });
    for (const s of this.src) s.a += 0.04;
    this.src = this.src.filter((s) => s.a < 8);
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      let v = 0;
      for (const s of this.src) v += Math.sin(Math.hypot(x - s.x, (y - s.y) * 2) * 0.5 - s.a * 6) / (1 + s.a);
      const av = Math.abs(v);
      if (av > 0.15) {
        const g = gly(av), c = mul(acc(env, v > 0 ? 0 : 1), 0.3 + Math.min(0.9, av + env.beat * 0.3));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Helix = E('DNA HELIX', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let y = 0; y < R; y++) {
      const a = y * 0.28 + this.t * 2.5;
      const x1 = C / 2 + Math.sin(a) * C * 0.28, x2 = C / 2 + Math.sin(a + Math.PI) * C * 0.28;
      const f1 = Math.cos(a) > 0;
      px(eng, x1, y, f1 ? '@' : 'o', mul(acc(env, 0), f1 ? 1 : 0.5), f1 ? 300 : 320);
      px(eng, x2, y, !f1 ? '@' : 'o', mul(acc(env, 1), !f1 ? 1 : 0.5), !f1 ? 300 : 320);
      if (y % 3 === 0) {
        let xa = x1 | 0, xb = x2 | 0, s = xa < xb ? 1 : -1;
        for (let x = xa; x !== xb; x += s) px(eng, x, y, '-', mul(acc(env, 2), 0.3 + env.beat * 0.4), 350);
      }
    }
  });
  const Starburst = E('STARBURST', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, n = 28, rad = (Math.min(C / 2, R) * (0.4 + env.beat * 0.5));
    for (let i = 0; i < n; i++) {
      const a = i / n * 6.283 + this.t * (1 + env.energy);
      for (let r = 2; r < rad; r += 1.5)
        px(eng, C / 2 + Math.cos(a) * r, R / 2 + Math.sin(a) * r * 0.6,
          gly(1 - r / rad), mul(acc(env, i % 3), 0.3 + (1 - r / rad) * (0.7 + env.beat * 0.5)));
    }
  });
  const Rain = E('DIGITAL RAIN', function (eng) { this.d = []; for (let i = 0; i < eng.cols; i += 2) this.d.push({ x: i, y: Math.random() * eng.rows, s: 8 + Math.random() * 18 }); }, function (eng, env) {
    const R = eng.rows, gs = '01<>[]{}/\\|=+*'.split('');
    for (const c of this.d) {
      c.y += c.s * 0.03 * (1 + env.beat); if (c.y > R + 12) { c.y = -2; c.s = 8 + Math.random() * 18; }
      for (let k = 0; k < 12; k++) {
        const yy = (c.y - k) | 0;
        px(eng, c.x, yy, gs[(yy + k) % gs.length], mul(acc(env, k === 0 ? 2 : 0), k === 0 ? 1 : 0.5 - k * 0.035), 400);
      }
    }
  });
  const Torus = E('TORUS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, A = this.t, B = this.t * 0.5;
    for (let th = 0; th < 6.28; th += 0.22) for (let ph = 0; ph < 6.28; ph += 0.1) {
      const cr = 1 + 0.45 * Math.cos(ph);
      let x = cr * Math.cos(th), y = 0.45 * Math.sin(ph), z = cr * Math.sin(th);
      let y1 = y * Math.cos(A) - z * Math.sin(A), z1 = y * Math.sin(A) + z * Math.cos(A);
      let x1 = x * Math.cos(B) - z1 * Math.sin(B); z1 = x * Math.sin(B) + z1 * Math.cos(B);
      if (z1 < -1.4) continue;
      const p = 2.5 / (3 + z1), L = (Math.cos(ph - A) + 1) / 2;
      px(eng, C / 2 + x1 * R * p, R / 2 - y1 * R * p, gly(0.2 + L * 0.8), mul(acc(env, (ph * 2 | 0) % 3), 0.3 + L + env.beat * 0.3), 3 + z1);
    }
  });
  const Hex = E('HEX ZOOM', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, zo = 6 + Math.sin(this.t * 0.6) * 4 + env.beat * 3;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const q = (x - C / 2) / zo, r = (y - R / 2) / zo * 1.6;
      const hx = Math.abs(((q + r * 0.5) % 1 + 1) % 1 - 0.5) + Math.abs(((r) % 1 + 1) % 1 - 0.5);
      const v = 1 - hx;
      if (v > 0.45) {
        const g = gly(v), c = mul(acc(env, ((q | 0) + (r | 0)) % 3), 0.3 + v * (0.7 + env.beat * 0.4));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Lissa = E('LISSAJOUS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, a = 3 + Math.sin(this.t * 0.2), b = 2 + Math.cos(this.t * 0.17);
    for (let i = 0; i < 700; i++) {
      const t = i * 0.02 + this.t;
      px(eng, C / 2 + Math.sin(a * t) * C * 0.44, R / 2 + Math.sin(b * t + this.t) * R * 0.44,
        '*', mul(acc(env, i % 3), 0.4 + env.beat * 0.5), 300);
    }
  });
  const PlasTun = E('PLASMA TUNNEL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const dx = (x - C / 2) / (C / 2), dy = (y - R / 2) / (R / 2), d = Math.hypot(dx, dy) + 1e-3;
      const u = 1 / d + this.t * 2, a = Math.atan2(dy, dx) * 3;
      const v = (Math.sin(u) + Math.sin(a + this.t) + Math.sin(u * 0.5 + a)) / 3;
      const k = (v + 1) / 2;
      const g = gly(k * Math.min(1, d * 1.5)), c = mul(lerpC(acc(env, 0), acc(env, 1), k), 0.3 + k + env.beat * 0.3);
      px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
      px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
    }
  });
  const VBallGrid = E('VECTOR BALL GRID', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let gy = 0; gy < 5; gy++) for (let gx = 0; gx < 7; gx++) {
      const ph = this.t * 2 + gx * 0.5 + gy * 0.4;
      const x = (gx + 1) / 8 * C, y = (gy + 1) / 6 * R + Math.sin(ph) * R * 0.12 * (1 + env.beat);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -2; dx <= 2; dx++)
        if (dx * dx / 4 + dy * dy <= 1) px(eng, x + dx, y + dy, dx || dy ? 'o' : '@', mul(acc(env, (gx + gy) % 3), 0.5 + env.beat * 0.5), 300);
    }
  });
  const Spiral = E('COLOR SPIRAL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    // perf: a (angle) & d (radius) depend only on x,y — cache the
    // time-invariant phase (a*4 + d*0.3) and colour angle once; per frame
    // only sin(phase - t*4) (was atan2+hypot per cell every frame).
    if (!this._ph || this._pw !== C || this._phh !== R) {
      this._pw = C; this._phh = R;
      const ph = this._ph = new Float32Array(C * R);
      const ca = this._ca = new Float32Array(C * R);
      for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
        const dx = x - C / 2, dy = (y - R / 2) * 2;
        const a = Math.atan2(dy, dx), d = Math.sqrt(dx * dx + dy * dy);
        const i = y * C + x;
        ph[i] = a * 4 + d * 0.3; ca[i] = a * 0.5;
      }
    }
    const ph = this._ph, ca = this._ca, t = this.t, bb = 0.7 + env.beat * 0.4;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const i = y * C + x, v = Math.sin(ph[i] - t * 4);
      if (v > 0) {
        const g = gly(v), c = mul(acc(env, ((ca[i] + t) | 0) % 3), 0.3 + v * bb);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Checker = E('CHECKER FLOOR', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, hor = (R * 0.4) | 0;
    // sky: flat per-row gradient -> one hspan per row (was hor*C plots)
    for (let y = 0; y < hor; y++)
      eng.hspan(y, 0, C - 1, '.', mul(acc(env, 2), 0.05 + (y / hor) * 0.12), 800);
    // floor: 2x downsample + skip the empty squares entirely (was drawing bg)
    for (let y = hor; y < R; y += 2) {
      const z = 1 / ((y - hor) / (R - hor) + 0.04);
      const wz = z + this.t * 6;
      const col = mul(acc(env, 0), 0.3 + (1 - y / R) + env.beat * 0.3);
      for (let x = 0; x < C; x += 2) {
        const wx = (x - C / 2) * z * 0.06;
        if (((wx | 0) + (wz | 0)) & 1) {
          px(eng, x, y, '#', col, 600); px(eng, x + 1, y, '#', col, 600);
          px(eng, x, y + 1, '#', col, 600); px(eng, x + 1, y + 1, '#', col, 600);
        }
      }
    }
  });
  const Burst3D = E('DOT EXPLOSION', function () { this.p = []; this._arm = false; }, function (eng, env) {
    const C = eng.cols, R = eng.rows, p = this.p;
    const burst = () => { for (let i = 0; i < 60; i++) p.push({ x: 0, y: 0, z: 0, vx: Math.random() - 0.5, vy: Math.random() - 0.5, vz: Math.random() - 0.5, l: 1 }); };
    // explode on the BPM beat: beat() fires every 16th (router sends
    // /vis/beat per 16th), so latch rising edges and burst every 4th =
    // one explosion per quarter-note beat, locked to tempo.
    if (this.bt > 0.5) {
      if (!this._arm) {
        this._bn = (this._bn || 0) + 1;
        if (this._bn % 4 === 1 && p.length < 600) burst();
      }
      this._arm = true;
    } else if (this.bt < 0.2) this._arm = false;
    if (p.length === 0) burst();
    let w = 0;                                   // in-place compact, no realloc
    for (let r = 0; r < p.length; r++) {
      const q = p[r];
      q.x += q.vx * 0.05; q.y += q.vy * 0.05; q.z += q.vz * 0.05; q.l -= 0.012;
      if (q.l <= 0) continue;
      const pz = 2 / (2 + q.z + 1);
      px(eng, C / 2 + q.x * C * pz, R / 2 - q.y * R * pz, q.l > 0.6 ? '@' : '*', mul(acc(env, 0), q.l), 300);
      p[w++] = q;
    }
    p.length = w;
  });
  const Interf = E('INTERFERENCE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const v = Math.sin(x * 0.3 + this.t * 2) + Math.sin(y * 0.4 - this.t) + Math.sin((x + y) * 0.2 + this.t * 1.5) + Math.sin(Math.hypot(x - C / 2, y - R / 2) * 0.25 - this.t * 3);
      const k = (v + 4) / 8;
      if (k > 0.35) {
        const g = gly(k), c = mul(acc(env, (k * 3 | 0) % 3), 0.25 + k * (0.7 + env.beat * 0.4));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Grid3D = E('WAVE GRID', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let gz = 1; gz < 22; gz++) for (let gx = -12; gx <= 12; gx++) {
      const wy = Math.sin(gx * 0.4 + this.t * 2) * Math.cos(gz * 0.3 + this.t) * (1 + env.beat);
      const z = gz + 2, sx = C / 2 + gx / z * C * 0.9, sy = R * 0.6 - wy * R * 0.12 / z * 8;
      px(eng, sx, sy, gz % 2 ? '+' : 'o', mul(acc(env, gz % 3), 0.2 + (1 - gz / 22) + env.beat * 0.3), z);
    }
  });

  // ---- batch 2: more scene classics (each varied via this.P) ----
  const RotBars = E('ROTO BARS', null, function (eng, env) {
    // fluid bars: a snaking baseline + 3 travelling sine octaves (different
    // speeds/directions) so it undulates organically; amplitude & scroll
    // breathe with the music. One vspan/column -> very cheap, smooth.
    const C = eng.cols, R = eng.rows, P = this.P, t = this.t;
    const sp = P.dir * (2 + env.mv * 3) * P.spd;
    const f1 = 0.05 * P.k1, f2 = 0.11 * P.k2, f3 = 0.21;
    const amp = (0.30 + 0.20 * Math.sin(t * 0.7) + env.beat * 0.22 + env.mv * 0.18) * P.amp;
    for (let x = 0; x < C; x++) {
      const base = R * 0.5 + Math.sin(x * f1 + t * 0.8) * R * 0.16 * P.warp
        + Math.sin(x * 0.03 - t * 0.5) * R * 0.08;
      const w = Math.sin(x * f1 + t * sp)
        + 0.55 * Math.sin(x * f2 - t * sp * 1.7)
        + 0.30 * Math.sin(x * f3 + t * sp * 2.6);
      const v = (w + 1.85) / 3.7;
      const h = Math.max(1, (v * R * amp) | 0);
      const y0 = (base - h) | 0, y1 = (base + h) | 0;
      const ci = (x * 0.05 + t * 0.6) | 0;
      const cap = mul(acc(env, (ci + 1) % 3), 0.7 + env.beat * 0.3);
      eng.vspan(x, y0, y1, gly(0.3 + v * 0.7),
        mul(lerpC(acc(env, ((ci % 3) + 3) % 3), acc(env, (ci + 1) % 3), v),
          0.28 + v * (0.72 + env.beat * 0.45)), 500);
      px(eng, x, y0, '#', cap, 480); px(eng, x, y1, '#', cap, 480);
    }
  });
  const StarCyl = E('STAR CYLINDER', function () { this.s = []; for (let i = 0; i < 220; i++) this.s.push({ a: Math.random() * 6.28, z: Math.random() * 10, r: 0.6 + Math.random() * 0.5 }); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P;
    for (const s of this.s) {
      s.z -= 0.06 * P.spd * (1 + env.beat); if (s.z < 0.2) s.z = 10;
      const x = C / 2 + Math.cos(s.a + this.t * 0.3 * P.dir) * s.r / s.z * C;
      const y = R / 2 + Math.sin(s.a + this.t * 0.3 * P.dir) * s.r / s.z * R;
      px(eng, x, y, s.z < 3 ? '@' : '*', mul(acc(env, 0), 1 - s.z / 10), s.z);
    }
  });
  const Rings = E('PULSE RINGS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P, n = 6;
    for (let i = 0; i < n; i++) {
      const rr = ((this.t * 8 * P.spd + i * 9) % 60) + 2 + env.beat * 6;
      for (let a = 0; a < 6.28; a += 0.08)
        px(eng, C / 2 + Math.cos(a) * rr, R / 2 + Math.sin(a) * rr * 0.6, gly(1 - rr / 60), mul(acc(env, i % 3), 0.4 + env.beat * 0.5));
    }
  });
  const Spectrum = E('SPECTRUM', function () { this.bars = new Float32Array(64); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, n = 48;
    for (let i = 0; i < n; i++) {
      const tgt = (0.2 + 0.8 * Math.abs(Math.sin(i * 0.5 + this.t * 4 * this.P.spd))) * (0.4 + env.energy + env.beat);
      this.bars[i] += (tgt - this.bars[i]) * 0.3;
      const h = Math.min(R - 1, this.bars[i] * R * 0.8) | 0;
      const bx = (i / n * C) | 0, bw = (C / n) | 0;
      for (let y = 0; y < h; y++) for (let w = 0; w < bw - 1; w++)
        px(eng, bx + w, R - 1 - y, gly(0.4 + y / h * 0.6), mul(acc(env, y > h * 0.7 ? 2 : 0), 0.4 + y / h));
    }
  });
  const Julia = E('JULIA', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, M = 20;          // 2x downsample + cap
    const cr = 0.355 + Math.sin(this.t * 0.3) * 0.2, ci = 0.355 + Math.cos(this.t * 0.21) * 0.2;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      let zr = (x / C - 0.5) * 3.2 / this.P.zoom, zi = (y / R - 0.5) * 2.6 / this.P.zoom, n = 0;
      while (n < M && zr * zr + zi * zi < 4) { const t = zr * zr - zi * zi + cr; zi = 2 * zr * zi + ci; zr = t; n++; }
      if (n < M) {
        const g = gly(n / M), c = mul(acc(env, n % 3), 0.3 + n / M + env.beat * 0.3);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const DVD = E('BOUNCE LOGO', function (eng) {
    // bounce the SONG NAME (FNT5 full font), auto-scaled/truncated to fit.
    // _fit rebuilds whenever the song changes so it's never stuck on a
    // stale name (it used to capture once at reset -> 'STR FUNK' on refresh).
    this._fit = (src) => {
      let w = src, S = 2;
      while (S > 1 && w.length * 6 * S > eng.cols - 2) S--;
      const maxc = Math.max(1, ((eng.cols - 2) / (6 * S)) | 0);
      if (w.length > maxc) w = w.slice(0, maxc).trim();
      this.w = w; this.S = S; this._src = src;
    };
    this._fit(SONG_FULL());
    this.x = (eng.cols / 2) | 0; this.y = (eng.rows / 2) | 0;
    this.vx = this.P.dir * 22; this.vy = 14;
  }, function (eng, env) {
    const cur = SONG_FULL();
    if (cur !== this._src) this._fit(cur);          // song changed -> rebuild
    const C = eng.cols, R = eng.rows, w = this.w, S = this.S, GW = 6 * S;
    const W = w.length * GW, H = 7 * S;
    this.x += this.vx * 0.016 * this.P.spd; this.y += this.vy * 0.016 * this.P.spd;
    if (this.x < 1 || this.x > C - W) { this.vx *= -1; this.ci = (this.ci || 0) + 1; this.x = Math.max(1, Math.min(C - W, this.x)); }
    if (this.y < 1 || this.y > R - H - 1) { this.vy *= -1; this.ci = (this.ci || 0) + 1; this.y = Math.max(1, Math.min(R - H - 1, this.y)); }
    const col = mul(acc(env, (this.ci || 0) % 3), 0.6 + env.beat * 0.4);
    const ox = this.x | 0, oy = this.y | 0;
    for (let li = 0; li < w.length; li++) {
      const bmp = FNT5[w[li]] || FNT5[' ']; const lx = ox + li * GW;
      for (let ry = 0; ry < 7; ry++) for (let rx = 0; rx < 5; rx++)
        if (bmp[ry][rx] === '1')
          for (let s = 0; s < S; s++) for (let q = 0; q < S; q++)
            px(eng, lx + rx * S + s, oy + ry * S + q, '#', col);
    }
  });
  const PolarSwirl = E('POLAR SWIRL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const dx = x - C / 2, dy = (y - R / 2) * 2, a = Math.atan2(dy, dx), d = Math.hypot(dx, dy);
      const v = Math.sin(a * 5 * this.P.dir + d * 0.2 - this.t * 4);
      if (v > 1 - this.P.dens) {
        const g = gly(v), c = mul(acc(env, (d * 0.1 | 0) % 3), 0.3 + v * (0.6 + env.beat * 0.4));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const TunRings = E('TUNNEL RINGS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let i = 0; i < 18; i++) {
      const z = ((i * 1.0 - this.t * 4 * this.P.spd) % 18 + 18) % 18 + 0.5;
      const rr = (C * 0.55) / z;
      for (let a = 0; a < 6.28; a += 0.10)
        px(eng, C / 2 + Math.cos(a) * rr, R / 2 + Math.sin(a) * rr * 0.6, gly(1 - z / 18), mul(acc(env, i % 3), 0.25 + (1 - z / 18) + env.beat * 0.3), z);
    }
  });
  const DotWave = E('DOT WAVE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let gz = 1; gz < 26; gz++) for (let gx = -16; gx <= 16; gx++) {
      const w = Math.sin(gx * 0.3 + this.t * 3) * Math.cos(gz * 0.25 + this.t * 2) * this.P.amp;
      const z = gz + 1, sx = C / 2 + gx / z * C, sy = R * 0.62 - w * R * 0.1 / z * 7;
      px(eng, sx, sy, '+', mul(acc(env, gz % 3), 0.2 + (1 - gz / 26) + env.beat * 0.3), z);
    }
  });
  const WireSphere = E('WIRE SPHERE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.34, A = this.t * this.P.dir, B = this.t * 0.6;
    for (let la = -80; la <= 80; la += 20) for (let lo = 0; lo < 360; lo += 9) {
      const th = lo * 0.0174, ph = la * 0.0174;
      let x = Math.cos(ph) * Math.cos(th), y = Math.sin(ph), z = Math.cos(ph) * Math.sin(th);
      let y1 = y * Math.cos(A) - z * Math.sin(A), z1 = y * Math.sin(A) + z * Math.cos(A);
      let x1 = x * Math.cos(B) - z1 * Math.sin(B); z1 = x * Math.sin(B) + z1 * Math.cos(B);
      if (z1 < 0) continue;
      const p = 2.4 / (2.4 + z1);
      px(eng, C / 2 + x1 * s * p, R / 2 - y1 * s * p, z1 > 0.6 ? '@' : 'o', mul(acc(env, (la / 20 + 4 | 0) % 3), 0.4 + z1 + env.beat * 0.2), 3);
    }
  });
  const Glitch = E('DATAMOSH', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let y = 0; y < R; y += 2) {
      const sh = (Math.sin(y * 0.3 + this.t * 6) * 14 * (0.3 + env.beat) * this.P.amp) | 0;
      for (let x = 0; x < C; x += 2) {
        const v = (((x + sh) ^ y) + (this.t * 10 | 0)) & 15;
        const g = gly(v / 15), c = mul(acc(env, (sh & 3) % 3), 0.25 + v / 15 * (0.6 + env.beat * 0.5));
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Galaxy = E('GALAXY', function () { this.p = []; for (let i = 0; i < 400; i++) { const r = Math.random(); this.p.push({ r: r * 1, a: Math.random() * 6.28, arm: (Math.random() * 3 | 0) }); } }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (const q of this.p) {
      const a = q.a + this.t * (0.4 / (q.r + 0.2)) * this.P.dir + q.arm * 2.09;
      const x = C / 2 + Math.cos(a) * q.r * C * 0.46, y = R / 2 + Math.sin(a) * q.r * R * 0.46;
      px(eng, x, y, q.r < 0.3 ? '@' : '.', mul(acc(env, q.arm % 3), 0.4 + (1 - q.r) + env.beat * 0.3), 300);
    }
  });
  const Fireworks = E('FIREWORKS', function () { this.p = []; }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    if (this.bt > 0.5 || this.nt > 0.7) { const ox = Math.random() * C, oy = Math.random() * R * 0.6; for (let i = 0; i < 40; i++) { const a = i / 40 * 6.28, sp = 0.5 + Math.random(); this.p.push({ x: ox, y: oy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, l: 1, c: (Math.random() * 3 | 0) }); } }
    this.p = this.p.filter((q) => q.l > 0);
    for (const q of this.p) { q.x += q.vx; q.y += q.vy + (1 - q.l) * 0.6; q.l -= 0.02; px(eng, q.x, q.y, q.l > 0.5 ? '*' : '.', mul(acc(env, q.c), q.l), 300); }
  });
  const Metatun = E('META TUNNEL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const b = [[C / 2 + Math.sin(this.t) * C * 0.3, R / 2 + Math.cos(this.t * 1.3) * R * 0.3],
    [C / 2 + Math.cos(this.t * 0.8) * C * 0.3, R / 2 + Math.sin(this.t * 1.1) * R * 0.3]];
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const dx = (x - C / 2) / (C / 2), dy = (y - R / 2) / (R / 2), d = Math.hypot(dx, dy) + 1e-3;
      let s = Math.sin(1 / d * 1.4 + this.t * 2);
      for (const [bx, by] of b) s += 16 / (Math.hypot(x - bx, (y - by) * 2) + 1);
      const k = (s % 2 + 2) % 2 / 2;
      const g = gly(k * Math.min(1, d * 1.5)), c = mul(acc(env, (s | 0) % 3), 0.25 + k + env.beat * 0.3);
      px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
      px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
    }
  });
  const Cubes = E('CUBE FIELD', function () {
    this.cb = [];
    for (let i = 0; i < 11; i++) this.cb.push({
      ax: (Math.random() * 2 - 1) * 6, ay: (Math.random() * 2 - 1) * 4,
      z: 1 + Math.random() * 27, rx: Math.random() * 6, ry: Math.random() * 6,
      rz: Math.random() * 6, vx: (Math.random() - 0.5) * 1.0,
      vy: (Math.random() - 0.5) * 0.8, vz: (Math.random() - 0.5) * 1.0,
      s: 0.7 + Math.random() * 1.1, ci: (Math.random() * 3) | 0,
    });
    this._lt = 0;
  }, function (eng, env) {
    // a corridor of independently TUMBLING cubes streaming past — varied
    // size/colour/spin, depth-shaded, speed & pulse driven by the music.
    const C = eng.cols, R = eng.rows, P = this.P;
    let dt = env.t - (this._lt || env.t); if (dt < 0 || dt > 0.1) dt = 0.016;
    this._lt = env.t;
    const spd = (5 + env.mv * 6 + env.beat * 3) * P.spd;
    const F = Math.min(C, R * 2) * 0.15;
    const VV = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]];
    const EE = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
    for (const c of this.cb) {
      c.z -= spd * dt;
      c.rx += c.vx * dt * P.dir; c.ry += c.vy * dt; c.rz += c.vz * dt * P.dir;
      if (c.z < 1) {
        c.z += 28; c.ax = (Math.random() * 2 - 1) * 7; c.ay = (Math.random() * 2 - 1) * 4.5;
        c.ci = (Math.random() * 3) | 0; c.s = 0.7 + Math.random() * 1.1;
      }
      const cx = Math.cos(c.rx), sx = Math.sin(c.rx), cy = Math.cos(c.ry), sy = Math.sin(c.ry), cz = Math.cos(c.rz), sz = Math.sin(c.rz);
      const sc = c.s * (1 + env.beat * 0.18);
      const pr = VV.map(([x, y, z]) => {
        let y1 = y * cx - z * sx, z1 = y * sx + z * cx;
        let x1 = x * cy + z1 * sy; z1 = -x * sy + z1 * cy;
        const x2 = x1 * cz - y1 * sz, y2 = x1 * sz + y1 * cz;
        const dd = Math.max(0.4, c.z + z1);
        return [C / 2 + (c.ax + x2 * sc) / dd * F, R / 2 + (c.ay + y2 * sc) / dd * F, c.z + z1];
      });
      const dimf = Math.max(0.2, Math.min(1, 6 / c.z));
      const col = mul(acc(env, c.ci), 0.25 + dimf * 0.8 + env.beat * 0.25);
      for (const [i, j] of EE) LN(eng, pr[i][0], pr[i][1], pr[j][0], pr[j][1], '#', col, c.z);
    }
  });
  const SinScrollDots = E('SINE DOTS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let x = 0; x < C; x += 2) {
      const y = R / 2 + Math.sin(x * 0.12 + this.t * 3 * this.P.dir) * R * 0.3 * this.P.amp
        + Math.sin(x * 0.05 - this.t * 2) * R * 0.12;
      px(eng, x, y, '@', mul(acc(env, (x / 6 | 0) % 3), 0.5 + env.beat * 0.5), 300);
    }
  });
  const Voxel2 = E('VOXEL HILLS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const yb = new Int16Array(C).fill(R);
    for (let d = 1; d < 40; d += 0.6) {
      for (let x = 0; x < C; x++) {
        const wx = (x - C / 2) * d * 0.04, wz = d + this.t * 5 * this.P.spd;
        const h = (Math.sin(wx * 0.3) + Math.sin(wz * 0.2) + Math.sin((wx + wz) * 0.15)) * this.P.amp;
        const sy = (R * 0.55 - h * R * 0.16 / d * 6) | 0;
        if (sy < yb[x] && sy >= 0) { for (let y = sy; y < yb[x]; y++) px(eng, x, y, gly(Math.max(0.1, 1 - d / 38)), mul(acc(env, h > 0.5 ? 2 : 0), 0.3 + (1 - d / 40)), d); yb[x] = sy; }
      }
    }
  });
  const Plasma2 = E('PLASMA FRACTAL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, t = this.t;
    // separable: sin(x*f+t) + sin(y*f*1.3 - t*1.1) summed over octaves splits
    // into an x-only term + a y-only term -> precompute each once per frame
    // (was 8 sins/cell; now ~0). Bit-identical output, 2x downsample kept.
    const F = [0.08, 0.152, 0.2888, 0.54872];
    const sx = (this._sx && this._sx.length >= C) ? this._sx
      : (this._sx = new Float64Array(C));
    for (let x = 0; x < C; x += 2) {
      let s = 0;
      for (let o = 0; o < 4; o++) s += Math.sin(x * F[o] + t);
      sx[x] = s;
    }
    const c0 = acc(env, 0), c1 = acc(env, 1), bb = 0.3 + env.beat * 0.3;
    for (let y = 0; y < R; y += 2) {
      let sy = 0;
      for (let o = 0; o < 4; o++) sy += Math.sin(y * F[o] * 1.3 - t * 1.1);
      for (let x = 0; x < C; x += 2) {
        const v = sx[x] + sy;
        const k = (v + 8) / 16;
        const g = gly(k), c = mul(lerpC(c0, c1, (Math.sin(v) + 1) / 2), bb + k);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const Lens = E('LENS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, lx = C / 2 + Math.sin(this.t) * C * 0.3, ly = R / 2 + Math.cos(this.t * 1.2) * R * 0.3, LR = 14 * this.P.zoom;
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
      let sx = x, sy = y; const d = Math.hypot(x - lx, (y - ly) * 2);
      if (d < LR) { const k = 1 - d / LR; sx = x - (x - lx) * k * 0.6; sy = y - (y - ly) * k * 0.6; }
      const v = ((sx * 0.2 | 0) ^ (sy * 0.2 | 0)) & 7;
      px(eng, x, y, gly(v / 7), mul(acc(env, d < LR ? 2 : 0), 0.25 + v / 7 * (0.6 + env.beat * 0.4)));
    }
  });
  const Conway3 = E('TRI FRACTAL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, sc = Math.min(C, R * 2) * 0.9, ox = C / 2, oy = R - 2;
    let x = 0, y = 0;
    const A = [[0, 0], [1, 0], [0.5, 1]];
    for (let i = 0; i < 1400; i++) {
      const p = A[(Math.random() * 3) | 0]; x = (x + p[0]) / 2; y = (y + p[1]) / 2;
      px(eng, ox + (x - 0.5) * sc, oy - y * R * 0.92, gly(0.5 + Math.sin(i * 0.05 + this.t * 4) * 0.5), mul(acc(env, (i / 200 | 0) % 3), 0.4 + env.beat * 0.5), 300);
    }
  });

  // ===== batch 3: 10 higher-quality (shaded/lit/deep, music-driven) =====
  const LitTunnel = E('LIT TUNNEL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P, sp = this.t * (2 + env.mv * 4);
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
      const dx = (x - C / 2) / (C / 2), dy = (y - R / 2) / (R / 2), d = Math.hypot(dx, dy) + 1e-3;
      const u = (1 / d) * P.k1 + sp, v = Math.atan2(dy, dx) * P.dir;
      const tex = P.variant === 0 ? (((u | 0) + (((v / 6.28) * 12) | 0)) & 1)
        : P.variant === 1 ? ((Math.sin(u) * Math.sin(v * 4 + sp)) > 0 ? 1 : 0)
          : ((u * 0.5 + v) % 1 + 1) % 1 > 0.5 ? 1 : 0;
      const light = Math.max(0.05, Math.min(1, d * 1.6)) * (0.6 + Math.sin(v * 3 + sp) * 0.4);
      const sh = light * (0.5 + env.beat * 0.6);
      eng.plot(x, y, gly(tex ? sh : sh * 0.45),
        mul(acc(env, tex ? 0 : 1), 0.18 + sh), 1 + 1 / d);
    }
  });
  const IcoLit = E('LIT ICOSA', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.32 * (1 + env.mv * 0.3);
    const a = this.t * this.P.dir, b = this.t * 0.7 + this.P.ry;
    const ph = (1 + Math.sqrt(5)) / 2;
    let V = [[-1, ph, 0], [1, ph, 0], [-1, -ph, 0], [1, -ph, 0], [0, -1, ph], [0, 1, ph],
    [0, -1, -ph], [0, 1, -ph], [ph, 0, -1], [ph, 0, 1], [-ph, 0, -1], [-ph, 0, 1]];
    const F = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4],
    [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]];
    const rot = (p) => {
      let [x, y, z] = p;
      let y1 = y * Math.cos(a) - z * Math.sin(a), z1 = y * Math.sin(a) + z * Math.cos(a);
      let x1 = x * Math.cos(b) - z1 * Math.sin(b); z1 = x * Math.sin(b) + z1 * Math.cos(b);
      return [x1, y1, z1];
    };
    const PR = V.map(rot);
    for (const f of F) {
      const p0 = PR[f[0]], p1 = PR[f[1]], p2 = PR[f[2]];
      const nz = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]);
      if (nz <= 0) continue;                           // backface cull
      const cz = (p0[2] + p1[2] + p2[2]) / 3;
      const lit = Math.max(0.12, Math.min(1, (cz + 2) / 4)) * (0.6 + env.beat * 0.5);
      const tri = [p0, p1, p2].map((p) => [C / 2 + p[0] * s, R / 2 - p[1] * s]);
      // scanline-ish fill via edges midpoints (cheap)
      for (let u = 0; u <= 1; u += 0.06) for (let w = 0; w <= 1 - u; w += 0.06) {
        const X = tri[0][0] + (tri[1][0] - tri[0][0]) * u + (tri[2][0] - tri[0][0]) * w;
        const Y = tri[0][1] + (tri[1][1] - tri[0][1]) * u + (tri[2][1] - tri[0][1]) * w;
        eng.plot(X, Y, gly(lit), mul(acc(env, (f[0]) % 3), 0.2 + lit), 3 - cz);
      }
    }
  });
  // canonical 4-param de Jong. The old reused-frequency variant collapsed to
  // a fixed point / 2-cycle for almost all random params (-> "two dots").
  // Curated tuples that all yield dense strange attractors; pick one per
  // reset for variety, then skip the transient so frame 1 is already formed.
  const DEJONG = [
    [1.4, -2.3, 2.4, -2.1], [2.01, -2.53, 1.61, -0.33],
    [-2.7, -0.09, -0.86, -2.2], [-2.24, 0.43, -0.65, -2.43],
    [1.641, 1.902, 0.316, 1.525], [-2.0, -2.0, -1.2, 2.0],
    [-1.8, -2.0, -0.5, -0.9], [1.7, 1.7, 0.6, 1.2],
  ];
  const Attractor = E('ATTRACTOR', function () {
    const p = DEJONG[(Math.random() * DEJONG.length) | 0];
    this.a = p[0]; this.b = p[1]; this.c = p[2]; this.d = p[3];
    this.x = 0.1; this.y = 0.1;
    for (let i = 0; i < 60; i++) {                 // burn the transient
      const nx = Math.sin(this.a * this.y) - Math.cos(this.b * this.x);
      const ny = Math.sin(this.c * this.x) - Math.cos(this.d * this.y);
      this.x = nx; this.y = ny;
    }
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, n = 1400 + (env.energy * 1600 | 0);
    for (let i = 0; i < n; i++) {
      const nx = Math.sin(this.a * this.y) - Math.cos(this.b * this.x);
      const ny = Math.sin(this.c * this.x) - Math.cos(this.d * this.y);
      this.x = nx; this.y = ny;
      eng.plot(C / 2 + nx * C * 0.22, R / 2 + ny * R * 0.22, i % 3 ? '.' : '*',
        mul(acc(env, (i / 300 | 0) % 3), 0.35 + env.beat * 0.5), 300);
    }
  });
  const ReacDiff = E('REACTION', function (eng) {
    const C = eng.cols, R = eng.rows; this.g = new Float32Array(C * R);
    for (let i = 0; i < this.g.length; i++) this.g[i] = Math.random() < 0.5 ? 0 : 1;
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g, n = (this._n && this._n.length === C * R) ? this._n : (this._n = new Float32Array(C * R));
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
      let s = 0;
      for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++)
        s += g[((y + j + R) % R) * C + ((x + i + C) % C)];
      const v = g[y * C + x];
      n[y * C + x] = Math.max(0, Math.min(1, v + (s / 9 - 0.5) * 0.6
        + Math.sin(x * 0.1 + y * 0.1 + this.t * 2) * 0.05));
      if (env.hit > 0.7 && Math.random() < 0.001) n[y * C + x] = 1;
      if (v > 0.55 && (x & 1) === 0 && (y & 1) === 0) {
        const gC = gly(v), cC = mul(acc(env, v > 0.8 ? 2 : 0), 0.3 + v * (0.6 + env.beat * 0.4));
        px(eng, x, y, gC, cC); px(eng, x + 1, y, gC, cC);
        px(eng, x, y + 1, gC, cC); px(eng, x + 1, y + 1, gC, cC);
      }
    }
    this.g = n; this._n = g;            // ping-pong: old field -> next scratch
  });
  const MetaLit = E('META LIT', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, t = this.t;
    const b = [];
    for (let i = 0; i < 4; i++) b.push([C / 2 + Math.sin(t * (0.8 + i * 0.3) + i) * C * 0.32,
    R / 2 + Math.cos(t * (1.1 + i * 0.2) + i * 2) * R * 0.32, 18 + i * 6]);
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      let s = 0, gx = 0, gy = 0;
      for (const [bx, by, m] of b) { const dd = Math.hypot(x - bx, (y - by) * 2) + 1; s += m / dd; gx += (x - bx) / (dd * dd); gy += (y - by) / (dd * dd); }
      if (s > 1.0) {
        const nl = Math.max(0.1, (-gx * 0.5 - gy * 0.5 + 1) / 2);   // fake lighting
        const g = gly(nl), c = mul(acc(env, s > 2.2 ? 2 : 0), 0.25 + nl * (0.7 + env.beat * 0.4));
        eng.plot(x, y, g, c); eng.plot(x + 1, y, g, c);
        eng.plot(x, y + 1, g, c); eng.plot(x + 1, y + 1, g, c);
      }
    }
  });
  const DeepZoom = E('DEEP ZOOM', function () {
    const tgt = [[-0.745, 0.113], [-0.7436, 0.1318], [0.2925, 0.0149], [-1.25066, 0.02012]];
    this.c = tgt[(Math.random() * tgt.length) | 0];
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, M = 24;          // 2x downsample
    const zoom = Math.pow(1.6, (this.t * 0.5) % 14) * (1 + env.mv);
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 2) {
      const cr = this.c[0] + (x / C - 0.5) * 3 / zoom, ci = this.c[1] + (y / R - 0.5) * 2.4 / zoom;
      let zr = 0, zi = 0, k = 0;
      while (k < M && zr * zr + zi * zi < 4) { const tt = zr * zr - zi * zi + cr; zi = 2 * zr * zi + ci; zr = tt; k++; }
      if (k < M) {
        const g = gly(k / M), c = mul(acc(env, (k + (this.t * 4 | 0)) % 3), 0.3 + k / M + env.beat * 0.3);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const BumpPlasma = E('BUMP PLASMA', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, t = this.t;
    const h = (x, y) => Math.sin(x * 0.14 + t) + Math.sin(y * 0.18 - t * 1.2)
      + Math.sin((x + y) * 0.1 + t * 0.7);
    for (let y = 1; y < R - 1; y += 2) for (let x = 1; x < C - 1; x += 2) {
      const nx = h(x + 1, y) - h(x - 1, y), ny = h(x, y + 1) - h(x, y - 1);
      const L = Math.max(0.05, (-nx * 0.6 - ny * 0.6 + 1.6) / 3.2);   // emboss light
      const g = gly(L), c = mul(lerpC(acc(env, 0), acc(env, 1), L), 0.25 + L * (0.7 + env.beat * 0.5));
      eng.plot(x, y, g, c, 500); eng.plot(x + 1, y, g, c, 500);
      eng.plot(x, y + 1, g, c, 500); eng.plot(x + 1, y + 1, g, c, 500);
    }
  });
  const WarpStars = E('WARP STARS', function () {
    this.s = []; for (let i = 0; i < 240; i++) this.s.push({ a: Math.random() * 6.28, r: Math.random(), z: Math.random() });
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, wv = 0.4 + env.mv * 2.2;
    for (const p of this.s) {
      const pz0 = p.z; p.z -= 0.02 * (1 + wv * 3); if (p.z < 0.02) { p.z = 1; p.a = Math.random() * 6.28; p.r = Math.random(); }
      const proj = (z) => [C / 2 + Math.cos(p.a) * p.r / z * C, R / 2 + Math.sin(p.a) * p.r / z * R];
      const [x1, y1] = proj(p.z), [x0, y0] = proj(Math.min(1, pz0));
      const dx = x1 - x0, dy = y1 - y0, st = Math.max(1, Math.hypot(dx, dy) | 0);
      for (let i = 0; i <= st; i++)                     // motion-blur trail
        eng.plot(x0 + dx * i / st, y0 + dy * i / st, i === st ? '@' : '.',
          mul(acc(env, 2), (1 - p.z) * (i / st * 0.7 + 0.3)), p.z);
    }
  });
  const TorusKnot = E('TORUS KNOT', function () { this.p = 2 + (Math.random() * 3 | 0); this.q = 3 + (Math.random() * 4 | 0); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.24, A = this.t * this.P.dir, B = this.t * 0.5;
    for (let u = 0; u < 6.283; u += 0.025) {
      const r = 2 + Math.cos(this.q * u);
      let x = r * Math.cos(this.p * u), y = r * Math.sin(this.p * u), z = -Math.sin(this.q * u) * 1.4;
      let y1 = y * Math.cos(A) - z * Math.sin(A), z1 = y * Math.sin(A) + z * Math.cos(A);
      let x1 = x * Math.cos(B) - z1 * Math.sin(B); z1 = x * Math.sin(B) + z1 * Math.cos(B);
      const pp = 3 / (4 + z1);
      eng.plot(C / 2 + x1 * s * pp, R / 2 - y1 * s * pp, z1 > 0 ? '@' : 'o',
        mul(acc(env, (u * 2 | 0) % 3), 0.3 + (z1 + 2) / 4 + env.beat * 0.3), 4 + z1);
    }
  });
  const InkFluid = E('INK FLOW', function () { this.p = []; for (let i = 0; i < 300; i++) this.p.push({ x: Math.random(), y: Math.random(), l: Math.random() }); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, t = this.t;
    if (env.hit > 0.7) for (let i = 0; i < 30; i++) this.p.push({ x: 0.5 + (Math.random() - 0.5) * 0.2, y: 0.5, l: 1 });
    if (this.p.length > 700) this.p.splice(0, this.p.length - 700);
    for (const q of this.p) {
      const ang = (Math.sin(q.x * 6 + t) + Math.cos(q.y * 6 - t * 1.3)) * 3.14 * this.P.warp;
      q.x += Math.cos(ang) * 0.006 * (1 + env.mv); q.y += Math.sin(ang) * 0.006 * (1 + env.mv);
      q.l -= 0.004;
      if (q.l <= 0 || q.x < 0 || q.x > 1 || q.y < 0 || q.y > 1) { q.x = Math.random(); q.y = Math.random(); q.l = 1; }
      eng.plot(q.x * C, q.y * R, q.l > 0.6 ? '#' : q.l > 0.3 ? '+' : '.',
        mul(acc(env, (q.l * 3 | 0) % 3), 0.3 + q.l * (0.6 + env.beat * 0.4)), 300);
    }
  });

  // ===== batch 4: 20 fresh, original visual languages =====
  // compact 5x7 uppercase bitmap font (for big readable kinetic type)
  const FNT5 = {
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
    ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
  };
  const KineticType = E('KINETIC TYPE', function () {
    this.w = SONG_WORD(); this.tw = 0; this._lt = 0;
  }, function (eng, env) {
    // BIG readable typography: a word rendered from the 5x7 font, letters
    // revealing left->right, scale-pulsing on the beat, each glyph bouncing
    // + a beat kick, colour cycling. Reads as a word, not noise.
    const C = eng.cols, R = eng.rows, w = this.w, n = w.length;
    let dt = env.t - (this._lt || env.t); if (dt < 0 || dt > 0.1) dt = 0.016;
    this._lt = env.t; this.tw += dt;
    if (this.bt > 0.6 && this.tw > 0.7 && Math.random() < 0.5) {
      this.w = SONG_WORD(); this.tw = 0;
      return;
    }
    // base scale to fit ~78% width; gentle entrance overshoot + beat pulse
    const fitS = Math.max(2, Math.min(7, (C * 0.78 / (n * 6)) | 0));
    const ent = Math.min(1, this.tw * 3);
    const grow = ent < 1 ? (0.35 + 0.85 * ent - 0.20 * Math.sin(ent * Math.PI)) : 1;
    const s = Math.max(1, (fitS * grow * (1 + env.beat * 0.16 + env.mv * 0.10)) | 0);
    const gw = 6 * s, totW = n * gw - s;
    const ox = ((C - totW) / 2) | 0, oy = ((R - 7 * s) / 2) | 0;
    const ci = (env.t * 2) | 0;
    for (let i = 0; i < n; i++) {
      if (this.tw * 9 < i) break;                       // staggered reveal
      const g = FNT5[w[i]] || FNT5[' '];
      const kick = this.bt * (Math.sin(i * 2.3) * 0.5 + 0.5) * s * 1.6;
      const bob = Math.sin(env.t * 3 + i * 0.9) * s * 0.5;
      const lx = ox + i * gw, ly = (oy + bob - kick) | 0;
      const col = mul(acc(env, (i + ci) % 3), 0.55 + env.beat * 0.45);
      for (let ry = 0; ry < 7; ry++) for (let rx = 0; rx < 5; rx++) {
        if (g[ry][rx] !== '1') continue;
        const bx = lx + rx * s, by = ly + ry * s;
        for (let q = 0; q < s; q++) for (let p = 0; p < s; p++)
          px(eng, bx + p, by + q, '█', col, 200);
      }
    }
  });
  const Turmites = E('TURMITES', function (eng) {
    const C = eng.cols, R = eng.rows; this.g = new Uint8Array(C * R);
    this.a = []; for (let i = 0; i < 3; i++) this.a.push({ x: C / 2 | 0, y: R / 2 | 0, d: i });
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g, steps = 80 + (env.mv * 220 | 0);
    for (let s = 0; s < steps; s++) for (const a of this.a) {
      const i = a.y * C + a.x;
      if (g[i]) { a.d = (a.d + 1) & 3; g[i] = 0; } else { a.d = (a.d + 3) & 3; g[i] = 1; }
      a.x = (a.x + [1, 0, -1, 0][a.d] + C) % C; a.y = (a.y + [0, 1, 0, -1][a.d] + R) % R;
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++)
      if (g[y * C + x]) px(eng, x, y, '#', mul(acc(env, (x + y) % 3), 0.4 + env.beat * 0.4));
    for (const a of this.a) px(eng, a.x, a.y, '@', acc(env, 2), 100);
  });
  const MazeGrow = E('MAZE', function (eng) {
    const C = eng.cols, R = eng.rows; this.W = C; this.H = R;
    this.m = new Uint8Array(C * R); this.st = [[1, 1]]; this.m[C + 1] = 1; this.tr = [1, 1];
  }, function (eng, env) {
    const C = this.W, R = this.H, m = this.m, D = [[2, 0], [-2, 0], [0, 2], [0, -2]];
    for (let s = 0; s < 6; s++) if (this.st.length) {
      const [x, y] = this.st[this.st.length - 1], o = [];
      for (const [dx, dy] of D) { const nx = x + dx, ny = y + dy; if (nx > 0 && ny > 0 && nx < C - 1 && ny < R - 1 && !m[ny * C + nx]) o.push([nx, ny, dx, dy]); }
      if (!o.length) { this.st.pop(); continue; }
      const [nx, ny, dx, dy] = o[(Math.random() * o.length) | 0];
      m[(y + dy / 2) * C + (x + dx / 2)] = 1; m[ny * C + nx] = 1; this.st.push([nx, ny]);
    }
    if (!this.st.length) { this.st = [[1, 1]]; this.m = new Uint8Array(C * R); this.m[C + 1] = 1; }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++)
      px(eng, x, y, m[y * C + x] ? ' ' : (((x ^ y) & 1) ? '#' : '▓'),
        m[y * C + x] ? env.pal.bg : mul(acc(env, 0), 0.3 + env.beat * 0.4), m[y * C + x] ? 9e8 : 500);
    if (this.st.length) { const h = this.st[this.st.length - 1]; px(eng, h[0], h[1], '@', acc(env, 2), 100); }
  });
  const Scope = E('OSCILLOSCOPE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P, A = 1 + env.mv * 2;
    for (let i = 0; i < 480; i++) {
      const t = i * 0.02 + this.t;
      const x = C / 2 + Math.sin(t * P.k1) * Math.cos(t * 0.3) * C * 0.42 * A;
      const y = R / 2 + Math.sin(t * P.k2 + this.t) * R * 0.42;
      px(eng, x, y, i % 4 ? '.' : 'o', mul(acc(env, 0), 0.4 + env.beat * 0.5), 300);
    }
    for (let x = 0; x < C; x++) {                      // ground waveform
      const y = R - 3 + Math.sin(x * 0.3 + this.t * 8) * (1 + env.energy * 3);
      px(eng, x, y, '~', mul(acc(env, 2), 0.5 + env.beat * 0.4), 250);
    }
  });
  const Sand = E('FALLING SAND', function (eng) { this.g = new Uint8Array(eng.cols * eng.rows); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g;
    const src = (C / 2 + Math.sin(this.t * 1.5) * C * 0.35) | 0;
    for (let k = 0; k < 3 + (env.mv * 5 | 0); k++) g[(src + k - 1 + C) % C] = 1 + ((this.t * 2 | 0) % 3);
    for (let y = R - 2; y >= 0; y--) for (let x = 0; x < C; x++) {
      const i = y * C + x; if (!g[i]) continue;
      const b = (y + 1) * C + x;
      if (!g[b]) { g[b] = g[i]; g[i] = 0; }
      else { const d = Math.random() < 0.5 ? -1 : 1, s = (y + 1) * C + ((x + d + C) % C); if (!g[s]) { g[s] = g[i]; g[i] = 0; } }
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) { const v = g[y * C + x]; if (v) px(eng, x, y, '▒', mul(acc(env, v - 1), 0.5 + env.beat * 0.3)); }
  });
  const Raymarch = E('RAYMARCH', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, t = this.t, ST = 3;
    const rad = 1.1 + Math.sin(t * 2) * 0.2;          // hoisted (was per sdf)
    const cc = Math.cos(t * 0.4), sn = Math.sin(t * 0.4);  // hoisted (was per cell)
    const sdf = (x, y, z) => {
      const r = Math.sqrt(x * x + y * y + z * z) - rad;
      const tx = Math.sqrt(x * x + z * z) - 1.3;
      const to = Math.sqrt(tx * tx + y * y) - 0.35;
      return Math.min(r, to + Math.sin(x * 3 + t) * 0.12);
    };
    for (let py = 0; py < R; py += ST) for (let pxx = 0; pxx < C; pxx += ST) {
      const ox = (pxx / C - 0.5) * 2.2, oy = (py / R - 0.5) * 2.0;
      let oz = -3.5, hit = 0;
      for (let m = 0; m < 10; m++) {
        const xr = ox * cc - oz * sn, zr = ox * sn + oz * cc;
        const d = sdf(xr, oy, zr);
        if (d < 0.02) { hit = 1; break; }
        oz += d; if (oz > 4) break;
      }
      const sh = hit ? Math.max(0.1, 1 - (oz + 3.5) / 6) : 0;
      if (sh > 0.05) {
        const g = gly(sh), c = mul(acc(env, 0), 0.3 + sh * (0.7 + env.beat * 0.4));
        for (let a = 0; a < ST; a++) for (let b = 0; b < ST; b++)
          px(eng, pxx + b, py + a, g, c, 500);
      }
    }
  });
  const Boids = E('BOIDS', function (eng) {
    this.b = []; for (let i = 0; i < 60; i++) this.b.push({ x: Math.random() * eng.cols, y: Math.random() * eng.rows, a: Math.random() * 6.28 });
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, sp = 0.6 + env.mv * 1.2;
    for (const p of this.b) {
      let ax = 0, ay = 0, n = 0;
      for (const q of this.b) { const dx = q.x - p.x, dy = q.y - p.y, dd = dx * dx + dy * dy; if (dd > 0 && dd < 80) { ax += Math.cos(q.a) - (dx / (dd + 1)) * 4; ay += Math.sin(q.a) - (dy / (dd + 1)) * 4; n++; } }
      if (n) { const ta = Math.atan2(ay, ax); p.a += Math.atan2(Math.sin(ta - p.a), Math.cos(ta - p.a)) * 0.1; }
      p.x = (p.x + Math.cos(p.a) * sp + C) % C; p.y = (p.y + Math.sin(p.a) * sp + R) % R;
      const g = '>↗^↖<↙v↘'[((p.a / 0.785) | 0) & 7] || '>';
      px(eng, p.x, p.y, g, mul(acc(env, 0), 0.6 + env.beat * 0.4), 200);
    }
  });
  const Harmono = E('HARMONOGRAPH', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P;
    for (let i = 0; i < 900; i++) {
      const t = i * 0.03;
      const dec = Math.exp(-t * 0.06);
      const x = C / 2 + (Math.sin(t * P.k1 + this.t) + Math.sin(t * P.k2 * 1.01)) * C * 0.24 * dec;
      const y = R / 2 + (Math.sin(t * P.k2 + this.t * 0.7) + Math.sin(t * P.k1 * 0.99)) * R * 0.24 * dec;
      px(eng, x, y, '.', mul(acc(env, (i / 150 | 0) % 3), 0.3 + dec * (0.6 + env.beat * 0.4)), 300);
    }
  });
  const Mandala = E('MANDALA', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, sym = 6 + (this.P.variant * 2), rad = Math.min(C / 2, R) * (0.5 + env.beat * 0.4);
    for (let r = 2; r < rad; r += 1.3) {
      const pts = (sym * (1 + (r / 6 | 0)));
      for (let k = 0; k < pts; k++) {
        const a = k / pts * 6.28 + this.t * this.P.dir * (1 + r * 0.01);
        const rr = r + Math.sin(a * sym + this.t * 3) * 3;
        px(eng, C / 2 + Math.cos(a) * rr, R / 2 + Math.sin(a) * rr * 0.6,
          gly(1 - r / rad), mul(acc(env, (r / 4 | 0) % 3), 0.3 + (1 - r / rad) * (0.7 + env.beat * 0.5)));
      }
    }
  });
  const CodeHall = E('JAVASCRIPT', function () { this._lo = -1; this._rows = null; }, function (eng, env) {
    // perf: rebuild the row strings only when the integer scroll offset
    // changes (~1 frame in 5); precompute the 4 colour tiers per frame
    // (no per-char mul/acc); draw via glyph2d to bypass the symmetry
    // multiply (mirrored code is gibberish anyway).
    const C = eng.cols, R = eng.rows;
    this.off = (this.off || 0) + (0.2 + env.mv * 0.5);
    const off = this.off | 0;
    if (off !== this._lo || !this._rows) {
      const K = ['def ', 'for(', 'if(', 'return ', 'while ', '{ }', '=> ', 'const ', '0x', '<<', '||', '/* */', 'fn ', 'let '];
      const G = '.abx_0192=+(){}', rows = new Array(R);
      for (let y = 0; y < R; y++) {
        const seed = (y + off) * 2654435761 % 100000;
        const ind = (seed % 6) * 2, len = Math.min(C, 6 + seed % (C - 12));
        let s = ' '.repeat(ind) + K[seed % K.length];
        while (s.length < len) s += G[(seed * (s.length + 3)) % 15];
        rows[y] = { s: s.slice(0, C), ind };
      }
      this._rows = rows; this._lo = off;
    }
    const bb = 0.5 + env.beat * 0.3, bh = 0.9 + env.beat * 0.3, hY = off % R;
    const c0n = mul(acc(env, 0), bb), c2n = mul(acc(env, 2), bb);
    const c0h = mul(acc(env, 0), bh), c2h = mul(acc(env, 2), bh);
    for (let y = 0; y < R; y++) {
      const r = this._rows[y], s = r.s, lim = r.ind + 4, hl = (y === hY);
      const ck = hl ? c2h : c2n, cb = hl ? c0h : c0n;
      for (let x = 0; x < s.length; x++) {
        const ch = s[x];
        if (ch !== ' ') eng.glyph2d(x, y, ch, x < lim ? ck : cb);
      }
    }
  });
  const AsmHall = E('HARDWARE REFERENCE MANUAL', function () { this._lo = -1; this._rows = null; }, function (eng, env) {
    // perf: same treatment as JAVASCRIPT — cached rows, precomputed colour
    // tiers, glyph2d (no symmetry multiply).
    const C = eng.cols, R = eng.rows;
    this.off = (this.off || 0) + (0.18 + env.mv * 0.45) * this.P.spd;
    const off = this.off | 0;
    if (off !== this._lo || !this._rows) {
      const OP = ['move.l ', 'move.w ', 'lea ', 'bsr ', 'rts', 'dc.w ',
        'addq.l ', 'tst.b ', 'bne.s ', 'bra ', 'and.w ', 'moveq #',
        'dbf ', 'jsr ', 'eor.w '];
      const RG = ['d0', 'd1', 'd2', 'a0', 'a1', 'a6', '(a0)+', 'CUSTOM',
        'COP1LC', 'DMACON', 'BPLCON0', 'COLOR00', 'INTENA'];
      const CM = ['wait beam', 'set bplptr', 'irq', 'copperlist', 'blit',
        'audio dma', 'vblank'];
      const rows = new Array(R);
      for (let y = 0; y < R; y++) {
        const seed = (y + off) * 2654435761 % 100000;
        const ind = (seed % 4) * 2;
        let s = ' '.repeat(ind) + OP[seed % OP.length];
        if ((seed >> 3) % 3 === 0) s += '$DFF' + ((seed % 256).toString(16).toUpperCase().padStart(3, '0'));
        else s += RG[(seed >> 2) % RG.length] + (((seed >> 5) % 2) ? ',' + RG[(seed >> 7) % RG.length] : '');
        if ((seed % 7) === 0) s += '   ; ' + CM[(seed >> 4) % CM.length];
        rows[y] = { s: s.slice(0, C), ind };
      }
      this._rows = rows; this._lo = off;
    }
    const bb = 0.5 + env.beat * 0.3, bh = 0.9 + env.beat * 0.3, hY = off % R;
    const t0n = mul(acc(env, 0), bb), t1n = mul(acc(env, 1), bb), t2n = mul(acc(env, 2), bb);
    const t0h = mul(acc(env, 0), bh), t1h = mul(acc(env, 1), bh), t2h = mul(acc(env, 2), bh);
    for (let y = 0; y < R; y++) {
      const r = this._rows[y], s = r.s, lim = r.ind + 6, hl = (y === hY);
      for (let x = 0; x < s.length; x++) {
        const ch = s[x];
        if (ch === ' ') continue;
        let c;
        if (ch === '$') c = hl ? t2h : t2n;
        else if (ch === ';' || ch === ',') c = hl ? t1h : t1n;
        else if (x < lim) c = hl ? t2h : t2n;
        else c = hl ? t0h : t0n;
        eng.glyph2d(x, y, ch, c);
      }
    }
  });
  const WireRidge = E('NIGHT RIDGES', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let i = 0; i < 50; i++) px(eng, (Math.abs(Math.sin(i * 12.9) * C)) | 0, (Math.abs(Math.sin(i * 7.7) * R * 0.5)) | 0, '.', mul(acc(env, 2), 0.4), 900);
    for (let layer = 5; layer >= 1; layer--) {
      const base = R * 0.45 + layer * 4, sc = layer * 1.4;
      let prevY = base;
      for (let x = 0; x <= C; x += 2) {
        const h = (Math.sin((x + this.t * 12 / layer) * 0.06) + Math.sin((x) * 0.13 + layer)) * sc;
        const y = base - h;
        const s = x === 0 ? 1 : (y < prevY ? -1 : 1);
        for (let yy = Math.min(y, prevY) | 0; yy <= (Math.max(y, prevY) | 0); yy++)
          px(eng, x, yy, '/', mul(acc(env, layer % 3), 0.15 + (6 - layer) * 0.12 + env.beat * 0.2), layer);
        prevY = y;
      }
    }
  });
  const BallPit = E('BALL PIT', function (eng) { this.b = []; for (let i = 0; i < 22; i++) this.b.push({ x: Math.random() * eng.cols, y: Math.random() * eng.rows * 0.5, vx: (Math.random() - 0.5) * 2, vy: 0 }); }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    // cap bounce speed so the peak height stays on screen (h = v^2/2g),
    // give a modest ONE-SHOT beat kick on contact, and clamp the ceiling.
    const G = 0.06, vmax = Math.sqrt(2 * G * R * 0.8);
    for (const p of this.b) {
      p.vy += G; p.x += p.vx; p.y += p.vy;
      if (p.x < 1 || p.x > C - 1) { p.vx *= -0.9; p.x = Math.max(1, Math.min(C - 1, p.x)); }
      if (p.y > R - 2) {
        p.y = R - 2; p.vy = -Math.abs(p.vy) * 0.72; p.vx *= 0.96;
        if (this.bt > 0.5) p.vy -= 0.4 + env.mv * 0.6;
        if (p.vy < -vmax) p.vy = -vmax;       // hard cap -> peak stays on screen
      }
      if (p.y < 1) { p.y = 1; p.vy = Math.abs(p.vy) * 0.5; }
      for (let dy = -1; dy <= 1; dy++) for (let dx = -2; dx <= 2; dx++)
        if (dx * dx / 4 + dy * dy <= 1) px(eng, p.x + dx, p.y + dy, dx || dy ? 'o' : '@', mul(acc(env, 0), 0.6 + env.beat * 0.4), 200);
    }
  });
  const DLA = E('CRYSTAL', function (eng) {
    const C = eng.cols, R = eng.rows; this.g = new Uint8Array(C * R); this.g[(R / 2 | 0) * C + (C / 2 | 0)] = 1;
    this.w = { x: 0, y: 0 };
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g, tries = 120 + (env.mv * 200 | 0);
    for (let s = 0; s < tries; s++) {
      let x = (Math.random() * C) | 0, y = (Math.random() * R) | 0;
      for (let m = 0; m < 60; m++) {
        x = (x + ((Math.random() * 3) | 0) - 1 + C) % C; y = (y + ((Math.random() * 3) | 0) - 1 + R) % R;
        if (g[((y + 1) % R) * C + x] || g[((y - 1 + R) % R) * C + x] || g[y * C + (x + 1) % C] || g[y * C + (x - 1 + C) % C]) { g[y * C + x] = 1; break; }
      }
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++)
      if (g[y * C + x]) px(eng, x, y, '*', mul(acc(env, ((x + y) / 5 | 0) % 3), 0.4 + env.beat * 0.4));
  });
  const Plume = E('SMOKE', function (eng) { this.d = new Float32Array(eng.cols * eng.rows); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, d = this.d, n = (this._n && this._n.length === C * R) ? this._n : (this._n = new Float32Array(C * R)); n.fill(0);
    const src = (C / 2 + Math.sin(this.t) * C * 0.15) | 0;
    for (let k = -2; k <= 2; k++) d[(R - 2) * C + ((src + k + C) % C)] = 1 + env.energy;
    for (let y = 1; y < R - 1; y++) for (let x = 1; x < C - 1; x++) {
      const curl = Math.sin(x * 0.2 + this.t * 2) * 1.4;
      const sx = x + (curl | 0);
      let v = (d[(y + 1) * C + x] * 0.5 + d[(y + 1) * C + ((x + 1) % C)] * 0.2 + d[(y + 1) * C + ((x - 1 + C) % C)] * 0.2 + d[y * C + x] * 0.1) * 0.985;
      n[y * C + ((sx % C + C) % C)] = Math.max(n[y * C + ((sx % C + C) % C)], v);
    }
    this.d = n; this._n = d;            // ping-pong: old field -> next scratch
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) { const v = n[y * C + x]; if (v > 0.05) px(eng, x, y, gly(Math.min(1, v)), mul(acc(env, v > 0.6 ? 2 : 0), 0.2 + Math.min(0.85, v))); }
  });
  const PendWave = E('PENDULUM WAVE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, N = 26;
    for (let i = 0; i < N; i++) {
      const len = 1 + i * 0.03, a = Math.sin(this.t * (1 + len) * 1.2) * 1.1;
      const px0 = (i + 1) / (N + 1) * C, py0 = 3;
      const L = R * 0.7;
      const ex = px0 + Math.sin(a) * 6, ey = py0 + Math.cos(a) * L * (0.4 + i * 0.02);
      for (let s = 0; s <= 1; s += 0.1) px(eng, px0 + (ex - px0) * s, py0 + (ey - py0) * s, '.', mul(acc(env, 1), 0.2), 300);
      for (let r = -1; r <= 1; r++) for (let c2 = -1; c2 <= 1; c2++) px(eng, ex + c2, ey + r, '@', mul(acc(env, i % 3), 0.6 + env.beat * 0.4), 200);
    }
  });
  const Tesseract = E('TESSERACT', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.18, a = this.t * 0.5, b = this.t * 0.33;
    const V = [];
    for (let i = 0; i < 16; i++) V.push([(i & 1 ? 1 : -1), (i & 2 ? 1 : -1), (i & 4 ? 1 : -1), (i & 8 ? 1 : -1)]);
    const P = V.map(([x, y, z, w]) => {
      let X = x * Math.cos(a) - w * Math.sin(a), W = x * Math.sin(a) + w * Math.cos(a);
      let Y = y * Math.cos(b) - z * Math.sin(b), Z = y * Math.sin(b) + z * Math.cos(b);
      const k4 = 2 / (3 + W), k3 = 2.4 / (3 + Z * k4);
      return [C / 2 + X * k4 * k3 * s * 3, R / 2 - Y * k4 * k3 * s * 3];
    });
    for (let i = 0; i < 16; i++) for (let j = i + 1; j < 16; j++) {
      let diff = (i ^ j); if (diff && !(diff & (diff - 1))) {
        let x0 = P[i][0] | 0, y0 = P[i][1] | 0, x1 = P[j][0] | 0, y1 = P[j][1] | 0;
        const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1; let er = dx - dy, gd = dx + dy + 1;
        while (gd-- > 0) { px(eng, x0, y0, '#', mul(acc(env, 0), 0.4 + env.beat * 0.4), 300); if (x0 === x1 && y0 === y1) break; const e2 = 2 * er; if (e2 > -dy) { er -= dy; x0 += sx; } if (e2 < dx) { er += dx; y0 += sy; } }
      }
    }
  });
  const Radar = E('RADAR', function () { this.blips = []; }, function (eng, env) {
    const C = eng.cols, R = eng.rows, cx = C / 2, cy = R / 2, rad = Math.min(C / 2, R) * 0.92;
    const sweep = this.t * 2.2 * this.P.dir;
    for (let rr = rad / 4; rr < rad; rr += rad / 4) for (let a = 0; a < 6.28; a += 0.12)
      px(eng, cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * 0.6, '.', mul(acc(env, 1), 0.2), 600);
    for (let r = 0; r < rad; r += 0.7) px(eng, cx + Math.cos(sweep) * r, cy + Math.sin(sweep) * r * 0.6, '#', mul(acc(env, 0), 0.5 * (1 - r / rad) + 0.4), 300);
    if (env.hit > 0.7) this.blips.push({ a: Math.random() * 6.28, r: Math.random() * rad, l: 1 });
    this.blips = this.blips.filter((b) => (b.l -= 0.012) > 0);
    for (const b of this.blips) px(eng, cx + Math.cos(b.a) * b.r, cy + Math.sin(b.a) * b.r * 0.6, '@', mul(acc(env, 2), b.l), 200);
  });
  const Truchet = E('TRUCHET', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, T = 5;
    for (let gy = 0; gy < R; gy += T) for (let gx = 0; gx < C; gx += T) {
      const seed = Math.sin((gx + (this.t * this.P.dir * 4 | 0)) * 1.3 + gy * 2.7);
      const o = seed > 0;
      for (let i = 0; i < T; i++) {
        const t1 = i / T;
        const a1x = gx + (o ? t1 * T : T - t1 * T), a1y = gy + (o ? 0 : 0) + t1 * 0;
        px(eng, gx + (o ? i : T - 1 - i), gy + i, '/', mul(acc(env, (gx + gy) / T % 3 | 0), 0.3 + env.beat * 0.4), 500);
        px(eng, gx + (o ? T - 1 - i : i), gy + i, ' ', env.pal.bg, 9e8);
      }
    }
  });
  const Voronoi = E('VORONOI', function () {
    this.s = []; for (let i = 0; i < 7; i++) this.s.push({ a: Math.random() * 6.28, r: 0.2 + Math.random() * 0.3, sp: 0.3 + Math.random() });
    this.pxb = new Float64Array(this.s.length); this.pyb = new Float64Array(this.s.length);
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = this.s, N = s.length;
    const PX = this.pxb, PY = this.pyb, t = this.t, dir = this.P.dir, mv = 1 + env.mv * 0.5;
    for (let i = 0; i < N; i++) {                 // reused buffers, no realloc
      const q = s[i];
      PX[i] = C / 2 + Math.cos(q.a + t * q.sp * dir) * C * q.r * mv;
      PY[i] = R / 2 + Math.sin(q.a + t * q.sp) * R * q.r;
    }
    const ce = mul(acc(env, 2), 0.6 + env.beat * 0.4);   // edge colour: hoisted
    for (let y = 0; y < R; y += 4) for (let x = 0; x < C; x += 4) {
      let b = 1e9, b2 = 1e9, bi = 0;
      for (let i = 0; i < N; i++) {
        const ddx = x - PX[i], ddy = y - PY[i];
        const d = ddx * ddx + ddy * ddy * 4;
        if (d < b) { b2 = b; b = d; bi = i; } else if (d < b2) b2 = d;
      }
      const edge = (Math.sqrt(b2) - Math.sqrt(b)) < 2.6;
      const g = edge ? '#' : gly(0.3 + (bi / 7));
      const c = edge ? ce : mul(acc(env, bi % 3), 0.18 + env.beat * 0.18);
      for (let yy = 0; yy < 4; yy++) for (let xx = 0; xx < 4; xx++) px(eng, x + xx, y + yy, g, c);
    }
  });
  const BurnShip = E('BURNING SHIP', function () { this.cx = -1.755; this.cy = -0.03; }, function (eng, env) {
    const C = eng.cols, R = eng.rows, M = 16;          // 4x downsample
    const zoom = 0.5 + (Math.sin(this.t * 0.15) * 0.5 + 0.5) * (40 + env.mv * 30);
    const sxc = 3 / zoom, syc = 2.4 / zoom, iC = 1 / C, iR = 1 / R;
    const cx = this.cx, cy = this.cy, bb = 0.3 + env.beat * 0.3;
    for (let y = 0; y < R; y += 4) for (let x = 0; x < C; x += 4) {
      let zr = 0, zi = 0, k = 0;
      const cr = cx + (x * iC - 0.5) * sxc, ci = cy + (y * iR - 0.5) * syc;
      while (k < M && zr * zr + zi * zi < 4) {
        const xr = zr * zr - zi * zi + cr;
        const xi = Math.abs(2 * zr * zi) + ci;
        zr = Math.abs(xr); zi = Math.abs(xi); k++;
      }
      if (k < M) {
        const g = gly(k / M), c = mul(acc(env, k % 3), bb + k / M);
        for (let yy = 0; yy < 4; yy++) for (let xx = 0; xx < 4; xx++)
          px(eng, x + xx, y + yy, g, c);
      }
    }
  });

  // ===== batch 5: super-performant Amiga classics (O(points/lines), no
  //               full-grid per-cell loops) =====
  const CopperBars = E('COPPER', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let b = 0; b < 5; b++) {
      const cy = R / 2 + Math.sin(this.t * (0.6 + b * 0.25) + b * 1.7) * R * 0.42;
      const col = acc(env, b % 3);
      for (let d = -3; d <= 3; d++) {
        const k = (1 - Math.abs(d) / 3) * (0.7 + env.beat * 0.4);
        eng.hspan(cy + d, 0, C - 1, gly(0.5 + k * 0.5),
          mul(col, 0.25 + k), 210 + b);
      }
    }
  });
  const StarWarp = E('STAR WARP', function () {
    this.s = []; for (let i = 0; i < 240; i++)
      this.s.push({ x: (Math.random() - 0.5) * 2, y: (Math.random() - 0.5) * 2, z: Math.random() });
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, sp = 0.35 + env.mv * 1.4;
    for (const p of this.s) {
      p.z -= 0.012 * sp * this.P.spd; if (p.z <= 0.02) { p.x = (Math.random() - 0.5) * 2; p.y = (Math.random() - 0.5) * 2; p.z = 1; }
      const sx = C / 2 + p.x / p.z * C * 0.5, sy = R / 2 + p.y / p.z * R * 0.5;
      const b = 1 - p.z;
      px(eng, sx, sy, b > 0.7 ? '@' : b > 0.4 ? '*' : '.', mul(acc(env, b > 0.6 ? 2 : 0), 0.35 + b), p.z);
    }
  });
  const SineCols = E('SINE COLUMNS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P;
    for (let x = 0; x < C; x += 1) {
      const h = (0.5 + 0.5 * Math.sin(x * 0.13 * P.k1 + this.t * 2 * P.dir)
        + 0.3 * Math.sin(x * 0.05 - this.t)) * R * 0.45 * P.amp;
      const cy = R / 2;
      const col = acc(env, (x / 6 | 0) % 3);
      for (let y = (cy - h) | 0; y <= (cy + h) | 0; y++)
        px(eng, x, y, gly(1 - Math.abs(y - cy) / (h + 1)), mul(col, 0.3 + env.beat * 0.5));
    }
  });
  const BobsLissa = E('BOBS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, n = 30;
    for (let i = 0; i < n; i++) {
      const p = i / n * 6.283 + this.t;
      const x = C / 2 + Math.sin(p * 1.0 + this.t * this.P.dir) * C * 0.42;
      const y = R / 2 + Math.sin(p * 1.6 + this.t * 0.8) * R * 0.42;
      const col = acc(env, i % 3);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -2; dx <= 2; dx++)
        if (dx * dx / 4 + dy * dy <= 1)
          px(eng, x + dx, y + dy, (dx || dy) ? 'o' : '@', mul(col, 0.6 + env.beat * 0.4), 300 - i);
    }
  });
  const WireCube = E('VECTOR CUBE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.26;
    const a = this.t * this.P.dir, b = this.t * 0.6;
    const V = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map(([x, y, z]) => {
      let y1 = y * Math.cos(a) - z * Math.sin(a), z1 = y * Math.sin(a) + z * Math.cos(a);
      let x1 = x * Math.cos(b) - z1 * Math.sin(b); z1 = x * Math.sin(b) + z1 * Math.cos(b);
      const p = 3 / (3 + z1);
      return [C / 2 + x1 * s * p, R / 2 - y1 * s * p];
    });
    const ln = (i, j, ch) => {
      let x0 = V[i][0] | 0, y0 = V[i][1] | 0, x1 = V[j][0] | 0, y1 = V[j][1] | 0;
      const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
      const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
      let er = dx - dy, gd = dx + dy + 1;
      const col = mul(acc(env, 0), 0.6 + env.beat * 0.4);
      while (gd-- > 0) { px(eng, x0, y0, ch, col, 300); if (x0 === x1 && y0 === y1) break; const e2 = 2 * er; if (e2 > -dy) { er -= dy; x0 += sx; } if (e2 < dx) { er += dx; y0 += sy; } }
    };
    [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4],
    [0, 4], [1, 5], [2, 6], [3, 7]].forEach(([i, j]) => ln(i, j, '#'));
  });

  // ===== batch 6: 22 new performant demoscene effects =====
  const LN = (eng, x0, y0, x1, y1, g, c, z) => {
    x0 |= 0; y0 |= 0; x1 |= 0; y1 |= 0;
    const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let er = dx - dy, n = dx + dy + 2;
    while (n-- > 0) {
      eng.plot(x0, y0, g, c, z || 400);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * er;
      if (e2 > -dy) { er -= dy; x0 += sx; }
      if (e2 < dx) { er += dx; y0 += sy; }
    }
  };
  const SLUT = (() => {
    const a = new Float32Array(1024);
    for (let i = 0; i < 1024; i++) a[i] = Math.sin(i * Math.PI / 512);
    return a;
  })();
  const BG = (eng, rgb) => { for (let y = 0; y < eng.rows; y++) eng.hspan(y, 0, eng.cols - 1, '█', rgb, 9e8); };

  const RotoTex = E('ROTOTEX', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, a = this.t * 0.5 * this.P.dir;
    const z = 0.6 + Math.sin(this.t * 0.3) * 0.35 * this.P.zoom;
    const ca = Math.cos(a) * z, sa = Math.sin(a) * z, cx = C / 2, cy = R / 2;
    for (let y = 0; y < R; y += 2) {
      let u = (-cx) * ca - (y - cy) * sa, v = (-cx) * sa + (y - cy) * ca;
      for (let x = 0; x < C; x += 2) {
        const tex = (((u | 0) ^ (v | 0)) & 12);
        const g = tex ? '#' : '+';
        const col = mul(acc(env, tex ? 0 : 1), 0.32 + (tex ? 0.45 : 0.12) + env.beat * 0.4);
        px(eng, x, y, g, col); px(eng, x + 1, y, g, col);
        px(eng, x, y + 1, g, col); px(eng, x + 1, y + 1, g, col);
        u += ca * 2; v += sa * 2;
      }
    }
  });
  const LutPlasma = E('LUT PLASMA', null, function (eng, env) {
    const P = this.P, sp = P.dir * (1 + env.mv * 0.6) * P.spd;
    const C = eng.cols, R = eng.rows;
    const t1 = (this.t * 70 * sp) | 0, t2 = (this.t * 48 * sp) | 0;
    const f1 = (5 + P.k1 * 5) | 0, f2 = (4 + P.k2 * 5) | 0, fy = (8 + P.k1 * 6) | 0;
    const c0 = acc(env, 0), c1 = acc(env, 1), bb = 0.3 + env.beat * 0.3;
    for (let y = 0; y < R; y += 2) {
      const sy = SLUT[(y * fy + t2) & 1023];
      for (let x = 0; x < C; x += 2) {
        const v = SLUT[(x * f1 + t1) & 1023] + sy + SLUT[((x + y) * f2 - t1) & 1023];
        const k = (v + 3) / 6;
        const g = gly(k), c = mul(lerpC(c0, c1, (SLUT[((v * 150) | 0) & 1023] + 1) / 2), bb + k);
        px(eng, x, y, g, c); px(eng, x + 1, y, g, c);
        px(eng, x, y + 1, g, c); px(eng, x + 1, y + 1, g, c);
      }
    }
  });
  const FracTree = E('FRACTAL TREE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const sway = Math.sin(this.t * 1.3) * 0.16 + env.mv * 0.22;
    const stack = [[C / 2, R - 2, -Math.PI / 2, Math.min(R, C) * 0.30, 0]];
    let guard = 0;
    while (stack.length && guard++ < 7000) {
      const s = stack.pop();
      const x = s[0], y = s[1], a = s[2], len = s[3], d = s[4];
      if (d > 9 || len < 1.1) continue;
      const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len;
      LN(eng, x, y, x2, y2, '#', mul(acc(env, d % 3), 0.3 + (9 - d) * 0.075 + env.beat * 0.3), 300);
      const na = 0.5 + sway;
      stack.push([x2, y2, a - na, len * 0.75, d + 1]);
      stack.push([x2, y2, a + na, len * 0.75, d + 1]);
      if (d < 2) stack.push([x2, y2, a + sway * 0.5, len * 0.62, d + 1]);
    }
  });
  const Bolt = E('LIGHTNING', function () { this.seg = []; this.life = 0; this.cd = 0; }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    this.cd = Math.max(0, this.cd - 0.04);
    if (this.cd <= 0 && (this.bt > 0.5 || (this.life <= 0 && Math.random() < 0.012))) {
      this.seg = [];
      const grow = (sx, sy, ang, len, depth) => {
        let cx = sx, cy = sy, a = ang, steps = 0;
        while (cy < R && steps++ < 50 && this.seg.length < 280) {
          a += (Math.random() - 0.5) * 0.7;
          const nx = cx + Math.cos(a) * len, ny = cy + Math.sin(a) * len;
          this.seg.push([cx, cy, nx, ny, depth]);
          if (depth < 2 && Math.random() < 0.15 && this.seg.length < 240)
            grow(nx, ny, a + (Math.random() < 0.5 ? -1 : 1) * (0.5 + Math.random()), len * 0.78, depth + 1);
          cx = nx; cy = ny;
        }
      };
      const bolts = 1 + (Math.random() < 0.3 ? 1 : 0);
      for (let b = 0; b < bolts; b++)
        grow(C * (0.2 + Math.random() * 0.6), 0, Math.PI / 2 + (Math.random() - 0.5) * 0.5, 4 + Math.random() * 3, 0);
      this.life = 1; this.cd = 0.5 + Math.random() * 1.3;
    }
    this.life = Math.max(0, this.life - 0.05);
    if (this.life <= 0) return;
    const fl = this.life, core = [235, 240, 255], halo = mul(acc(env, 2), 0.5 + fl * 0.5);
    for (let y = 0; y < 4; y++) eng.hspan(y, 0, C - 1, '.', mul(acc(env, 2), 0.04 + fl * 0.18 * (1 - y / 4)), 850);
    for (const s of this.seg) {
      const main = s[4] === 0;
      if (main) {
        LN(eng, s[0] - 1, s[1], s[2] - 1, s[3], '.', mul(halo, 0.45), 210);
        LN(eng, s[0] + 1, s[1], s[2] + 1, s[3], '.', mul(halo, 0.45), 210);
      }
      LN(eng, s[0], s[1], s[2], s[3], main ? '#' : '|',
        main ? mul(core, 0.4 + fl * 0.6) : mul(halo, 0.4 + fl * 0.5), 200);
    }
  });
  const Hilb = E('HILBERT', function () {
    const order = 5, n = 1 << order, N = n * n, pts = [];
    for (let s = 0; s < N; s++) {
      let rx, ry, t = s, x = 0, y = 0;
      for (let q = 1; q < n; q *= 2) {
        rx = 1 & ((t / 2) | 0); ry = 1 & (t ^ rx);
        if (ry === 0) { if (rx === 1) { x = q - 1 - x; y = q - 1 - y; } const tm = x; x = y; y = tm; }
        x += q * rx; y += q * ry; t = (t / 4) | 0;
      }
      pts.push([x - (n - 1) / 2, y - (n - 1) / 2]);   // centred
    }
    this.pts = pts; this.n = n;
  }, function (eng, env) {
    // the WHOLE curve drawn faint (ghost) with slow rotation + beat pulse,
    // and 2 bright comets racing along it with long fading trails.
    const C = eng.cols, R = eng.rows, p = this.pts, n = this.n, P = this.P, L = p.length;
    const sc = Math.min(C / n, R / n) * (1.4 + P.zoom * 0.6) * (1 + env.beat * 0.10);
    const rot = this.t * 0.25 * P.dir, cr = Math.cos(rot), sr = Math.sin(rot);
    const cx = C / 2, cy = R / 2;
    const SC = (a) => { const X = a[0] * sc, Y = a[1] * sc * 0.62; return [cx + X * cr - Y * sr, cy + X * sr + Y * cr]; };
    const ghost = mul(acc(env, 0), 0.10 + env.beat * 0.08);
    for (let i = 0; i < L - 1; i += 2) { const a = SC(p[i]), b = SC(p[i + 1]); LN(eng, a[0], a[1], b[0], b[1], '.', ghost, 600); }
    for (let cmt = 0; cmt < 2; cmt++) {
      const head = (((this.t * 170 * P.spd) | 0) + cmt * ((L / 2) | 0)) % L, tail = 150;
      for (let k = 0; k < tail; k++) {
        const i = (head - k + L) % L, a = SC(p[i]), b = SC(p[(i + 1) % L]), f = 1 - k / tail;
        LN(eng, a[0], a[1], b[0], b[1], f > 0.7 ? '#' : f > 0.35 ? '+' : '.',
          mul(acc(env, (cmt + (i >> 6)) % 3), 0.2 + f * 0.8 + env.beat * 0.3), 300);
      }
    }
  });
  const Rule30 = E('RULE 30', function (eng) {
    const C = eng.cols; this.row = new Uint8Array(C); this.row[C >> 1] = 1;
    this.hist = []; this.ac = 0; this.rules = [30, 90, 110, 150, 90, 184]; this.ri = 0;
  }, function (eng, env) {
    // generic Wolfram CA cycling iconic rules (30 chaos, 90 Sierpinski,
    // 110/150/184) — reseeds + switches rule on a strong beat so you watch
    // a fresh famous pattern build; cells coloured by generation age.
    const C = eng.cols, R = eng.rows;
    // switch rule + reseed only once the pattern has FILLED the screen
    // (then on a strong beat) — so the famous CA builds top->bottom across
    // the whole screen instead of perpetually rebuilding a stub at the
    // bottom. Grows one generation per frame.
    if (this.hist.length >= R && this.bt > 0.7) {
      this.ri = (this.ri + 1) % this.rules.length;
      const rl = this.rules[this.ri];
      this.row = new Uint8Array(C);
      if (rl === 30 || rl === 90 || rl === 150) this.row[C >> 1] = 1;
      else for (let x = 0; x < C; x++) this.row[x] = Math.random() < 0.3 ? 1 : 0;
      this.hist = [this.row];
    }
    if (!this.hist.length) this.hist = [this.row];
    if (this.hist.length < R) {
      const rule = this.rules[this.ri], r = this.row, nr = new Uint8Array(C);
      for (let x = 0; x < C; x++) {
        const p = (r[(x - 1 + C) % C] << 2) | (r[x] << 1) | r[(x + 1) % C];
        nr[x] = (rule >> p) & 1;
      }
      this.row = nr; this.hist.push(nr);
    }
    const H = this.hist, gen = H.length;
    const cA = acc(env, 0), cB = acc(env, 2);
    for (let y = 0; y < gen; y++) {                 // oldest at TOP, grows down
      const row = H[y], k = y / R;
      const col = mul(lerpC(cA, cB, k), 0.34 + k * 0.5 + env.beat * 0.35);
      for (let x = 0; x < C; x++) if (row[x]) px(eng, x, y, '#', col, 500);
    }
  });
  const Brain = E('BRIANS BRAIN', function (eng) {
    const C = eng.cols, R = eng.rows; this.g = new Uint8Array(C * R);
    for (let i = 0; i < this.g.length; i++) this.g[i] = Math.random() < 0.22 ? 1 : 0;
    this.ac = 0;
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, g = this.g;
    this.ac = (this.ac || 0) + 1;
    if (this.ac % 3 === 0 || this.bt > 0.5) {
      const n = (this._n && this._n.length === C * R) ? this._n : (this._n = new Uint8Array(C * R)); n.fill(0);
      for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
        const i = y * C + x, s = g[i];
        if (s === 1) { n[i] = 2; } else if (s === 2) { n[i] = 0; } else {
          let c = 0;
          for (let j = -1; j <= 1; j++) for (let k = -1; k <= 1; k++) {
            if (!j && !k) continue;
            if (g[((y + j + R) % R) * C + ((x + k + C) % C)] === 1) c++;
          }
          n[i] = (c === 2) ? 1 : 0;
        }
      }
      if (this.bt > 0.6) for (let q = 0; q < 24; q++) n[(Math.random() * n.length) | 0] = 1;
      this.g = n; this._n = g;          // ping-pong: old field -> next scratch
    }
    for (let y = 0; y < R; y++) for (let x = 0; x < C; x++) {
      const v = this.g[y * C + x];
      if (v) px(eng, x, y, v === 1 ? '#' : 'o', mul(acc(env, v === 1 ? 0 : 2), v === 1 ? 0.7 + env.beat * 0.4 : 0.4));
    }
  });
  const Spiro = E('SPIROGRAPH', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, Rr = Math.min(C / 2, R) * 0.46;
    const rk = 0.22 + this.P.k2 * 0.16, d = 0.5 + this.P.amp * 0.5;
    for (let i = 0; i < 900; i++) {
      const a = i * 0.06 + this.t;
      const x = (1 - rk) * Math.cos(a) + d * rk * Math.cos((1 - rk) / rk * a);
      const y = (1 - rk) * Math.sin(a) - d * rk * Math.sin((1 - rk) / rk * a);
      px(eng, C / 2 + x * Rr * 1.2, R / 2 + y * Rr, '.', mul(acc(env, (i / 150 | 0) % 3), 0.35 + env.beat * 0.5), 300);
    }
  });
  const VecTun = E('VECTOR TUNNEL', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, sides = 4 + (this.P.variant % 3);
    for (let i = 0; i < 16; i++) {
      const z = (((i - this.t * 3 * this.P.spd) % 16) + 16) % 16 + 0.6;
      const rr = (C * 0.5) / z, rot = this.t * 0.5 * this.P.dir + z * 0.2;
      let lx = 0, ly = 0;
      for (let s = 0; s <= sides; s++) {
        const a = rot + s / sides * 6.283;
        const X = C / 2 + Math.cos(a) * rr, Y = R / 2 + Math.sin(a) * rr * 0.6;
        if (s > 0) LN(eng, lx, ly, X, Y, '#', mul(acc(env, i % 3), 0.25 + (1 - z / 16) * 0.7 + env.beat * 0.3), z);
        lx = X; ly = Y;
      }
    }
  });
  const HyperJump = E('HYPERJUMP', function () {
    this.s = []; for (let i = 0; i < 220; i++) this.s.push({ a: Math.random() * 6.283, r: Math.random(), z: Math.random() });
    this.ch = 0;
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    this.ch = Math.min(1, Math.max(0, (this.ch || 0) + (this.bt > 0.6 ? 0.5 : -0.02)));
    const warp = 0.02 + this.ch * 0.22 + env.mv * 0.05;
    for (const p of this.s) {
      const pz0 = p.z; p.z -= warp; if (p.z < 0.02) { p.z = 1; p.a = Math.random() * 6.283; p.r = Math.random(); }
      const x1 = C / 2 + Math.cos(p.a) * p.r / p.z * C, y1 = R / 2 + Math.sin(p.a) * p.r / p.z * R * 0.6;
      const zz = Math.min(1, pz0), x0 = C / 2 + Math.cos(p.a) * p.r / zz * C, y0 = R / 2 + Math.sin(p.a) * p.r / zz * R * 0.6;
      LN(eng, x0, y0, x1, y1, this.ch > 0.5 ? '@' : '.', mul(acc(env, this.ch > 0.5 ? 2 : 0), (1 - p.z) * (0.45 + this.ch * 0.55)), p.z);
    }
  });
  const PhongCube = E('PHONG CUBE', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, s = Math.min(C, R * 2) * 0.28, a = this.t * this.P.dir, b = this.t * 0.7;
    const V = [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map(([x, y, z]) => {
      let y1 = y * Math.cos(a) - z * Math.sin(a), z1 = y * Math.sin(a) + z * Math.cos(a);
      let x1 = x * Math.cos(b) - z1 * Math.sin(b); z1 = x * Math.sin(b) + z1 * Math.cos(b);
      return [C / 2 + x1 * s, R / 2 - y1 * s, z1];
    });
    const F = [[0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7], [1, 5, 6, 2], [4, 5, 1, 0], [3, 2, 6, 7]];
    F.forEach((f, fi) => {
      const p0 = V[f[0]], p1 = V[f[1]], p2 = V[f[2]], p3 = V[f[3]];
      const nz = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]);
      if (nz <= 0) return;
      const cz = (p0[2] + p1[2] + p2[2] + p3[2]) / 4;
      const lit = Math.max(0.12, Math.min(1, (cz + 2.2) / 4)) * (0.6 + env.beat * 0.5);
      const col = mul(acc(env, fi % 3), 0.18 + lit), gl = gly(lit);
      const tri = (A, Bp, Cp) => {
        for (let u = 0; u <= 1; u += 0.075) for (let w = 0; w <= 1 - u; w += 0.075)
          eng.plot((A[0] + (Bp[0] - A[0]) * u + (Cp[0] - A[0]) * w) | 0,
            (A[1] + (Bp[1] - A[1]) * u + (Cp[1] - A[1]) * w) | 0, gl, col, 3 - cz);
      };
      tri(p0, p1, p2); tri(p0, p2, p3);
    });
  });
  const MetaDiscs = E('META DISCS', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P, t = this.t * P.spd * P.dir;
    const rm = 0.7 + P.amp * 0.7;
    const b = [[C / 2 + Math.sin(t) * C * 0.28, R / 2 + Math.cos(t * 1.3) * R * 0.28, 10 * rm],
    [C / 2 + Math.sin(t * 1.7 + 2) * C * 0.30, R / 2 + Math.sin(t * 0.9) * R * 0.30, 13 * rm],
    [C / 2 + Math.cos(t * 0.8) * C * 0.25, R / 2 + Math.cos(t * 1.5) * R * 0.28, 9 * rm]];
    for (const [cx, cy, rad] of b) {
      const r = rad + env.beat * 4 + env.mv * 3;
      for (let y = -r; y <= r; y += 2) {
        const xs = Math.sqrt(Math.max(0, r * r - y * y));
        for (let x = -xs; x <= xs; x += 2) {
          const k = 1 - (x * x + y * y) / (r * r);
          px(eng, cx + x, cy + y * 0.6, gly(0.3 + k * 0.7), mul(acc(env, k > 0.6 ? 2 : 0), 0.25 + k * (0.6 + env.beat * 0.4)), 400);
        }
      }
    }
  });
  const Donut = E('ASCII DONUT', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, P = this.P;
    const A = this.t * 0.8 * P.spd * P.dir, B = this.t * 0.5 * P.spd;
    const sc = Math.min(C, R * 2) * 0.40 * (0.78 + P.zoom * 0.45) * (1 + env.mv * 0.12);
    for (let th = 0; th < 6.283; th += 0.14) for (let ph = 0; ph < 6.283; ph += 0.07) {
      const cr = 1 + 0.42 * Math.cos(ph);
      let x = cr * Math.cos(th), y = 0.42 * Math.sin(ph), z = cr * Math.sin(th);
      let y1 = y * Math.cos(A) - z * Math.sin(A), z1 = y * Math.sin(A) + z * Math.cos(A);
      let x1 = x * Math.cos(B) - z1 * Math.sin(B); z1 = x * Math.sin(B) + z1 * Math.cos(B);
      if (z1 < -1.5) continue;
      const p = 2.6 / (3.4 + z1), L = Math.cos(ph - A) * 0.5 + 0.5;
      eng.plot((C / 2 + x1 * sc * p) | 0, (R / 2 - y1 * sc * p) | 0, gly(0.15 + L * 0.85),
        mul(acc(env, (ph * 2 | 0) % 3), 0.25 + L + env.beat * 0.3), 3.4 + z1);
    }
  });
  const WaveTerr = E('WAVE TERRAIN', null, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    for (let gz = 1; gz < 20; gz++) {
      let lx = 0, ly = 0;
      for (let gx = -12; gx <= 12; gx++) {
        const w = Math.sin(gx * 0.4 + this.t * 2) * Math.cos(gz * 0.3 + this.t) * (1 + env.beat) * this.P.amp;
        const z = gz + 2, X = C / 2 + gx / z * C * 0.95, Y = R * 0.62 - w * R * 0.14 / z * 8;
        if (gx > -12) LN(eng, lx, ly, X, Y, '#', mul(acc(env, gz % 3), 0.2 + (1 - gz / 20) + env.beat * 0.3), z);
        lx = X; ly = Y;
      }
    }
  });
  const PFire = E('PLASMA FIRE', function (eng) { this.w = eng.cols; this.h = eng.rows; this.b = new Float32Array(this.w * this.h); }, function (eng, env) {
    const w = this.w, h = this.h, b = this.b;
    // classic Doom fire: every cell = the cell below (with a small random
    // lateral drift) MINUS a random decay -> strictly cooling, flames die
    // out with height so most of the screen stays dark (never a flat
    // single-colour wall). Sparse hot source = licking tongues.
    const P = this.P;
    const sP = (0.50 + env.beat * 0.30) * (0.7 + P.amp * 0.6);
    const cool = (0.050 + env.mv * 0.02) * (0.75 + P.spd * 0.5);
    for (let x = 0; x < w; x++) b[(h - 1) * w + x] = (Math.random() < sP) ? (0.85 + Math.random() * 0.15) : 0;
    for (let y = h - 2; y >= 0; y--) for (let x = 0; x < w; x++) {
      const r = (Math.random() * 3) | 0;                  // 0..2
      const sx = (x + r - 1 + w) % w;                     // drift -1..+1
      const nv = b[(y + 1) * w + sx] - r * cool;
      b[y * w + x] = nv < 0 ? 0 : nv;
    }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const v = b[y * w + x]; if (v < 0.10) continue;
      const col = v > 0.72 ? acc(env, 2) : v > 0.40 ? acc(env, 0) : acc(env, 1);
      px(eng, x, y, gly(v), mul(col, 0.35 + v * 0.75), 500);
    }
  });
  const Shutter = E('SHUTTER', null, function (eng, env) {
    // venetian-blind iris: slats open/close (snapping wide on the beat)
    // revealing a flowing diagonal colour wash behind; metallic sheen edge.
    const C = eng.cols, R = eng.rows, P = this.P;
    const bands = 6 + (P.variant % 4), bh = Math.max(2, (R / bands) | 0);
    this.snap = Math.max(0, (this.snap || 0) - 0.05);
    if (this.bt > 0.5) this.snap = 1;
    const c0 = acc(env, 0), c1 = acc(env, 1), c2 = acc(env, 2);
    for (let y = 0; y < R; y++) {
      const bi = (y / bh) | 0, inb = y - bi * bh;
      let open = (Math.sin(this.t * 1.6 * P.spd + bi * 0.6) * 0.5 + 0.5) * 0.7 + this.snap * 0.35;
      if (open > 1) open = 1;
      const lit = Math.max(1, (bh * open) | 0);
      if (inb < lit) {
        const hue = Math.sin(y * 0.16 + this.t * 2 * P.dir) * 0.5 + 0.5;
        eng.hspan(y, 0, C - 1, gly(0.5 + 0.4 * hue),
          mul(lerpC(c0, c2, hue), 0.4 + 0.45 * hue + env.beat * 0.4), 500);
      } else if (inb === lit) {
        eng.hspan(y, 0, C - 1, '─', mul(c1, 0.7 + env.beat * 0.35), 510);
      } else {
        eng.hspan(y, 0, C - 1, '·', mul(c1, 0.12), 510);
      }
    }
  });
  const GravWell = E('GRAVITY WELL', function () { this.p = []; for (let i = 0; i < 150; i++) this.p.push({ x: Math.random(), y: Math.random(), vx: 0, vy: 0 }); }, function (eng, env) {
    const C = eng.cols, R = eng.rows;
    const wx = 0.5 + Math.sin(this.t * 0.6) * 0.3, wy = 0.5 + Math.cos(this.t * 0.8) * 0.3;
    for (const q of this.p) {
      const dx = wx - q.x, dy = wy - q.y, d = Math.sqrt(dx * dx + dy * dy) + 0.02;
      const f = 0.0007 / (d * d);
      q.vx = (q.vx + dx / d * f) * 0.995; q.vy = (q.vy + dy / d * f) * 0.995;
      q.x += q.vx; q.y += q.vy;
      if (d < 0.03 || q.x < -0.1 || q.x > 1.1 || q.y < -0.1 || q.y > 1.1) {
        q.x = Math.random(); q.y = Math.random(); q.vx = (Math.random() - 0.5) * 0.01; q.vy = (Math.random() - 0.5) * 0.01;
      }
      px(eng, q.x * C, q.y * R, '*', mul(acc(env, 0), 0.4 + Math.min(0.6, (Math.abs(q.vx) + Math.abs(q.vy)) * 45) + env.beat * 0.3), 300);
    }
    px(eng, wx * C, wy * R, '@', mul(acc(env, 2), 0.85 + env.beat * 0.2), 200);
  });
  const BoingShadow = E('BOING SHADOW', null, function (eng, env) {
    const C = eng.cols, R = eng.rows, T = env.t;       // smooth time -> no jerk
    const fl = R * 0.82;                                // floor line
    for (let y = 0; y < R; y += 2) for (let x = 0; x < C; x += 4) px(eng, x, y, '+', mul(acc(env, 1), 0.12), 800);
    const rr = Math.min(C * 0.12, R * 0.28);
    const hgt = Math.abs(Math.sin(T * 2.2 * this.P.spd));   // 0 floor .. 1 top
    const cx = C / 2 + Math.sin(T * 1.0 * this.P.dir) * C * 0.30;
    const cy = (fl - rr) - hgt * (fl - rr - R * 0.20);
    const sp = T * 3 * this.P.dir;
    const ss = 1.0 - hgt * 0.55;                        // shadow shrinks high
    for (let a = 0; a < 6.283; a += 0.12) px(eng, cx + Math.cos(a) * rr * 1.15 * ss, fl + Math.sin(a) * rr * 0.2 * ss, '#', [46, 46, 56], 700);
    for (let yy = -rr; yy <= rr; yy++) for (let xx = -rr * 2; xx <= rr * 2; xx++) {
      const nx = xx / (rr * 2), ny = yy / rr;
      if (nx * nx + ny * ny > 1) continue;
      const lon = Math.atan2(nx, Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny))) + sp, lat = Math.asin(ny);
      const chk = ((((lon / 0.5) | 0) + ((lat / 0.4) | 0)) & 1);
      px(eng, cx + xx, cy + yy, chk ? '@' : 'o', chk ? mul(acc(env, 0), 0.7 + env.beat * 0.3) : mul(acc(env, 1), 0.5), 300);
    }
  });
  const TextRing = E('TEXT RINGS', function () { this.w = SONG_WORD(); }, function (eng, env) {
    const C = eng.cols, R = eng.rows, w = this.w, n = w.length;
    for (let i = 0; i < 6; i++) {
      const z = (((i * 1.4 - this.t * 2 * this.P.spd) % 9) + 9) % 9 + 0.7;
      const rr = (C * 0.42) / z, yr = R * 0.42 / z;
      for (let k = 0; k < n; k++) {
        const a = k / n * 6.283 + this.t * this.P.dir + i * 0.5;
        px(eng, C / 2 + Math.cos(a) * rr, R / 2 + Math.sin(a) * yr, w[k],
          mul(acc(env, i % 3), 0.25 + (1 - z / 9) * 0.7 + env.beat * 0.3), z);
      }
    }
  });
  const Elite = E('ELITE', function () {
    const ZF = 16; this.ZF = ZF;
    this.mkv = (t) => {
      if (t === 1) return { V: [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]],
        E: [[4, 0], [4, 2], [4, 1], [4, 3], [5, 0], [5, 2], [5, 1], [5, 3], [0, 2], [2, 1], [1, 3], [3, 0]] };
      if (t === 2) { const j = () => (Math.random() - 0.5) * 0.5;
        return { V: [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map(([x, y, z]) => [x + j(), y + j(), z + j()]),
          E: [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]] }; }
      return { V: [[0, 0, 1.7], [-1.5, 0, -0.9], [1.5, 0, -0.9], [0, 0.5, -0.9], [0, -0.35, -0.9], [-0.5, 0, -1.2], [0.5, 0, -1.2]],
        E: [[0, 1], [0, 2], [1, 2], [0, 3], [0, 4], [1, 5], [2, 6], [3, 5], [3, 6], [4, 5], [4, 6], [5, 6]] };
    };
    this.spawn = () => ({ t: (Math.random() * 3) | 0, x: (Math.random() * 2 - 1) * 4, y: (Math.random() * 2 - 1) * 2.5,
      z: 8 + Math.random() * ZF, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.25,
      rx: Math.random() * 6, ry: Math.random() * 6, vrx: (Math.random() - 0.5) * 1.4, vry: (Math.random() - 0.5) * 1.4,
      sc: 0.7 + Math.random() * 0.7 });
    this.st = [];
    for (let i = 0; i < 80; i++) this.st.push({ x: (Math.random() * 2 - 1) * 1.4, y: (Math.random() * 2 - 1) * 1.4, z: 0.3 + Math.random() * ZF });
    this.ob = [this.spawn(), this.spawn()];
    for (const o of this.ob) o.geo = this.mkv(o.t);
    this.planet = { z: ZF * 4, x: (Math.random() * 2 - 1) * 3, y: (Math.random() * 2 - 1) * 1.4, r: 1.8 };
    this.las = 0; this._lt = 0;
  }, function (eng, env) {
    const C = eng.cols, R = eng.rows, ZF = this.ZF;
    const BLK = [6, 7, 12], WHT = [214, 219, 230], DIM = [120, 126, 150], GRN = [110, 235, 130];
    let dt = env.t - (this._lt || env.t); if (dt < 0 || dt > 0.1) dt = 0.016; this._lt = env.t;
    const spd = (2.2 + env.mv * 4 + env.beat * 1.6) * this.P.spd;
    const F = C * 0.62 * (0.85 + this.P.zoom * 0.3), hY = R * 0.44;
    BG(eng, BLK);
    for (const s of this.st) {
      const z0 = s.z; s.z -= spd * dt * 1.5;
      if (s.z < 0.25) { s.z = ZF; s.x = (Math.random() * 2 - 1) * 1.4; s.y = (Math.random() * 2 - 1) * 1.4; continue; }
      const b = 1 - s.z / ZF;
      LN(eng, C / 2 + s.x / z0 * F, hY - s.y / z0 * F, C / 2 + s.x / s.z * F, hY - s.y / s.z * F,
        b > 0.7 ? '@' : b > 0.4 ? '*' : '.', mul(WHT, 0.28 + b * 0.72), s.z);
    }
    const pl = this.planet; pl.z -= spd * dt * 0.12;
    if (pl.z < 2.2) { pl.z = ZF * 4; pl.x = (Math.random() * 2 - 1) * 3; pl.y = (Math.random() * 2 - 1) * 1.4; }
    const ppx = C / 2 + pl.x / pl.z * F, ppy = hY - pl.y / pl.z * F, ppr = pl.r / pl.z * F;
    if (ppr > 1.5) {
      for (let aa = 0; aa < 6.283; aa += 0.09) px(eng, ppx + Math.cos(aa) * ppr, ppy + Math.sin(aa) * ppr * 0.62, '#', DIM, pl.z);
      for (let li = -0.6; li <= 0.6; li += 0.6) LN(eng, ppx - ppr, ppy + li * ppr * 0.62, ppx + ppr, ppy + li * ppr * 0.62, '.', mul(DIM, 0.7), pl.z - 0.01);
    }
    for (const o of this.ob) {
      o.z -= spd * dt; o.x += o.vx * dt; o.y += o.vy * dt;
      o.rx += o.vrx * dt * this.P.dir; o.ry += o.vry * dt;
      if (o.z < 1.1) { Object.assign(o, this.spawn()); o.geo = this.mkv(o.t); continue; }
      const ca = Math.cos(o.rx), sa = Math.sin(o.rx), cb = Math.cos(o.ry), sb = Math.sin(o.ry);
      const P2 = o.geo.V.map(([x, y, z]) => {
        let y1 = y * ca - z * sa, z1 = y * sa + z * ca;
        let x1 = x * cb - z1 * sb; z1 = x * sb + z1 * cb;
        const cz = Math.max(0.3, o.z + z1 * o.sc);
        return [C / 2 + (o.x + x1 * o.sc) / cz * F, hY - (o.y + y1 * o.sc) / cz * F];
      });
      const dimf = Math.max(0.25, Math.min(1, 2.4 / o.z));
      const col = mul(WHT, 0.3 + dimf * 0.8 + env.beat * 0.2);
      o.geo.E.forEach(([i, j]) => LN(eng, P2[i][0], P2[i][1], P2[j][0], P2[j][1], '#', col, o.z));
    }
    const ccx = (C / 2) | 0, ccy = hY | 0;
    LN(eng, ccx - 4, ccy, ccx - 1, ccy, '-', GRN, 40); LN(eng, ccx + 1, ccy, ccx + 4, ccy, '-', GRN, 40);
    LN(eng, ccx, ccy - 3, ccx, ccy - 1, '|', GRN, 40); LN(eng, ccx, ccy + 1, ccx, ccy + 3, '|', GRN, 40);
    px(eng, ccx, ccy, '+', GRN, 38);
    this.las = this.bt > 0.5 ? 1 : Math.max(0, this.las - 0.12);
    if (this.las > 0.05) {
      const lc = mul([255, 95, 95], 0.5 + this.las * 0.6);
      LN(eng, 1, R - 7, ccx, ccy, '/', lc, 35); LN(eng, C - 2, R - 7, ccx, ccy, '\\', lc, 35);
    }
    const dy = R - 5;
    for (let y = dy; y < R; y++) eng.hspan(y, 0, C - 1, '-', [40, 44, 60], 250);
    const scx = (C / 2) | 0, scy = R - 3, sw = C * 0.16, sh = 2.4;
    for (let aa = 0; aa < 6.283; aa += 0.09) px(eng, scx + Math.cos(aa) * sw, scy + Math.sin(aa) * sh, '.', [70, 120, 70], 200);
    LN(eng, scx - sw, scy, scx + sw, scy, '.', [58, 96, 58], 199);
    for (const o of this.ob) px(eng, scx + (o.x / Math.max(1, o.z * 0.5)) * sw, scy - Math.max(0.05, 1 - o.z / ZF) * sh * 0.8, '+', GRN, 190);
  });
  window.Worlds = window.Worlds || {};
  window.Worlds.demos = [
    Plasma, Roto, Stars, Copper, Bobs, Tunnel, Twister, Glenz, Boing,
    CopperBars, StarWarp, SineCols, BobsLissa, WireCube,
    Meta, DotSphere, Raster, Kefrens, Shadebobs, Moire, Road, Mandel, Worm,
    Life, XOR, Ripple, Helix, Starburst, Rain, Torus, Hex, Lissa, PlasTun,
    VBallGrid, Spiral, Checker, Burst3D, Interf, Grid3D,
    RotBars, StarCyl, Rings, Spectrum, Julia, DVD, PolarSwirl, TunRings,
    DotWave, WireSphere, Glitch, Galaxy, Fireworks, Metatun, Cubes,
    SinScrollDots, Voxel2, Plasma2, Lens, Conway3,
    LitTunnel, IcoLit, Attractor, ReacDiff, MetaLit, DeepZoom, BumpPlasma,
    WarpStars, TorusKnot, InkFluid,
    KineticType, Turmites, MazeGrow, Scope, Sand, Raymarch, Boids, Harmono,
    Mandala, CodeHall, WireRidge, BallPit, DLA, Plume, PendWave, Tesseract,
    Radar, Truchet, Voronoi, BurnShip,
    RotoTex, LutPlasma, FracTree, Bolt, Hilb, Rule30, Brain, Spiro,
    VecTun, HyperJump, PhongCube, MetaDiscs, Donut, WaveTerr,
    PFire, Shutter, GravWell, BoingShadow, TextRing, Elite, AsmHall,
  ];
})();
