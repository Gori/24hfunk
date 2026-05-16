// a3d.js — shared ASCII 3D engine. One char/colour/depth framebuffer that all
// worlds render into: perspective projection, depth-tested plotting, 3D line
// raster, depth-scaled ASCII sprite blit, distance fog, and a colour-run
// batched flush() (one fillText per same-colour run = fast at ~9k cells).
(function () {
  const RAMP = ' .,:;!=+*oxX%#&@█'.split('').map((c) => c.charCodeAt(0));
  const SPACE = 32;

  function A3D(canvas) {
    this.cv = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.W = this.H = 0;
    this.cols = 0; this.rows = 0; this.cw = 9; this.chh = 18; this.fontPx = 14;
    this.ch = null; this.col = null; this.z = null;
    this.bg = [0, 0, 0];
    this.cam = { x: 0, y: 0, z: 0, yaw: 0, pitch: 0, roll: 0, fov: 1.0 };
    // cinematic overlay added at projection time (manager drives this)
    this.fx = { dx: 0, dy: 0, dz: 0, dyaw: 0, dpitch: 0, droll: 0, dfov: 0 };
    this.farFog = 26;
    this.resize();
  }
  A3D.prototype.resize = function () {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.W = Math.floor(window.innerWidth);
    this.H = Math.floor(window.innerHeight);
    this.cv.width = this.W * dpr; this.cv.height = this.H * dpr;
    this.cv.style.width = this.W + 'px'; this.cv.style.height = this.H + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.cols = 168;
    this.cw = this.W / this.cols;
    this.fontPx = Math.round(this.cw * 1.85);
    this.chh = Math.round(this.fontPx * 1.0);
    this.rows = Math.max(8, Math.floor(this.H / this.chh));
    const n = this.cols * this.rows;
    this.ch = new Uint16Array(n);
    this.col = new Int32Array(n);
    this.z = new Float32Array(n);
    this.ctx.font = `${this.fontPx}px "JetBrains Mono","SF Mono",Menlo,Monaco,monospace`;
    this.ctx.textBaseline = 'top';
    this.ctx.textAlign = 'left';
  };
  const pack = (c) => ((c[0] & 255) << 16) | ((c[1] & 255) << 8) | (c[2] & 255);

  A3D.prototype.clear = function (bg) {
    this.bg = bg || [0, 0, 0];
    this.ch.fill(SPACE);
    this.z.fill(1e9);
  };
  A3D.prototype.fog = function (rgb, depth) {
    let k = 1 - depth / this.farFog;
    if (k < 0.06) k = 0.06; if (k > 1) k = 1;
    return [(rgb[0] * k) | 0, (rgb[1] * k) | 0, (rgb[2] * k) | 0];
  };
  // shade ramp glyph by brightness 0..1
  A3D.prototype.ramp = function (b) {
    let i = (b * (RAMP.length - 1)) | 0;
    if (i < 0) i = 0; if (i >= RAMP.length) i = RAMP.length - 1;
    return RAMP[i];
  };
  A3D.prototype.plot = function (cx, cy, glyph, rgb, depth) {
    cx |= 0; cy |= 0;
    if (cx < 0 || cy < 0 || cx >= this.cols || cy >= this.rows) return;
    const i = cy * this.cols + cx;
    if (depth >= this.z[i]) return;
    this.z[i] = depth;
    this.ch[i] = typeof glyph === 'number' ? glyph : glyph.charCodeAt(0);
    this.col[i] = pack(rgb);
  };
  A3D.prototype.vspan = function (cx, y0, y1, glyph, rgb, depth) {
    if (cx < 0 || cx >= this.cols) return;
    if (y0 < 0) y0 = 0; if (y1 >= this.rows) y1 = this.rows - 1;
    const gc = typeof glyph === 'number' ? glyph : glyph.charCodeAt(0);
    const pc = pack(rgb);
    for (let cy = y0 | 0; cy <= y1; cy++) {
      const i = cy * this.cols + cx;
      if (depth < this.z[i]) { this.z[i] = depth; this.ch[i] = gc; this.col[i] = pc; }
    }
  };
  // fast horizontal run — one tight loop, no per-cell call overhead
  A3D.prototype.hspan = function (cy, x0, x1, glyph, rgb, depth) {
    if (cy < 0 || cy >= this.rows) return;
    if (x0 < 0) x0 = 0; if (x1 >= this.cols) x1 = this.cols - 1;
    const gc = typeof glyph === 'number' ? glyph : glyph.charCodeAt(0);
    const pc = pack(rgb), base = (cy | 0) * this.cols, z = this.z, ch = this.ch, col = this.col;
    for (let x = x0 | 0; x <= x1; x++) {
      const i = base + x;
      if (depth < z[i]) { z[i] = depth; ch[i] = gc; col[i] = pc; }
    }
  };
  // world -> screen cell. returns {x,y,z,vis}
  A3D.prototype.project = function (wx, wy, wz) {
    const c = this.cam, X = this.fx;
    const yaw = c.yaw + X.dyaw, pitch = c.pitch + X.dpitch;
    const roll = c.roll + X.droll, fovv = c.fov + X.dfov;
    let dx = wx - (c.x + X.dx), dy = wy - (c.y + X.dy), dz = wz - (c.z + X.dz);
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    let rx = dx * cy - dz * sy;
    let rz = dx * sy + dz * cy;
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    let ry = dy * cp - rz * sp;
    rz = dy * sp + rz * cp;
    if (rz < 0.05) return { vis: false };
    const cr = Math.cos(roll), sr = Math.sin(roll);
    const fx = rx * cr - ry * sr;
    const fy = rx * sr + ry * cr;
    const f = (this.cols * 0.5) / (fovv * rz);
    return {
      x: this.cols * 0.5 + fx * f,
      y: this.rows * 0.5 - fy * f,
      z: rz, vis: true,
    };
  };
  A3D.prototype.line3 = function (a, b, rgb, glyph) {
    const p = this.project(a[0], a[1], a[2]);
    const q = this.project(b[0], b[1], b[2]);
    if (!p.vis || !q.vis) return;
    let x0 = p.x | 0, y0 = p.y | 0, x1 = q.x | 0, y1 = q.y | 0;
    const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx - dy, steps = 0, mx = dx + dy + 1;
    const gc = (glyph || '#').charCodeAt(0);
    while (steps++ < mx) {
      const t = mx > 1 ? steps / mx : 0;
      const dep = p.z + (q.z - p.z) * t;
      const i = y0 * this.cols + x0;
      if (x0 >= 0 && y0 >= 0 && x0 < this.cols && y0 < this.rows && dep < this.z[i]) {
        const fc = this.fog(rgb, dep);
        this.z[i] = dep; this.ch[i] = gc; this.col[i] = pack(fc);
      }
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 > -dy) { err -= dy; x0 += sx; }
      if (e2 < dx) { err += dx; y0 += sy; }
    }
  };
  // ascii sprite at world pos; art = array of strings, rgb base colour.
  A3D.prototype.sprite = function (wx, wy, wz, art, rgb, scaleMul) {
    const p = this.project(wx, wy, wz);
    if (!p.vis) return;
    const aw = art.reduce((m, s) => Math.max(m, s.length), 0);
    const ah = art.length;
    const sc = ((this.rows / p.z) * (scaleMul || 1)) / ah;
    if (sc < 0.05) return;
    const dw = Math.max(1, (aw * sc) | 0), dh = Math.max(1, (ah * sc) | 0);
    const ox = (p.x - dw / 2) | 0, oy = (p.y - dh / 2) | 0;
    const fc = this.fog(rgb, p.z);
    const pc = pack(fc);
    for (let yy = 0; yy < dh; yy++) {
      const srcR = art[(yy / sc) | 0] || '';
      for (let xx = 0; xx < dw; xx++) {
        const chr = srcR[(xx / sc) | 0];
        if (!chr || chr === ' ') continue;
        const cx = ox + xx, cy = oy + yy;
        if (cx < 0 || cy < 0 || cx >= this.cols || cy >= this.rows) continue;
        const i = cy * this.cols + cx;
        if (p.z < this.z[i]) {
          this.z[i] = p.z; this.ch[i] = chr.charCodeAt(0); this.col[i] = pc;
        }
      }
    }
  };
  // 2D screen-space glyph (HUD/text), always on top
  A3D.prototype.glyph2d = function (cx, cy, chr, rgb) {
    cx |= 0; cy |= 0;
    if (cx < 0 || cy < 0 || cx >= this.cols || cy >= this.rows) return;
    const i = cy * this.cols + cx;
    this.z[i] = -1; this.ch[i] = chr.charCodeAt(0); this.col[i] = pack(rgb);
  };
  A3D.prototype.text2d = function (cx, cy, str, rgb) {
    for (let k = 0; k < str.length; k++) this.glyph2d(cx + k, cy, str[k], rgb);
  };

  A3D.prototype.flush = function () {
    // tight hot loop: hoisted locals, a persistent packed-int -> css cache,
    // skip redundant fillStyle writes, no O(n^2) run concatenation.
    const ctx = this.ctx, ch = this.ch, col = this.col;
    const rows = this.rows, cols = this.cols, cw = this.cw, chh = this.chh;
    const css = this._css || (this._css = new Map());
    const scratch = this._scr && this._scr.length >= cols
      ? this._scr : (this._scr = new Array(cols));
    ctx.fillStyle = `rgb(${this.bg[0]},${this.bg[1]},${this.bg[2]})`;
    ctx.fillRect(0, 0, this.W, this.H);
    let lastStyle = -1;
    for (let r = 0; r < rows; r++) {
      const base = r * cols, ry = r * chh;
      let c = 0;
      while (c < cols) {
        const code = ch[base + c];
        if (code === SPACE) { c++; continue; }
        const color = col[base + c];
        scratch[0] = code;
        let len = 1, c2 = c + 1;
        while (c2 < cols) {
          const cc = ch[base + c2];
          if (cc === SPACE || col[base + c2] !== color) break;
          scratch[len++] = cc; c2++;
        }
        if (color !== lastStyle) {
          let s = css.get(color);
          if (s === undefined) {
            s = 'rgb(' + ((color >> 16) & 255) + ',' + ((color >> 8) & 255)
              + ',' + (color & 255) + ')';
            css.set(color, s);
          }
          ctx.fillStyle = s;
          lastStyle = color;
        }
        ctx.fillText(
          String.fromCharCode.apply(null, len === scratch.length
            ? scratch : scratch.slice(0, len)),
          c * cw, ry);
        c = c2;
      }
    }
  };

  window.A3D = A3D;
})();
