// bass — ROUND digital sub, EXPRESSIVE + GLIDING, now with analog character.
// Driven as a persistent MONO voice by the router (\freq Lag'd for glide,
// \t_trig re-articulates amp, \gate sustains/releases). No doneAction.
//  #2 slow VCO drift  #3 Moog-ladder filter (analog, ladder-saturating)
//  #4 multi-stage nonlinearity (pre-drive into the ladder + a gentle
//     asymmetric 2nd stage). Gain-matched to the old clean version.
// params: amp(vel), freq, cutoff, res, drive, sub, glide, fenv, decay, gate, t_trig, pan
SynthDef(\bass, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.2, sub=0.85,
		glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var gEnv   = EnvGen.kr(Env.asr(0.006, 1.0, 0.12), gate);
	var aEnv   = EnvGen.kr(Env.perc(0.004, decay, 1, -4), t_trig);
	var fEnv   = EnvGen.kr(Env.perc(0.005, decay * 0.7, 1, -3), t_trig);
	var drift  = LFNoise2.kr(0.11) * 0.0016;                        // analog VCO drift
	var f      = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4)) * (1 + drift);
	var defAmt = ((freq - 40) / 130).clip(0.0, 1.0);
	var subOsc = SinOsc.ar(f) * sub;
	var click  = SinOsc.ar(f * 2) * 0.12 * EnvGen.kr(Env.perc(0.002, 0.05, 1, -6), t_trig);
	var upper  = LPF.ar(Pulse.ar(f, 0.42), (cutoff * 2).clip(200, 6000)) * defAmt * 0.45;
	var cf     = (cutoff * (0.55 + v * 0.9) * (1 + (fenv * 3 * fEnv))).clip(90, 5500);
	var pre    = (subOsc + click + upper) * (1 + (drive * 0.32 * defAmt * (0.5 + v * 0.6)));
	var sig    = MoogFF.ar(pre, cf, (res * 2.6).clip(0, 3.3));       // analog ladder
	sig = LeakDC.ar(((sig + (sig * sig * 0.05)).tanh) * 2.25);       // gentle asym 2nd stage (+50% level)
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.7 + 0.3) * gEnv * amp * level, pan));
}).add;
