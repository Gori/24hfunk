// bassSquare — resonant acid square bass (303-ish), digital. Mono-glide contract.
SynthDef(\bassSquare, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2,
		sub=0.85, glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.004, 1.0, 0.09), gate);
	var aEnv = EnvGen.kr(Env.perc(0.003, decay, 1, -4), t_trig);
	var fE   = EnvGen.kr(Env.perc(0.004, decay * 0.6, 1, -4), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	var osc  = Pulse.ar(f, 0.48) + (Saw.ar(f) * 0.4) + (SinOsc.ar(f) * sub);
	var cf   = (cutoff * (0.4 + v) * (1 + fenv * 7 * fE)).clip(90, 6500);
	var sig  = RLPF.ar(osc, cf, (1 - res).clip(0.05, 0.9));
	sig = (sig * (1 + drive * 0.6)).tanh;
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.75 + 0.25) * gEnv * amp, pan));
}).add;
