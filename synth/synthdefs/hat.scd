// hat (closed) — clean metallic digital tick: 6 detuned square partials at
// inharmonic ratios, high-passed, very tight. Smoother than raw noise.
// params: amp, cutoff, decay, metal(0..1), pan
SynthDef(\hat, { |out=0, amp=0.5, cutoff=9500, decay=0.04, metal=0.6, pan=0|
	var aEnv = EnvGen.kr(Env.perc(0.0004, decay, 1, -10), doneAction: 2);
	var rat  = [1.0, 1.34, 1.79, 2.27, 2.83, 3.41];
	var met  = Mix(Pulse.ar(360 * rat, 0.5)) * 0.09;
	var nz   = WhiteNoise.ar * 0.5;
	var src  = (met * metal) + (nz * (1 - metal));
	var sig  = HPF.ar(HPF.ar(src, cutoff.clip(3500, 14000)), cutoff.clip(3500, 14000));
	sig = sig.softclip;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
