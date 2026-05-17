// keys — warm DIGITAL poly / FM e-piano for comp + pad, now analog-flavoured.
// Velocity opens the filter + FM "tine". Self-terminating (doneAction:2).
//  #2 per-note tuning/level/cutoff/env TOLERANCE + slow drift (no two
//     notes identical, like a real poly)  #3 Moog-ladder filter
//  #4 pre-drive into the ladder + a gentle asymmetric stage.
//  (keeps the +35% chord level — the other lever is canned.py velocities)
// params: amp(vel), freq, cutoff, sus(seconds), drive, vib, pan
SynthDef(\keys, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var det   = Rand(-0.045, 0.045).midiratio;                      // per-note tuning tolerance
	var drift = LFNoise2.kr(0.2) * 0.0018;                           // slow analog drift
	var env   = EnvGen.kr(Env([0, 1, 0.55, 0],
		[0.008 * Rand(0.8, 1.25), 0.14, (sus * Rand(0.92, 1.08)).clip(0.15, 3.0)],
		[2, -2, -4]), doneAction: 2);
	var vibe  = SinOsc.kr(5.4, Rand(0, 6.283)) * vib * 0.012
		* EnvGen.kr(Env([0, 0, 1], [0.18, 0.5]));
	var f     = freq * det * (1 + vibe + drift);
	var tine  = SinOsc.ar(f * 5) * (0.12 + v * 0.30)
		* EnvGen.kr(Env.perc(0.001, 0.10, 1, -6));
	var body  = SinOsc.ar(f + (tine * f * 0.35))
		+ (SinOsc.ar(f * 1.003) * 0.5)
		+ (SinOsc.ar(f * 2) * 0.14);
	var cf    = (cutoff * (0.40 + v * 0.55) * Rand(0.93, 1.07)).clip(280, 4200);
	var pre   = (body + (tine * 0.18)) * (1 + drive * 0.35);
	var sig   = MoogFF.ar(pre, cf, 0.7);                             // analog ladder
	sig = ((sig + (sig * sig * 0.04)).tanh) * 0.98 * Rand(0.96, 1.05);
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}).add;
