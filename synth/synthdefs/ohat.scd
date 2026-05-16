// ohat (open hat) — same metallic source, long sizzly decay with shimmer.
// params: amp, cutoff, decay, metal, pan
SynthDef(\ohat, { |out=0, amp=0.46, cutoff=8500, decay=0.34, metal=0.6, pan=0|
	var aEnv = EnvGen.kr(Env.perc(0.0008, decay, 1, -3.5), doneAction: 2);
	var rat  = [1, 1.41, 1.87, 2.33, 2.91, 3.74];
	var shim = SinOsc.kr(43).range(0.85, 1.0);
	var clk  = Mix(Pulse.ar(317 * rat, 0.5)) * 0.09 * metal;
	var nz   = WhiteNoise.ar * (1 - metal);
	var sig  = HPF.ar(clk + nz, cutoff.clip(3000, 14000)) * shim;
	sig = (sig * 1.2).tanh;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
