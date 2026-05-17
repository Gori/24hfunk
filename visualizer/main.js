// main.js — WS client + RAF loop. Render is time-driven; missed packets never stall it.
(function () {
  const canvas = document.getElementById('c');
  const statusEl = document.getElementById('status');
  window.Renderer.init(canvas);

  let ws = null;
  let connected = false;
  let stats = { notes: 0, beats: 0, lastBeat: null, section: '—' };

  const musicEl = document.getElementById('hud-music');

  function setStatus() {
    document.body.classList.toggle('live', connected);
    statusEl.textContent =
      `${connected ? 'live' : 'offline'}  ·  section ${stats.section}  ·  ` +
      `notes ${stats.notes}  ·  beat ${stats.lastBeat ?? '—'}`;
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
      setStatus();
    };
  }

  let last = performance.now();
  function loop(now) {
    let dt = (now - last) / 1000;
    last = now;
    if (dt > 0.1) dt = 0.1; // clamp after tab-hide
    window.Renderer.frame(dt);
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
