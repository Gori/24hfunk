// kickHard — short hard distorted punch. One-shot. Same params as \kick.
SynthDef(\kickHard, { |out=0, amp=0.95, freq=52, fmRatio=1.0, fmIndex=2.0, decay=0.24, drive=4.0, click=0.6, pan=0|
	var f0   = freq * 0.6;                          // deeper fundamental
	var pEnv = EnvGen.kr(Env([9, 1.6, 1], [0.003, decay * 0.3], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0006, decay * 1.3, 1, -6), doneAction: 2);
	var f    = f0 * pEnv;
	var sub  = SinOsc.ar(f0) * EnvGen.kr(Env.perc(0.001, decay * 1.7, 1, -4));
	var body = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fmIndex * f));
	var clk  = HPF.ar(WhiteNoise.ar, 4000) * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -10)) * click * 1.4;
	var sig  = ((body * (1 + drive)).tanh * 0.7) + clk;
	// clean deep sub UNDER the punch (added post-clip so it isn't crushed)
	sig = ((sig * 1.2).clip2(1.0) * 0.85) + (sub * 0.9);
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp, pan));
}).add;
