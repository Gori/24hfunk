// lead — clean digital, now EXPRESSIVE: velocity (amp) opens the filter and
// adds grit (soft playing = mellow, hard = bright/edgy); a vibrato LFO fades
// in on held notes. Detuned-saw ensemble blended with a clean FM tone.
// `maxSustain` hard-frees the voice even with no /midi/noteoff.
// params: amp(vel), freq, fmRatio, fmIndex, detune, wave, cutoff, decay,
//         gate, maxSustain, drive, pan
SynthDef(\lead, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=0.8, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2, pan=0|
	var v      = amp.clip(0.05, 1.0);
	// softer & more organic: gentler attack, slightly longer release
	var env    = EnvGen.kr(Env.adsr(0.010, 0.11, 0.58, decay * 1.12, curve: -2), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(5.4) * 0.009 * EnvGen.kr(Env([0, 0, 1], [0.18, 0.65]));
	// subtle organic pitch drift so held notes aren't perfectly static
	var drift  = LFNoise2.kr(0.25) * 0.003;
	var f      = freq * (1 + vib + drift);
	var sp     = detune.clip(0, 0.4) * [-1, -0.45, 0.45, 1];
	// saw ensemble with the harsh top gently rolled off + a little sine body
	var saws   = LPF.ar(Mix(Saw.ar(f * (1 + (sp * 0.02)))), (f * 8 + 2200).clip(900, 11000)) * 0.19;
	var fund   = SinOsc.ar(f) * 0.28;
	var fm     = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fmIndex * f * 0.55));
	var sig    = ((saws + fund) * (1 - wave)) + (fm * wave * 0.65);
	var cf     = (cutoff * (0.40 + v * 1.05)).clip(340, 11000);
	sig = RLPF.ar(sig, cf, 0.40);
	sig = (sig * (1 + (drive * 0.40 * (0.55 + v * 0.6)))).softclip;
	sig = LeakDC.ar(sig);
	// lead mix trim — lead sat too hot vs drums/bass across genres (tune here)
	Out.ar(out, Pan2.ar(sig * env * safety * amp * 0.85, pan));
}).add;
