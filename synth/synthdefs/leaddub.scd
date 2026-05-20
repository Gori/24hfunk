// leadDub — long evolving FM pad-lead. Slow attack, long release, LFO on
// cutoff + a soft chorus = motion. Sits behind the beat. Gated contract.
SynthDef(\leadDub, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=2200, decay=0.5, gate=1, maxSustain=4.5, drive=1.0,
		glide=0.07, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(60, 3000), glide.clip(0, 0.25));
	var env     = EnvGen.kr(Env.asr(0.55, 1.0, 1.6, -3), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 8), 0.2]),
		1, doneAction: 2);
	var lfo     = SinOsc.kr(0.18 + decay * 0.1).range(0.7, 1.3);
	var det     = SinOsc.kr(0.27).range(0.998, 1.002);             // slow drift
	var mod     = SinOsc.ar(fHz * fmRatio * det) * fmIndex * fHz * 0.35 * lfo;
	var car     = SinOsc.ar(fHz * det + mod);
	var sub     = SinOsc.ar(fHz * 0.5) * 0.35;
	var sig     = car + sub;
	sig = RLPF.ar(sig, (cutoff * lfo * (0.6 + v * 0.5)).clip(120, 5000), 0.45);
	sig = sig + (DelayC.ar(sig, 0.05,
		0.022 + SinOsc.kr(0.31).range(0, 0.006)) * 0.55);           // chorus
	sig = (sig * (1 + drive * 0.15)).tanh * 0.55;
	sig = LPF.ar(sig, 3200);
	// slow breathing on the output level (dubby, laid-back)
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.03, 0.012),
		pan.clip(-1, 1) * 0.35)
		* SinOsc.kr(0.13, Rand(0, 6.28)).range(0.78, 1.0)
		* env * safety * amp * 2.4 * level);
}).add;
