// ohat (open hat) — same metallic source, long sizzly decay with shimmer.
// params: amp, cutoff, decay, metal, pan
// Per-hit metal detune, random shimmer phase + wide decay/level drift so
// repeated open hats breathe instead of cloning. Velocity opens the tone.
// v~1.0 == the old fixed sound.
SynthDef(\ohat, { |out=0, amp=0.46, cutoff=8500, decay=0.34, metal=0.6, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var dr   = decay * Rand(0.85, 1.18);
	var fj   = Rand(0.97, 1.03);
	var cj   = (cutoff * (0.78 + v * 0.22) * Rand(0.95, 1.05)).clip(3000, 14000);
	var aEnv = EnvGen.kr(Env.perc(0.0008, dr, 1, -3.5), doneAction: 2);
	var rat  = [1, 1.41, 1.87, 2.33, 2.91, 3.74];
	var shim = SinOsc.kr(43, Rand(0, 6.283)).range(0.85, 1.0);
	var clk  = Mix(Pulse.ar(317 * fj * rat, 0.5)) * 0.09 * metal;
	var nz   = WhiteNoise.ar * (1 - metal);
	var sig  = HPF.ar(clk + nz, cj) * shim;
	sig = (sig * 1.2).tanh;
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.93, 1.07), pan));
}).add;
