// leadGlitch — short, crunchy, adventurous: pulse + slight FM, bit-reduced
// and S&H-decimated for a digital-grit texture. Core SC UGens only (Latch
// + Impulse as the downsampler — no sc3-plugins). Gated contract.
SynthDef(\leadGlitch, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.14, gate=1, maxSustain=1.8, drive=1.0,
		glide=0.02, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 4500), glide.clip(0, 0.1));
	var env     = EnvGen.kr(Env.asr(0.002, 1.0, 0.12, -5), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 4), 0.04]),
		1, doneAction: 2);
	var pw      = 0.5 + LFNoise1.kr(8).range(-0.25, 0.25);
	var sig     = Pulse.ar(fHz, pw) + (SinOsc.ar(fHz * 2.01) * 0.18);
	// crunch: bit-reduction
	sig = (sig * 6).round(1) / 6;
	// crunch: S&H downsample (sample-rate decimation, audible grit)
	sig = Latch.ar(sig, Impulse.ar(6000 + LFNoise1.kr(4).range(-2500, 2500)));
	sig = RLPF.ar(sig, (cutoff * (0.6 + v)).clip(400, 8000), 0.4);
	sig = (sig * (1 + drive * 0.3)).tanh * 0.7;
	sig = LPF.ar(sig, 3600);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.006),
		pan.clip(-1, 1) * 0.35) * env * safety * amp * 2.0 * level);
}).add;
