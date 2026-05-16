// Fires synthetic note-ons at the bridge: node scripts/smoke/send-test-note.js [count] [intervalMs]
const PORT = process.env.BRIDGE_HTTP_PORT || '8080';
const count = parseInt(process.argv[2] || '8', 10);
const interval = parseInt(process.argv[3] || '300', 10);

let i = 0;
const timer = setInterval(async () => {
  if (i >= count) { clearInterval(timer); return; }
  const ch = [0, 1, 9][i % 3];
  const pitch = ch === 9 ? [36, 38, 42][i % 3] : 48 + ((i * 5) % 24);
  try {
    const r = await fetch(`http://localhost:${PORT}/test/noteon`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ch, pitch, vel: 0.8 }),
    });
    console.log(i, await r.json());
  } catch (e) {
    console.error('request failed:', e.message);
  }
  i++;
}, interval);
