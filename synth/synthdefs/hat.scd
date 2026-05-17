// hat (closed) — clean metallic digital tick. params: amp cutoff decay metal
// loose pan.  `loose` (0..1, 0.0=neutral) stretches the decay + softens the
// gate curve toward a half-open "loose" hat (per genre). Per-hit metal
// detune + decay/level drift; velocity opens the tone a touch.
// loose~0.0 + v~1.0 == the prior fixed sound.
SynthDef(\hat, { |out=0, amp=0.5, cutoff=9500, decay=0.04, metal=0.6, loose=0.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var lo   = loose.clip(0, 1);
	var dr   = decay * (1 + (lo * 3.0)) * Rand(0.88, 1.14);
	var fj   = Rand(0.97, 1.03);                          // per-hit metal detune
	var cj   = (cutoff * (0.78 + v * 0.22) * Rand(0.95, 1.05)).clip(3500, 14000);
	var aEnv = EnvGen.kr(Env.perc(0.0004, dr, 1, -10 + (lo * 6)), doneAction: 2);
	var rat  = [1.0, 1.34, 1.79, 2.27, 2.83, 3.41];
	var met  = Mix(Pulse.ar(360 * fj * rat, 0.5)) * 0.09;
	var nz   = WhiteNoise.ar * 0.5;
	var src  = (met * metal) + (nz * (1 - metal));
	var sig  = HPF.ar(HPF.ar(src, cj), cj);
	sig = sig.softclip;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.92, 1.08), pan));
}).add;
