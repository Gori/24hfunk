// duckTrig — fired by the router on every kick note-on. Writes a 0..1 kick
// envelope to the sidechain control bus (ReplaceOut so overlapping kicks
// re-trigger rather than accumulate). The bass FX (\fx) reads this bus and
// ducks by its per-genre `duck` depth. Lives in the instrument group so it
// runs BEFORE the FX synths read the bus (no one-block latency). Self-frees.
SynthDef(\duckTrig, { |bus=0, atk=0.003, rel=0.16|
	var env = EnvGen.kr(Env.perc(atk, rel, 1, -4), doneAction: 2);
	ReplaceOut.kr(bus, env);
}).add;
