// main.js — WS client + RAF loop. Render is time-driven; missed packets never stall it.
(function () {
  const canvas = document.getElementById('c');
  const statusEl = document.getElementById('status');
  window.Renderer.init(canvas);

  let ws = null;
  let connected = false;
  let stats = { notes: 0, beats: 0, lastBeat: null, section: '—' };

  function setStatus() {
    document.body.classList.toggle('live', connected);
    statusEl.textContent =
      `${connected ? 'live' : 'offline'}  ·  section ${stats.section}  ·  ` +
      `notes ${stats.notes}  ·  beat ${stats.lastBeat ?? '—'}`;
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
          if (m.scroll) window.Renderer.setScroll(m.scroll);
          if (m.section) { window.Renderer.onSection(m.section); stats.section = m.section.id || 'set'; }
          break;
        case 'section':
          window.Renderer.onSection(m.section);
          stats.section = (m.section && m.section.id) || 'set';
          break;
        case 'scroll':
          window.Renderer.setScroll(m.text);
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

  setStatus();
  connect();
  requestAnimationFrame(loop);
})();
