// fx — clean send bus: damped stereo delay + freeverb + stereo width + soft
// glue limiter. Tighter / less washy than before; digital-clean.
// params: reverb(0..1), delay(0..1 mix), delayTime(s), width(0..1)
SynthDef(\fx, { |in=0, out=0, reverb=0.3, delay=0.2, delayTime=0.357, width=0.6,
		duckBus=0, duck=0|
	// kick->bass sidechain: the router writes a 0..1 kick envelope to duckBus;
	// `duck` (0 = off, per-genre) scales how deep. Only the bass bus sets duck>0,
	// so mel/perc/drums are unaffected (duck=0 -> d=1 -> no change).
	var d    = 1 - (In.kr(duckBus, 1).clip(0, 1) * duck.clip(0, 1));
	var dry  = In.ar(in, 2) * d;
	var dt   = delayTime.clip(0.02, 1.0);
	var dl   = LPF.ar(CombC.ar(dry[0], 1.0, dt, dt * 5), 4500) * delay.clip(0, 0.8);
	var dr   = LPF.ar(CombC.ar(dry[1], 1.0, dt * 1.5, dt * 5), 4500) * delay.clip(0, 0.8);
	var wet  = dry + [dl, dr];
	var verb = FreeVerb2.ar(wet[0], wet[1], reverb.clip(0, 0.9), 0.72, 0.4);
	var w    = (width.clip(0, 1) * 0.5);
	var mid  = (verb[0] + verb[1]) * 0.5;
	var sid  = (verb[0] - verb[1]) * 0.5;
	var sig  = [mid + (sid * (0.5 + w)), mid - (sid * (0.5 + w))];
	sig = (sig * 1.08).softclip;
	Out.ar(out, Limiter.ar(LeakDC.ar(sig), 0.95));
}).add;
