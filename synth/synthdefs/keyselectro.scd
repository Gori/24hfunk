// keysElectro — hard, bright electro stab for the chord comp (electro genre).
// PWM + detuned-square stack with a sub octave, snappy percussive envelope,
// resonant lowpass that opens with velocity. Kraftwerk / Cybotron stab.
// Same param contract as \keys (amp/freq/cutoff/sus/drive/vib/pan), self-frees.
SynthDef(\keysElectro, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var det  = Rand(-0.03, 0.03).midiratio;
	var f    = freq * det;
	var sl   = (sus * Rand(0.92, 1.08)).clip(0.12, 1.6);
	var pw   = SinOsc.kr(0.2, Rand(0, 6.283)).range(0.35, 0.62);   // slow PWM motion
	var osc  = (Pulse.ar(f, pw) * 0.5)
		+ (Pulse.ar(f * 1.006, 0.5) * 0.3)                         // detuned twin
		+ (Pulse.ar(f * 0.5, 0.5) * 0.26);                         // sub octave
	var env  = EnvGen.kr(Env.perc(0.004, sl, 1, -3.6), doneAction: 2);
	var cf   = (cutoff * (0.5 + v * 0.7) * Rand(0.95, 1.06)).clip(400, 6500);
	var sig  = RLPF.ar(osc, cf, 0.55);
	sig = ((sig * (1 + drive * 0.4)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig * env * amp * 1.35, pan));
}).add;
