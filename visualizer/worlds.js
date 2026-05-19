// worlds.js — distinct classic-game worlds, all drawn by the one A3D engine.
// Each world: reset(eng,section) / note(n) / beat() / step(dt,env) / draw(eng,env)
// env = { pal:{bg,fg,accent[]}, beat:0..1, t:seconds }.
(function () {
  function hash2(x, y) {
    let n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
    return n - Math.floor(n);
  }
  function vnoise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash2(xi, yi), b = hash2(xi + 1, yi);
    const c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  const acc = (env, i) => env.pal.accent[i % env.pal.accent.length];
  const scale = (c, k) => [(c[0] * k) | 0, (c[1] * k) | 0, (c[2] * k) | 0];

  // ===================================================== DOOM
  const ART = {
    lamp: [' | ', '(O)', ' | '],
    barrel: [' __ ', '|##|', '|##|', '|__|'],
    imp: [' ^^ ', '/oo\\', ' \\/ ', ' /\\ '],
    medkit: [' +++ ', '+MED+', ' +++ '],
    ammo: ['[===]', '[|||]'],
    key: [' o ', '=|=', ' | '],
    fire: [' (*) ', '(***)', ' (*) '],
    portal: [' /~\\ ', '|( )|', ' \\~/ '],
  };
  const Doom = {
    title: 'E1M1',
    reset(eng) {
      this.N = 21; this.level = 1; this.t = 0; this.lvlT = 0;
      this.flash = 0; this.balls = []; this.spark = null; this.fireCd = 0;
      this._gen();
    },
    _gen() {
      const N = this.N;
      this.m = Array.from({ length: N }, () => new Array(N).fill(1));
      const st = [[1, 1]]; this.m[1][1] = 0;
      const D = [[0, -2], [0, 2], [-2, 0], [2, 0]];
      while (st.length) {
        const [x, y] = st[st.length - 1], o = [];
        for (const [dx, dy] of D) {
          const nx = x + dx, ny = y + dy;
          if (nx > 0 && ny > 0 && nx < N - 1 && ny < N - 1 && this.m[ny][nx] === 1)
            o.push([nx, ny, dx, dy]);
        }
        if (!o.length) { st.pop(); continue; }
        const [nx, ny, dx, dy] = o[(Math.random() * o.length) | 0];
        this.m[y + dy / 2][x + dx / 2] = 0; this.m[ny][nx] = 0; st.push([nx, ny]);
      }
      this.px = 1.5; this.pz = 1.5; this.ang = 0; this.turn = 0;
      const open = [];
      for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++)
        if (this.m[y][x] === 0) open.push([x, y]);
      let best = open[0], bd = -1;
      for (const [x, y] of open) { const d = x + y; if (d > bd) { bd = d; best = [x, y]; } }
      this.exit = { x: best[0] + 0.5, z: best[1] + 0.5 };
      this.lava = new Set();
      for (const [x, y] of open)
        if (x + y > 5 && (x !== best[0] || y !== best[1]) && Math.random() < 0.06)
          this.lava.add(y * N + x);
      const free = open.filter(([x, y]) =>
        !this.lava.has(y * N + x) && (x > 2 || y > 2) && (x !== best[0] || y !== best[1]));
      this.pickups = [];
      for (let i = 0; i < 5 && free.length; i++) {
        const j = (Math.random() * free.length) | 0, cell = free.splice(j, 1)[0];
        const k = ['medkit', 'ammo', 'key', 'ammo', 'medkit'][i];
        this.pickups.push({ x: cell[0] + 0.5, z: cell[1] + 0.5, kind: k, art: ART[k], got: 0 });
      }
      this.props = [];
      for (let i = 0; i < 72; i++) {
        const x = 1 + ((Math.random() * (N - 2)) | 0);
        const y = 1 + ((Math.random() * (N - 2)) | 0);
        if (this.m[y][x] === 0 && !this.lava.has(y * N + x)) {
          const k = ['lamp', 'imp', 'barrel', 'imp', 'imp'][(Math.random() * 5) | 0];
          this.props.push({ x: x + 0.5, z: y + 0.5, kind: k, art: ART[k], ph: Math.random() * 6 });
        }
      }
      this.foes = [];
      for (let i = 0; i < 2; i++) {
        let fx = this.px + 1.5 + i * 1.2, fz = this.pz, a = 0.6 + i * 2;
        for (let ti = 0; ti < 16; ti++) {
          const tx = this.px + Math.cos(a) * (1.5 + i), tz = this.pz + Math.sin(a) * (1.5 + i);
          if (this._clear(tx, tz, 0.42)) { fx = tx; fz = tz; break; }
          a += 1.3;
        }
        this.foes.push({ x: fx, z: fz, ang: a, ph: Math.random() * 6,
          sp: 0.26 + Math.random() * 0.12, art: ART.imp, hit: 0 });
      }
      this.title = 'E1M' + this.level;
    },
    _advance() {
      this.level++; this.lvlT = this.t; this.flash = 1;
      this.balls = []; this._gen();
    },
    note() { this.flash = Math.min(1, this.flash + 0.5); },
    beat() { if (this.fireCd <= 0) { this._shoot(); this.fireCd = 0.12; } },
    wall(x, z) { return x < 0 || z < 0 || x >= this.N || z >= this.N || this.m[z | 0][x | 0] === 1; },
    _clear(x, z, r) {
      return !this.wall(x - r, z - r) && !this.wall(x + r, z - r)
        && !this.wall(x - r, z + r) && !this.wall(x + r, z + r) && !this.wall(x, z);
    },
    _probe(a) {
      let d = 0;
      while (d < 6 && !this.wall(this.px + Math.cos(a) * d, this.pz + Math.sin(a) * d)) d += 0.35;
      return d;
    },
    _foeProbe(f, a) {
      let d = 0;
      while (d < 4 && !this.wall(f.x + Math.cos(a) * d, f.z + Math.sin(a) * d)) d += 0.35;
      return d;
    },
    _shoot() {
      const ca = Math.cos(this.ang), sa = Math.sin(this.ang);
      let wd = 0;
      while (wd < 9 && !this.wall(this.px + ca * wd, this.pz + sa * wd)) wd += 0.2;
      for (const f of this.foes) {
        const dx = f.x - this.px, dz = f.z - this.pz;
        const fwd = dx * ca + dz * sa, lat = -dx * sa + dz * ca;
        if (fwd > 0.4 && fwd < Math.min(wd, 7) && Math.abs(lat) < 0.7) {
          f.hit = 1;
          const kx = f.x + ca * 0.6, kz = f.z + sa * 0.6;
          if (this._clear(kx, f.z, 0.42)) f.x = kx;
          if (this._clear(f.x, kz, 0.42)) f.z = kz;
        }
      }
      this.spark = { x: this.px + ca * Math.min(wd, 7), z: this.pz + sa * Math.min(wd, 7), t: 1 };
      this.flash = Math.max(this.flash, 0.7);
    },
    step(dt) {
      this.t += dt;
      this.fireCd = Math.max(0, this.fireCd - dt);
      const fx = Math.cos(this.ang), fz = Math.sin(this.ang);
      const blocked = this.wall(this.px + fx * 0.55, this.pz + fz * 0.55);
      if (blocked) {
        const L = this._probe(this.ang - 1.15), R = this._probe(this.ang + 1.15);
        this.turn = (L > R ? -1 : 1) * 2.0;
      } else if (Math.random() < 0.02) {
        this.turn = (Math.random() - 0.5) * 1.4;
      }
      this.ang += (this.turn || 0) * dt;
      this.turn = (this.turn || 0) * 0.90;
      const sp = (blocked ? 0 : 1.5) * dt;
      const nx = this.px + fx * sp, nz = this.pz + fz * sp;
      let moved = 0;
      if (!this.wall(nx, this.pz)) { moved += Math.abs(nx - this.px); this.px = nx; }
      if (!this.wall(this.px, nz)) { moved += Math.abs(nz - this.pz); this.pz = nz; }
      this._stuck = moved < 1e-4 ? (this._stuck || 0) + dt : 0;
      if (this._stuck > 0.8) { this.ang += 1.7; this._stuck = 0; }
      for (const f of this.foes) {
        f.hit = Math.max(0, (f.hit || 0) - dt * 3);
        let da = Math.atan2(this.pz - f.z, this.px - f.x) - f.ang;
        while (da > Math.PI) da -= 6.283;
        while (da < -Math.PI) da += 6.283;
        f.ang += da * 0.6 * dt + (Math.random() - 0.5) * 0.7 * dt;
        let ffx = Math.cos(f.ang), ffz = Math.sin(f.ang);
        if (!this._clear(f.x + ffx * 0.6, f.z + ffz * 0.6, 0.42)) {
          const lp = this._foeProbe(f, f.ang - 1.2), rp = this._foeProbe(f, f.ang + 1.2);
          f.ang += (lp > rp ? -1 : 1) * 2.4 * dt + 0.7;
          ffx = Math.cos(f.ang); ffz = Math.sin(f.ang);
        }
        const fsp = f.sp * dt;
        let fm = 0;
        if (this._clear(f.x + ffx * fsp, f.z, 0.42)) { f.x += ffx * fsp; fm += Math.abs(ffx * fsp); }
        if (this._clear(f.x, f.z + ffz * fsp, 0.42)) { f.z += ffz * fsp; fm += Math.abs(ffz * fsp); }
        f._st = fm < 1e-4 ? (f._st || 0) + dt : 0;
        if (f._st > 0.6) { f.ang += 1.9; f._st = 0; }
        if (this.balls.length < 5 && Math.random() < 0.4 * dt) {
          const d = Math.hypot(this.px - f.x, this.pz - f.z);
          if (d > 1.6 && d < 9)
            this.balls.push({ x: f.x, z: f.z, dx: (this.px - f.x) / d, dz: (this.pz - f.z) / d, t: 0 });
        }
        if (Math.hypot(f.x - this.px, f.z - this.pz) > 10) {
          for (let ti = 0; ti < 12; ti++) {
            const a = this.ang + (Math.random() - 0.5) * 1.4, r = 2 + Math.random() * 1.6;
            const rx = this.px + Math.cos(a) * r, rz = this.pz + Math.sin(a) * r;
            if (this._clear(rx, rz, 0.42)) { f.x = rx; f.z = rz; f.ang = a; f._st = 0; break; }
          }
        }
      }
      for (let i = this.balls.length - 1; i >= 0; i--) {
        const b = this.balls[i]; b.t += dt;
        b.x += b.dx * dt * 2.4; b.z += b.dz * dt * 2.4;
        if (b.t > 3 || Math.hypot(b.x - this.px, b.z - this.pz) < 0.5 || this.wall(b.x, b.z))
          this.balls.splice(i, 1);
      }
      for (const p of this.pickups) {
        if (p.got > 0) {
          p.got = Math.max(0, p.got - dt);
          if (p.got === 0 && p._to) { p.x = p._to.x; p.z = p._to.z; p._to = null; }
        } else if (Math.hypot(p.x - this.px, p.z - this.pz) < 0.85) {
          p.got = 0.6;
          for (let ti = 0; ti < 14; ti++) {
            const cx = 1 + ((Math.random() * (this.N - 2)) | 0);
            const cz = 1 + ((Math.random() * (this.N - 2)) | 0);
            if (this.m[cz][cx] === 0 && !this.lava.has(cz * this.N + cx)) {
              p._to = { x: cx + 0.5, z: cz + 0.5 }; break;
            }
          }
          this.flash = Math.max(this.flash, 0.5);
        }
      }
      if (this.spark) { this.spark.t -= dt * 3; if (this.spark.t <= 0) this.spark = null; }
      if (Math.hypot(this.px - this.exit.x, this.pz - this.exit.z) < 1.0
        || this.t - this.lvlT > 105) this._advance();
      this.flash = Math.max(0, this.flash - dt * 2.2);
    },
    draw(eng, env) {
      const c = eng.cam;
      c.x = this.px; c.z = this.pz; c.y = 0.56; c.yaw = -this.ang;
      c.pitch = 0; c.fov = 0.66;
      const cols = eng.cols, rows = eng.rows;
      const lrp = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
      const horizon = (rows * 0.5 + Math.sin(env.t * 1.6) * 0.8 + env.beat * 2.2) | 0;
      const A1 = acc(env, 1), floorC = acc(env, 0);
      const WT = [scale(A1, 0.95), lrp(A1, [185, 140, 80], 0.55), lrp(A1, [165, 50, 45], 0.6)];
      const lavaPulse = 0.7 + 0.3 * Math.sin(env.t * 6);
      for (let sx = 0; sx < cols; sx++) {
        const camX = (2 * sx) / cols - 1;
        const ra = this.ang + Math.atan(camX * c.fov);
        const rdx = Math.cos(ra), rdz = Math.sin(ra);
        let mx = this.px | 0, mz = this.pz | 0;
        const ddx = Math.abs(1 / (rdx || 1e-9)), ddz = Math.abs(1 / (rdz || 1e-9));
        let sxx, szz, sdx, sdz;
        if (rdx < 0) { sxx = -1; sdx = (this.px - mx) * ddx; } else { sxx = 1; sdx = (mx + 1 - this.px) * ddx; }
        if (rdz < 0) { szz = -1; sdz = (this.pz - mz) * ddz; } else { szz = 1; sdz = (mz + 1 - this.pz) * ddz; }
        let side = 0, hit = false, g = 0;
        while (!hit && g++ < 80) {
          if (sdx < sdz) { sdx += ddx; mx += sxx; side = 0; }
          else { sdz += ddz; mz += szz; side = 1; }
          if (mx < 0 || mz < 0 || mx >= this.N || mz >= this.N || this.m[mz][mx] === 1) hit = true;
        }
        let dist = side === 0 ? (mx - this.px + (1 - sxx) / 2) / (rdx || 1e-9)
          : (mz - this.pz + (1 - szz) / 2) / (rdz || 1e-9);
        dist = Math.max(0.1, Math.abs(dist) * Math.cos(ra - this.ang));
        const wh = Math.min(rows * 3, (rows / dist) | 0);
        const top = horizon - (wh >> 1), bot = horizon + (wh >> 1);
        const lit = Math.max(0.08, 1 - dist / 16) + this.flash * 0.4;
        const wt = (hash2(mx, mz) * 3) | 0;
        const base = side ? scale(WT[wt], 0.7) : WT[wt];
        const wc = eng.fog(base, dist);
        eng.vspan(sx, 0, top - 1, eng.ramp(0.04), scale(env.pal.fg, 0.18), 50);
        const gl = eng.ramp(Math.min(0.99, lit));
        eng.vspan(sx, top, bot, gl, [Math.min(255, wc[0] * (1 + lit * 0.4)) | 0,
          Math.min(255, wc[1] * (1 + lit * 0.4)) | 0, Math.min(255, wc[2] * (1 + lit * 0.4)) | 0], dist);
        for (let yy = bot + 1; yy < rows; yy += 1) {
          const fd = (rows * 0.5) / (yy - horizon || 1), ad = Math.abs(fd);
          const lx = (this.px + rdx * ad) | 0, lz = (this.pz + rdz * ad) | 0;
          if (lx >= 0 && lz >= 0 && lx < this.N && lz < this.N && this.lava.has(lz * this.N + lx))
            eng.vspan(sx, yy, yy, '~', eng.fog(scale([255, 120, 45], lavaPulse), ad + 1), ad + 1);
          else
            eng.vspan(sx, yy, yy, ':', eng.fog(floorC, ad + 1), ad + 1);
        }
      }
      for (const p of this.props) {
        const bob = p.kind === 'imp' ? Math.sin(env.t * 4 + p.ph) * 0.12 : 0;
        const col = p.kind === 'lamp'
          ? scale(acc(env, 2), 0.7 + 0.3 * Math.sin(env.t * 7 + p.ph) + this.flash)
          : (p.kind === 'imp' ? acc(env, 0) : env.pal.fg);
        eng.sprite(p.x, 0.5 + bob, p.z, p.art, col, 0.9);
      }
      for (const p of this.pickups) {
        if (p.got > 0) { eng.sprite(p.x, 0.7, p.z, ['+'], scale(acc(env, 2), 1.3), 1.0); continue; }
        eng.sprite(p.x, 0.45 + Math.sin(env.t * 4) * 0.1, p.z, p.art,
          scale(acc(env, 2), 0.7 + 0.3 * Math.sin(env.t * 6) + env.beat * 0.3), 0.85);
      }
      eng.sprite(this.exit.x, 0.55, this.exit.z, ART.portal,
        scale(acc(env, 2), 0.8 + 0.4 * Math.sin(env.t * 5) + this.flash * 0.4), 1.1);
      for (const f of this.foes) {
        const fc = f.hit > 0 ? [255, 255, 255]
          : scale(acc(env, 0), 0.8 + this.flash + env.beat * 0.35);
        eng.sprite(f.x, 0.5 + Math.sin(env.t * 5 + f.ph) * 0.14, f.z, f.art, fc, 1.2);
      }
      for (const b of this.balls)
        eng.sprite(b.x, 0.5, b.z, ART.fire,
          lrp([255, 180, 60], [255, 90, 30], Math.min(1, b.t * 0.4)), 1.3);
      if (this.spark)
        eng.sprite(this.spark.x, 0.5, this.spark.z, ['\\|/', '-+-', '/|\\'],
          scale([255, 240, 200], this.spark.t), 0.7);
      if (this.flash > 0.45) {
        const mxp = (cols / 2) | 0, myp = (rows * 0.62) | 0;
        eng.glyph2d(mxp, myp, '*', [255, 255, 220]);
        eng.glyph2d(mxp - 1, myp, '(', [255, 230, 160]);
        eng.glyph2d(mxp + 1, myp, ')', [255, 230, 160]);
      }
      eng.text2d(2, rows - 2, 'E1M' + this.level, scale(acc(env, 2), 0.7 + this.flash * 0.3));
    },
  };

  // ===================================================== LANDSCAPE
  const Land = {
    title: 'TERRAIN',
    reset(eng) { this.cx = 0; this.cz = 0; this.ang = 0; this.birds = []; this.t = 0; },
    note() { this.birds.push({ x: this.cx + 6 + Math.random() * 8, y: 3 + Math.random() * 3, z: this.cz + (Math.random() - 0.5) * 8, life: 1 }); },
    beat() { this._lift = 0.6; },
    h(x, z) { return vnoise(x * 0.12, z * 0.12) * 5.5 + vnoise(x * 0.4, z * 0.4) * 1.1; },
    step(dt) {
      this.t += dt;
      this.ang = Math.sin(this.t * 0.13) * 0.5;
      this.cx += Math.sin(this.ang) * dt * 3.2;
      this.cz += Math.cos(this.ang) * dt * 3.2;
      this._lift = Math.max(0, (this._lift || 0) - dt);
      this.birds = this.birds.filter((b) => (b.life -= dt * 0.25) > 0);
      for (const b of this.birds) b.x -= dt * 1.5;
    },
    draw(eng, env) {
      const c = eng.cam, rows = eng.rows, cols = eng.cols;
      const groundY = this.h(this.cx, this.cz);
      c.x = this.cx; c.z = this.cz; c.y = groundY + 3.4 + (this._lift || 0) + Math.sin(this.t) * 0.2;
      c.yaw = -this.ang - Math.PI / 2; c.pitch = -0.12;
      c.roll = Math.sin(this.t * 0.4) * 0.06; c.fov = 0.95;
      // sky gradient + sun
      for (let r = 0; r < rows; r++) {
        const k = r / rows;
        const sky = [env.pal.bg[0] + (acc(env, 2)[0] - env.pal.bg[0]) * (0.5 - k) * 0.5,
          env.pal.bg[1] + (acc(env, 2)[1] - env.pal.bg[1]) * (0.5 - k) * 0.5,
          env.pal.bg[2] + (acc(env, 2)[2] - env.pal.bg[2]) * (0.5 - k) * 0.5].map((v) => Math.max(0, v | 0));
        const gch = ' .`·:'[Math.min(4, (k * 5) | 0)] || ' ';
        for (let sx = 0; sx < cols; sx += 1) eng.plot(sx, r, gch, sky, 900);
      }
      const sunx = (cols * 0.5 + Math.sin(this.t * 0.1) * cols * 0.3) | 0;
      for (let a = 0; a < 6.28; a += 0.25)
        eng.plot(sunx + Math.cos(a) * 4, rows * 0.22 + Math.sin(a) * 3, '@', acc(env, 2), 880);
      // voxel terrain, front-to-back with per-column floor
      const ybuf = new Int16Array(cols).fill(rows);
      for (let d = 1; d < 60; d += 0.5) {
        const ca = Math.cos(c.yaw + Math.PI / 2), sa = Math.sin(c.yaw + Math.PI / 2);
        for (let sx = 0; sx < cols; sx++) {
          const camX = (2 * sx) / cols - 1;
          const rx = this.cx + (ca + Math.sin(c.yaw + Math.PI / 2 + 1.5708) * camX * 0.9) * d;
          const rz = this.cz + (sa + Math.cos(c.yaw + Math.PI / 2 + 1.5708) * camX * 0.9) * d;
          const th = this.h(rx, rz);
          const sy = (rows * 0.5 + (c.y - th) * (rows * 0.5) / (c.fov * d) - rows * 0.5 + rows * 0.5) | 0;
          const py = Math.max(0, sy);
          if (py < ybuf[sx]) {
            const b = Math.max(0.08, Math.min(1, th / 7)) * Math.max(0.1, 1 - d / 55);
            const col = th > 4.3 ? env.pal.fg : (th > 2 ? acc(env, 0) : acc(env, 1));
            for (let yy = py; yy < ybuf[sx]; yy++)
              eng.plot(sx, yy, eng.ramp(b), eng.fog(col, d), d);
            ybuf[sx] = py;
          }
        }
      }
      for (const b of this.birds)
        eng.sprite(b.x, b.y, b.z, ['\\/'], scale(env.pal.fg, b.life), 0.8);
    },
  };

  // ===================================================== 2D SIDE-SCROLLER
  const Side = {
    title: 'STAGE 1-1',
    reset(eng) {
      this.sx = 0; this.run = 0; this.jump = 0; this.vy = 0; this.y = 0;
      this.level = 1; this._hop = 0; this.flash = 0;
      this.coins = []; this.t = 0;
      for (let i = 0; i < 60; i++) this.coins.push({ x: 8 + i * 3.5 + Math.random() * 2, y: 1 + Math.random() * 2.5 });
      this.gaps = [];
      for (let i = 0; i < 30; i++) this.gaps.push(14 + i * 9 + ((Math.random() * 4) | 0));
    },
    note() { for (const co of this.coins) if (Math.abs(co.x - (this.sx + 4)) < 1.5) co.got = 0.4; },
    beat() { if (this.y <= 0.01) { this.vy = 7.2; } },
    overGap() { for (const g of this.gaps) if (Math.abs((this.sx + 4) - g) < 1.1) return true; return false; },
    groundY(wx) { return ((hash2(Math.floor(wx / 7), 5) * 4) | 0) * 0.8; },  // stepped plateaus
    step(dt) {
      this.t += dt; this.sx += dt * 5.5; this.run = (this.run + dt * 14) % 4;
      // distinct stages: every 90 units is a new level (flash on entry)
      const lv = 1 + Math.floor(this.sx / 90);
      if (lv !== this.level) { this.level = lv; this.flash = 1; }
      this.flash = Math.max(0, this.flash - dt * 1.5);
      // a platformer that's always BOUNDING along (steady hop), with
      // bigger jumps on the beat (beat()) and over gaps.
      this._hop -= dt;
      if (this.y <= 0.01 && this._hop <= 0) { this.vy = 5.2; this._hop = 0.42 + Math.random() * 0.22; }
      if (this.y <= 0.01 && this.overGap()) this.vy = 7.0;
      this.vy -= 22 * dt; this.y += this.vy * dt;
      if (this.y < 0) { this.y = 0; this.vy = 0; }
      for (const co of this.coins) if (co.got !== undefined) co.got = Math.max(0, co.got - dt);
    },
    draw(eng, env) {
      const c = eng.cam, rows = eng.rows, cols = eng.cols;
      // flat 2D side-scroller. A far ortho cam pushed all geometry past
      // farFog(26) so fog() crushed it to the 6% floor (invisible) and
      // collapsed sprites to 1px. Sane cam depth + no distance fog here.
      const _ff = eng.farFog; eng.farFog = 1e6;
      c.x = this.sx + 4; c.y = 2; c.z = -12;
      c.yaw = 0; c.pitch = 0; c.roll = 0; c.fov = 0.62;
      // the global music camera-swim zooms a flat 2D world far too hard —
      // keep just a hint of it here.
      // a flat 2D side-scroller: NO camera scene movement at all.
      const fx = eng.fx;
      const _dfov = fx.dfov, _dz = fx.dz, _dyaw = fx.dyaw,
        _dpitch = fx.dpitch, _droll = fx.droll, _dx = fx.dx, _dy = fx.dy;
      fx.dfov = 0; fx.dz = 0; fx.dyaw = 0; fx.dpitch = 0;
      fx.droll = 0; fx.dx = 0; fx.dy = 0;
      // INCREMENT 1 — dusk sky gradient + deeper multi-layer parallax.
      // ground/coins/hero are byte-identical to the working original;
      // every new layer uses ONLY line3 (no sprite art) so the prior
      // undefined-art crash class cannot recur.
      const lrp = (a, b, k) => [a[0] + (b[0] - a[0]) * k | 0,
        a[1] + (b[1] - a[1]) * k | 0, a[2] + (b[2] - a[2]) * k | 0];
      const camX = this.sx + 4;
      const LO = (this.level - 1) % 3;        // per-stage palette rotation
      const skyHz = lrp(acc(env, LO), [255, 225, 185], 0.42);
      const skyTop = lrp(scale(acc(env, 2 + LO), 0.16), [26, 16, 46], 0.55);
      // FILLED dusk gradient backdrop — every cell, behind all geometry
      // (deep moody top -> warm horizon). Shadow-of-the-Beast sky.
      for (let r = 0; r < rows; r++) {
        const k = r / (rows - 1);
        const col = lrp(skyTop, skyHz, k * k);
        const g = ' .,:'[Math.min(3, (k * 4) | 0)];
        for (let sx = 0; sx < cols; sx++) eng.plot(sx, r, g, col, 950);
      }
      // parallax layers (far -> near). 'ground' unchanged from original.
      const layers = [
        [24, scale(env.pal.fg, 0.18), 0.12, 'ridge'],
        [18, acc(env, 2 + LO), 0.25, 'mountains'],
        [11, scale(env.pal.fg, 0.30), 0.45, 'hills'],
        [3.5, env.pal.fg, 1, 'ground'],
        [2.0, scale(env.pal.fg, 0.12), 1.4, 'fore'],
      ];
      for (const [pz, colr, par, kind] of layers) {
        for (let i = -2; i < 40; i++) {
          const wx = Math.floor((this.sx * par) / 4) * 4 + i * 4;
          if (kind === 'ridge') {
            const hh = 5 + 3 * vnoise(wx * 0.12, 9);
            eng.line3([wx, 0, pz], [wx + 3, hh, pz], colr, '/');
            eng.line3([wx + 3, hh, pz], [wx + 6, 0, pz], colr, '\\');
          } else if (kind === 'mountains') {
            const hh = 3 + 2 * vnoise(wx * 0.2, 0);
            eng.line3([wx, 0, pz], [wx + 2, hh, pz], scale(colr, 0.4), '/');
            eng.line3([wx + 2, hh, pz], [wx + 4, 0, pz], scale(colr, 0.4), '\\');
          } else if (kind === 'hills') {
            const r = hash2(wx, 7);
            if (r < 0.5) {
              const hh = 1.6 + r * 2;
              eng.line3([wx, 0, pz], [wx + 1.5, hh, pz], scale(colr, 0.8), '/');
              eng.line3([wx + 1.5, hh, pz], [wx + 3, 0, pz], scale(colr, 0.8), '\\');
              eng.line3([wx, 0, pz], [wx + 3, 0, pz], scale(colr, 0.8), '_');
            } else if (r < 0.78) {
              eng.line3([wx + 1, 0, pz], [wx + 2.4, 0.9, pz], scale(colr, 0.7), '(');
              eng.line3([wx + 2.4, 0.9, pz], [wx + 3.8, 0, pz], scale(colr, 0.7), ')');
            }
          } else if (kind === 'ground') {
            const gap = this.gaps.some((g) => Math.abs(wx + 2 - g) < 2);
            if (!gap) {
              const gy = this.groundY(wx);                       // plateau height
              eng.line3([wx, gy, pz], [wx + 4, gy, pz], colr, '=');
              for (let yy = gy - 0.5; yy > -1.4; yy -= 0.6)
                eng.line3([wx, yy, pz], [wx + 4, yy, pz], scale(colr, 0.45), '#');
            }
          } else {
            if (hash2(wx, 21) < 0.4) {
              eng.line3([wx, -1, pz], [wx + 2, 1.4, pz], colr, '|');
              eng.line3([wx + 2, 1.4, pz], [wx + 4, -1, pz], colr, '|');
            }
          }
        }
      }
      eng.text2d(2, 1, 'STAGE 1-' + this.level,
        scale(env.pal.fg, 0.55 + this.flash * 0.45));
      for (const co of this.coins) {
        if (co.x < this.sx - 2 || co.x > this.sx + 30) continue;
        eng.sprite(co.x, this.groundY(co.x) + co.y + 0.5, 3.4, co.got ? ['*'] : ['o'],
          co.got ? acc(env, 2) : acc(env, 0), 0.7);
      }
      const fr = this.run | 0;
      const hero = [
        [' o ', '/|\\', '/ \\'], [' o ', '/|\\', '|  '],
        [' o ', '/|\\', ' \\ '], [' o ', '/|\\', '  |'],
      ][fr];
      eng.sprite(this.sx + 4, this.y + 1.2, 3.4, hero, acc(env, 0), 1.0);
      fx.dfov = _dfov; fx.dz = _dz;
      fx.dyaw = _dyaw; fx.dpitch = _dpitch; fx.droll = _droll;
      fx.dx = _dx; fx.dy = _dy;
      eng.farFog = _ff;
    },
  };

  // ===================================================== WIREFRAME (Battlezone)
  const Wire = {
    title: 'SECTOR-7',
    reset(eng) {
      this.z = 0; this.ang = 0; this.t = 0;
      this.obs = [];
      for (let i = 0; i < 14; i++) this.obs.push(this._mk(8 + i * 7));
      this.ships = [];
    },
    _mk(zz) {
      const k = ['pyr', 'cube', 'spike'][(Math.random() * 3) | 0];
      return { x: (Math.random() - 0.5) * 22, z: zz, k, s: 1 + Math.random() * 1.5 };
    },
    note() { this.ships.push({ x: (Math.random() - 0.5) * 16, y: 1 + Math.random() * 3, z: this.z + 30, life: 1 }); },
    beat() { this._hud = 1; },
    step(dt) {
      this.t += dt; this.z += dt * 7;
      this.ang = Math.sin(this.t * 0.25) * 0.35;
      this._hud = Math.max(0, (this._hud || 0) - dt * 2);
      for (const o of this.obs) if (o.z < this.z - 4) { o.z += 14 * 7; o.x = (Math.random() - 0.5) * 22; }
      this.ships = this.ships.filter((s) => (s.life -= dt * 0.3) > 0);
      for (const s of this.ships) s.z -= dt * 16;
    },
    draw(eng, env) {
      const c = eng.cam, cols = eng.cols, rows = eng.rows;
      c.x = 0; c.y = 1.6; c.z = this.z; c.yaw = -Math.PI / 2 - this.ang;
      c.pitch = -0.04; c.roll = -this.ang * 0.5; c.fov = 0.9;
      const gC = acc(env, 1), eC = acc(env, 0), hC = acc(env, 2);
      // receding ground grid
      for (let gx = -24; gx <= 24; gx += 3)
        eng.line3([gx, 0, this.z + 2], [gx, 0, this.z + 60], scale(gC, 0.6), '.');
      for (let gz = 0; gz < 60; gz += 3)
        eng.line3([-24, 0, this.z + 2 + gz], [24, 0, this.z + 2 + gz], scale(gC, 0.5), '-');
      // starfield
      for (let i = 0; i < 40; i++)
        eng.plot((hash2(i, 3) * cols) | 0, (hash2(i, 9) * rows * 0.4) | 0, '.', scale(env.pal.fg, 0.5), 950);
      // wireframe obstacles
      for (const o of this.obs) {
        const x = o.x, z = o.z, s = o.s;
        if (o.k === 'pyr') {
          const ap = [x, 2.4 * s, z];
          const b = [[x - s, 0, z - s], [x + s, 0, z - s], [x + s, 0, z + s], [x - s, 0, z + s]];
          for (let i = 0; i < 4; i++) {
            eng.line3(b[i], b[(i + 1) % 4], eC, '/');
            eng.line3(b[i], ap, eC, '\\');
          }
        } else if (o.k === 'cube') {
          const lo = [[x - s, 0, z - s], [x + s, 0, z - s], [x + s, 0, z + s], [x - s, 0, z + s]];
          const hi = lo.map((p) => [p[0], 2 * s, p[2]]);
          for (let i = 0; i < 4; i++) {
            eng.line3(lo[i], lo[(i + 1) % 4], eC, '#');
            eng.line3(hi[i], hi[(i + 1) % 4], eC, '#');
            eng.line3(lo[i], hi[i], eC, '|');
          }
        } else {
          eng.line3([x, 0, z], [x, 3 * s, z], eC, '|');
          eng.line3([x - s, 0, z], [x, 3 * s, z], eC, '/');
          eng.line3([x + s, 0, z], [x, 3 * s, z], eC, '\\');
        }
      }
      for (const sh of this.ships) {
        eng.line3([sh.x - 1, sh.y, sh.z], [sh.x + 1, sh.y, sh.z], scale(hC, sh.life + 0.3), '=');
        eng.line3([sh.x, sh.y + 0.6, sh.z], [sh.x, sh.y - 0.4, sh.z], scale(hC, sh.life + 0.3), 'I');
      }
      // HUD
      const fl = this._hud > 0.4;
      const hud = fl ? hC : scale(hC, 0.7);
      eng.text2d(2, rows - 2, 'SPD ' + (this.z | 0), hud);
      const mx = (cols / 2) | 0, my = (rows / 2) | 0;
      eng.glyph2d(mx, my, '+', hC);
      eng.glyph2d(mx - 3, my, '[', hud); eng.glyph2d(mx + 3, my, ']', hud);
      eng.text2d(cols - 10, 1, 'SECTOR', hud);
    },
  };

  // ===================================================== GLYPH FIELD (fallback)
  const Glyph = {
    title: 'FIELD',
    reset(eng) { this.f = []; this.imp = []; const n = (eng.cols * eng.rows * 0.05) | 0;
      for (let i = 0; i < n; i++) this.f.push({ c: (Math.random() * eng.cols) | 0, r: (Math.random() * eng.rows) | 0, a: Math.random() }); },
    note(n) { this.imp.push({ c: ((n.pitch || 60) % 80) + 4, r: 4 + ((n.ch * 5) % 30), life: 1 }); if (this.imp.length > 300) this.imp.shift(); },
    beat() {},
    step(dt) { for (const p of this.imp) p.life -= dt / 0.7; this.imp = this.imp.filter((p) => p.life > 0); },
    draw(eng, env) {
      const G = '.,:;|=+*ox%#'.split('');
      for (const c of this.f) {
        if (Math.random() < 0.04) c.a = Math.random();
        eng.plot(c.c, c.r, G[(c.a * G.length) | 0], scale(env.pal.fg, 0.3 + c.a * 0.4 + env.beat * 0.3), 100);
      }
      for (const p of this.imp)
        eng.plot(p.c, p.r, '@', scale(acc(env, 0), Math.min(1, p.life + env.beat * 0.3)), 50);
    },
  };

  window.Worlds = {
    classics: [Doom, Land, Side, Wire],
    Doom, Land, Side, Wire, Glyph,
  };
})();
