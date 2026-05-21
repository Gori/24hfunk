// leadMoog — Mini-Moog-style mono lead (P-funk / Bernie Worrell). Three
// oscillators (saw + slightly-detuned saw + sub-octave square pulse) for
// the FAT bottom, 4-pole-ish ladder via two cascaded resonant LPFs,
// SHARP filter envelope per note (the classic Moog "wow"), and tanh
// saturation for warmth. The router runs this on CH_LEAD as a single
// persistent mono voice when the section's lead synth is leadMoog, so
// glide takes effect between notes via the freq Lag. Gated contract.
SynthDef(\leadMoog, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=3200, decay=0.4, gate=1, t_trig=1, maxSustain=5.0,
		drive=1.0, glide=0.1, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	// ARTICULATION + MOVEMENT layered on the freq:
	// - vibrato: 5.5 Hz +/- a slow drift, depth ~3-8 cents (vocal-like)
	// - attack pitch-bend: brief upward "horn-lip" slur into pitch on each note
	//   (re-fires per note via t_trig)
	// === MOD WHEEL: a slow 'hand' riding the wheel (0..1, drifts over a few
	// seconds). CLEARLY audible — it drives a big FILTER sweep (the Moog wah,
	// see cf below) + the vibrato depth/rate. Pitch stays IN KEY (vibrato is
	// centered, and notes connect by LEGATO portamento, no bends). ===
	var modWheel = Lag.kr(LFNoise1.kr(0.35).range(0.0, 1.0), 0.25);
	var vib_rate = 5.2 + (modWheel * 1.5) + LFNoise2.kr(0.3).range(-0.4, 0.4);
	var vib_dep  = 0.003 + (modWheel * 0.012);                    // audible vibrato when wheel up
	var vibSwell = EnvGen.kr(Env([0, 0, 1], [0.16, 0.5]), t_trig); // swells in per note
	var vib      = SinOsc.kr(vib_rate, Rand(0, 6.28)) * vib_dep * vibSwell.max(0.3);
	// LEGATO: portamento glide slides smoothly between notes (in key, no bends)
	var fHz      = Lag.kr(freq.clip(55, 2400), glide.clip(0, 0.25)) * (1 + vib);
	var env     = EnvGen.kr(Env.asr(0.006, 1.0, 0.55, -3), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 8), 0.2]),
		1, doneAction: 2);
	// 3 oscillators: 2 saws (slight detune) + sub-octave square = big body
	var saw1    = Saw.ar(fHz);
	var saw2    = Saw.ar(fHz * (1 + detune * 0.04));
	var sub     = Pulse.ar(fHz * 0.5, 0.5);
	var src     = (saw1 + saw2 * 0.85 + sub * 0.65) * 0.30;
	// FILTER ENVELOPE — retriggers per-note via t_trig (mono voice keeps
	// the synth alive across notes; t_trig re-fires the "wow" on each hit).
	var fenv    = EnvGen.kr(Env([0, 1, 0.35], [0.005, decay * 0.9], [-3, -2]),
		t_trig);
	// FILTER LFO — slow organic cutoff wobble layered over the envelope:
	// keeps the tone breathing/talking instead of sitting at a static cutoff
	var cf_lfo  = LFNoise2.kr(0.7).range(0.85, 1.15);
	// MOD WHEEL -> big filter sweep (0.45x .. 1.65x cutoff): the clearly
	// audible Moog wah as the player rides the wheel up and down.
	var cf      = (cutoff * (0.3 + 0.5 * v + 1.3 * fenv) * cf_lfo
		* (0.45 + (modWheel * 1.2))).clip(150, 8000);
	// 4-pole ladder approximation: two cascaded resonant lowpass filters
	var sig     = RLPF.ar(src, cf, 0.45);
	sig = RLPF.ar(sig, cf * 1.08, 0.55);
	// Moog warmth: tanh saturation BEFORE the global high-cut
	sig = (sig * (1 + drive * 0.45)).tanh * 0.78;
	sig = LPF.ar(sig, 3200);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.009),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.6 * level);
}).add;
