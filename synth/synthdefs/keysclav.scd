// keysClav — a CLAVINET for funk comping (Bernie Worrell / Junie Morrison /
// Stevie "chank"). Bright narrow pulse + saw = the struck string; a fast
// percussive pluck envelope; a resonant filter that snaps open then closes
// (the metallic "twang" of a clav being plucked). Short + punchy so rhythmic
// chank chords stay tight. Same \keys param contract, self-frees.
SynthDef(\keysClav, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.3, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var det  = Rand(-0.015, 0.015).midiratio;
	var f    = freq * det;
	var sl   = (sus * Rand(0.9, 1.1)).clip(0.08, 0.5);
	var env  = EnvGen.kr(Env.perc(0.002, sl, 1, -4.5), doneAction: 2);
	// bright narrow pulse + saw = clavinet string
	var osc  = (Pulse.ar(f, 0.2) * 0.7) + (Saw.ar(f) * 0.3);
	// the pluck: filter snaps open then closes fast (struck-string twang)
	var fenv = EnvGen.kr(Env([1.0, 0.35], [sl * 0.7], -4));
	var cf   = (cutoff * (0.7 + v * 0.9) * fenv.max(0.2)).clip(500, 6500);
	var sig  = RLPF.ar(osc, cf, 0.3);                    // resonant, bright twang
	sig = ((sig * (1 + drive * 0.5)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig * env * amp * 1.4, pan));
}).add;
