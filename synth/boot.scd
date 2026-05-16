// boot.scd — entrypoint: `sclang synth/boot.scd`
// Boots the default server, loads all SynthDefs, then the OSC router.
(
var here = thisProcess.nowExecutingPath.dirname;   // .../str/synth
var s = Server.default;

s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;
s.options.memSize = 65536;                          // headroom for FreeVerb/Comb

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
