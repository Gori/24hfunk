// leadFM — bright digital 2-op FM/DX lead. Per-note gated contract (same args
// + safety env as \lead so genre SYNTH_PARAMS apply and no notes hang).
SynthDef(\leadFM, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var env    = EnvGen.kr(Env.adsr(0.005, 0.12, 0.55, decay, curve: -3), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(5.5) * 0.008 * EnvGen.kr(Env([0, 0, 1], [0.18, 0.6]));
	var f      = freq * (1 + vib);
	var iEnv   = EnvGen.kr(Env.perc(0.004, decay, 0.6, -3), gate);
	var mod    = SinOsc.ar(f * (fmRatio + 0.001)) * f * (fmIndex * 4 + wave * 6)
	             * (0.4 + v * 0.7) * iEnv;
	var sig    = SinOsc.ar(f + mod) + (SinOsc.ar(f * 2.01) * 0.2);
	sig = LPF.ar(sig, (cutoff * (0.5 + v)).clip(400, 13000));
	sig = (sig * (1 + drive * 0.4)).softclip;
	Out.ar(out, Pan2.ar(sig * env * safety * amp, pan));
}).add;
