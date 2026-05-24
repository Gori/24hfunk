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
	// harder parallel "glue" compression — audibly tightens the kit
	var comp = Compander.ar(dry0, dry0, 0.18, 1.0, 0.35, 0.003, 0.12);
	var glud = (dry0 * (1 - (g * 0.7))) + (comp * (g * 1.3));
	// transient designer: fast vs slow amplitude follower -> boost ONLY the
	// attack region (audible snap), not the sustain (the old single-Lag pumped).
	var fenv = Amplitude.ar(glud, 0.0008, 0.0008);
	var senv = Amplitude.ar(glud, 0.020, 0.020);
	var trans= (fenv - senv).max(0);
	var dry  = glud * (1 + (trans * (pu * 6)).clip(0, 3.5));
	var dt   = delayTime.clip(0.02, 1.0);
	var dl   = LPF.ar(CombC.ar(dry[0], 1.0, dt, dt * 5), 4500) * delay.clip(0, 0.8);
	var dr   = LPF.ar(CombC.ar(dry[1], 1.0, dt * 1.5, dt * 5), 4500) * delay.clip(0, 0.8);
	var wet  = dry + [dl, dr];
	// tight drum ROOM (Schroeder: parallel mutually-prime combs + series
	// allpasses) — replaces FreeVerb2: tighter/more natural, no GVerb spike,
	// trivial CPU. `reverb` = room mix; ~8ms pre-delay keeps the attack dry.
	var rmix  = reverb.clip(0, 0.9);
	var rin   = (wet[0] + wet[1]) * 0.5;
	var pre   = DelayC.ar(rin, 0.05, 0.008);
	var comb  = Mix([0.0197, 0.0237, 0.0289, 0.0331].collect { |dt|
		CombC.ar(pre, 0.05, dt, 0.55) }) * 0.25;          // short decay = room, not hall
	var tank  = LPF.ar(comb, 5000);                        // air damping
	var diff  = AllpassC.ar(AllpassC.ar(tank, 0.05, 0.0071, 0.05), 0.05, 0.0053, 0.05);
	var roomL = AllpassC.ar(diff, 0.05, 0.0119, 0.05);
	var roomR = AllpassC.ar(diff, 0.05, 0.0133, 0.05);
	var verb  = [(wet[0] * (1 - rmix)) + (roomL * rmix),
		(wet[1] * (1 - rmix)) + (roomR * rmix)];
	var w    = (width.clip(0, 1) * 0.5);
	var mid  = (verb[0] + verb[1]) * 0.5;
	var sid  = (verb[0] - verb[1]) * 0.5;
	var sig  = [mid + (sid * (0.5 + w)), mid - (sid * (0.5 + w))];
	// ONE musical tanh colour stage — more present drive (audible warmth/weight)
	sig = [(sig[0] * 1.35).tanh * 0.86, (sig[1] * 1.35).tanh * 0.86];
	// high-cut lifted 8.5k -> 12k now the saturation is gentler -> more hat air
	sig = [LPF.ar(sig[0], 12000), LPF.ar(sig[1], 12000)];
	Out.ar(out, Limiter.ar(LeakDC.ar(sig), 0.95));
}).add;
