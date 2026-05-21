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
	// (code 0..5 = MIDI 60..65), so a repeating phrase scratches IDENTICALLY
	// (deterministic, NOT re-randomized per note). Decode:
	//   divIdx = code % 3  -> speed: 0=8th, 1=16th, 2=32nd back-and-forth
	//   dir    = code >= 3 -> swoop direction
	var code     = (freq.cpsmidi - 60).round.clip(0, 5);
	var divIdx   = code % 3;
	var div      = Select.kr(divIdx, [2, 4, 8]);    // cycles per beat (tempo-locked)
	var gestRate = (beatHz * div).clip(1.0, 24.0);
	var sign     = ((code >= 3) * 2) - 1;           // -1 / +1, baked per note
	var gestDep  = 1.2 * sign;
	// RELEASE: after ~0.22 s the DJ "lets the record go" -> crossfade to clean
	// forward playback (rate 1) so the WORD plays out. Short chops end before
	// the ramp = pure scratch; long notes release into playback.
	var rel      = EnvGen.kr(Env([0, 0, 1], [0.22, 0.07], \lin), gate);
	var osc      = LFTri.kr(gestRate, 0);           // fixed phase -> identical repeats
	var scratchMotion = osc * gestDep;
	var motion   = (scratchMotion * (1 - rel)) + (1.0 * rel);   // -> forward play
	// pitch only encodes the gesture; the sample plays at its recorded rate
	var rate   = motion * BufRateScale.kr(buf);
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
