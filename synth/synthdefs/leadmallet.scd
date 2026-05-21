// leadMallet — an AFRICAN MALLET (balafon / marimba / kalimba) for the
// afro_rnb melodic lead. A struck tone: fundamental + a tuned bar overtone
// (~4th harmonic) + a faint inharmonic ping, hit by a woody "knock", with a
// faint gourd-resonator buzz (balafon character). PERCUSSIVE (rings out +
// self-frees), so melodic phrases overlap warmly on the mono lead channel.
SynthDef(\leadMallet, { |out=0, amp=0.5, freq=440, fmRatio=4.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=3200, decay=0.4, gate=1, t_trig=1, maxSustain=2.0, drive=1.0,
		glide=0.0, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var fHz  = freq.clip(120, 2400);
	// overtones decay faster than the fundamental (the wooden-bar timbre)
	var p2   = SinOsc.ar(fHz * 3.98) * 0.42 * EnvGen.kr(Env.perc(0.001, 0.28, 1, -6));
	var p3   = SinOsc.ar(fHz * 6.85) * 0.14 * EnvGen.kr(Env.perc(0.001, 0.10, 1, -8));
	// woody mallet "knock" transient
	var knock = BPF.ar(WhiteNoise.ar, (fHz * 2).clip(300, 4500), 0.5)
		* EnvGen.kr(Env.perc(0.0004, 0.03, 1, -6)) * 0.5;
	// faint gourd-resonator buzz (balafon)
	var buzz = SinOsc.ar(fHz * 2.0) * 0.07
		* EnvGen.kr(Env.perc(0.003, 0.45, 1, -5)) * LFNoise2.kr(45).range(0.4, 1.0);
	var amp_env = EnvGen.kr(Env.perc(0.0015, 0.85, 1, -4.0), doneAction: 2);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 4), 0.1]),
		1, doneAction: 2);
	var sig = SinOsc.ar(fHz) + p2 + p3 + buzz + knock;
	sig = LPF.ar(sig, (cutoff * (0.6 + (v * 0.5))).clip(800, 5200));
	sig = ((sig * 0.9).tanh);
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * amp_env * safety * amp * 1.7 * level);
}).add;
