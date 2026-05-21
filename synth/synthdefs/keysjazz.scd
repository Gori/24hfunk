// keysJazz — a SYNTHESIZED acoustic jazz piano (no samples). Additive
// detuned partials with slight INHARMONIC stretch (real piano strings are
// inharmonic), each partial decaying faster the higher it is, plus a hammer
// "thunk" transient and a velocity-tracking lowpass that closes as the note
// decays. Percussive attack, natural ringing decay. Self-terminating.
// Same gated-free contract + param names as \keys (amp/freq/cutoff/sus/
// drive/vib/pan) so the router/comp can drive it interchangeably.
SynthDef(\keysJazz, { |out=0, amp=0.4, freq=220, cutoff=2600, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var det     = Rand(-0.04, 0.04).midiratio;                  // per-note tuning tolerance
	var f       = freq * det;
	var inh     = { |n| n * (1 + (0.0007 * n * n)).sqrt };      // inharmonicity stretch
	var amps    = [1.0, 0.6, 0.42, 0.28, 0.17, 0.10, 0.06];     // piano-ish spectral rolloff
	var decs    = [1.0, 0.86, 0.72, 0.56, 0.43, 0.33, 0.25];    // highs decay first
	var baseDec = (sus * Rand(0.9, 1.12)).clip(0.3, 3.0) * 2.4;
	var strings = Mix.fill(7, { |i|
		var n = i + 1;
		SinOsc.ar(f * inh.(n) * (1 + (LFNoise2.kr(0.2) * 0.0012)))
			* amps[i]
			* EnvGen.kr(Env.perc(0.001, baseDec * decs[i], 1, -4.5));
	});
	// hammer thunk — short noise burst, brighter + louder with velocity
	var hammer  = BPF.ar(WhiteNoise.ar, (f * 3).clip(200, 6000), 0.7)
		* EnvGen.kr(Env.perc(0.0008, 0.045, 1, -6)) * (0.25 + v * 0.5);
	// brightness tracks velocity then closes over the decay
	var cf      = (cutoff * (0.45 + v * 0.6) * Rand(0.95, 1.06)).clip(400, 7000);
	var dyn     = EnvGen.kr(Env([1.0, 0.35], [baseDec * 0.7], -3));
	var amp_env = EnvGen.kr(Env.perc(0.002, baseDec * 1.1, 1, -3.6), doneAction: 2);
	var sig     = (strings * (0.4 + v * 0.6)) + hammer;
	sig = LPF.ar(sig, cf * dyn.max(0.18));
	sig = ((sig * (1 + drive * 0.25)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig * amp_env * amp * 1.5, pan));
}).add;
