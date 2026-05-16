// bassReese — dark detuned-saw "reese" bass. Mono-glide contract (router owns
// the node; \freq Lag, \gate sustain, \t_trig re-articulate, no free-on-done).
// Same param names as \bass so the genre SYNTH_PARAMS still apply.
SynthDef(\bassReese, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2,
		sub=0.85, glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.006, 1.0, 0.12), gate);
	var aEnv = EnvGen.kr(Env.perc(0.005, decay, 1, -4), t_trig);
	var fE   = EnvGen.kr(Env.perc(0.01, decay * 0.8, 1, -3), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	var det  = [-0.13, -0.06, 0, 0.06, 0.13] * (0.4 + res);
	var saws = Mix(Saw.ar(f * (1 + det))) * 0.18;
	var subo = SinOsc.ar(f) * sub;
	var cf   = (cutoff * (0.5 + v * 0.9) * (1 + fenv * 3 * fE)).clip(80, 5000);
	var sig  = RLPF.ar(saws, cf, (1 - res).clip(0.08, 1)) + subo;
	sig = (sig * (1 + drive * 0.7)).tanh;
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.7 + 0.3) * gEnv * amp, pan));
}).add;
