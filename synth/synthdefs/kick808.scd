// kick808 — long 808-style sine boom. One-shot (doneAction:2). Same params as \kick.
SynthDef(\kick808, { |out=0, amp=0.95, freq=46, fmRatio=1.0, fmIndex=1.0, decay=0.45, drive=1.6, click=0.4, pan=0|
	var pEnv = EnvGen.kr(Env([4.5, 1.05, 1], [0.006, decay * 0.5], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.001, decay * 1.6, 1, -4), doneAction: 2);
	var f    = freq * pEnv;
	var body = SinOsc.ar(f);
	var clk  = HPF.ar(WhiteNoise.ar, 3000) * EnvGen.kr(Env.perc(0.0003, 0.012, 1, -9)) * click;
	var sig  = ((body * (1 + drive * 0.5)).tanh) + clk;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp, pan));
}).add;
