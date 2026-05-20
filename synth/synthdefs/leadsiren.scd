// leadSiren — classic dub siren (sound-system air-horn). Sine carrier whose
// pitch sweeps WHOOP-UP then WHOOP-DOWN over ~4 s, drenched in feedback
// delay + a long FreeVerb tail. Used very rarely (cooldown-gated in
// canned.py) as a punctuation in dub-family genres. Gated contract.
SynthDef(\leadSiren, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.5, gate=1, maxSustain=6.0, drive=1.0,
		glide=0.04, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	// the whoop: low -> peak -> mid -> low. Sine curve = smooth glissando.
	var sweep   = EnvGen.kr(
		Env([1.0, 2.4, 2.7, 1.8, 0.9], [0.9, 0.5, 1.0, 1.6], \sin),
		gate, doneAction: 0);
	var fHz     = freq.clip(80, 4000) * sweep;
	var env     = EnvGen.kr(Env.asr(0.05, 1.0, 1.8, -3), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 10), 0.4]),
		1, doneAction: 2);
	// twin-sine carrier for body (very slight detune = analogue siren feel)
	var car     = SinOsc.ar(fHz) + (SinOsc.ar(fHz * 1.004) * 0.6);
	var sig     = car * 0.42;
	// classic dub: long feedback comb + heavy reverb wash
	sig = sig + (CombC.ar(sig, 0.6, 0.375, 2.5) * 0.55);
	sig = sig + (FreeVerb.ar(sig, 0.75, 0.88, 0.5) * 0.40);
	sig = (sig * (1 + drive * 0.18)).tanh * 0.6;
	// siren is bright by nature — slightly higher LPF than other leads
	sig = LPF.ar(sig, 3500);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.025, 0.014),
		pan.clip(-1, 1) * 0.55) * env * safety * amp * 2.4 * level);
}).add;
