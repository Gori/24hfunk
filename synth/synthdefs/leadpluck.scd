// leadPluck — short, articulate Karplus-Strong-style plucked lead. Gated
// contract identical to the other leads. Each note re-plucks the string
// (excitation envelope on the gate transition); the natural decay is the
// pluck physics, not the env release.
SynthDef(\leadPluck, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.25, gate=1, maxSustain=2.2, drive=1.0,
		glide=0.03, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 3200), glide.clip(0, 0.15));
	var env     = EnvGen.kr(Env.asr(0.001, 1.0, 0.30, -4), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.05]),
		1, doneAction: 2);
	var trig    = T2A.ar(EnvGen.kr(Env.perc(0.0003, 0.001), gate));
	var excite  = WhiteNoise.ar(1) * 0.6;
	var pluck   = Pluck.ar(excite, trig, 0.05, fHz.reciprocal,
		0.7 + decay * 1.6, (0.3 + v * 0.2));
	// subtle living wobble on the body's sub — analogue pitch quiver
	var body    = pluck + (SinOsc.ar(fHz * (1 + LFNoise2.kr(2.5).range(-0.0018, 0.0018))) * 0.18);
	var sig     = RLPF.ar(body, (cutoff * (0.7 + v * 0.6)).clip(500, 8000), 0.35);
	sig = (sig * (1 + drive * 0.2)).tanh * 1.25;
	sig = LPF.ar(sig, 3200);                                       // global high-cut
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.0065),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.2 * level);
}).add;
