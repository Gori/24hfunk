// keysFunk — warm but DEFINED analog synth comp for 70s funk (Bernie Worrell
// / Junie Morrison). 3 detuned saws (analog ensemble, NO muddy sub), a
// Moog-style cascaded RESONANT ladder filter with a per-note envelope "wow"
// (opens on attack then settles) + slow LFO breathing — that resonant, vocal
// analog character. Moderate sustain so chords ring without piling into mud.
// Same \keys param contract, self-frees.
SynthDef(\keysFunk, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.7, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var sl   = (sus * Rand(0.95, 1.08)).clip(0.3, 1.8);
	var det  = [-0.04, 0.0, 0.04];
	var osc  = Mix.fill(3, { |i|
		Saw.ar(freq * (det[i].midiratio) * (1 + (LFNoise2.kr(0.2 + (0.08 * i)) * 0.0014)));
	}) * 0.28;
	var env  = EnvGen.kr(Env([0, 1, 0.78, 0], [0.03, sl, 0.4], [2, 0, -3]),
		doneAction: 2);
	// analog "wow": filter opens on the attack, settles back
	var fenv = EnvGen.kr(Env([0.5, 1.0, 0.5], [0.04, sl * 0.8], [-2, -3]));
	var lfo  = SinOsc.kr(0.16, Rand(0, 6.28)).range(0.9, 1.1);
	var cf   = (cutoff * (0.5 + (v * 0.5) + (0.8 * fenv)) * lfo).clip(450, 6500);
	// Moog ladder: two cascaded RESONANT lowpass filters = analog voice
	var sig  = RLPF.ar(osc, cf, 0.22);
	sig = RLPF.ar(sig, cf * 1.05, 0.28);
	sig = ((sig * (1 + drive * 0.3)).tanh) * 0.72;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * amp * 1.15);
}).add;
