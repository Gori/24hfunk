// keysFunk — warm analog synth comp for 70s funk (Bernie Worrell / Junie
// Morrison). A lush detuned-saw ENSEMBLE (4 voices beating against each other
// = the analog warmth + gentle movement, no muddy sub) through a SMOOTH
// non-resonant lowpass with only a slow, shallow drift. No resonant per-note
// sweep (that croaked). Short-ish sustain so the comp grooves rhythmically.
// Same \keys param contract, self-frees.
SynthDef(\keysFunk, { |out=0, amp=0.4, freq=220, cutoff=1950, sus=0.4, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	// note length tracks VELOCITY: loud comp hits (the held 'one') ring long,
	// quiet chanks are short -> a comp with VARYING lengths, never a hard stab
	// (soft attack + 0.3s floor). The funk comp drives this via per-note vel.
	var sl   = (sus * (0.5 + (v * 2.5)) * Rand(0.96, 1.06)).clip(0.3, 1.6);
	var det  = [-0.03, 0.0, 0.03];
	// detuned-saw ensemble — tighter detune = clearer (less beating thickness)
	var osc  = Mix.fill(3, { |i|
		Saw.ar(freq * (det[i].midiratio) * (1 + (LFNoise2.kr(0.18 + (0.07 * i)) * 0.0015)));
	}) * 0.24;
	var env  = EnvGen.kr(Env([0, 1, 0.72, 0], [0.02, sl, 0.24], [2, 0, -3]),
		doneAction: 2);
	// EVOLVING tone: the filter opens gradually as the chord rings (a slow
	// smooth swell) over a gentle slow LFO drift. Non-resonant -> no croak.
	var swell = EnvGen.kr(Env([0.55, 1.0], [sl * 0.85], -2));
	var lfo  = SinOsc.kr(0.16, Rand(0, 6.28)).range(0.8, 1.2);
	var cf   = (cutoff * (0.5 + (v * 0.45)) * swell * lfo).clip(450, 4800);
	var sig  = LPF.ar(osc, cf);                          // smooth, non-resonant
	sig = HPF.ar(sig, 280);                              // roll off low-end mud (clarity)
	sig = ((sig * (1 + drive * 0.2)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * amp * 1.2);
}).add;
