// leadBell — 2-op FM bell with a high shimmer partial. Sparkly, garage-y;
// the high-index FM gives the bell its inharmonic character. Gated contract.
SynthDef(\leadBell, { |out=0, amp=0.5, freq=440, fmRatio=3.5, fmIndex=2.0, detune=0.12,
		wave=0.5, cutoff=4500, decay=0.4, gate=1, maxSustain=3.0, drive=1.0,
		glide=0.03, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 4000), glide.clip(0, 0.15));
	var env     = EnvGen.kr(Env.asr(0.003, 1.0, 0.9, -4), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.1]),
		1, doneAction: 2);
	var ienv    = EnvGen.kr(Env.perc(0.001, 0.6, 1, -4), gate);
	var mod     = SinOsc.ar(fHz * fmRatio) * fmIndex * fHz * ienv;
	var car     = SinOsc.ar(fHz + mod)
		+ (SinOsc.ar(fHz * 4.01) * 0.10 * ienv);                   // shimmer
	var sig     = car;
	sig = RLPF.ar(sig, (cutoff * (0.7 + v * 0.6)).clip(800, 9000), 0.4);
	sig = (sig * (1 + drive * 0.15)).tanh * 0.9;
	sig = LPF.ar(sig, 4000);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.008),
		pan.clip(-1, 1) * 0.4) * env * safety * amp * 2.2 * level);
}).add;
