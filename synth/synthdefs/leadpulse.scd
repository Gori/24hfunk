// leadPulse — chiptune PWM square lead, digital + bright. Per-note gated
// contract (same args + safety env as \lead).
SynthDef(\leadPulse, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2,
		glide=0.03, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	// plucky: tight chip-pluck percussive env (no sustain) for crisp rhythm
	var env    = EnvGen.kr(Env.perc(0.002, (decay * 1.3).clip(0.05, 0.7), 1, -5), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(6.0) * 0.009 * EnvGen.kr(Env([0, 0, 1], [0.14, 0.5]));
	var port   = EnvGen.kr(Env([-1, 0], [glide.clip(0, 0.25) + 0.01], -4)) * 0.04;  // #8
	var drift  = LFNoise2.kr(0.17) * 0.0018;          // subtle analog detune
	var f      = freq * (1 + vib + port + drift);
	var pw     = SinOsc.kr(0.7 + wave * 4).range(0.15, 0.85);
	var sig    = Pulse.ar(f, pw) + (Pulse.ar(f * (1 + detune * 0.04), pw) * 0.5);
	// slightly softened: less octave-buzz harmonic, lower top, less drive
	sig = sig + (Pulse.ar(f * 2, 0.5) * fmIndex * 0.10);
	sig = LPF.ar(sig, (cutoff * (0.55 + v)).clip(500, 9500));
	// #6 gentle musical saturation instead of a hard clip
	sig = ((((sig * (1 + drive * 0.4)) + (sig * sig * 0.07)).tanh) * 0.92) * 0.6;
	// #1-lite: subtle Haas stereo widen
	sig = LPF.ar(sig, 4000);                               // global high-cut (lead taming)
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.0065),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.55 * level);
}).add;
