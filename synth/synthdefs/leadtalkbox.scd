// leadTalkbox — vowel-formant lead (Roger Troutman / Zapp / G-funk talkbox).
// 3 resonant bandpasses tuned to vowel formants F1/F2/F3, summed over a
// detuned dual-saw + sub-pulse source. A slow LFNoise + sinusoid jitter
// continuously sweeps the vowel between "oo" and "ah" — keeps even held
// notes sounding like they're forming words. Core SC UGens only. Gated.
SynthDef(\leadTalkbox, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.4, gate=1, maxSustain=2.8, drive=1.0,
		glide=0.06, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 3200), glide.clip(0, 0.25));
	var env     = EnvGen.kr(Env.asr(0.025, 1.0, 0.45, -3), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 5), 0.12]),
		1, doneAction: 2);
	// vowel position: slow drift + a "talk wobble" — never sits still
	var vowel   = (LFNoise2.kr(0.45).range(0, 1)
		+ SinOsc.kr(2.4, Rand(0, 6.28)).range(-0.18, 0.18)).clip(0, 1);
	// vowel 0 = "oo" (closed), vowel 1 = "ah" (open) — F1/F2/F3
	var f1      = vowel.linlin(0, 1, 320, 850);
	var f2      = vowel.linlin(0, 1, 870, 1220);
	var f3      = vowel.linlin(0, 1, 2240, 2810);
	// rich source: dual-saw + sub-pulse — talkbox needs harmonics to filter
	var src     = Saw.ar(fHz)
		+ (Saw.ar(fHz * (1 + detune * 0.04)) * 0.7)
		+ (Pulse.ar(fHz * 0.5, 0.5) * 0.22);
	// formant bank — high-Q BPFs at the three formants
	var b1      = BPF.ar(src, f1, 0.16) * 4.5;
	var b2      = BPF.ar(src, f2, 0.20) * 3.6;
	var b3      = BPF.ar(src, f3, 0.24) * 2.2;
	var sig     = (b1 + b2 + b3) * 0.42;
	// keep a hint of the unfiltered source = the funky "rasp" through the tube
	sig = sig + (src * 0.06);
	sig = RLPF.ar(sig, (cutoff * (0.7 + v * 0.6)).clip(900, 9500), 0.45);
	sig = (sig * (1 + drive * 0.3)).tanh * 0.85;
	sig = LPF.ar(sig, 3200);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.009),
		pan.clip(-1, 1) * 0.35) * env * safety * amp * 2.4 * level);
}).add;
