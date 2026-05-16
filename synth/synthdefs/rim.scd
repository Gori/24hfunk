// rim — rimshot/click: short bright resonant tick.
// params: amp, freq, decay, pan
SynthDef(\rim, { |out=0, amp=0.5, freq=1700, decay=0.05, pan=0|
	var aEnv = EnvGen.kr(Env.perc(0.0002, decay, 1, -8), doneAction: 2);
	var res  = Ringz.ar(Impulse.ar(0), freq.clip(800, 3000), 0.012, 0.6)
	           + Ringz.ar(Impulse.ar(0), freq.clip(800, 3000) * 1.47, 0.008, 0.3);
	var clk  = HPF.ar(WhiteNoise.ar, 4000) * EnvGen.kr(Env.perc(0.0002, 0.006, 1, -9));
	var sig  = (res + clk);
	sig = (sig * 2.0).tanh;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
