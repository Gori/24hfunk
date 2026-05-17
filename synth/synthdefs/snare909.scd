// snare909 — bright electronic 909-ish snare. One-shot. Same params as \snare.
// Velocity shapes crack + noise brightness; per-hit detune/decay/level drift
// for a less robotic backbeat. v~1.0 == the old fixed sound.
SynthDef(\snare909, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var dr    = decay * Rand(0.94, 1.06);
	var det   = Rand(-0.04, 0.04).midiratio;
	var sn    = snap * (0.4 + v * 0.6);
	var aEnv  = EnvGen.kr(Env.perc(0.001, dr * 1.1, 1, -3), doneAction: 2);
	var tEnv  = EnvGen.kr(Env.perc(0.001, dr * 0.35, 1, -7));
	var two   = (SinOsc.ar(238 * det) + SinOsc.ar(476 * det) * 0.6) * tEnv * (1 - tone) * 0.7;
	var noise = HPF.ar(WhiteNoise.ar, (1300 + (v * 500))) * (0.4 + tone * 0.8);
	var snp   = HPF.ar(WhiteNoise.ar, 7000) * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -9)) * sn;
	var sig   = two + (noise * aEnv) + snp;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = (sig * 1.2).tanh;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.96, 1.04), pan));
}).add;
