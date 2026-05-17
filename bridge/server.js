// bridge/server.js — HTTP (static visualizer) + WS (/live) + OSC-in from SC.
require('dotenv').config();
const path = require('path');
const http = require('http');
const express = require('express');
const { WebSocketServer } = require('ws');
const { startOscIn } = require('./osc_in');
const stateMod = require('./state');

const HTTP_PORT = parseInt(process.env.BRIDGE_HTTP_PORT || '8080', 10);
const VIS_OSC_PORT = parseInt(process.env.VIS_OSC_PORT || '57130', 10);

const app = express();
app.use(express.json({ limit: '256kb' }));
// no-store: the visualizer is edited constantly while the 24/7 stream
// runs, so every browser reload MUST fetch the latest JS/CSS — never a
// cached copy (stale assets made every browser-only fix look broken).
app.use(express.static(path.join(__dirname, '..', 'visualizer'), {
  etag: false,
  lastModified: false,
  cacheControl: false,
  setHeaders: (res) => res.set('Cache-Control', 'no-store'),
}));

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/live' });

function broadcast(obj) {
  const data = JSON.stringify(obj);
  for (const client of wss.clients) {
    if (client.readyState === 1) client.send(data);
  }
}

wss.on('connection', (ws) => {
  ws.send(JSON.stringify(stateMod.snapshot()));
});

// director (or fake-section.py) pushes a SectionState here
app.post('/section', (req, res) => {
  const section = req.body;
  if (!section || typeof section !== 'object') {
    return res.status(400).json({ error: 'expected SectionState JSON body' });
  }
  stateMod.setSection(section);
  broadcast({ type: 'section', section });
  res.json({ ok: true });
});

// smoke test: synthesize a note-on without SC
app.post('/test/noteon', (req, res) => {
  const b = req.body || {};
  const note = {
    type: 'noteon',
    ch: b.ch | 0,
    pitch: (b.pitch ?? 60) | 0,
    vel: typeof b.vel === 'number' ? b.vel : 0.8,
    phase: typeof b.phase === 'number' ? b.phase : 0,
    t: Date.now(),
  };
  stateMod.pushNote(note);
  broadcast(note);
  res.json({ ok: true, note });
});

app.get('/healthz', (_req, res) => res.json({ ok: true }));
app.get('/state', (_req, res) => res.json(stateMod.snapshot()));

startOscIn(VIS_OSC_PORT, broadcast);

server.listen(HTTP_PORT, () => {
  console.log(`[bridge] http+ws on http://localhost:${HTTP_PORT}  (ws path /live)`);
});

// periodic heartbeat so the client can detect a dead bridge
setInterval(() => broadcast({ type: 'heartbeat', t: Date.now() }), 5000);
