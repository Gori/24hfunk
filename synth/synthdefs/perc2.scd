// perc2 — the dedicated percussion layer. One flexible one-shot voice that
// morphs across archetypes via `tone` (glitch ~0.0 / shaker ~0.45 / organic
// ~1.0) AND randomises itself on EVERY hit (each note is a fresh Synth, so
// the Rand/IRand UGens differ per note) — pitch, bend, decay, timbre, plus
// an occasional metallic bell/clave/agogo colour and stereo placement. No
// two hits are identical, while the genre's `tone` keeps its character.
// params: amp(vel) freq(organic pitch) decay drive tone crush noise pan
SynthDef(\perc2, { |out=0, amp=0.5, freq=220, decay=0.18, drive=1.0,
		tone=0.5, crush=0.35, noise=0.5, pan=0|
	var t    = tone.clip(0, 1);
	var jD   = Rand(0.78, 1.30);                     // per-hit decay jitter
	var dec  = (decay * (0.5 + t) * jD).clip(0.02, 0.95);
	var env  = EnvGen.kr(Env.perc(0.001, dec, 1, -4.5), doneAction: 2);
	var pEnv = EnvGen.kr(Env.perc(0.001, dec * Rand(0.35, 0.60), 1, -6));
	var f0   = freq.clip(50, 1200) * Rand(-2.0, 2.0).midiratio;  // pitch jitter
	// organic membrane: pitched body, randomised pitch-bend + skin slap
	var bf   = f0 * (1 + (pEnv * Rand(0.8, 2.0)));
	var body = (SinOsc.ar(bf) * 0.8) + (LFTri.ar(bf * 1.5) * 0.2)
	           + (HPF.ar(WhiteNoise.ar, 1800)
	              * EnvGen.kr(Env.perc(0.0005, 0.02)) * 0.5);
	// metallic / tonal colour (bell · clave · agogo) — inharmonic Ringz bank,
	// ratios randomised per hit
	var exc  = HPF.ar(WhiteNoise.ar, 2000) * EnvGen.kr(Env.perc(0.0003, 0.012));
	var metal= (Ringz.ar(exc, (f0 * Select.kr(IRand(0, 3), [3, 5, 7, 11]))
	                .clip(40, 14000), dec * 0.7) * 0.5
	            + Ringz.ar(exc, (f0 * Rand(1.4, 3.0) * 4).clip(40, 16000),
	                dec * 0.45) * 0.32)
	           * EnvGen.kr(Env.perc(0.001, dec * 0.8, 1, -5));
	// shaker: soft dark "shh", band + swell randomised per hit
	var shk  = BPF.ar(WhiteNoise.ar, 3000 * Rand(0.8, 1.3), 1.0)
	           * EnvGen.kr(Env([0, 1, 0.45, 0],
	             [0.02 * Rand(0.7, 1.4), dec * 0.5, dec * 0.6])) * 1.25;
	// glitch: decimated noise, decimation rate randomised per hit
	var gRate= ((1400 + (9000 * (1 - crush.clip(0, 1)))) * Rand(0.6, 1.7))
	           .clip(600, 14000);
	var gl   = Latch.ar(HPF.ar(WhiteNoise.ar, 3000 * Rand(0.7, 1.4)),
	             Impulse.ar(gRate))
	           * EnvGen.kr(Env.perc(0.0003, dec * 0.4, 1, -8)) * 1.5;
	// tone picks the base archetype; a per-hit metallic dusting adds colour
	var wG   = (1 - (t * 2.4)).clip(0, 1);
	var wS   = (1 - ((t - 0.45) * 3.4).abs).clip(0, 1);
	var wB   = ((t - 0.5) * 2.2).clip(0, 1);
	var wM   = (Rand(0, 1) < (0.16 + (t * 0.40))) * Rand(0.22, 0.60);
	var sig  = (gl * wG) + (shk * wS) + (body * wB) + (metal * wM);
	sig = (sig * (1 + drive * 0.5)).tanh;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * env * amp * 0.7,
		(pan + Rand(-0.3, 0.3)).clip(-1, 1)));
}).add;
