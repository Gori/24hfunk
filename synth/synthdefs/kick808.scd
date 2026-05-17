// kick808 — long 808-style sine boom. One-shot. Same params as \kick (+punch).
// punch tightens the drop + lifts the click a touch; velocity adds click/drop;
// tiny per-hit drift. v~1.0 + punch~0.5 == the prior fixed sound.
SynthDef(\kick808, { |out=0, amp=0.95, freq=46, fmRatio=1.0, fmIndex=1.0, decay=0.45,
		drive=1.6, click=0.4, punch=0.5, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var pk   = 0.7 + (punch.clip(0, 1) * 0.6);
	var dr   = decay * Rand(0.96, 1.04);
	var f0   = freq * Rand(-0.04, 0.04).midiratio * 0.82;
	var pEnv = EnvGen.kr(Env([3.6 + (v * 1.8), 1.05, 1], [0.006, (dr * 0.5) / pk], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.001, dr * 1.9, 1, -4), doneAction: 2);
	var f    = f0 * pEnv;
	var body = SinOsc.ar(f) + (SinOsc.ar(f0) * 0.3);
	var cEnv = EnvGen.kr(Env.perc(0.0003, 0.012, 1, -9));
	var nz   = HPF.ar(WhiteNoise.ar, 2400 + (v * 1200)) * 0.75;
	var bea  = Ringz.ar(WhiteNoise.ar * EnvGen.kr(Env.perc(0.0001, 0.0035)),
	           (1300 + (v * 900)) * pk, 0.045) * 0.4;
	var clk  = (nz + bea) * cEnv * click * (0.4 + v * 0.6);
	var sig  = ((body * (1 + drive * 0.5)).tanh) + clk;
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp * Rand(0.97, 1.03), pan));
}).add;
