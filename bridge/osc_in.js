// Listens for /vis/* OSC from SuperCollider (UDP) and fans out to WS clients.
const osc = require('osc');
const { pushNote, setBeat } = require('./state');

function startOscIn(port, broadcast) {
  const udp = new osc.UDPPort({
    localAddress: '0.0.0.0',
    localPort: port,
    metadata: false,
  });

  udp.on('message', (msg) => {
    const a = msg.args || [];
    if (msg.address === '/vis/noteon') {
      // ch, pitch, vel, beatPhase
      const note = {
        type: 'noteon',
        ch: a[0] | 0,
        pitch: a[1] | 0,
        vel: +a[2] || 0,
        phase: +a[3] || 0,
        t: Date.now(),
      };
      pushNote(note);
      broadcast(note);
    } else if (msg.address === '/vis/beat') {
      // bar, beatInBar(0..15), bpm
      const beat = {
        type: 'beat',
        bar: a[0] | 0,
        beat: a[1] | 0,
        bpm: +a[2] || 0,
        t: Date.now(),
      };
      setBeat(beat);
      broadcast(beat);
    }
  });

  udp.on('error', (e) => console.error('[osc_in] error', e.message));
  udp.on('ready', () =>
    console.log(`[osc_in] listening for /vis/* on udp ${port}`)
  );
  udp.open();
  return udp;
}

module.exports = { startOscIn };
