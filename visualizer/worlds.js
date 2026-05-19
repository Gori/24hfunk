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
  const Doom = {
    title: 'E1M1',
    reset(eng) {
      const N = (this.N = 21);
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
      this.px = 1.5; this.pz = 1.5; this.ang = 0; this.turn = 0; this.flash = 0;
      this.props = [];
      const art = {
        lamp: [' | ', '(O)', ' | '],
        barrel: [' __ ', '|##|', '|##|', '|__|'],
        imp: [' ^^ ', '/oo\\', ' \\/ ', ' /\\ '],
      };
      for (let i = 0; i < 72; i++) {
        const x = 1 + ((Math.random() * (N - 2)) | 0);
        const y = 1 + ((Math.random() * (N - 2)) | 0);
        if (this.m[y][x] === 0) {
          const k = ['lamp', 'imp', 'barrel', 'imp', 'imp'][(Math.random() * 5) | 0];
          this.props.push({ x: x + 0.5, z: y + 0.5, kind: k, art: art[k], ph: Math.random() * 6 });
        }
      }
      // roaming enemy imps that wander the corridors AND drift toward the
      // player, so they're actually seen up close (not lost in far cells)
      this.foes = [];
      for (let i = 0; i < 2; i++) {
        let fx = this.px + 1.5 + i * 1.2, fz = this.pz, a = 0.6 + i * 2;
        for (let ti = 0; ti < 16; ti++) {            // place into an OPEN cell
          const tx = this.px + Math.cos(a) * (1.5 + i), tz = this.pz + Math.sin(a) * (1.5 + i);
          if (!this.wall(tx, tz)) { fx = tx; fz = tz; break; }
          a += 1.3;
        }
        this.foes.push({
          x: fx, z: fz, ang: a,
          ph: Math.random() * 6, sp: 1.05 + Math.random() * 0.3, art: art.imp,
        });
      }
    },
    note() { this.flash = Math.min(1, this.flash + 0.5); },
    beat() {},
    wall(x, z) { return x < 0 || z < 0 || x >= this.N || z >= this.N || this.m[z | 0][x | 0] === 1; },
    _probe(a) {                       // free distance along heading a
      let d = 0;
      while (d < 6 && !this.wall(this.px + Math.cos(a) * d, this.pz + Math.sin(a) * d)) d += 0.35;
      return d;
    },
    _foeProbe(f, a) {                 // free distance ahead of a foe
      let d = 0;
      while (d < 4 && !this.wall(f.x + Math.cos(a) * d, f.z + Math.sin(a) * d)) d += 0.35;
      return d;
    },
    step(dt) {
      // simple, ALWAYS-progressing wander: walk forward; at a wall steer
      // toward the more open side; gentle drift; un-stick if cornered.
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
      // anti-stuck: if it can't make progress, spin to find an opening
      this._stuck = moved < 1e-4 ? (this._stuck || 0) + dt : 0;
      if (this._stuck > 0.8) { this.ang += 1.7; this._stuck = 0; }
      // roaming enemy imp: walk forward, steer at walls, gently home on the
      // player so it stays close/visible; respawn ahead if it drifts away.
      for (const f of this.foes) {
        // home toward the player + a little wander, THEN derive heading
        let da = Math.atan2(this.pz - f.z, this.px - f.x) - f.ang;
        while (da > Math.PI) da -= 6.283;
        while (da < -Math.PI) da += 6.283;
        f.ang += da * 0.6 * dt + (Math.random() - 0.5) * 0.7 * dt;
        let ffx = Math.cos(f.ang), ffz = Math.sin(f.ang);
        // wall ahead -> turn toward the more open side (don't clip through)
        if (this.wall(f.x + ffx * 0.6, f.z + ffz * 0.6)) {
          const lp = this._foeProbe(f, f.ang - 1.2), rp = this._foeProbe(f, f.ang + 1.2);
          f.ang += (lp > rp ? -1 : 1) * 2.4 * dt + 0.7;
          ffx = Math.cos(f.ang); ffz = Math.sin(f.ang);
        }
        // axis-separated move with a body margin so it can't nose into walls
        const fsp = f.sp * dt;
        let fm = 0;
        if (!this.wall(f.x + ffx * (0.34 + fsp), f.z)) { f.x += ffx * fsp; fm += Math.abs(ffx * fsp); }
        if (!this.wall(f.x, f.z + ffz * (0.34 + fsp))) { f.z += ffz * fsp; fm += Math.abs(ffz * fsp); }
        f._st = fm < 1e-4 ? (f._st || 0) + dt : 0;
        if (f._st > 0.6) { f.ang += 1.9; f._st = 0; }   // cornered -> spin out
        // respawn ahead of the player, but only into an OPEN cell
        if (Math.hypot(f.x - this.px, f.z - this.pz) > 9) {
          for (let ti = 0; ti < 10; ti++) {
            const a = this.ang + (Math.random() - 0.5) * 1.4;
            const r = 2 + Math.random() * 1.6;
            const rx = this.px + Math.cos(a) * r, rz = this.pz + Math.sin(a) * r;
            if (!this.wall(rx, rz)) { f.x = rx; f.z = rz; f.ang = a; f._st = 0; break; }
          }
        }
      }
      this.flash = Math.max(0, this.flash - dt * 2.2);
    },
    draw(eng, env) {
      const c = eng.cam;
      c.x = this.px; c.z = this.pz; c.y = 0.56; c.yaw = -this.ang;
      c.pitch = 0; c.fov = 0.66;
      const cols = eng.cols, rows = eng.rows;
      // steady horizon: gentle slow bob + a soft beat lift (no fast jitter)
      const horizon = (rows * 0.5 + Math.sin(env.t * 1.6) * 0.8
        + env.beat * 2.2) | 0;
      const wallC = acc(env, 1), sideC = env.pal.fg, floorC = acc(env, 0);
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
        const wc = eng.fog(side ? scale(sideC, 0.7) : wallC, dist);
        eng.vspan(sx, 0, top - 1, eng.ramp(0.04), scale(env.pal.fg, 0.18), 50);
        const gl = eng.ramp(Math.min(0.99, lit));
        eng.vspan(sx, top, bot, gl, [Math.min(255, wc[0] * (1 + lit * 0.4)) | 0,
          Math.min(255, wc[1] * (1 + lit * 0.4)) | 0, Math.min(255, wc[2] * (1 + lit * 0.4)) | 0], dist);
        for (let yy = bot + 1; yy < rows; yy += 1) {
          const fd = (rows * 0.5) / (yy - horizon || 1);
          eng.vspan(sx, yy, yy, ':', eng.fog(floorC, Math.abs(fd) + 1), Math.abs(fd) + 1);
        }
      }
      for (const p of this.props) {
        const bob = p.kind === 'imp' ? Math.sin(env.t * 4 + p.ph) * 0.12 : 0;
        const col = p.kind === 'lamp'
          ? scale(acc(env, 2), 0.7 + 0.3 * Math.sin(env.t * 7 + p.ph) + this.flash)
          : (p.kind === 'imp' ? acc(env, 0) : env.pal.fg);
        eng.sprite(p.x, 0.5 + bob, p.z, p.art, col, 0.9);
      }
      for (const f of this.foes)
        eng.sprite(f.x, 0.5 + Math.sin(env.t * 5 + f.ph) * 0.14, f.z, f.art,
          scale(acc(env, 0), 0.8 + this.flash + env.beat * 0.35), 1.2);
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
      this.sx = 0; this.run = 0; this.vy = 0; this.y = 0; this.t = 0;
      this.land = 0; this.stomp = 0;
      this.coins = [];
      for (let i = 0; i < 90; i++) this.coins.push({ x: 8 + i * 3.5 + Math.random() * 2, y: 1 + Math.random() * 2.5 });
      this.gaps = [];
      for (let i = 0; i < 60; i++) this.gaps.push(20 + i * 11 + ((Math.random() * 4) | 0));
    },
    note() { for (const co of this.coins) if (Math.abs(co.x - (this.sx + 4)) < 1.6) co.got = 0.45; },
    beat() {
      if (this.y <= 0.01) this.vy = 7.4;
      this._bp = 1;                                   // beat pulse (piranha/blocks)
    },
    overGap() { for (const g of this.gaps) if (Math.abs((this.sx + 4) - g) < 1.1) return true; return false; },
    step(dt) {
      this.t += dt; this.sx += dt * 5.5; this.run = (this.run + dt * 14) % 4;
      if (this.y <= 0.01 && this.overGap()) this.vy = 7.0;
      const wasAir = this.y > 0.05;
      this.vy -= 22 * dt; this.y += this.vy * dt;
      if (this.y < 0) { this.y = 0; this.vy = 0; if (wasAir) this.land = 1; }
      this.land = Math.max(0, this.land - dt * 5);
      this.stomp = Math.max(0, this.stomp - dt * 4);
      this._bp = Math.max(0, (this._bp || 0) - dt * 3);
      for (const co of this.coins) if (co.got !== undefined) co.got = Math.max(0, co.got - dt);
    },
    draw(eng, env) {
      const c = eng.cam;
      // flat 2D side-scroller — sane cam depth, no distance fog, and the
      // global music camera-swim is suppressed (it wrecks a flat world).
      const _ff = eng.farFog; eng.farFog = 1e6;
      const camX = this.sx + 4;
      c.x = camX; c.y = 3.4; c.z = -13;
      c.yaw = 0; c.pitch = 0; c.roll = 0; c.fov = 0.62;
      const fx = eng.fx;
      const _s = [fx.dfov, fx.dz, fx.dyaw, fx.dpitch, fx.droll, fx.dx, fx.dy];
      fx.dfov = fx.dz = fx.dyaw = fx.dpitch = fx.droll = fx.dx = fx.dy = 0;

      const fg = env.pal.fg, bs = 1 + env.beat * 0.22, bp = this._bp || 0;
      const lrp = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
      const A0 = acc(env, 0), A1 = acc(env, 1), A2 = acc(env, 2);
      const sil = scale(fg, 0.14), silF = scale(fg, 0.24), silM = scale(fg, 0.34);
      // content keyed by a layer's own parallax scroll so it tiles forever:
      // drawn near the camera (always visible), identity shifts at `par`.
      const key = (par, off, step) => Math.floor((camX * par + off) / step);

      // ── L1 sky: dusk gradient bands (warm horizon -> dark indigo top)
      const skyHz = lrp(A0, [255, 235, 200], 0.35), skyTop = scale(A2, 0.22);
      for (let b = 0; b < 13; b++) {
        const k = b / 12, yy = 1 + k * 15;
        eng.line3([camX - 90, yy, 62], [camX + 90, yy, 62],
          scale(lrp(skyHz, skyTop, k), 0.5 + bp * 0.15), ':');
      }
      // ── L2 sun/moon disc — big, slow, low on the horizon
      const sunX = camX - (camX * 0.96 % 200) + 60;
      eng.sprite(sunX, 7.5, 55, [
        '  #####  ', ' ####### ', '#########', '#########',
        '#########', ' ####### ', '  #####  '],
        scale(lrp(A0, [255, 220, 170], 0.5), bs), 1.0);
      // ── L3 far mountain range
      for (let i = -14; i <= 14; i++) {
        const dx = camX + i * 4, kk = key(0.12, i * 4, 4);
        const h = 2 + 4 * vnoise(kk * 0.5, 1);
        eng.line3([dx, 0, 42], [dx + 2, h, 42], silF, '/');
        eng.line3([dx + 2, h, 42], [dx + 4, 0, 42], silF, '\\');
        eng.line3([dx, 0, 42], [dx + 4, 0, 42], silF, '_');
      }
      // ── L4 mid silhouette — temples & forest
      for (let i = -10; i <= 10; i++) {
        const dx = camX + i * 6, kk = key(0.3, i * 6, 6), r = hash2(kk, 3);
        if (r < 0.42) {                                  // stepped temple
          const w = 2 + (hash2(kk, 4) * 3 | 0), h = 3 + (hash2(kk, 5) * 4 | 0);
          for (let yy = 0; yy < h; yy++)
            eng.line3([dx - (w - yy * w / h), yy, 26], [dx + (w - yy * w / h), yy, 26], silM, '#');
        } else if (r < 0.8) {                            // pine
          eng.sprite(dx, 2.6, 26, ['  ^  ', ' /#\\ ', '/###\\', '  |  '], silM, 1.0);
        }
      }
      // ── L5 Mario hills / bushes / clouds
      for (let i = -9; i <= 9; i++) {
        const dx = camX + i * 7, kk = key(0.55, i * 7, 7), r = hash2(kk, 6);
        if (r < 0.34) eng.sprite(dx, 0.9, 12, [' .__. ', '/ .. \\', '/_____\\'], lrp(A1, [70, 170, 90], 0.5), 1.0);
        else if (r < 0.6) eng.sprite(dx, 0.4, 12, ['(())', 'OOOO'], lrp(A1, [70, 170, 90], 0.55), 0.9);
        const ck = key(0.42, i * 7, 7);
        if (hash2(ck, 8) < 0.3) eng.sprite(dx + 2, 7 + hash2(ck, 9) * 3, 12,
          [' .--. ', '(    )', " '--' "], scale([235, 240, 255], 0.7 * bs), 0.85);
      }

      // ── L6 GAMEPLAY plane (z = 3.5, par = 1) ───────────────────────────
      const GZ = 3.5;
      for (let i = -8; i <= 18; i++) {
        const wx = Math.floor(camX) + i;
        const gap = this.gaps.some((g) => Math.abs(wx + 0.5 - g) < 1.2);
        if (!gap) {
          eng.line3([wx, 0, GZ], [wx + 1, 0, GZ], A1, '=');           // ground top
          eng.line3([wx, -0.6, GZ], [wx + 1, -0.6, GZ], scale(A1, 0.6), (wx & 1) ? '[' : ']');
        }
        const n = wx;                                                 // stable per-tile id
        // green pipes (some with a beat-popping piranha)
        if (!gap && hash2(n, 11) < 0.10) {
          const ph = 2 + (hash2(n, 12) * 3 | 0), grn = lrp(A1, [60, 180, 80], 0.6);
          for (let yy = 0; yy <= ph; yy += 0.5) {
            eng.line3([wx, yy, GZ], [wx, yy, GZ], grn, '|');
            eng.line3([wx + 1.6, yy, GZ], [wx + 1.6, yy, GZ], grn, '|');
          }
          eng.line3([wx - 0.3, ph + 0.5, GZ], [wx + 1.9, ph + 0.5, GZ], grn, '#');
          if (hash2(n, 13) < 0.5) {
            const py = ph + (bp > 0.4 ? 1.6 : -0.4);                  // snaps up on the beat
            eng.sprite(wx + 0.8, py, GZ, [' \\^/ ', ' )=( '], scale(A2, bs), 0.8);
          }
        }
        // floating ? / brick row
        if (!gap && hash2(n, 21) < 0.16) {
          const bw = 1 + (hash2(n, 22) * 3 | 0);
          for (let k = 0; k < bw; k++) {
            const q = (k === (bw >> 1));
            eng.sprite(wx + k, 4.2 + (bp > 0.4 ? 0.18 : 0), GZ, [q ? '[?]' : '[#]'],
              q ? scale(A2, bs) : scale(A1, 0.8), 0.85);
          }
        }
        // stair pyramid
        if (!gap && hash2(n, 31) < 0.05) {
          for (let s = 0; s < 4; s++)
            for (let yy = 0; yy <= s; yy++)
              eng.sprite(wx + s, 0.5 + yy, GZ, ['[#]'], scale(A1, 0.75), 0.8);
        }
        // goomba / koopa walking left toward the hero
        if (!gap && hash2(n, 41) < 0.10) {
          const walk = (wx - this.t * 1.4);
          if (walk > camX - 8 && walk < camX + 22) {
            const stomped = (Math.abs(walk - camX) < 1.1 && this.y > 0.5);
            if (stomped) this.stomp = 1;
            eng.sprite(walk, stomped ? 0.35 : 0.7, GZ,
              stomped ? ['_dead_'] : (hash2(n, 42) < 0.5
                ? [' .--. ', ' |oo| ', ' /__\\ ']
                : [' (oo) ', ' /||\\ ']),
              scale(lrp(A0, [180, 110, 70], 0.5), 0.9), 0.85);
          }
        }
        // flagpole landmark every ~150 units
        if (((wx % 150) + 150) % 150 === 0 && wx > 30) {
          for (let yy = 0; yy < 9; yy += 0.5) eng.line3([wx, yy, GZ], [wx, yy, GZ], scale(fg, 0.7), '|');
          eng.sprite(wx + 1, 8 - (this.t * 2 % 6), GZ, ['|>>', '|> '], scale(A2, bs), 0.9);
          eng.sprite(wx + 5, 2.2, GZ, ['/##\\', '|[]|', '|__|'], silM, 1.0);   // castle
        }
      }
      // coins — spinning, bright pop on note
      for (const co of this.coins) {
        if (co.x < camX - 10 || co.x > camX + 24) continue;
        const sp = ['O', '0', '|', '0'][(this.t * 8 + co.x) | 0 & 3];
        eng.sprite(co.x, co.y + 0.6 + (co.got ? 0.5 : 0), GZ,
          [co.got ? '+' : sp], co.got ? scale(A2, 1.3) : A2, co.got ? 0.95 : 0.75);
      }
      // hero — chunky, run cycle, squash on land, beat-jump, stomp flash
      const fr = this.run | 0;
      const air = this.y > 0.25;
      const body = air ? [' (o) ', '<[#]>', ' / \\ ']
        : this.land > 0.4 ? ['     ', '(o)  ', '[###]']
          : [[' (o) ', ' [#] ', ' /\\  '], [' (o) ', ' [#] ', ' || '],
          [' (o) ', ' [#] ', '  /\\ '], [' (o) ', ' [#] ', ' ||  ']][fr];
      eng.sprite(camX, this.y + 1.3, GZ, body,
        this.stomp > 0.3 ? scale(A2, 1.4) : A0, 1.05);

      // ── L7 FOREGROUND — slow giant trunks + a fast grass fringe
      for (let i = -3; i <= 3; i++) {
        const dx = camX + i * 11, kk = key(1.45, i * 11, 11);
        if (hash2(kk, 51) < 0.28)
          eng.sprite(dx, 3, 2.4, ['|||', '|||', '|||', '|||', '|||', '/|\\'], scale(sil, 1.0), 1.0);
      }
      for (let i = -10; i <= 10; i++) {
        const dx = camX + i * 2;
        eng.line3([dx, -0.2, 2.0], [dx + 0.6, 0.5, 2.0], scale(A1, 0.5), (i & 1) ? 'v' : 'w');
      }

      fx.dfov = _s[0]; fx.dz = _s[1]; fx.dyaw = _s[2];
      fx.dpitch = _s[3]; fx.droll = _s[4]; fx.dx = _s[5]; fx.dy = _s[6];
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
