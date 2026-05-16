// bassFM — punchy 2-op FM pluck bass. Mono-glide contract (same as \bass).
SynthDef(\bassFM, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2,
		sub=0.85, glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.005, 1.0, 0.1), gate);
	var aEnv = EnvGen.kr(Env.perc(0.003, decay, 1, -4), t_trig);
	var iEnv = EnvGen.kr(Env.perc(0.002, decay * 0.5, 1, -5), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	var mod  = SinOsc.ar(f * 2.0) * f * (2 + fenv * 8) * iEnv * (0.5 + v * 0.6);
	var car  = SinOsc.ar(f + mod);
	var subo = SinOsc.ar(f) * sub;
	var sig  = LPF.ar(car, (cutoff * (0.6 + v)).clip(120, 6000)) + (subo * 0.8);
	sig = (sig * (1 + drive * 0.4)).softclip;
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.8 + 0.2) * gEnv * amp, pan));
}).add;
