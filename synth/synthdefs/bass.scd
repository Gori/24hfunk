// bass — clean ROUND digital sub, EXPRESSIVE + GLIDING. Driven as a persistent
// MONO voice by the router: \freq is Lag'd so pitch portamentos between notes;
// \t_trig re-articulates the amp envelope per note; \gate sustains/releases.
// No doneAction free — the router owns the single node (/panic frees it).
// params: amp(vel), freq, cutoff, res, drive, sub, glide, fenv, decay, gate, t_trig, pan
SynthDef(\bass, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2, sub=0.85,
		glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.006, 1.0, 0.12), gate);          // sustain/release
	var aEnv = EnvGen.kr(Env.perc(0.004, decay, 1, -4), t_trig);     // per-note attack
	var fEnv = EnvGen.kr(Env.perc(0.005, decay * 0.7, 1, -3), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	var defAmt = ((freq - 40) / 130).clip(0.0, 1.0);
	var subOsc = SinOsc.ar(f) * sub;
	var click  = SinOsc.ar(f * 2) * 0.12 * EnvGen.kr(Env.perc(0.002, 0.05, 1, -6), t_trig);
	var upper  = LPF.ar(Pulse.ar(f, 0.42), (cutoff * 2).clip(200, 6000)) * defAmt * 0.45;
	var cf     = (cutoff * (0.55 + v * 0.9) * (1 + (fenv * 3 * fEnv))).clip(90, 5500);
	var sig    = subOsc + click + upper;
	sig = LPF.ar(sig, cf, 1);
	sig = (sig * (1 + (drive * 0.4 * defAmt * (0.6 + v * 0.6)))).softclip;
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.7 + 0.3) * gEnv * amp, pan));
}).add;
