// lead — EVOLVED, but kept subtle/warm (not "overtly digital"):
//  #1 stereo super-unison: 7 gently-detuned saws splayed across the field
//  #2 per-OSCILLATOR analog drift: each voice its own slow LFNoise2 wander
//  #5 richer filter: key-tracked, own envelope, cascaded LPF (low Q -> no
//     digital whistle), a touch of drive into the filter
//  #6 musical saturation: gentle asymmetric warmth, NOT a fuzz/clip
//  #8 expressive onset glide: each note softly scoops into pitch
// `maxSustain` hard-frees the voice even with no /midi/noteoff. The pre-
// rework version is git 415cee0 (restore verbatim if ever wanted).
// params: amp(vel), freq, fmRatio, fmIndex, detune, wave, cutoff, decay,
//         gate, maxSustain, drive, glide, pan
SynthDef(\lead, { |out=0, amp=0.5, freq=440, fmRatio=2.0, fmIndex=0.8, detune=0.12,
		wave=0.4, cutoff=4600, decay=0.45, gate=1, maxSustain=6, drive=1.2,
		glide=0.03, level=1.0, pan=0|
	var v      = amp.clip(0.05, 1.0);
	var env    = EnvGen.kr(Env.perc(0.003, (decay * 1.5).clip(0.07, 0.85), 1, -4.5), gate, doneAction: 2);
	var safety = EnvGen.kr(Env([1, 1, 0], [maxSustain, 0.2], \lin), doneAction: 2);
	var vib    = SinOsc.kr(5.4) * 0.009 * EnvGen.kr(Env([0, 0, 1], [0.18, 0.65]));
	var port   = EnvGen.kr(Env([-1, 0], [glide.clip(0, 0.25) + 0.01], -4)) * 0.045;
	var det    = detune.clip(0, 0.4);
	var sprd   = #[-1, -0.62, -0.28, 0, 0.3, 0.66, 1];
	var dr     = LFNoise2.kr(#[0.21, 0.27, 0.19, 0.24, 0.30, 0.22, 0.26]) * 0.0026;
	var fc     = freq * (1 + vib + port);
	var f      = fc * (1 + (sprd * det * 0.013) + dr);
	var saws   = Saw.ar(f) * 0.13;
	var fund   = (SinOsc.ar(fc) * 0.30) + (SinOsc.ar(fc * 0.5) * 0.12);
	var fm     = SinOsc.ar(fc + (SinOsc.ar(fc * fmRatio) * fmIndex * fc * 0.55));
	var wide   = Splay.ar(saws, 0.85);
	var mid    = fund + (fm * wave * 0.65);
	var fenv   = EnvGen.kr(Env([0.45, 1, 0.7], [0.06, decay], [-3, -2]), gate);
	var cf     = ((cutoff * (0.42 + v * 0.95) * fenv) + (fc * 0.6)).clip(320, 9000);
	var lc     = (wide[0] * (1 - wave)) + mid;
	var rc     = (wide[1] * (1 - wave)) + mid;
	lc = LPF.ar(RLPF.ar(lc * (1 + drive * 0.18), cf, 0.42), (cf * 1.4).clip(320, 16000));
	rc = LPF.ar(RLPF.ar(rc * (1 + drive * 0.18), cf, 0.42), (cf * 1.4).clip(320, 16000));
	lc = ((lc + (lc * lc * 0.10)).tanh * 0.92);
	rc = ((rc + (rc * rc * 0.10)).tanh * 0.92);
	lc = LPF.ar(lc, 4000);                                 // global high-cut (lead taming)
	rc = LPF.ar(rc, 4000);
	Out.ar(out, Balance2.ar(LeakDC.ar(lc), LeakDC.ar(rc), pan.clip(-1, 1) * 0.3)
		* env * safety * amp * 2.55 * level);
}).add;
