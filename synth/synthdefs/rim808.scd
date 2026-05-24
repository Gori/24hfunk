// rim808 — a TR-808 RIMSHOT: the bright pitched "tick" that defines the
// Triggerman / New Orleans bounce backbeat (not a fat snare). Two short
// bridged-T-style tones (~1.7 kHz + ~460 Hz) struck together + a bright noise
// click, very fast decay. The MIDI note pitch is IGNORED — the 808 rim is a
// FIXED pitched tick. One-shot (doneAction:2). amp = note velocity.
SynthDef(\rim808, { |out=0, amp=0.5, freq=1700, decay=0.03, pan=0|
	var env  = EnvGen.kr(Env.perc(0.0003, decay.clip(0.018, 0.06), 1, -9), doneAction: 2);
	var t1   = SinOsc.ar(1667);                       // the bright "tick"
	var t2   = SinOsc.ar(457);                         // body
	var tone = (t1 * 0.5) + (t2 * 0.55);
	var clk  = HPF.ar(WhiteNoise.ar, 3500)
		* EnvGen.kr(Env.perc(0.0001, 0.004, 1, -9)) * 0.6;
	var sig  = (tone + clk) * env;
	sig = (sig * 1.6).tanh;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * amp * 1.5);
}).add;
