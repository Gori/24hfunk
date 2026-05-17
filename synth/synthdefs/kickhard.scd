// kickHard — short hard distorted punch. One-shot. Same params as \kick.
// Velocity drives FM bite + click + drop (soft hits cleaner, hard hits
// nastier); small per-hit pitch/decay/level drift. v~1.0 == the old sound.
SynthDef(\kickHard, { |out=0, amp=0.95, freq=52, fmRatio=1.0, fmIndex=2.0, decay=0.24, drive=4.0, click=0.6, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var dr   = decay * Rand(0.96, 1.04);
	var f0   = freq * Rand(-0.04, 0.04).midiratio * 0.6;
	var pEnv = EnvGen.kr(Env([7.5 + (v * 1.5), 1.6, 1], [0.003, dr * 0.3], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0006, dr * 1.3, 1, -6), doneAction: 2);
	var f    = f0 * pEnv;
	var fi   = fmIndex * (0.55 + v * 0.45);              // vel -> FM bite
	var sub  = SinOsc.ar(f0) * EnvGen.kr(Env.perc(0.001, dr * 1.7, 1, -4));
	var body = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fi * f));
	var clk  = HPF.ar(WhiteNoise.ar, 3200 + (v * 1400))
	           * EnvGen.kr(Env.perc(0.0002, 0.01, 1, -10)) * click * (0.9 + v * 0.5);
	var sig  = ((body * (1 + drive)).tanh * 0.7) + clk;
	// clean deep sub UNDER the punch (added post-clip so it isn't crushed)
	sig = ((sig * 1.2).clip2(1.0) * 0.85) + (sub * 0.9);
	Out.ar(out, Pan2.ar(LeakDC.ar(sig) * aEnv * amp * Rand(0.97, 1.03), pan));
}).add;
