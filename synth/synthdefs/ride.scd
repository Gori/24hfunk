// ride — REWRITE (option A): a real shimmering ride, not a cowbell. The old
// one was a tiny fixed-pitch Ringz bank (~520Hz, ±2%) -> the same metallic
// "tonk" every hit = cowbell. Now: a DENSE inharmonic metal cluster (10
// partials) at a lower base with WIDE per-hit detune so no two hits are the
// same pitch, a long noise SIZZLE wash with shimmer (the 'ssss' sustain), a
// soft stick attack, an HPF stack that removes the boxy cowbell fundamental,
// and a much lower output level so it sits BACK under the kit. `tone`
// morphs ping<->wash + ring length; `bell` (default 0) = a soft ride-bell.
// One-shot (doneAction:2). Same args/contract as before.
SynthDef(\ride, { |out=0, amp=0.5, decay=0.5, tone=0.4, bell=0.0, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var t     = tone.clip(0, 1);
	var be    = bell.clip(0, 1);
	var dr    = (decay * Rand(0.85, 1.18)).clip(0.12, 1.3);
	var fj    = Rand(0.94, 1.07);                 // WIDE per-hit detune (no fixed cowbell)
	var rat   = [1.0, 1.48, 1.93, 2.41, 2.98, 3.46, 4.07, 4.71, 5.32, 6.13];
	var metal = Mix(Pulse.ar((286 * fj) * rat,
	            LFNoise1.kr(0.7).range(0.42, 0.58))) * 0.045;
	var nz    = BPF.ar(WhiteNoise.ar, 7400 * fj, 0.5)
	            + (HPF.ar(WhiteNoise.ar, 5200) * 0.6);
	var shim  = SinOsc.kr(31, Rand(0, 6.283)).range(0.82, 1.0);
	var stick = HPF.ar(WhiteNoise.ar, 4600)
	            * EnvGen.kr(Env.perc(0.0004, 0.013, 1, -9)) * (0.30 + v * 0.30);
	var mEnv  = EnvGen.kr(Env.perc(0.002, dr * (0.45 + t * 0.8), 1, -3.2));
	var wEnv  = EnvGen.kr(Env.perc(0.004, dr * (0.9 + t * 1.5), 1, -2.3)) * shim;
	var bll   = (SinOsc.ar(560 * fj) + (SinOsc.ar(845 * fj) * 0.45))
	            * EnvGen.kr(Env.perc(0.001, dr * 1.3, 1, -2)) * 0.10 * be;
	var aEnv  = EnvGen.kr(Env.perc(0.0008, dr * 1.2, 1, -2.6), doneAction: 2);
	var sig   = stick
	            + (HPF.ar(metal, 3800) * mEnv * (0.45 + (0.30 * (1 - t))))
	            + (HPF.ar(nz, 5000) * wEnv * (0.40 + t * 0.70))
	            + bll;
	sig = HPF.ar(sig, 2600);                       // kill the boxy cowbell fundamental
	sig = (sig * 1.12).tanh;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp * 0.62 * Rand(0.93, 1.07), pan));
}).add;
