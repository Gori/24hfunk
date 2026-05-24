// leadChant — plays a Kokoro-rendered VOCAL PHRASE buffer NATURALLY (NOT
// robotized like leadVox) for New Orleans bounce: the rap/roll-call chant
// "phrases played as samples." The router picks the buffer slot from the note
// octave (60-71=slot0, 72-83=slot1, ...). Light drive/compression for hyped
// energy + a gentle high-cut; the note pitch-class adds a small playback-rate
// shift so different chops sit a touch higher/lower. Voice-stealing mono,
// self-frees. Same gated/buffer contract as leadVox.
SynthDef(\leadChant, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=8000, decay=0.2, gate=1, t_trig=1, maxSustain=2.5,
		drive=1.0, glide=0.02, level=1.0, pan=0, buf=0, beatHz=2|
	// the note octave carries the buffer slot (router picks it); the pitch-class
	// (0-11) plays the sample SLOWER = pitched DOWN that many semitones (chopped-
	// &-screwed). The bounce builder always sends 2-5, so the vocal is never at
	// original tempo. 2 -> ~0.89x (2 semis down); 5 -> ~0.75x (5 semis down).
	var pc   = (freq.cpsmidi - 60).round % 12;
	var rate = BufRateScale.kr(buf) * (pc.neg.midiratio);   // <= ~+5% over an octave
	var play = PlayBuf.ar(1, buf, rate, trigger: gate, startPos: 0, loop: 0);
	var env  = EnvGen.kr(Env.asr(0.003, 1.0, 0.08, -3), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 4), 0.05]),
		1, doneAction: 2);
	var sig  = play;
	sig = (sig * (1 + (drive * 0.6))).tanh;                  // hyped chant energy
	sig = LPF.ar(sig, cutoff.clip(2000, 12000));
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * safety * amp * 2.0 * level);
}).add;
