// fxdrum — the drums-bus FX. Identical send/space chain & param contract as
// \fx (so the existing fxDrums plumbing is unchanged) PLUS a front-end glue:
// gentle parallel bus compression + a soft transient lift. Makes a
// deliberately varied kit read as one cohesive kit per genre, dialable via
// fxDrums.glue / fxDrums.punch. glue~0.25 / punch~0.2 = a light musical smack.
SynthDef(\fxdrum, { |in=0, out=0, reverb=0.3, delay=0.2, delayTime=0.357,
		width=0.6, glue=0.25, punch=0.2|
	var dry0 = In.ar(in, 2);
	var g    = glue.clip(0, 1);
	var pu   = punch.clip(0, 1);
	var comp = Compander.ar(dry0, dry0, 0.28, 1.0, 0.45, 0.004, 0.10);
	var glud = (dry0 * (1 - (g * 0.5))) + (comp * (g * 0.8));
	var slow = Lag.ar(glud, 0.012);
	var dry  = glud + ((glud - slow) * (pu * 1.4));
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
