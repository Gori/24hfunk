// snare — crisp digital: tight tonal shell + controlled noise + sharp crack.
// Bandlimited noise (less harsh), short designed envelopes.
// params: amp, tone(shell<->noise), decay, snap(crack), crush, pan
SynthDef(\snare, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0, pan=0|
	var aEnv  = EnvGen.kr(Env.perc(0.0008, decay, 1, -4.5), doneAction: 2);
	var shEnv = EnvGen.kr(Env.perc(0.0008, decay * 0.4, 1, -8));
	var nzEnv = EnvGen.kr(Env.perc(0.001, decay * 0.85, 1, -3.5));
	var crEnv = EnvGen.kr(Env.perc(0.0002, 0.009, 1, -10));
	var shell = (SinOsc.ar(180) + (SinOsc.ar(274) * 0.55)) * shEnv * (1 - tone) * 0.75;
	var noise = BPF.ar(WhiteNoise.ar, 3400, 0.8) * nzEnv * tone * 1.2;
	var crack = HPF.ar(WhiteNoise.ar, 7000) * crEnv * snap * 0.9;
	var sig   = shell + noise + crack;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = sig.softclip;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
