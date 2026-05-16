// clap — 808-style: 3 fast noise bursts + diffuse tail, band-passed.
// params: amp, decay(tail), tone(center Hz scale), pan
SynthDef(\clap, { |out=0, amp=0.6, decay=0.22, tone=1.0, pan=0|
	var burst = EnvGen.kr(Env(
		[0, 1, 0.25, 1, 0.25, 1, 0.5, 0],
		[0.001, 0.010, 0.001, 0.010, 0.001, 0.010, decay],
		[-2, -3, -2, -3, -2, -3, -4]), doneAction: 2);
	var nz  = WhiteNoise.ar;
	var sig = BPF.ar(nz, (1250 * tone).clip(600, 3000), 0.55) * 2.0;
	sig = sig + (BPF.ar(nz, (2100 * tone).clip(900, 5000), 0.7) * 0.5);
	sig = (sig * burst * 1.2).tanh;
	Out.ar(out, Pan2.ar(sig * amp, pan));
}).add;
