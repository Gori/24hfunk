// kick — clean punchy digital: tight pitch-drop sub (kept undistorted for a
// solid low end) + short body + crisp HPF beater click. Saturation only on the
// body so the sub stays round. params: amp, freq, fmRatio, fmIndex, decay, drive, click, pan
SynthDef(\kick, { |out=0, amp=0.95, freq=49, fmRatio=1.0, fmIndex=1.2, decay=0.3, drive=2.2, click=0.5, pan=0|
	var f0   = freq * 0.66;                       // deeper fundamental
	var pEnv = EnvGen.kr(Env([6.5, 1.5, 1], [0.0035, decay * 0.32], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0008, decay * 1.35, 1, -5.5), doneAction: 2);
	var f    = f0 * pEnv;
	var sub  = SinOsc.ar(f) + (SinOsc.ar(f0) * 0.45);   // sustained deep layer
	var body = SinOsc.ar(f * 1.55) * EnvGen.kr(Env.perc(0.001, decay * 0.5, 1, -7));
	var clk  = HPF.ar(WhiteNoise.ar, 3500)
	           * EnvGen.kr(Env.perc(0.0002, 0.013, 1, -10)) * click * 1.3;
	var sig;
	body = (body * (1 + drive)).tanh * 0.4;
	sig  = LeakDC.ar((sub + body + clk).softclip);
	Out.ar(out, Pan2.ar(sig * aEnv * amp, pan));
}).add;
