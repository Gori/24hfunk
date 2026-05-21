// leadMoog — Mini-Moog-style mono lead (P-funk / Bernie Worrell). Three
// oscillators (saw + slightly-detuned saw + sub-octave square pulse) for
// the FAT bottom, 4-pole-ish ladder via two cascaded resonant LPFs,
// SHARP filter envelope per note (the classic Moog "wow"), and tanh
// saturation for warmth. The router runs this on CH_LEAD as a single
// persistent mono voice when the section's lead synth is leadMoog, so
// glide takes effect between notes via the freq Lag. Gated contract.
SynthDef(\leadMoog, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=3200, decay=0.4, gate=1, t_trig=1, maxSustain=5.0,
		drive=1.0, glide=0.08, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	// ARTICULATION + MOVEMENT layered on the freq:
	// - vibrato: 5.5 Hz +/- a slow drift, depth ~3-8 cents (vocal-like)
	// - attack pitch-bend: brief upward "horn-lip" slur into pitch on each note
	//   (re-fires per note via t_trig)
	// === MOD WHEEL: a slow expressive 'hand' riding the wheel (0..1, drifts
	// over a few seconds). Drives vibrato depth+rate AND filter brightness, so
	// the tone sings/swells and opens up as if the player works the wheel. ===
	var modWheel = Lag.kr(LFNoise1.kr(0.3).range(0.0, 1.0), 0.3);
	var vib_rate = (4.8 + (modWheel * 2.8)) + LFNoise2.kr(0.3).range(-0.5, 0.5);
	var vib_dep  = 0.0015 + (modWheel * 0.015);                   // up to ~1.2 semis when wheel up
	var vibSwell = EnvGen.kr(Env([0, 0, 1], [0.12, 0.4]), t_trig); // swells in per note
	var vib      = SinOsc.kr(vib_rate, Rand(0, 6.28)) * vib_dep * vibSwell.max(0.25);
	// === PITCH WHEEL: the player working the bend, extensively ===
	// (a) scoop UP into each note (depth + time vary per note)
	var bDepth   = TRand.kr(0.86, 0.965, t_trig);
	var bTime    = TRand.kr(0.05, 0.13, t_trig);
	var scoop    = EnvGen.kr(Env([bDepth, 1.0], [bTime], -3), t_trig);
	// (b) a continuous wandering bend (the hand never quite still) ~+/-0.35 semi
	var wander   = Lag.kr(LFNoise1.kr(0.5), 0.1) * 0.02;
	// (c) occasional BIG bend gesture (~a tone up/down, then resolve to pitch)
	var gTrig    = Dust.kr(0.35);
	var gAmt     = TRand.kr(-0.11, 0.13, gTrig);                  // up to ~+/-2 semis
	var bigBend  = EnvGen.kr(Env([0, 1, 1, 0], [0.12, 0.18, 0.45], \sin), gTrig) * gAmt;
	var pitchW   = scoop * (1 + wander + bigBend);
	var fHz      = Lag.kr(freq.clip(55, 2400), glide.clip(0, 0.25))
		* (1 + vib) * pitchW;
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
	// mod wheel also opens the filter (brightness rides the wheel)
	var cf      = (cutoff * (0.35 + 0.6 * v + 1.4 * fenv) * cf_lfo
		* (0.75 + (modWheel * 0.6))).clip(150, 8000);
	// 4-pole ladder approximation: two cascaded resonant lowpass filters
	var sig     = RLPF.ar(src, cf, 0.45);
	sig = RLPF.ar(sig, cf * 1.08, 0.55);
	// Moog warmth: tanh saturation BEFORE the global high-cut
	sig = (sig * (1 + drive * 0.45)).tanh * 0.78;
	sig = LPF.ar(sig, 3200);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.009),
		pan.clip(-1, 1) * 0.3) * env * safety * amp * 2.6 * level);
}).add;
