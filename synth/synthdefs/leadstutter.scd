// leadStutter — a RHYTHMIC glitch lead for experimental electronic. A clearly
// SYNTH core (pulse + square sub + a touch of FM sparkle) chopped by a fast
// rhythmic STUTTER gate (a pulse train whose rate jitters + random per-chop
// amplitude) so it reads as rhythm/percussion first, synth second — then
// bit-reduced + sample-rate-decimated for digital grit. More rhythmic than
// synthy, but still unmistakably a synth. Gated contract (same lead params).
SynthDef(\leadStutter, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4200, decay=0.16, gate=1, maxSustain=1.8, drive=1.0,
		glide=0.02, level=1.0, pan=0|
	var v       = amp.clip(0.05, 1.0);
	var fHz     = Lag.kr(freq.clip(80, 4500), glide.clip(0, 0.1));
	var env     = EnvGen.kr(Env.asr(0.002, 1.0, 0.08, -5), gate);
	var safety  = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 4), 0.04]),
		1, doneAction: 2);
	// SYNTH core: pulse + square sub-osc + faint FM partial (still synthy)
	var core = Pulse.ar(fHz, 0.35)
		+ (Pulse.ar(fHz * 0.5, 0.5) * 0.4)
		+ (SinOsc.ar(fHz * (fmRatio + 0.01)) * fmIndex * 0.18);
	// RHYTHMIC stutter: a ~13 Hz pulse train (jittered) gates the amplitude,
	// each chop given a random level -> a stuttering rhythmic chatter, not a
	// smooth tone. A second slow gate drops whole chops for glitch syncopation.
	var rate  = 13 + LFNoise1.kr(2.5).range(-4, 7);
	var chop  = LFPulse.ar(rate, 0, LFNoise1.kr(3).range(0.4, 0.7))
		* LFNoise0.kr(rate).range(0.25, 1.0);
	var drop  = LFPulse.kr(rate / 4, 0, 0.82);          // occasional whole-chop dropout
	var sig   = core * chop * drop;
	// digital grit: bit-reduction + S&H sample-rate decimation
	sig = (sig * 5).round(1) / 5;
	sig = Latch.ar(sig, Impulse.ar(5500 + LFNoise1.kr(4).range(-2200, 2600)));
	sig = RLPF.ar(sig, (cutoff * (0.6 + v)).clip(400, 8000), 0.4);
	sig = ((sig * (1 + drive * 0.4)).tanh) * 0.7;
	sig = LPF.ar(sig, 3400);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.006),
		pan.clip(-1, 1) * 0.35) * env * safety * amp * 2.0 * level);
}).add;
