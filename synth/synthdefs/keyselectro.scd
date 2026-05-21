// keysElectro — a SOFT digital-synth voice for the electro arpeggio. Clean
// digital tone (triangle + sine sub + a faint saw edge), gentle attack (not a
// hard stab), rounded lowpass, very light drive. Plucky short notes so a fast
// arp stays articulate. Electro-only; self-frees. Same \keys param contract.
SynthDef(\keysElectro, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.25, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var det  = Rand(-0.02, 0.02).midiratio;
	var f    = freq * det;
	var sl   = (sus * Rand(0.95, 1.06)).clip(0.08, 0.6);
	// clean DIGITAL tone, but soft: triangle lead + sine sub + faint saw
	var osc  = (LFTri.ar(f) * 0.62)
		+ (SinOsc.ar(f * 0.5) * 0.26)
		+ (Saw.ar(f * 1.001) * 0.12);
	// soft pluck: gentle attack, short decay (articulate arp notes)
	var env  = EnvGen.kr(Env.perc(0.012, sl, 1, -3.2), doneAction: 2);
	var cf   = (cutoff * (0.4 + v * 0.4) * Rand(0.97, 1.04)).clip(500, 4200);
	var sig  = LPF.ar(osc, cf);
	sig = ((sig * (1 + drive * 0.1)).tanh) * 0.6;        // very light drive, soft
	Out.ar(out, Pan2.ar(sig * env * amp * 1.0, pan));    // gentle output
}).add;
