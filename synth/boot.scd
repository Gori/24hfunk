// boot.scd — entrypoint: `sclang synth/boot.scd`
// Boots the default server, loads all SynthDefs, then the OSC router.
(
var here = thisProcess.nowExecutingPath.dirname;   // .../str/synth
var s = Server.default;
var dev = "STR_AUDIO_DEVICE".getenv;               // e.g. "BlackHole 16ch"

s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;
s.options.memSize = 65536;                          // headroom for FreeVerb/Comb
// for streaming: route audio to a capture device (BlackHole / Multi-Output)
if(dev.notNil and: { dev.isEmpty.not }) {
	s.options.device = dev;
	("[synth] output device -> " ++ dev).postln;
};

s.waitForBoot {
	(here +/+ "synthdefs/*.scd").pathMatch.do { |f|
		f.load;
		("[synthdef] loaded " ++ PathName(f).fileName).postln;
	};
	s.sync;
	// --- procedural vocal sample for the scratch lead (buffer-scratching) ---
	// Synthesize a vocal WORD into a buffer; leadScratch then PlayBufs it with
	// rate-modulation = real turntable scratching. The word is a 3-frame
	// formant trajectory (F1/F2/F3 glide) + optional head/tail consonant
	// noise. router.scd holds the word recipes (~scratchWords) and re-renders
	// on /scratch/word. Stays hermetic (no files). Default render = "ahh".
	~scratchBuf = Buffer.alloc(s, (s.sampleRate * 0.6).asInteger, 1);
	SynthDef(\_vocalRender, { |buf = 0, dur = 0.42,
		f1a = 700, f1b = 700, f1c = 700,
		f2a = 1100, f2b = 1100, f2c = 1100,
		f3a = 2600, f3b = 2600, f3c = 2600,
		head = 0, tail = 0|
		// formants glide start->mid->end (sin shape = smoother vowel motion)
		var f1   = EnvGen.kr(Env([f1a, f1b, f1c], [dur * 0.45, dur * 0.55], \sin));
		var f2   = EnvGen.kr(Env([f2a, f2b, f2c], [dur * 0.45, dur * 0.55], \sin));
		var f3   = EnvGen.kr(Env([f3a, f3b, f3c], [dur * 0.45, dur * 0.55], \sin));
		var env  = EnvGen.kr(
			Env([0, 1, 1, 0.9, 0], [0.02, dur * 0.35, dur * 0.4, (dur * 0.23).max(0.03)], \sin),
			doneAction: 2);
		// natural pitch contour (rise then declination) + vibrato — more vocal
		var f0   = EnvGen.kr(Env([128, 162, 138], [dur * 0.30, dur * 0.70], \sin))
			* (1 + SinOsc.kr(5.5).range(-0.010, 0.010));
		// glottal source: saw rolled off ~-12dB/oct (vocal spectrum) + a little
		// pulse for buzz. Sharper formants (low rq) = clearer, more word-like.
		var glot = LPF.ar(Saw.ar(f0), 4200) + (Pulse.ar(f0, 0.35) * 0.18);
		var vow  = (BPF.ar(glot, f1.clip(120, 5000), 0.085) * 6.0)
			+ (BPF.ar(glot, f2.clip(200, 7000), 0.095) * 4.0)
			+ (BPF.ar(glot, f3.clip(400, 9500), 0.110) * 2.2)
			+ (BPF.ar(glot, 3400,               0.130) * 0.8);   // F4 sheen
		// consonant noise: head (first ~60ms) + tail (last ~95ms). Types:
		// 0 none, 1 f/s hiss (HPF), 2 g/k burst (low-mid), 3 sh (mid BPF)
		var noise   = WhiteNoise.ar;
		var headEnv = EnvGen.kr(Env([0, 1, 0], [0.008, 0.055], \sin));
		var tailEnv = EnvGen.kr(Env([0, 0, 1, 0], [(dur - 0.11).max(0.02), 0.03, 0.085], \sin));
		var pick    = { |sel| Select.ar(sel, [
			Silent.ar,
			HPF.ar(noise, 5200) * 0.9,                       // 1: f / s hiss
			LPF.ar(BPF.ar(noise, 1500, 0.7), 2600) * 1.1,    // 2: g / k burst
			BPF.ar(noise, 2900, 0.5) * 1.0]) };              // 3: sh
		var sig = ((vow * 1.25).tanh * env)
			+ (pick.(head) * headEnv * 0.6)
			+ (pick.(tail) * tailEnv * 0.6);
		RecordBuf.ar(sig, buf, loop: 0, doneAction: 0);
	}).add;
	s.sync;
	(here +/+ "router.scd").load;
	"=== str synth ready ===".postln;
};
)
