// bassSquare — resonant acid square bass (303-ish), digital. Mono-glide contract.
SynthDef(\bassSquare, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2,
		sub=0.85, glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.004, 1.0, 0.09), gate);
	var aEnv = EnvGen.kr(Env.perc(0.003, decay, 1, -4), t_trig);
	var fE   = EnvGen.kr(Env.perc(0.004, decay * 0.6, 1, -4), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	// Deep, round, RECESSED bass (electro/broken_house/minneapolis_funk/
	// minimal_techno all share this). No saw at all (it was the buzz), the
	// filter env barely opens to a low ceiling, almost no drive, a hard top
	// roll-off and a clearly lower level -> felt, not buzzy.
	var osc  = (Pulse.ar(f, 0.46) * 0.8) + (SinOsc.ar(f) * (sub + 0.25));
	var cf   = (cutoff * (0.28 + v * 0.5) * (1 + fenv * 1.2 * fE)).clip(60, 1000);
	var sig  = RLPF.ar(osc, cf, (1 - res).clip(0.30, 0.85));
	sig = (sig * (1 + drive * 0.1)).tanh;
	sig = LPF.ar(sig, 1100);
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.75 + 0.25) * gEnv * amp * 0.5 * level, pan));
}).add;
