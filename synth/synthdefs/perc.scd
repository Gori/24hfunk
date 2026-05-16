// perc — tuned conga/blip: pitch-drop sine + a little noise. Pitched by \freq.
// params: amp, freq, decay, pan
SynthDef(\perc, { |out=0, amp=0.5, freq=220, decay=0.14, pan=0|
	var aEnv = EnvGen.kr(Env.perc(0.001, decay, 1, -5), doneAction: 2);
	var pEnv = EnvGen.kr(Env([2.2, 1, 1], [0.012, decay * 0.5], \exp));
	var tone = SinOsc.ar(freq.clip(80, 1200) * pEnv);
	var nz   = BPF.ar(WhiteNoise.ar, freq.clip(80, 1200) * 2, 0.6)
	           * EnvGen.kr(Env.perc(0.001, 0.03, 1, -8)) * 0.25;
	var sig  = ((tone + nz) * 1.3).tanh;
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
