// Compile-check all SynthDefs WITHOUT booting a server (no port conflict with
// a running stack). UGen-graph/syntax errors surface at SynthDef build time.
(
var here = thisProcess.nowExecutingPath.dirname +/+ "../../synth";
var files = (here +/+ "synthdefs/*.scd").pathMatch;
var ok = 0, fail = 0;
files.do { |f|
	try {
		thisProcess.interpreter.executeFile(f);
		("OK    " ++ PathName(f).fileName).postln;
		ok = ok + 1;
	} { |err|
		("FAIL  " ++ PathName(f).fileName ++ " :: " ++ err.errorString).postln;
		fail = fail + 1;
	};
};
("=== compile: " ++ ok ++ " ok, " ++ fail ++ " fail ===").postln;
0.exit;
)
