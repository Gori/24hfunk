// leadMarimba — a WOODY struck MARIMBA for tropical house (NOT a bell). The
// fundamental dominates; a single tuned 4·f0 bar overtone gives the marimba
// colour but decays VERY fast (woody, not ringing); a present wooden mallet
// "knock" transient sells the struck-bar attack. NO high inharmonic shimmer
// (that read as a bell) and a WARM rolled-off lowpass (no glassy top). Short
// percussive decay — a marimba note is short. Self-frees so the riff overlaps
// on the mono lead. Gated contract (same lead params).
SynthDef(\leadMarimba, { |out=0, amp=0.5, freq=440, fmRatio=4.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=3600, decay=0.4, gate=1, t_trig=1, maxSustain=2.0, drive=1.0,
		glide=0.0, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var fHz  = freq.clip(120, 2600);
	// the tuned 4·f0 bar overtone — woody colour, decays FAST (no bell ring)
	var p2env = EnvGen.kr(Env.perc(0.001, 0.09, 1, -7));
	var p2   = SinOsc.ar(fHz * 4.0) * 0.40 * p2env;
	// wooden mallet "knock" transient (struck bar)
	var knock = BPF.ar(WhiteNoise.ar, (fHz * 2).clip(400, 3500), 0.7)
		* EnvGen.kr(Env.perc(0.0005, 0.025, 1, -6)) * 0.6;
	// short warm decay — a marimba note is short, not a sustained bell
	var amp_env = EnvGen.kr(Env.perc(0.002, (0.35 + (decay * 0.5)), 1, -4.5),
		doneAction: 2);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 4), 0.1]),
		1, doneAction: 2);
	var sig = SinOsc.ar(fHz) + p2 + knock;
	sig = LPF.ar(sig, (cutoff * (0.5 + (v * 0.4))).clip(900, 4800));   // WARM, no glassy top
	sig = ((sig * 0.95).tanh);
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * amp_env * safety * amp * 1.9 * level);
}).add;
