// leadScratch — REAL buffer-scratching of a procedural vocal sample. The
// boot script renders a vowel "ahh" into ~scratchBuf; the router passes its
// bufnum here. Each note plays the buffer with a bipolar rate driven by the
// scratch-motion envelope: rate > 0 = forward (pitch up), rate < 0 = reverse
// (the backspin). Because we're moving a fixed RECORDING back and forth, the
// pitch+formant shift is physically correct = it actually sounds scratched.
// Friction noise + an attack "chk" add the groove drag and crossfader cut.
// Voice-stealing, self-frees. Gated contract.
SynthDef(\leadScratch, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=1.0, detune=0.12,
		wave=0.5, cutoff=4000, decay=0.2, gate=1, t_trig=1, maxSustain=1.0,
		drive=1.0, glide=0.02, level=1.0, pan=0, buf=0, beatHz=2|
	var v      = amp.clip(0.05, 1.0);
	// The scratch GESTURE is ENCODED in the incoming pitch by the pattern
	// (code 0..7 = MIDI 60..67), so a repeating phrase scratches IDENTICALLY
	// (deterministic, NOT re-randomized per note). Decode:
	//   divIdx = code % 4  -> speed: 0=quarter,1=8th,2=triplet,3=16th wobble
	//   dir    = code >= 4 -> swoop direction
	// Slower set than before (quarter/8th/16th, not 8th/16th/32nd).
	var code     = (freq.cpsmidi - 60).round.clip(0, 7);
	var divIdx   = code % 4;
	var div      = Select.kr(divIdx, [1, 2, 3, 4]); // cycles per beat (tempo-locked)
	var gestRate = (beatHz * div).clip(0.8, 16.0);
	var sign     = ((code >= 4) * 2) - 1;           // -1 / +1, baked per note
	// pitch tracks record VELOCITY: a faster gesture swings the rate WIDER,
	// so fast scratches reach HIGHER pitch (like a real turntable), not just
	// swoop the same range faster. spd scales the throw by gesture speed
	// (div/2: quarter 0.5x .. 16th 2x).
	var spd      = div / 2.0;
	var gestDep  = 1.2 * sign * spd;
	// RELEASE: after ~0.22 s the DJ "lets the record go" -> crossfade to clean
	// forward playback (rate 1) so the WORD plays out. Short chops end before
	// the ramp = pure scratch; long notes release into playback.
	var rel      = EnvGen.kr(Env([0, 0, 1], [0.22, 0.07], \lin), gate);
	var osc      = LFTri.kr(gestRate, 0);           // fixed phase -> identical repeats
	var scratchMotion = osc * gestDep;
	var motion   = (scratchMotion * (1 - rel)) + (1.0 * rel);   // -> forward play
	// pitch only encodes the gesture; the sample plays at its recorded rate.
	// clip to keep the fastest swings musical (~±1.5 octaves).
	var rate   = (motion * BufRateScale.kr(buf)).clip(-3.0, 3.0);
	// read the vocal buffer; reset into the vowel body on each note
	var scr    = PlayBuf.ar(1, buf, rate, trigger: gate,
		startPos: BufFrames.kr(buf) * 0.20, loop: 1);
	// friction: noise band tracking the scratch motion = the groove drag.
	// Fades out on release so the played-out vocal is clean.
	var fHz    = (220 * (2 ** scratchMotion)).clip(80, 4000);
	var friction = BPF.ar(PinkNoise.ar, (fHz * 2).clip(180, 6000), 0.5) * 0.85 * (1 - rel);
	// attack "chk" — the crossfader cut
	var click  = BPF.ar(WhiteNoise.ar, 1500, 0.5)
		* EnvGen.kr(Env.perc(0.0005, 0.025, 1, -5)) * 1.4;
	// amp: sustains while gate held (long notes play out), releases on gate off
	var env    = EnvGen.kr(Env.asr(0.004, 1.0, 0.06, -3), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain.clip(0.05, 3), 0.05]),
		1, doneAction: 2);
	var sig    = (scr * 1.5) + (friction * 0.4) + click;
	sig = (sig * (1 + drive * 0.8)).tanh * 0.7;
	sig = LPF.ar(sig, 3600);
	Out.ar(out, Balance2.ar(sig, DelayC.ar(sig, 0.02, 0.004),
		pan.clip(-1, 1) * 0.4) * env * safety * amp * 2.3 * level);
}).add;
