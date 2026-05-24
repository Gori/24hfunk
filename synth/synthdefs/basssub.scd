// bassSub — a CLEAN, round sub bass for liquid DnB (and anywhere a warm, non-
// growly low end is wanted). Pure sine fundamental + faint 2nd/3rd harmonics
// for body, a gentle lowpass, and only a whisper of drive — NO saws, NO pulse,
// NO resonant ladder, so it never growls or buzzes. Mono-glide contract (same
// params as \bass) so the router's persistent-voice glide + genre SYNTH_PARAMS
// apply unchanged.
SynthDef(\bassSub, { |out=0, amp=0.8, freq=45, cutoff=600, res=0.2, drive=1.0, sub=0.9,
		glide=0.06, fenv=0.4, decay=0.5, gate=1, t_trig=1, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.008, 1.0, 0.12), gate);
	var aEnv = EnvGen.kr(Env.perc(0.005, decay, 1, -4), t_trig);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	// round sub: sine + quiet upper harmonics for warmth (no saws/pulse)
	var sig  = SinOsc.ar(f) + (SinOsc.ar(f * 2) * (0.12 * sub)) + (SinOsc.ar(f * 3) * 0.04);
	sig = LPF.ar(sig, (cutoff * (0.6 + (v * 0.5))).clip(120, 2000));
	sig = (sig * (1 + (drive * 0.12))).tanh;                    // barely-there warmth, no growl
	Out.ar(out, Pan2.ar(sig * (aEnv * 0.7 + 0.3) * gEnv * amp * 1.7 * level, pan));
}).add;
