// leadBrass — punchy "horn-y" lead with a soft attack swell on the
// brightness (envelope-driven cutoff = brass bite). Funky bite for the
// funk family. Gated contract.
SynthDef(\leadBrass, { |out=0, amp=0.5, freq=440, fmRatio=1.0, fmIndex=1.2, detune=0.06,
		wave=0.5, cutoff=2800, decay=0.22, gate=1, maxSustain=2.0, drive=1.0,
		glide=0.04, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 4000), glide.clip(0, 0.15));
	var env     = EnvGen.kr(Env.asr(0.012, 1.0, 0.22, -4), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.05]),
		1, doneAction: 2);
	var bite    = EnvGen.kr(Env.perc(0.008, 0.18, 1, -4), gate);
	var mod     = SinOsc.ar(fHz * (fmRatio + 0.001))
		* fmIndex * fHz * (0.5 + bite * 0.9);
	var car     = SinOsc.ar(fHz + mod);
	var saw     = Saw.ar(fHz * (1 + 0.005)) * 0.22;
	var sig     = car + saw;
	sig = RLPF.ar(sig,
		(cutoff * (0.6 + v * 0.8 + bite * 0.7)).clip(400, 7500), 0.4);
	sig = (sig * (1 + drive * 0.35)).tanh * 0.95;
	sig = LPF.ar(sig, 4000);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.006),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.3 * level);
}).add;
