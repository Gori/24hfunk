// leadJazz — BRIGHT VIBRAPHONE mallet: a struck metal bar — fast bright
// mallet attack + a hard click, near-harmonic bar partials (1 : ~3.98 :
// ~9.6, uppers decay faster), long ringing decay, and the signature
// motor TREMOLO (amplitude). Per-note gated contract + safety env
// identical to \lead so the genre SYNTH_PARAMS / glide / level apply.
SynthDef(\leadJazz, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2,
		glide=0.03, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var dr     = (decay * 2.6).clip(0.4, 2.6);              // long bar ring
	var env    = EnvGen.kr(Env.perc(0.001, dr, 1, -4.5), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.3], \lin), doneAction: 2);
	var port   = EnvGen.kr(Env([-1, 0], [glide.clip(0, 0.25) + 0.01], -4)) * 0.03;
	var drift  = LFNoise2.kr(0.15) * 0.0014;               // subtle analog detune
	var f      = freq * (1 + port + drift);
	// vibraphone bar modes — uppers decay faster, brighter with velocity
	var p1     = SinOsc.ar(f)        * EnvGen.kr(Env.perc(0.001, dr,        1, -4));
	var p2     = SinOsc.ar(f * 3.98) * EnvGen.kr(Env.perc(0.001, dr * 0.45, 1, -6)) * (0.30 + v * 0.24);
	var p3     = SinOsc.ar(f * 9.6)  * EnvGen.kr(Env.perc(0.001, dr * 0.16, 1, -8)) * (0.10 + v * 0.18);
	// hard bright mallet click (hardness scales with velocity)
	var click  = HPF.ar(WhiteNoise.ar, 4200)
	             * EnvGen.kr(Env.perc(0.0003, 0.011, 1, -9)) * (0.16 + v * 0.40);
	var tone   = ((p1 + p2 + p3) * 0.5) + click;
	var sig    = LPF.ar(tone, (cutoff * (0.7 + v * 0.7)).clip(1200, 9500));
	sig = (sig * 1.15).tanh;                                // gentle metal body
	// the motor tremolo (classic vibraphone), gentle fade-in
	sig = sig * SinOsc.kr(5.2, 1.5).range(0.74 + (0.26 * EnvGen.kr(Env([1, 0], [0.5]))), 1.0);
	sig = LPF.ar(sig, 4000);                               // global high-cut (lead taming)
	Out.ar(out, Balance2.ar(LeakDC.ar(sig),
		DelayC.ar(LeakDC.ar(sig), 0.02, 0.006),
		pan.clip(-1, 1) * 0.25) * env * safety * amp * 1.25 * level);
}).add;
