// kick — clean punchy digital: tight pitch-drop sub (kept undistorted for a
// solid low end) + short body + crisp HPF beater click. Saturation only on the
// body so the sub stays round. params: amp, freq, fmRatio, fmIndex, decay, drive, click, pan
// Velocity (amp) shapes timbre: harder hits drop further + brighter/louder
// click; soft hits stay round. Every hit drifts slightly (pitch/decay/level)
// so no two kicks are spectrally identical. v~1.0 == the old fixed sound.
SynthDef(\kick, { |out=0, amp=0.95, freq=49, fmRatio=1.0, fmIndex=1.2, decay=0.3, drive=2.2, click=0.5, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var dr   = decay * Rand(0.94, 1.06);                // per-hit decay drift
	var f0   = freq * Rand(-0.06, 0.06).midiratio * 0.66;
	var pEnv = EnvGen.kr(Env([5.0 + (v * 2.5), 1.5, 1], [0.0035, dr * 0.32], \exp));
	var aEnv = EnvGen.kr(Env.perc(0.0008, dr * 1.35, 1, -5.5), doneAction: 2);
	var f    = f0 * pEnv;
	var sub  = SinOsc.ar(f) + (SinOsc.ar(f0) * 0.45);   // sustained deep layer
	var body = SinOsc.ar(f * 1.55) * EnvGen.kr(Env.perc(0.001, dr * 0.5, 1, -7));
	var ck   = click * (0.5 + v * 0.8) * Rand(0.88, 1.12) * 1.3;
	var clk  = HPF.ar(WhiteNoise.ar, 2700 + (v * 1400))
	           * EnvGen.kr(Env.perc(0.0002, 0.013, 1, -10)) * ck;
	var sig;
	body = (body * (1 + drive)).tanh * 0.4;
	sig  = LeakDC.ar((sub + body + clk).softclip);
	Out.ar(out, Pan2.ar(sig * aEnv * amp * Rand(0.96, 1.04), pan));
}).add;
