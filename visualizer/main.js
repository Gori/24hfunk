// main.js — WS client + RAF loop. Render is time-driven; missed packets never stall it.
(function () {
  const canvas = document.getElementById('c');
  const statusEl = document.getElementById('status');
  window.Renderer.init(canvas);

  let ws = null;
  let connected = false;
  let stats = { notes: 0, beats: 0, lastBeat: null, section: '—' };

  const musicEl = document.getElementById('hud-music');

  let _fps = 0, _heap = 0, _ms = 0, _ls = '?', _wr = 0, _wc = 0, _gap = 0;
  function setStatus() {
    document.body.classList.toggle('live', connected);
    statusEl.textContent =
      `${connected ? 'live' : 'offline'}  ·  ${stats.section}  ·  ` +
      `notes ${stats.notes}  ·  beat ${stats.lastBeat ?? '—'}  ·  ` +
      `${_fps}fps  ·  ${_ms}ms/f  ·  g${_gap}ms  ·  ls:${_ls}  ·  ` +
      `ws${_wr}/s${_heap ? '  ·  ' + _heap + 'MB' : ''}`;
  }

  // Big "what music is playing" HUD line, from the live SectionState.
  function setNowPlaying(section) {
    if (!musicEl || !section) return;
    const up = (s) => String(s || '').replace(/_/g, ' ').trim().toUpperCase();
    const parts = [up(section.genre)];
    if (section.mood) parts.push(up(section.mood));
    if (section.bpm) parts.push(`${section.bpm | 0} BPM`);
    if (section.key) parts.push(up(section.key));
    musicEl.textContent = parts.filter(Boolean).join('  ·  ');
  }

  function connect() {
    ws = new WebSocket(`ws://${location.host}/live`);
    ws.onopen = () => { connected = true; setStatus(); };
    ws.onclose = () => { connected = false; setStatus(); setTimeout(connect, 1000); };
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
    ws.onmessage = (ev) => {
      let m;
      try { m = JSON.parse(ev.data); } catch (e) { return; }
      switch (m.type) {
        case 'snapshot':
          if (m.section) {
            window.Renderer.onSection(m.section, true); // restore instantly, no fade
            setNowPlaying(m.section);
            stats.section = m.section.id || 'set';
          }
          break;
        case 'section':
          window.Renderer.onSection(m.section);
          setNowPlaying(m.section);
          stats.section = (m.section && m.section.id) || 'set';
          break;
        case 'noteon':
          window.Renderer.onNoteOn(m);
          stats.notes++;
          break;
        case 'beat':
          window.Renderer.onBeat(m);
          stats.beats++;
          stats.lastBeat = `${m.bar}:${m.beat}`;
          break;
        case 'heartbeat':
          break;
      }
      _wc++;            // WS msg counter (status now updates 1x/s in loop,
                        // not per message — no per-message DOM reflow)
    };
  }

  let last = performance.now();
  let _fc = 0, _ft = last, _wmax = 0, _gmax = 0;
  function loop(now) {
    const gap = now - last;             // rAF interval (paint-bound if big)
    let dt = gap / 1000;
    last = now;
    if (dt > 0.1) dt = 0.1; // clamp after tab-hide
    const t0 = performance.now();
    window.Renderer.frame(dt);
    const w = performance.now() - t0;   // actual JS frame work (was unmeasured)
    if (w > _wmax) _wmax = w;
    if (gap > _gmax) _gmax = gap;
    _fc++;
    if (now - _ft >= 1000) {
      const span = now - _ft;
      _fps = Math.round((_fc * 1000) / span);
      _ms = Math.round(_wmax);
      _gap = Math.round(_gmax);
      _wr = Math.round((_wc * 1000) / span);
      _wmax = 0; _gmax = 0; _wc = 0; _fc = 0; _ft = now;
      if (performance.memory) _heap = (performance.memory.usedJSHeapSize / 1048576) | 0;
      const d = window.Renderer.diag && window.Renderer.diag();
      _ls = d ? (d.ls ? 'Y' : 'N') : '?';
      setStatus();
    }
    requestAnimationFrame(loop);
  }

  // When the tab is hidden/throttled rAF stalls; without this the lost time
  // is clamped away every stall and the visual clock falls further behind
  // real time (motion looks progressively slow until a refresh). Re-zero the
  // dt baseline on resume so there is no accumulated backlog.
  function resync() { last = performance.now(); }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) resync(); });
  window.addEventListener('pageshow', resync);
  window.addEventListener('focus', resync);

  setStatus();
  connect();
  requestAnimationFrame(loop);
})();
