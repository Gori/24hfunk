// snare909 — bright electronic 909-ish snare. One-shot. Same params as \snare.
SynthDef(\snare909, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0, pan=0|
	var aEnv  = EnvGen.kr(Env.perc(0.001, decay * 1.1, 1, -3), doneAction: 2);
	var tEnv  = EnvGen.kr(Env.perc(0.001, decay * 0.35, 1, -7));
	var two   = (SinOsc.ar(238) + SinOsc.ar(476) * 0.6) * tEnv * (1 - tone) * 0.7;
	var noise = HPF.ar(WhiteNoise.ar, 1800) * (0.4 + tone * 0.8);
	var snp   = HPF.ar(WhiteNoise.ar, 7000) * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -9)) * snap;
	var sig   = two + (noise * aEnv) + snp;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = (sig * 1.2).tanh;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
