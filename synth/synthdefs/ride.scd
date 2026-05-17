// ride — digital ride cymbal: a short stick attack + a defined inharmonic
// "ping" + a shimmering sizzle wash, with an optional ride-bell. One-shot
// (doneAction:2). Synthesised (Ringz/Pulse/noise) to match the kit aesthetic,
// no samples. params: amp decay tone(ping<->wash) bell pan. Per-hit detune /
// decay / level drift so a swing ride breathes instead of machine-gunning.
SynthDef(\ride, { |out=0, amp=0.5, decay=0.5, tone=0.4, bell=0.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var t    = tone.clip(0, 1);
	var be   = bell.clip(0, 1);
	var dr   = decay * Rand(0.9, 1.12);
	var fj   = Rand(0.98, 1.02);
	var rat  = [1.0, 2.34, 3.16, 4.21, 5.43];
	var stk  = HPF.ar(WhiteNoise.ar, 5000)
	           * EnvGen.kr(Env.perc(0.0003, 0.012, 1, -9)) * 0.5;
	var exc  = WhiteNoise.ar * EnvGen.kr(Env.perc(0.0006, 0.02));
	var ping = Mix(Ringz.ar(exc, (520 * fj) * rat, dr * 0.6))
	           * EnvGen.kr(Env.perc(0.001, dr * 0.7, 1, -3.5)) * 0.06;
	var wash = HPF.ar(Mix(Pulse.ar((430 * fj) * rat, 0.5)) * 0.05
	           + (WhiteNoise.ar * 0.18), 6500)
	           * EnvGen.kr(Env.perc(0.003, dr, 1, -2.5))
	           * SinOsc.kr(38, Rand(0, 6.283)).range(0.8, 1.0);
	var bll  = (SinOsc.ar(840 * fj) + (SinOsc.ar(1267 * fj) * 0.5))
	           * EnvGen.kr(Env.perc(0.001, dr * 1.4, 1, -2)) * 0.12 * be;
	var aEnv = EnvGen.kr(Env.perc(0.0008, dr * 1.1, 1, -2.5), doneAction: 2);
	var sig  = stk + (ping * (1 - t)) + (wash * (0.4 + t * 0.8)) + bll;
	sig = (sig * 1.4).tanh;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp * Rand(0.93, 1.07), pan));
}).add;
