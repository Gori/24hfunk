// Reproduces the drone bug condition: many gated noteons, NO noteoff.
// Asserts the safety envelope frees them so only the persistent \fx remains.
(
var here = thisProcess.nowExecutingPath.dirname +/+ "../../synth";
var s = Server.default;
s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;
s.options.memSize = 65536;

s.waitForBoot {
	var me;
	(here +/+ "synthdefs/*.scd").pathMatch.do { |f| f.load };
	s.sync;
	(here +/+ "router.scd").load;
	s.sync;
	me = NetAddr("127.0.0.1", NetAddr.langPort);

	Routine({
		"[drone-test] firing 8 gated notes with NO noteoff".postln;
		8.do { |i|
			me.sendMsg("/midi/noteon", 0, 40 + i, 0.8, 0.0);   // bass
			me.sendMsg("/midi/noteon", 1, 60 + i, 0.7, 0.0);   // lead
			0.1.wait;
		};
		1.wait;
		s.sync;
		("[drone-test] numSynths after 1s (expect > 1): " ++ s.numSynths).postln;
		8.wait;                                                 // > maxSustain(6)
		s.sync;
		("[drone-test] numSynths after 9s (expect 1 = only fx): " ++ s.numSynths).postln;
		if(s.numSynths <= 1) {
			"[drone-test] PASS — safety envelope freed all held notes".postln;
		} {
			("[drone-test] FAIL — " ++ s.numSynths ++ " synths still alive").postln;
		};
		0.5.wait;
		0.exit;
	}).play;
};
)
