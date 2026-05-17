// master — analog "console/tape" colour + glue bus compression + a VERY
// slight cohesive reverb + final brickwall on the SUMMED mix. All FX buses
// feed ~masterBus; this is the only thing writing out 0.
//  #1 analog bus stage: tape wow/flutter (tiny pitch wobble) -> gentle
//     asymmetric tube/console saturation (even harmonics = warmth) -> a
//     soft HF roll (analog top is never brick-clean), then the glue
//     compressor + light verb + safety limiter. All subtle, gain-matched.
SynthDef(\master, { |in=0, out=0|
	var sig  = In.ar(in, 2);
	var wob  = (LFNoise2.kr(0.7) * 0.6 + SinOsc.kr(5.8) * 0.4) * 0.0008;
	var tape = DelayC.ar(sig, 0.03, (0.012 + wob).clip(0.001, 0.028));
	var drv  = tape * 1.10;
	var sat  = ((drv + (drv * drv * 0.045)) * 0.98).tanh;
	var soft = (sat * 0.72) + (LPF.ar(sat, 12000) * 0.28);
	var comp = Compander.ar(soft, soft, 0.32, 1.0, 0.55, 0.01, 0.20) * 1.10;
	var wet  = FreeVerb2.ar(comp[0], comp[1], 1.0, 0.5, 0.5);
	var glue = comp + (wet * 0.025);
	Out.ar(out, Limiter.ar(LeakDC.ar(glue), 0.97, 0.002));
}).add;
