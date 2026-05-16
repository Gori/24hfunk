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
	(here +/+ "router.scd").load;
	"=== str synth ready ===".postln;
};
)
