// snare — crisp digital: tight tonal shell + controlled noise + sharp crack,
// now with a 2nd detuned noise band + a soft band-limited wire-buzz tail for
// body & realism (no extra brightness). params: amp tone decay snap crush
// body buzz pan.  `body` (0..1, 0.5=neutral) = tonal-shell weight; `buzz`
// (0..1, ~0.35 default) = wire-rattle tail length/level. Velocity shapes
// crack + noise; per-hit detune/decay/level drift. v~1.0 == prior sound.
SynthDef(\snare, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0,
		body=0.5, buzz=0.35, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var dr    = decay * Rand(0.93, 1.07);
	var det   = Rand(-0.05, 0.05).midiratio;            // per-hit shell detune
	var sn    = snap * (0.4 + v * 0.6);                 // vel -> crack amount
	var bw    = 0.7 + (body.clip(0, 1) * 0.6);          // 0.5 -> 1.0
	var bz    = buzz.clip(0, 1);
	var aEnv  = EnvGen.kr(Env.perc(0.0008, dr, 1, -4.5), doneAction: 2);
	var shEnv = EnvGen.kr(Env.perc(0.0008, dr * 0.4, 1, -8));
	var nzEnv = EnvGen.kr(Env.perc(0.001, dr * 0.85, 1, -3.5));
	var bzEnv = EnvGen.kr(Env.perc(0.002, dr * (0.9 + bz * 1.3), 1, -3));
	var crEnv = EnvGen.kr(Env.perc(0.0002, 0.009, 1, -10));
	var shell = (SinOsc.ar(180 * det) + (SinOsc.ar(274 * det) * 0.55)) * shEnv * (1 - tone) * 0.75 * bw;
	var nz1   = BPF.ar(WhiteNoise.ar, (2300 + (v * 1100)) * Rand(0.94, 1.06), 0.8) * nzEnv * tone * 1.2;
	var nz2   = BPF.ar(WhiteNoise.ar, 5200 * Rand(0.93, 1.07), 1.4) * bzEnv * (0.18 + bz * 0.5);
	var crack = HPF.ar(WhiteNoise.ar, 7000) * crEnv * sn * 0.9;
	var sig   = shell + nz1 + nz2 + crack;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = sig.softclip;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.96, 1.04), pan));
}).add;
