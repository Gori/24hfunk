// leadHyper — fat 5-voice detuned supersaw lead. Bright, neon, 80s/synthwave
// energy; the 4000 Hz global LPF keeps it from being shrill. Gated contract.
SynthDef(\leadHyper, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=3200, decay=0.25, gate=1, t_trig=1, maxSustain=2.5,
		drive=1.0, glide=0.04, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	// ARTICULATION: vibrato w/ evolving rate + per-note attack pitch-bend
	var vib_rate = 5.2 + LFNoise2.kr(0.3).range(-0.6, 0.6);
	var vib_dep  = LFNoise2.kr(0.2).range(0.0025, 0.0065);
	var vib      = SinOsc.kr(vib_rate, Rand(0, 6.28)) * vib_dep;
	var bend     = EnvGen.kr(Env([0.975, 1.0], [0.06], -2), t_trig);
	var fHz      = Lag.kr(freq.clip(80, 3500), glide.clip(0, 0.15))
		* (1 + vib) * bend;
	var env     = EnvGen.kr(Env.asr(0.012, 1.0, 0.45, -3), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.08]),
		1, doneAction: 2);
	// slow per-voice drift adds life vs a static stack (analogue feel)
	var det     = [-0.18, -0.09, 0, 0.09, 0.18] * (detune + 0.02);
	var drift   = LFNoise2.kr(0.3 ! 5) * 0.004;
	var saws    = Mix(Saw.ar(fHz * (1 + det + drift))) * 0.18;
	// Filter env now retriggers via t_trig so each note gets a fresh "wow"
	// even on the persistent-mono path (was firing only once)
	var fenv    = EnvGen.kr(Env([0.4, 1, 0.7], [0.02, decay * 1.4], [-3, -2]),
		t_trig);
	// Slow filter LFO on top of the env — breathing tone
	var cf_lfo  = LFNoise2.kr(0.5).range(0.88, 1.12);
	var cf      = (cutoff * (0.5 + v * 0.9) * fenv * cf_lfo).clip(300, 9000);
	var sig     = RLPF.ar(saws, cf, 0.45);
	sig = (sig * (1 + drive * 0.25)).tanh * 0.9;
	sig = LPF.ar(sig, 3200);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.0075),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.4 * level);
}).add;
