// leadFM — bright digital 2-op FM/DX lead. Per-note gated contract (same args
// + safety env as \lead so genre SYNTH_PARAMS apply and no notes hang).
SynthDef(\leadFM, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2,
		glide=0.03, pan=0|
	var v      = amp.clip(0.05, 1.0);
	// plucky: percussive env so each FM note plucks and decays (tight rhythm)
	var env    = EnvGen.kr(Env.perc(0.002, (decay * 1.4).clip(0.06, 0.8), 1, -4.5), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(5.5) * 0.008 * EnvGen.kr(Env([0, 0, 1], [0.18, 0.6]));
	var port   = EnvGen.kr(Env([-1, 0], [glide.clip(0, 0.25) + 0.01], -4)) * 0.04;  // #8
	var f      = freq * (1 + vib + port);
	var iEnv   = EnvGen.kr(Env.perc(0.004, decay, 0.6, -3), gate);
	// slightly softened: a touch less FM index and brightness
	var mod    = SinOsc.ar(f * (fmRatio + 0.001)) * f * (fmIndex * 3.3 + wave * 5)
	             * (0.4 + v * 0.65) * iEnv;
	var sig    = SinOsc.ar(f + mod) + (SinOsc.ar(f * 2.01) * 0.17);
	sig = LPF.ar(sig, (cutoff * (0.5 + v)).clip(400, 10500));
	// #6 gentle musical saturation (warm even harmonics, not a hard clip)
	sig = (((sig * (1 + drive * 0.30)) + (sig * sig * 0.09)).tanh) * 0.92;
	// #1-lite: a subtle Haas widen for stereo body without changing timbre
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.0065),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.55);
}).add;
