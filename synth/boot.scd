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
		var f1   = EnvGen.kr(Env([f1a, f1b, f1c], [dur * 0.5, dur * 0.5]));
		var f2   = EnvGen.kr(Env([f2a, f2b, f2c], [dur * 0.5, dur * 0.5]));
		var f3   = EnvGen.kr(Env([f3a, f3b, f3c], [dur * 0.5, dur * 0.5]));
		var env  = EnvGen.kr(
			Env([0, 1, 0.9, 0.85, 0], [0.02, dur * 0.4, dur * 0.4, (dur * 0.2).max(0.03)]),
			doneAction: 2);
		var f0   = 145 * (1 + SinOsc.kr(5.5).range(-0.012, 0.012));
		var glot = (Saw.ar(f0) * 0.6) + (Pulse.ar(f0, 0.4) * 0.3);
		var vow  = (BPF.ar(glot, f1.clip(100, 5000), 0.10) * 5.0)
			+ (BPF.ar(glot, f2.clip(200, 7000), 0.12) * 3.2)
			+ (BPF.ar(glot, f3.clip(400, 10000), 0.15) * 1.6);
		// consonant noise: head (first ~55ms) + tail (last ~80ms). Types:
		// 0 none, 1 f/s hiss (HPF), 2 g/k burst (low-mid BPF), 3 sh (mid BPF)
		var noise   = WhiteNoise.ar;
		var headEnv = EnvGen.kr(Env.perc(0.004, 0.05));
		var tailEnv = EnvGen.kr(Env([0, 0, 1, 0], [(dur - 0.10).max(0.02), 0.02, 0.08]));
		var pick    = { |sel| Select.ar(sel, [
			Silent.ar, HPF.ar(noise, 4800), BPF.ar(noise, 1700, 0.55), BPF.ar(noise, 3000, 0.4)]) };
		var sig = ((vow * 1.2).tanh * env)
			+ (pick.(head) * headEnv * 0.55)
			+ (pick.(tail) * tailEnv * 0.55);
		RecordBuf.ar(sig, buf, loop: 0, doneAction: 0);
	}).add;
	s.sync;
	(here +/+ "router.scd").load;
	"=== str synth ready ===".postln;
};
)
