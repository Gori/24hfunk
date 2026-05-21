// keysFunk — warm ANALOG synth comp for 70s funk (Bernie Worrell / Junie
// Morrison). Fat detuned-saw ensemble + sub octave, SOFT attack and a long
// warm sustain/release so chords RING and connect (never stabby), through a
// gently resonant lowpass that breathes via a slow LFO (analog movement).
// Same \keys param contract, self-frees.
SynthDef(\keysFunk, { |out=0, amp=0.4, freq=220, cutoff=2200, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var sl   = (sus * Rand(0.95, 1.1)).clip(0.4, 2.6) * 1.5;       // rings, not a stab
	var det  = [-0.06, -0.02, 0.03, 0.06];
	// fat detuned-saw ensemble (the analog warmth) + a sub octave
	var ens  = Mix.fill(4, { |i|
		Saw.ar(freq * (det[i].midiratio) * (1 + (LFNoise2.kr(0.18 + (0.06 * i)) * 0.0016)));
	}) * 0.2;
	var sub  = Pulse.ar(freq * 0.5, 0.5) * 0.18;
	// SOFT attack, warm sustain, gentle release (doneAction frees)
	var env  = EnvGen.kr(Env([0, 1, 0.82, 0], [0.05, sl, 0.55], [2, 0, -3]),
		doneAction: 2);
	// gently resonant lowpass, slow analog breathing
	var lfo  = SinOsc.kr(0.14, Rand(0, 6.28)).range(0.82, 1.18);
	var cf   = (cutoff * (0.45 + v * 0.4) * lfo).clip(280, 3600);
	var sig  = RLPF.ar(ens + sub, cf, 0.3);
	sig = ((sig * (1 + drive * 0.25)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * amp * 1.2);
}).add;
