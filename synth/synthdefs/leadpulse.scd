// leadPulse — chiptune PWM square lead, digital + bright. Per-note gated
// contract (same args + safety env as \lead).
SynthDef(\leadPulse, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var env    = EnvGen.kr(Env.adsr(0.004, 0.10, 0.5, decay, curve: -3), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(6.0) * 0.009 * EnvGen.kr(Env([0, 0, 1], [0.14, 0.5]));
	var f      = freq * (1 + vib);
	var pw     = SinOsc.kr(0.7 + wave * 4).range(0.15, 0.85);
	var sig    = Pulse.ar(f, pw) + (Pulse.ar(f * (1 + detune * 0.04), pw) * 0.5);
	// slightly softened: less octave-buzz harmonic, lower top, less drive
	sig = sig + (Pulse.ar(f * 2, 0.5) * fmIndex * 0.10);
	sig = LPF.ar(sig, (cutoff * (0.55 + v)).clip(500, 9500));
	sig = (sig * (1 + drive * 0.4)).softclip * 0.6;
	// lead mix trim — lead sat too hot vs drums/bass across genres (tune here)
	Out.ar(out, Pan2.ar(sig * env * safety * amp * 0.6, pan));
}).add;
