// lead — clean digital, now EXPRESSIVE: velocity (amp) opens the filter and
// adds grit (soft playing = mellow, hard = bright/edgy); a vibrato LFO fades
// in on held notes. Detuned-saw ensemble blended with a clean FM tone.
// `maxSustain` hard-frees the voice even with no /midi/noteoff.
// params: amp(vel), freq, fmRatio, fmIndex, detune, wave, cutoff, decay,
//         gate, maxSustain, drive, pan
SynthDef(\lead, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=0.8, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var env    = EnvGen.kr(Env.adsr(0.006, 0.10, 0.55, decay, curve: -3), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(5.6) * 0.010 * EnvGen.kr(Env([0, 0, 1], [0.16, 0.6]));
	var f      = freq * (1 + vib);
	var sp     = detune.clip(0, 0.4) * [-1, -0.45, 0.45, 1];
	var saws   = Mix(Saw.ar(f * (1 + (sp * 0.02)))) * 0.2;
	var fm     = SinOsc.ar(f + (SinOsc.ar(f * fmRatio) * fmIndex * f * 0.6));
	var sig    = (saws * (1 - wave)) + (fm * wave * 0.7);
	var cf     = (cutoff * (0.42 + v * 1.15)).clip(350, 13000);
	sig = RLPF.ar(sig, cf, 0.55);
	sig = (sig * (1 + (drive * 0.5 * (0.55 + v * 0.7)))).softclip;
	sig = LeakDC.ar(sig);
	Out.ar(out, Pan2.ar(sig * env * safety * amp, pan));
}).add;
