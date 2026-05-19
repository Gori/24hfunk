// kickHard — short hard distorted punch. One-shot. Same params as \kick (+punch).
// Velocity drives FM bite + click + drop; punch tightens the drop + beater;
// small per-hit drift. v~1.0 + punch~0.5 == the prior fixed sound.
SynthDef(\kickHard, { |out=0, amp=0.95, freq=52, fmRatio=1.0, fmIndex=2.0, decay=0.24,
		drive=4.0, click=0.6, punch=0.5, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var pk   = 0.7 + (punch.clip(0, 1) * 0.6);
	var dr   = decay * Rand(0.96, 1.04);
	var f0   = freq * Rand(-0.04, 0.04).midiratio * 0.6;
	var pEnv = EnvGen.kr(Env([7.5 + (v * 1.5), 1.6, 1], [0.003, (dr * 0.3) / pk], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0006, dr * 1.3, 1, -6), doneAction: 2);
	var f    = f0 * pEnv;
	var fi   = fmIndex * (0.55 + v * 0.45);              // vel -> FM bite
	var sub  = (SinOsc.ar(f0) + (SinOsc.ar(f0 * 1.5) * 0.6))
	           * EnvGen.kr(Env.perc(0.001, dr * 1.9, 1, -3.5));
	var body = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fi * f));
	var cEnv = EnvGen.kr(Env.perc(0.0002, 0.01, 1, -10));
	var nz   = HPF.ar(WhiteNoise.ar, 3200 + (v * 1400)) * 0.7;
	var bea  = Ringz.ar(WhiteNoise.ar * EnvGen.kr(Env.perc(0.0001, 0.0035)),
	           (1900 + (v * 1300)) * pk, 0.04) * 0.55;
	var clk  = (nz + bea) * cEnv * click * (0.9 + v * 0.5);
	var sig  = ((body * (1 + drive)).tanh * 0.7) + clk;
	// clean deep sub UNDER the punch (added post-clip so it isn't crushed)
	sig = ((sig * 1.2).clip2(1.0) * 0.85) + (sub * 1.2);
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp * Rand(0.97, 1.03), pan));
}).add;
