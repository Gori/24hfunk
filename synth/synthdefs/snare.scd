// snare — crisp digital: tight tonal shell + controlled noise + sharp crack.
// Bandlimited noise (less harsh), short designed envelopes.
// params: amp, tone(shell<->noise), decay, snap(crack), crush, pan
// Velocity shapes it: hard hits crack harder + brighter noise, ghost notes
// stay dull (as real snares do). Per-hit shell detune + noise/decay/level
// drift kills the machine-gun sameness. v~1.0 == the old fixed sound.
SynthDef(\snare, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var dr    = decay * Rand(0.93, 1.07);
	var det   = Rand(-0.05, 0.05).midiratio;            // per-hit shell detune
	var sn    = snap * (0.4 + v * 0.6);                 // vel -> crack amount
	var aEnv  = EnvGen.kr(Env.perc(0.0008, dr, 1, -4.5), doneAction: 2);
	var shEnv = EnvGen.kr(Env.perc(0.0008, dr * 0.4, 1, -8));
	var nzEnv = EnvGen.kr(Env.perc(0.001, dr * 0.85, 1, -3.5));
	var crEnv = EnvGen.kr(Env.perc(0.0002, 0.009, 1, -10));
	var shell = (SinOsc.ar(180 * det) + (SinOsc.ar(274 * det) * 0.55)) * shEnv * (1 - tone) * 0.75;
	var noise = BPF.ar(WhiteNoise.ar, (2300 + (v * 1100)) * Rand(0.94, 1.06), 0.8) * nzEnv * tone * 1.2;
	var crack = HPF.ar(WhiteNoise.ar, 7000) * crEnv * sn * 0.9;
	var sig   = shell + noise + crack;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = sig.softclip;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.96, 1.04), pan));
}).add;
