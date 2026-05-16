// sc-selftest.scd — boots, loads defs+router, triggers each instrument, exits.
// Run: /Applications/SuperCollider.app/Contents/MacOS/sclang scripts/smoke/sc-selftest.scd
(
var here = thisProcess.nowExecutingPath.dirname +/+ "../../synth";
var s = Server.default;
s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;
s.options.memSize = 65536;

s.waitForBoot {
	(here +/+ "synthdefs/*.scd").pathMatch.do { |f| f.load };
	s.sync;
	(here +/+ "router.scd").load;
	s.sync;
	"=== selftest: triggering instruments ===".postln;

	Routine({
		"kick".postln;  Synth(\kick,  [\out, ~fxBus.index]);            1.wait;
		"snare".postln; Synth(\snare, [\out, ~fxBus.index]);            1.wait;
		"hat".postln;   Synth(\hat,   [\out, ~fxBus.index]);            1.wait;
		"bass".postln;  Synth(\bass,  [\freq, 55,  \out, ~fxBus.index, \gate, 1]); 1.5.wait;
		"lead".postln;  Synth(\lead,  [\freq, 440, \out, ~fxBus.index, \gate, 1]); 1.5.wait;
		"=== selftest OK ===".postln;
		0.5.wait;
		0.exit;
	}).play;
};
)
