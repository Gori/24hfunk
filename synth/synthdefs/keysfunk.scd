// keysFunk — warm, MOVING analog synth comp for 70s funk (Bernie Worrell /
// Junie Morrison). 3 detuned saws (no muddy sub) through a Moog-style
// cascaded RESONANT ladder. Darker base cutoff + a deep, slightly fast filter
// LFO and a per-note envelope "wow" => an audible resonant sweep (the analog
// wah/movement). Short-ish sustain so the comp reads as RHYTHMIC chanks, not
// a sustained wash. Same \keys param contract, self-frees.
SynthDef(\keysFunk, { |out=0, amp=0.4, freq=220, cutoff=1400, sus=0.35, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var sl   = (sus * Rand(0.95, 1.08)).clip(0.18, 1.0);
	var det  = [-0.04, 0.0, 0.04];
	var osc  = Mix.fill(3, { |i|
		Saw.ar(freq * (det[i].midiratio) * (1 + (LFNoise2.kr(0.2 + (0.08 * i)) * 0.0014)));
	}) * 0.28;
	var env  = EnvGen.kr(Env([0, 1, 0.7, 0], [0.025, sl, 0.25], [2, 0, -3]),
		doneAction: 2);
	// analog "wow" + MOVEMENT: deep, slightly fast resonant sweep
	var fenv = EnvGen.kr(Env([0.4, 1.0, 0.45], [0.03, sl * 0.8], [-2, -3]));
	var lfo  = SinOsc.kr(0.25, Rand(0, 6.28)).range(0.6, 1.4);     // wide = audible movement
	var cf   = (cutoff * (0.45 + (v * 0.45) + (0.7 * fenv)) * lfo).clip(280, 3400);
	// Moog ladder: two cascaded RESONANT lowpass filters (the sweep "sings")
	var sig  = RLPF.ar(osc, cf, 0.18);
	sig = RLPF.ar(sig, cf * 1.05, 0.24);
	sig = ((sig * (1 + drive * 0.3)).tanh) * 0.72;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * amp * 1.18);
}).add;
