// leadRhodes — a SUSTAINED, singing FM electric-piano (Rhodes/DX7-EP) lead for
// neo-soul. 1:1 "body" FM + a high-ratio (~14:1) "tine" operator whose index is
// VELOCITY-SCALED (soft = round/creamy, hard = metallic bark) and decays fast
// (the strike), over a detuned twin for chorus shimmer. SUSTAINED amp env (sings
// while held), warm tanh, LPF opens with velocity. The opposite of a percussive
// bell — this is the neo-soul lead voice. Gated contract (same lead params).
SynthDef(\leadRhodes, { |out=0, amp=0.5, freq=440, fmRatio=1.0, fmIndex=1.0, detune=0.06,
		wave=0.5, cutoff=2600, decay=0.4, gate=1, t_trig=1, maxSustain=3.0, drive=1.0,
		glide=0.02, level=1.0, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var fHz  = Lag.kr(freq.clip(80, 2600), glide.clip(0, 0.12));
	var env  = EnvGen.kr(Env.asr(0.006, 1.0, 0.45, -3), gate);          // sustained, sings
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 6), 0.2]),
		1, doneAction: 2);
	var tineEnv = EnvGen.kr(Env.perc(0.001, 0.12, 1, -5));              // fast strike "bark"
	var idx  = (0.5 + (v * 3.5));                                       // velocity -> FM index
	var tine = SinOsc.ar(fHz * 14) * idx * 0.16 * tineEnv;
	var dr   = detune.linlin(0, 0.2, 1.004, 1.012);                    // chorus detune amount
	var b1   = SinOsc.ar(fHz + (tine * fHz));
	var b2   = SinOsc.ar((fHz * dr) + (tine * fHz)) * 0.7;
	var body = b1 + b2 + (SinOsc.ar(fHz * 2) * 0.08);
	var cf   = (cutoff * (0.5 + (v * 0.7))).clip(600, 4200);
	var sig  = LPF.ar(body, cf);
	sig = ((sig * (1 + drive * 0.2)).tanh) * 0.5;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * safety * amp * 1.8 * level);
}).add;
