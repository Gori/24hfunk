// router.scd — OSC handlers: /midi/* in, /synth/param in, /vis/* out to bridge.
// Loaded by boot.scd after SynthDefs are added and the server is booted.

(
var visHost = "127.0.0.1";
var visPort = (("VIS_OSC_PORT".getenv) ? "57130").asInteger;
~bridge = NetAddr(visHost, visPort);

// --- routing config ---
~chanMap = IdentityDictionary.new;          // MIDI channel -> synth symbol
~chanMap[0] = \bass;
~chanMap[1] = \lead;
~chanMap[2] = \keys;                          // comp/pad — self-terminating
~chanMap[9] = \drums;                        // pitch-routed to kick/snare/hat
~gated     = Set[\bass, \lead];              // synths that hold a gate (need noteoff)

~params = IdentityDictionary.new;            // synth -> IdentityDictionary(param->value)
[\kick, \snare, \hat, \ohat, \clap, \rim, \perc, \bass, \lead, \keys].do { |k|
	~params[k] = IdentityDictionary.new };
~fxParams = IdentityDictionary[\reverb -> 0.35, \delay -> 0.22, \delayTime -> 0.375];

~active = IdentityDictionary.new;            // "chan_pitch" -> Synth (gated only)
~mono   = IdentityDictionary.new;            // persistent mono voices (glide), by synth
~monoFor = IdentityDictionary.new;           // channel -> mono synth (glide voice)
~monoFor[0] = \bass;

~drumFor = { |pitch|
	case
	{ #[35, 36].includes(pitch) } { \kick }
	{ pitch == 37 } { \rim }
	{ #[38, 40].includes(pitch) } { \snare }
	{ pitch == 39 } { \clap }
	{ #[42, 44].includes(pitch) } { \hat }
	{ pitch == 46 } { \ohat }
	{ #[75, 76, 77].includes(pitch) } { \perc }
	{ \hat };
};

// --- audio graph: instruments -> ~fxBus -> \fx -> out 0 ---
~fxBus   = Bus.audio(Server.default, 2);
~instGrp = Group.new(Server.default);
~fxSynth = Synth.tail(Server.default, \fx, [\in, ~fxBus.index, \out, 0]);

// --- tempo / beat clock ---
~bpm   = 78;
~clock = TempoClock(~bpm / 60);
~bar   = 0;
~step  = 0;                                  // 16th index within bar (0..15)
~beatTask = Routine({
	loop {
		~bridge.sendMsg("/vis/beat", ~bar, ~step, ~bpm);
		~step = ~step + 1;
		if(~step >= 16) { ~step = 0; ~bar = ~bar + 1 };
		0.25.wait;                            // quarter-beat = one 16th
	}
}).play(~clock);

// --- helpers ---
~argsFor = { |synth, freq, vel|
	var a = [\freq, freq, \amp, vel, \out, ~fxBus.index];
	var p = ~params[synth];
	if(p.notNil) { p.keysValuesDo { |k, v| a = a ++ [k, v] } };
	a;
};

// --- /midi/noteon  ch pitch vel t_ms ---
OSCdef(\noteon, { |msg|
	var ch = msg[1].asInteger, pitch = msg[2].asInteger;
	var vel = msg[3].asFloat, synth, freq, node, key;
	synth = ~chanMap[ch];
	if(synth.notNil) {
		freq = pitch.midicps;
		if(synth == \drums) {
			synth = ~drumFor.(pitch);
			Synth(synth, ~argsFor.(synth, freq, vel), ~instGrp);
		} {
			if(~monoFor[ch] == synth) {
				// persistent MONO voice -> portamento between notes
				node = ~mono[synth];
				if(node.isNil) {
					node = Synth(synth, ~argsFor.(synth, freq, vel)
						++ [\gate, 1, \t_trig, 1], ~instGrp);
					~mono[synth] = node;
				} {
					node.set(\freq, freq, \amp, vel, \gate, 1, \t_trig, 1);
				};
			} {
				node = Synth(synth, ~argsFor.(synth, freq, vel) ++ [\gate, 1], ~instGrp);
				if(~gated.includes(synth)) {
					key = (ch.asString ++ "_" ++ pitch.asString).asSymbol;
					~active[key] = node;
				};
			};
		};
		// rebroadcast to the visualizer bridge
		~bridge.sendMsg("/vis/noteon", ch, pitch, vel, (~clock.beats % 1));
	};
}, '/midi/noteon');

// --- /midi/noteoff  ch pitch t_ms ---
OSCdef(\noteoff, { |msg|
	var ch = msg[1].asInteger, pitch = msg[2].asInteger;
	var ms = ~monoFor[ch], key, node;
	if(ms.notNil and: { ~mono[ms].notNil }) {
		~mono[ms].set(\gate, 0);             // release but KEEP node (glide cont.)
	} {
		key = (ch.asString ++ "_" ++ pitch.asString).asSymbol;
		node = ~active[key];
		if(node.notNil) { node.set(\gate, 0); ~active.removeAt(key) };
	};
}, '/midi/noteoff');

// --- /midi/tempo  bpm ---
OSCdef(\tempo, { |msg|
	~bpm = msg[1].asFloat.clip(40, 200);
	~clock.tempo = ~bpm / 60;
}, '/midi/tempo');

// --- /midi/bar  idx  (optional resync) ---
OSCdef(\barmsg, { |msg| ~bar = msg[1].asInteger; ~step = 0; }, '/midi/bar');

// --- /synth/param  synthName paramName value ---
OSCdef(\param, { |msg|
	var synth = msg[1].asString.asSymbol;
	var param = msg[2].asString.asSymbol;
	var value = msg[3].asFloat;
	if(synth == \fx) {
		~fxParams[param] = value;
		~fxSynth.set(param, value);
	} {
		if(~params[synth].notNil) { ~params[synth][param] = value };
	};
}, '/synth/param');

~releaseAll = {
	~active.values.do { |n| n.set(\gate, 0) };
	~active.clear;
	// free mono voices so the new section's bass timbre/params take effect
	~mono.values.do { |n| n.free };
	~mono.clear;
};

// --- /section/begin  id  : release held notes so drones don't cross sections ---
OSCdef(\sectionbegin, { |msg|
	("[section] " ++ msg[1]).postln;
	~releaseAll.value;
}, '/section/begin');

// --- /panic : hard-stop everything currently sounding ---
OSCdef(\panic, { |msg|
	~active.clear;
	~mono.clear;                 // refs become invalid once the group is freed
	~instGrp.freeAll;
	"[panic] freed all instrument nodes".postln;
}, '/panic');

"router.scd loaded — listening on langPort %, vis -> %:%".format(
	NetAddr.langPort, visHost, visPort).postln;
)
