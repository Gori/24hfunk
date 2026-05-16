// keys — expressive warm DIGITAL poly / FM e-piano for comp + pad. Velocity
// opens the filter and the FM "tine" (harder = brighter). Gentle chorus +
// late vibrato. Self-terminating (doneAction:2) so ch2 needs no note-off.
// params: amp(vel), freq, cutoff, sus(seconds), drive, vib, pan
SynthDef(\keys, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var env  = EnvGen.kr(Env([0, 1, 0.55, 0], [0.008, 0.14, sus.clip(0.15, 3.0)],
		[2, -2, -4]), doneAction: 2);
	var vibe = SinOsc.kr(5.4) * vib * 0.012
		* EnvGen.kr(Env([0, 0, 1], [0.18, 0.5]));   // vibrato fades in
	var f    = freq * (1 + vibe);
	var tine = SinOsc.ar(f * 7) * (0.18 + v * 0.5)
		* EnvGen.kr(Env.perc(0.001, 0.10, 1, -6));   // bright FM attack tine
	var body = SinOsc.ar(f + (tine * f * 0.5))
		+ (SinOsc.ar(f * 1.003) * 0.5)               // slight chorus detune
		+ (SinOsc.ar(f * 2) * 0.18);
	var sig  = (body + tine * 0.3);
	sig = LPF.ar(sig, (cutoff * (0.45 + v * 1.05)).clip(300, 9000));
	// chords/comp/pad sit louder in the mix vs the (now trimmed) lead
	sig = (sig * (1 + drive * 0.4)).softclip * 0.72;
	Out.ar(out, Pan2.ar(sig * env * amp, pan));
}).add;
