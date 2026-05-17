// snareBrush — soft brushed snare: a band-passed pink-noise "swish" + a soft
// low shell + a light "pat", NO sharp crack. A drop-in \snare-role variant
// (identical arg signature incl. body/buzz) selected per genre via
// /synth/map for jazz / lofi / indie. `snap` here = swish accent (not a
// crack), `tone` = shell <-> swish. Per-hit detune / decay / level drift.
SynthDef(\snareBrush, { |out=0, amp=0.62, tone=0.5, decay=0.18, snap=0.6, crush=0.0,
		body=0.5, buzz=0.35, pan=0|
	var v     = amp.clip(0.05, 1.0);
	var dr    = decay * Rand(0.9, 1.12);
	var det   = Rand(-0.05, 0.05).midiratio;
	var bw    = 0.7 + (body.clip(0, 1) * 0.6);
	var bz    = buzz.clip(0, 1);
	var aEnv  = EnvGen.kr(Env.perc(0.004, dr * (1.1 + bz * 0.8), 1, -3), doneAction: 2);
	var shEnv = EnvGen.kr(Env.perc(0.003, dr * 0.45, 1, -5));
	var swEnv = EnvGen.kr(Env([0, 1, 0.4, 0], [0.012, dr * 0.4, dr * 0.7], [-2, -3, -3]));
	var patE  = EnvGen.kr(Env.perc(0.001, 0.03, 1, -7));
	var shell = (SinOsc.ar(176 * det) + (SinOsc.ar(262 * det) * 0.5)) * shEnv * (1 - tone) * 0.6 * bw;
	var swish = BPF.ar(PinkNoise.ar, (2400 + (v * 900)) * Rand(0.94, 1.06), 0.7)
	            * swEnv * (0.5 + tone * 0.7) * (0.5 + snap * 0.6);
	var pat   = BPF.ar(WhiteNoise.ar, 3600 * Rand(0.95, 1.05), 1.2) * patE * 0.3;
	var sig   = shell + swish + pat;
	var bits  = 2 ** (4 + ((1 - crush.clip(0, 1)) * 11));
	sig = sig.softclip;
	sig = (sig * bits).round / bits;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.95, 1.05), pan));
}).add;
