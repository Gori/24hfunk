// kickHard — short hard distorted punch. One-shot. Same params as \kick.
SynthDef(\kickHard, { |out=0, amp=0.95, freq=52, fmRatio=1.0, fmIndex=2.0, decay=0.24, drive=4.0, click=0.6, pan=0|
	var pEnv = EnvGen.kr(Env([9, 1.6, 1], [0.003, decay * 0.3], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0006, decay, 1, -6), doneAction: 2);
	var f    = freq * pEnv;
	var body = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fmIndex * f));
	var clk  = HPF.ar(WhiteNoise.ar, 4000) * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -10)) * click * 1.4;
	var sig  = ((body * (1 + drive)).tanh * 0.8) + clk;
	sig = (sig * 1.3).clip2(1.0);
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp, pan));
}).add;
