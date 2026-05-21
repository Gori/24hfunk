// leadVox — ROBOT VOCAL: plays a Kokoro-rendered word buffer (from a
// ~scratchBufs slot, chosen by the router from the note octave) and robotizes
// it: ring-modulation by a carrier TUNED to the note (pitched metallic /
// vocoder buzz) + amplitude bitcrush + sample-rate reduction + drive. The
// electro genre triggers one word per beat (canned "robotvox" feel), so the
// phrase reads out word-by-word, on the grid, repeating across the section.
// Voice-stealing mono, self-frees. Same gated contract as leadScratch.
SynthDef(\leadVox, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.2, gate=1, t_trig=1, maxSustain=1.0,
		drive=1.0, glide=0.02, level=1.0, pan=0, buf=0, beatHz=2|
	// the note octave carries the WORD SLOT (router picks the buffer); the
	// pitch-class 0..11 sets the SUNG tone in a low robot register.
	var midi    = freq.cpsmidi;
	var deg     = (midi - 60).round % 12;
	var carFreq = (44 + deg).midicps;                  // ~G#2..G3 robot register
	// play the word buffer once per note (retrigger on gate)
	var play    = PlayBuf.ar(1, buf, BufRateScale.kr(buf), trigger: gate,
		startPos: 0, loop: 0);
	// ring-mod carrier: sine + square = classic pitched vocoder buzz
	var car     = (SinOsc.ar(carFreq) * 0.6) + (Pulse.ar(carFreq, 0.5) * 0.4);
	var ring    = play * car;
	var env     = EnvGen.kr(Env.asr(0.004, 1.0, 0.05, -3), gate, doneAction: 2);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 3), 0.05]),
		1, doneAction: 2);
	// blend mostly ring-mod (robotic) with a touch of dry for intelligibility
	var sig     = (ring * 0.85) + (play * 0.15);
	sig = sig.round(0.08);                             // amplitude bitcrush
	sig = Latch.ar(sig, Impulse.ar(13000));            // sample-rate reduction
	sig = LPF.ar(sig, cutoff.clip(800, 9000));
	sig = ((sig * (1 + drive * 0.5)).tanh) * 0.7;
	Out.ar(out, Pan2.ar(sig, pan.clip(-1, 1)) * env * safety * amp * 2.0 * level);
}).add;
