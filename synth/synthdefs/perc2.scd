// perc2 — the dedicated percussion layer. One flexible one-shot voice that
// morphs across three archetypes via `tone`:
//   tone ~0.0  -> glitchy short digital noise (sample-rate-reduced)
//   tone ~0.45 -> shaker (band-passed noise with a soft swell)
//   tone ~1.0  -> organic membrane (pitched conga/djembe + skin slap)
// params: amp(vel) freq(organic pitch) decay drive tone crush noise pan
SynthDef(\perc2, { |out=0, amp=0.5, freq=220, decay=0.18, drive=1.0,
		tone=0.5, crush=0.35, noise=0.5, pan=0|
	var t    = tone.clip(0, 1);
	var dec  = (decay * (0.5 + t)).clip(0.02, 0.9);   // glitch short, organic longer
	var env  = EnvGen.kr(Env.perc(0.001, dec, 1, -4.5), doneAction: 2);
	var pEnv = EnvGen.kr(Env.perc(0.001, dec * 0.5, 1, -6));
	// organic membrane: pitched body with a fast pitch drop + skin transient
	var bf   = freq.clip(60, 900) * (1 + (pEnv * 1.4));
	var body = (SinOsc.ar(bf) * 0.8) + (LFTri.ar(bf * 1.5) * 0.2)
	           + (HPF.ar(WhiteNoise.ar, 1800)
	              * EnvGen.kr(Env.perc(0.0005, 0.02)) * 0.5);
	// shaker: band-passed noise with a soft swell
	var shk  = BPF.ar(WhiteNoise.ar, 6200, 0.7)
	           * EnvGen.kr(Env([0, 1, 0.6, 0], [0.012, dec * 0.4, dec * 0.5])) * 2.4;
	// glitch: short high-passed noise, sample-rate-reduced (digital)
	var gN   = HPF.ar(WhiteNoise.ar, 3000);
	var gl   = Latch.ar(gN, Impulse.ar(
	             (1400 + (9000 * (1 - crush.clip(0, 1)))).clip(700, 13000)))
	           * EnvGen.kr(Env.perc(0.0003, dec * 0.4, 1, -8)) * 1.5;
	// crossfade weights across tone
	var wG   = (1 - (t * 2.4)).clip(0, 1);
	var wS   = (1 - ((t - 0.45) * 3.4).abs).clip(0, 1);
	var wB   = ((t - 0.5) * 2.2).clip(0, 1);
	var sig  = (gl * wG) + (shk * wS) + (body * wB);
	sig = (sig * (1 + drive * 0.5)).tanh;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * env * amp, pan));
}).add;
