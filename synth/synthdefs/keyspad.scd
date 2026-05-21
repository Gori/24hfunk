// keysPad — a mellow synth PAD for the chord comp (eighties_hiphop). Soft
// slow attack, warm detuned saw ensemble + sub, gentle lowpass, slow analog
// drift for movement. Sustains for `sus`, then releases. Self-terminating.
// Same param contract as \keys (amp/freq/cutoff/sus/drive/vib/pan).
SynthDef(\keysPad, { |out=0, amp=0.4, freq=220, cutoff=2200, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var sl   = (sus * Rand(0.92, 1.1)).clip(0.3, 4.0) * 1.6;     // pads ring longer
	var env  = EnvGen.kr(Env([0, 1, 0.82, 0], [0.16, sl, 0.55], [2, 0, -3]),
		doneAction: 2);
	var det  = [-0.07, -0.025, 0.025, 0.07];                    // detuned ensemble
	var ens  = Mix.fill(4, { |i|
		var d = det[i].midiratio;
		Saw.ar(freq * d * (1 + (LFNoise2.kr(0.13 + (0.05 * i)) * 0.0022)));
	}) * 0.24;
	var sub  = SinOsc.ar(freq * 0.5) * 0.28;
	var vibe = SinOsc.kr(4.8, Rand(0, 6.283)) * vib * 0.008
		* EnvGen.kr(Env([0, 0, 1], [0.3, 0.7]));
	var cf   = (cutoff * (0.5 + v * 0.45)).clip(300, 4200);
	var sig  = LPF.ar((ens + sub) * (1 + vibe), cf);
	sig = ((sig * (1 + drive * 0.15)).tanh) * 0.62;
	Out.ar(out, Pan2.ar(sig * env * amp * 1.25, pan));
}).add;
