// bassNeuro — a MODULATED / morphing "neuro" reese for neurofunk (the bass IS
// the genre). Detuned saws + inharmonic FM for the growl; a clean sub kept OUT
// of the distortion; the cutoff swept by a slow per-note envelope + free-
// running LFOs so it MOVES over every note; a short modulated comb for the
// metallic screech; two morphing vowel band-passes ("talking"); and serial
// fold/tanh distortion (harmonics get re-filtered = the morph). Mono-glide
// contract — same params as \bass / \bassReese so genre SYNTH_PARAMS apply.
SynthDef(\bassNeuro, { |out=0, amp=0.8, freq=45, cutoff=700, res=0.35, drive=1.6,
		sub=0.8, glide=0.06, fenv=0.6, decay=0.5, gate=1, t_trig=1, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var gEnv = EnvGen.kr(Env.asr(0.006, 1.0, 0.14), gate);
	var f    = Lag.ar(K2A.ar(freq.clip(20, 700)), glide.clip(0, 0.4));
	var subo = SinOsc.ar(f) * sub * 0.9;                         // clean sub (no distortion)
	var det  = [-0.18, -0.09, 0.08, 0.17] * (0.5 + res);
	var saws = Mix(Saw.ar(f * (1 + det))) * 0.045;
	var iEnv = EnvGen.kr(Env([0.0, 1.0], [decay * 1.6]), t_trig);  // FM index grows over the note
	var fm   = SinOsc.ar((f * 2.7) + (SinOsc.ar(f * 1.51) * f * 0.8 * iEnv)) * 0.04;
	var mid  = saws + fm;
	var swp  = EnvGen.kr(Env([0.12, 1.0, 0.35], [decay * 1.1, decay], \sin), t_trig);
	var lfo  = SinOsc.kr(LFNoise1.kr(0.3).range(3, 8)).range(0.45, 1.0);  // free-running
	var jit  = LFNoise1.kr(10).range(0.7, 1.0);
	var cf   = (cutoff * (0.5 + (fenv * 1.5 * swp)) * lfo * jit).clip(120, 2400);  // darker sweep
	mid = RLPF.ar(mid, cf, res.clip(0.08, 0.35));
	// (comb + vowel removed — they were the metallic noise/growl)
	mid = (mid * (1 + (drive * 0.18))).tanh;                    // very gentle (smooth, not growly)
	mid = mid * 0.8;
	mid = LPF.ar(mid, 4500);
	Out.ar(out, Pan2.ar((mid + subo) * gEnv * amp * level, pan));
}).add;
