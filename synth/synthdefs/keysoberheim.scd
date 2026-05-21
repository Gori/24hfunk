// keysOberheim — 80s Oberheim-style poly synth stab for Minneapolis funk
// (Prince / Jam & Lewis). Fat: saw + a detuned PWM pulse + a sub octave,
// through a smooth (mild-resonance) lowpass with a quick BRASSY filter-attack
// envelope (the OB "stab"). Punchy + bright, self-frees. \keys param contract.
SynthDef(\keysOberheim, { |out=0, amp=0.4, freq=220, cutoff=2800, sus=0.4, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var det  = Rand(-0.02, 0.02).midiratio;
	var f    = freq * det;
	var sl   = (sus * Rand(0.95, 1.06)).clip(0.12, 1.0);
	var pw   = SinOsc.kr(0.3, Rand(0, 6.28)).range(0.35, 0.6);   // slow PWM motion
	var osc  = (Saw.ar(f) * 0.5)
		+ (Pulse.ar(f * 1.007, pw) * 0.45)                       // detuned PWM twin
		+ (Pulse.ar(f * 0.5, 0.5) * 0.2);                        // sub octave
	// brassy stab: filter opens fast then settles (OB SEM character)
	var fenv = EnvGen.kr(Env([0.45, 1.0, 0.5], [0.02, sl * 0.7], [-2, -3]));
	var cf   = (cutoff * (0.5 + (v * 0.7)) * fenv).clip(450, 7000);
	var env  = EnvGen.kr(Env.perc(0.006, sl, 1, -3.5), doneAction: 2);
	var sig  = RLPF.ar(osc, cf, 0.42);                           // mild resonance, smooth
	sig = ((sig * (1 + drive * 0.25)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * amp * 1.3);
}).add;
