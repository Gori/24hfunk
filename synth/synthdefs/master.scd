// master — glue bus compression + a VERY slight cohesive reverb + final
// brickwall on the SUMMED mix. All FX buses feed ~masterBus; this is the
// only thing writing out 0. Gentle glue (~1.8:1 above ~-10 dBFS) + light
// makeup, ~5% wet glue verb, then a safety limiter so nothing clips.
SynthDef(\master, { |in=0, out=0|
	var sig  = In.ar(in, 2);
	var comp = Compander.ar(sig, sig, 0.32, 1.0, 0.55, 0.01, 0.20) * 1.18;
	var wet  = FreeVerb2.ar(comp[0], comp[1], 1.0, 0.5, 0.5);
	var glue = comp + (wet * 0.025);                 // ~half the prior add
	Out.ar(out, Limiter.ar(LeakDC.ar(glue), 0.97, 0.002));
}).add;
