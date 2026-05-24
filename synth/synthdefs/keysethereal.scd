// keysEthereal — a lush, washed-out ETHEREAL pad for cloud rap. Detuned saw
// ensemble + an octave-up shimmer halo + band-limited "air" noise + a slow
// swell and slow LFO cutoff drift = the "floating in clouds" bed. Self-
// terminating (doneAction:2), rings LONG so notes smear into one another;
// the genre's huge reverb send (fxMel) does the rest. Same param contract as
// \keys / \keysPad (amp/freq/cutoff/sus/drive/vib/pan).
SynthDef(\keysEthereal, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v   = amp.clip(0.05, 1.0);
	var sl  = (sus * Rand(0.95, 1.15)).clip(0.5, 5.0) * 2.6;        // ethereal: rings long
	var env = EnvGen.kr(Env([0, 1, 0.85, 0], [0.5, sl, 1.4], [2, 0, -3]), doneAction: 2);
	var det = [-0.08, -0.03, 0.03, 0.08];                          // wide detuned ensemble
	var ens = Mix.fill(4, { |i|
		var d = det[i].midiratio;
		Saw.ar(freq * d * (1 + (LFNoise2.kr(0.1 + (0.04 * i)) * 0.003)));
	}) * 0.20;
	var shim = Mix.fill(2, { |i|                                   // octave-up shimmer halo
		SinOsc.ar(freq * 2 * [1.001, 0.999][i]);
	}) * 0.10;
	var air = LPF.ar(HPF.ar(WhiteNoise.ar, 4000), 9000) * 0.045;   // band-limited "air"
	var drift = SinOsc.kr(0.08, Rand(0, 6.283)).range(0.82, 1.0);  // slow cutoff drift
	var cf  = (cutoff * (0.5 + (v * 0.5)) * drift).clip(400, 5200);
	var sig = LPF.ar(ens + shim + air, cf);
	sig = ((sig * (1 + drive * 0.12)).tanh) * 0.6;
	Out.ar(out, Pan2.ar(sig * env * amp * 1.2, pan));
}).add;
