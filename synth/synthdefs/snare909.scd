// snare909 — bright electronic 909-ish snare. One-shot. Same params as \snare
// (+body/buzz). Adds a band-limited rattle tail for body. Velocity shapes
// crack/noise; per-hit detune/decay/level drift. v~1.0 == prior sound.
SynthDef(\snare909, { |out=0, amp=0.62, tone=0.5, decay=0.16, snap=0.6, crush=0.0,
		body=0.5, buzz=0.35, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var dr    = decay * Rand(0.94, 1.06);
	var det   = Rand(-0.04, 0.04).midiratio;
	var sn    = snap * (0.4 + v * 0.6);
	var bw    = 0.7 + (body.clip(0, 1) * 0.6);
	var bz    = buzz.clip(0, 1);
	var aEnv  = EnvGen.kr(Env.perc(0.001, dr * 1.1, 1, -3), doneAction: 2);
	var tEnv  = EnvGen.kr(Env.perc(0.001, dr * 0.35, 1, -7));
	var bzEnv = EnvGen.kr(Env.perc(0.002, dr * (1.0 + bz * 1.3), 1, -3));
	var two   = (SinOsc.ar(238 * det) + SinOsc.ar(476 * det) * 0.6) * tEnv * (1 - tone) * 0.7 * bw;
	var noise = HPF.ar(WhiteNoise.ar, (1300 + (v * 500))) * (0.4 + tone * 0.8);
	var rat   = BPF.ar(WhiteNoise.ar, 4200 * Rand(0.93, 1.07), 1.3) * bzEnv * (0.16 + bz * 0.45);
	var snp   = HPF.ar(WhiteNoise.ar, 7000) * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -9)) * sn;
	var sig   = two + (noise * aEnv) + rat + snp;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = (sig * 1.2).tanh;
	sig = (sig * bits).round / bits;
	sig = LPF.ar(sig, 11000);             // dump the bit-crush alias hash
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.96, 1.04), pan));
}).add;
