// master — glue bus compression + final brickwall on the SUMMED mix.
// All three FX buses feed ~masterBus; this is the only thing writing out 0.
// Gentle, musical glue (~1.8:1 above ~-10 dBFS) with light makeup, then a
// safety limiter so nothing clips the device.
SynthDef(\master, { |in=0, out=0|
	var sig  = In.ar(in, 2);
	var comp = Compander.ar(sig, sig, 0.32, 1.0, 0.55, 0.01, 0.20) * 1.18;
	Out.ar(out, Limiter.ar(LeakDC.ar(comp), 0.97, 0.002));
}).add;
