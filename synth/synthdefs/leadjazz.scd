// leadJazz — a soft, intimate jazz lead: warm sine fundamental + a gentle
// fast-decaying FM "tine/bell" (Rhodes / vibraphone / muted-horn character),
// rounded slow attack, dark low-pass, subtle vibrato + Haas width. Designed
// QUIET (internal trim ~1.0 vs \lead's 2.55) and meant to sit well back in
// the mix. Per-note gated contract + safety env identical to \lead so the
// genre SYNTH_PARAMS / glide / level all apply and no note hangs.
SynthDef(\leadJazz, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2,
		glide=0.03, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	// soft, rounded, slightly legato envelope (no click, gentle release)
	var env    = EnvGen.kr(Env.perc(0.014, (decay * 2.2).clip(0.22, 1.7), 1, -3.2), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.3], \lin), doneAction: 2);
	var vib    = SinOsc.kr(4.5) * 0.005 * EnvGen.kr(Env([0, 0, 1], [0.24, 0.7]));
	var port   = EnvGen.kr(Env([-1, 0], [glide.clip(0, 0.25) + 0.01], -4)) * 0.03;
	var drift  = LFNoise2.kr(0.15) * 0.0016;          // subtle analog detune
	var f      = freq * (1 + vib + port + drift);
	// a brief bell/tine strike on attack, then a pure-ish warm tone
	var strike = EnvGen.kr(Env.perc(0.002, 0.45, 1, -4));
	var mod    = SinOsc.ar(f * 3.0) * f * (0.35 + fmIndex * 0.10) * strike;
	var tone   = SinOsc.ar(f + mod)
	             + (SinOsc.ar(f * 2.0) * 0.10)
	             + (SinOsc.ar(f * 0.5) * 0.10);
	var sig    = LPF.ar(tone, (cutoff * (0.42 + v * 0.42)).clip(650, 4800));
	sig = ((sig * 0.85).tanh) * 0.9;                       // round, never bites
	Out.ar(out, Balance2.ar(LeakDC.ar(sig),
		DelayC.ar(LeakDC.ar(sig), 0.02, 0.006),
		pan.clip(-1, 1) * 0.25) * env * safety * amp * 1.0 * level);
}).add;
