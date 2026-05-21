// leadSoftBell — a VERY SOFT, mid-frequency FM bell for the rnb arpeggio.
// Gentle FM index + a fast-decaying modulator = a soft mallet/bell tone; a
// PERCUSSIVE amp envelope that rings out and frees itself (doneAction), so
// arpeggiated notes overlap into a soft shimmer even though the lead channel
// is mono (the perc env ignores the voice-steal gate). A low-ish lowpass
// keeps it MID (no bright/piercing top). Gated contract.
SynthDef(\leadSoftBell, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=2600, decay=0.4, gate=1, t_trig=1, maxSustain=3.0, drive=1.0,
		glide=0.02, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var fHz  = freq.clip(120, 2200);
	// gentle FM bell: modest index, modulator decays fast -> soft mallet/bell
	var ienv = EnvGen.kr(Env.perc(0.002, 0.9, 1, -4));
	var mod  = SinOsc.ar(fHz * fmRatio) * fmIndex * 0.5 * fHz * ienv;
	var car  = SinOsc.ar(fHz + mod) + (SinOsc.ar(fHz * 3.01) * 0.08 * ienv);  // faint shimmer
	// PERCUSSIVE amp env: rings out + frees itself so the arp overlaps softly
	var env  = EnvGen.kr(Env.perc(0.005, 1.4, 1, -4.5), doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.1]),
		1, doneAction: 2);
	var sig  = car;
	sig = LPF.ar(sig, (1500 + (v * 1300)).clip(700, 3400));   // MID, soft (no bright top)
	sig = ((sig * 0.85).tanh);
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * safety * amp * 1.5 * level);
}).add;
