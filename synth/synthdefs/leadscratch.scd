// leadScratch — synthesized turntablist scratch (no samples). A vocal-ish
// formant tone whose pitch is swept rapidly back-and-forth per note (the
// record pushed/pulled under the needle), a tight percussive amplitude
// chop (the crossfader cut), and a short noise transient on the attack
// (the "ch" of the cut). Each note = ONE scratch gesture; runs
// voice-stealing (NOT in ~monoDef) so every note is a fresh swoop with a
// new random depth/direction. Gated contract.
SynthDef(\leadScratch, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.16, gate=1, t_trig=1, maxSustain=1.0,
		drive=1.0, glide=0.02, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	// scratch motion: bipolar pitch swoop. Random depth + random direction
	// per note (Rand fixes once per synth = once per note in voice-stealing)
	// -> forward-cut vs back-cut variation, like a hand working the platter.
	var sign   = (Rand(0.0, 1.0) - 0.5).sign;
	var depth  = Rand(0.5, 1.2) * sign;
	var scr    = EnvGen.kr(
		Env([0, 1, -0.7, 0.5, 0], [0.035, 0.05, 0.045, 0.05], \sin), gate) * depth;
	var fHz    = (freq * (2 ** scr)).clip(60, 5000);
	// vocal-ish source: saw + pulse through three formant bandpasses ("aah")
	var src    = Saw.ar(fHz) + (Pulse.ar(fHz, 0.4) * 0.5);
	var vow    = (BPF.ar(src, 800,  0.35) * 4.0)
		+ (BPF.ar(src, 1760, 0.45) * 3.0)
		+ (BPF.ar(src, 2680, 0.50) * 1.6);
	// attack transient: short noise "ch" of the cut
	var chh    = HPF.ar(WhiteNoise.ar, 3000)
		* EnvGen.kr(Env.perc(0.001, 0.02, 1, -6)) * 0.5;
	// amp env: tight percussive chop, self-frees after the gesture
	var env    = EnvGen.kr(Env.perc(0.004, decay, 1, -3), gate, doneAction: 2);
	var sig    = (vow * 0.22) + chh;
	sig = (sig * (1 + drive * 0.5)).tanh * 0.7;
	sig = LPF.ar(sig, 3600);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.005),
		pan.clip(-1, 1) * 0.4) * env * amp * 2.2 * level);
}).add;
