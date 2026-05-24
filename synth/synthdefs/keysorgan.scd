// keysOrgan — a reggae/ragga SKANK organ (Hammond / Farfisa flavour) for
// uk_jungle: drawbar harmonics (fundamental + octave + reedy 12th) plus a
// touch of Pulse for the Farfisa reed edge, a Hammond-style key-click on the
// attack, light vibrato, and a SHORT staccato/choked envelope = the offbeat
// "chick". Self-terminating (doneAction:2). Same keys param contract as
// \keys / \keysPad (amp/freq/cutoff/sus/drive/vib/pan).
SynthDef(\keysOrgan, { |out=0, amp=0.4, freq=220, cutoff=3200, sus=0.9, drive=1.0, vib=0.12, pan=0|
	var v    = amp.clip(0.05, 1.0);
	var det  = Rand(-0.008, 0.008).midiratio;
	var vibe = SinOsc.kr(5.6, Rand(0, 6.283)) * vib * 0.008;
	var f    = freq * det * (1 + vibe);
	var env  = EnvGen.kr(Env.perc(0.004, 0.2, 1, -3.5), doneAction: 2);   // choked skank "chick"
	var org  = (SinOsc.ar(f) * 0.6)
		+ (SinOsc.ar(f * 2) * 0.4)
		+ (SinOsc.ar(f * 3) * 0.24)                                       // reedy 12th
		+ (Pulse.ar(f, 0.5) * 0.12);                                      // Farfisa reed edge
	var click = HPF.ar(WhiteNoise.ar, 4000)
		* EnvGen.kr(Env.perc(0.001, 0.012, 1, -8)) * 0.14;                // Hammond key click
	var sig  = LPF.ar(org + click, cutoff.clip(800, 6000));
	sig = ((sig * (1 + (drive * 0.25))).tanh) * 0.6;
	Out.ar(out, Pan2.ar(sig * env * amp * 1.4, pan));
}).add;
