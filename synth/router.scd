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
~chanMap[3] = \perc2;                         // dedicated percussion layer
~chanMap[9] = \drums;                        // pitch-routed to kick/snare/hat
~gated     = Set[\bass, \lead];              // ROLES that hold a gate (need noteoff)
// role -> actual SynthDef (genre picks variants via /synth/map). Default = self.
~roleMap = IdentityDictionary.new;
[\kick, \snare, \hat, \ohat, \clap, \rim, \perc, \ride, \bass, \lead, \keys].do { |r|
	~roleMap[r] = r };

~params = IdentityDictionary.new;            // synth -> IdentityDictionary(param->value)
[\kick, \snare, \hat, \ohat, \clap, \rim, \perc, \ride, \bass, \lead, \keys].do { |k|
	~params[k] = IdentityDictionary.new };

~active = IdentityDictionary.new;            // "chan_pitch" -> Synth (gated only)
~mono   = IdentityDictionary.new;            // persistent mono voices (glide), by synth
~monoFor = IdentityDictionary.new;           // channel -> mono synth (glide voice)
~monoFor[0] = \bass;
// def-keyed mono routing — synthDefs in this set get the persistent-voice
// path (portamento via Lag.kr(\freq) + filter-env retrigger via \t_trig)
// regardless of channel. Used for genre-chosen leads that need glide
// without forcing ALL leads on CH_LEAD to be mono.
~monoDef = Set[\leadMoog];

~drumFor = { |pitch|
	case
	{ #[35, 36].includes(pitch) } { \kick }
	{ pitch == 37 } { \rim }
	{ #[38, 40].includes(pitch) } { \snare }
	{ pitch == 39 } { \clap }
	{ #[42, 44].includes(pitch) } { \hat }
	{ pitch == 46 } { \ohat }
	{ #[51, 53, 59].includes(pitch) } { \ride }
	{ #[75, 76, 77].includes(pitch) } { \perc }
	{ \hat };
};

// --- audio graph: instruments -> per-track FX bus -> \fx -> MASTER -> 0 ---
// three independent FX chains, then a glue compressor + brickwall on the
// summed master mix.
~instGrp   = Group.new(Server.default);
~masterBus = Bus.audio(Server.default, 2);
~fxBuses   = IdentityDictionary.new;
~fxSynths  = IdentityDictionary.new;
[\drums, \bass, \mel, \perc].do { |g|
	~fxBuses[g] = Bus.audio(Server.default, 2);
	~fxSynths[g] = Synth.tail(Server.default, (g == \drums).if(\fxdrum, \fx),
		[\in, ~fxBuses[g].index, \out, ~masterBus.index]);
};
~master = Synth.tail(Server.default, \master,
	[\in, ~masterBus.index, \out, 0]);
// which FX bus each role feeds
~busFor = IdentityDictionary.new;
[\kick, \snare, \hat, \ohat, \clap, \rim, \perc, \ride].do { |r| ~busFor[r] = \drums };
~busFor[\bass]  = \bass;
~busFor[\lead]  = \mel;
~busFor[\keys]  = \mel;
~busFor[\perc2] = \perc;                      // dedicated percussion FX bus
~fxParams = IdentityDictionary.new;
[\drums, \bass, \mel, \perc].do { |g| ~fxParams[g] = IdentityDictionary.new };

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
~argsFor = { |role, freq, vel|
	var grp = ~busFor[role] ? \mel;              // role -> its FX bus
	var a = [\freq, freq, \amp, vel, \out, ~fxBuses[grp].index];
	var p = ~params[role];                       // params are keyed by ROLE
	if(p.notNil) { p.keysValuesDo { |k, v| a = a ++ [k, v] } };
	a;
};

// --- /midi/noteon  ch pitch vel t_ms ---
OSCdef(\noteon, { |msg|
	var ch = msg[1].asInteger, pitch = msg[2].asInteger;
	var vel = msg[3].asFloat, role, def, freq, node, key;
	role = ~chanMap[ch];
	if(role.notNil) {
		freq = pitch.midicps;
		if(role == \drums) { role = ~drumFor.(pitch) };
		def = ~roleMap[role] ? role;                 // genre-chosen variant
		if(#[\kick, \snare, \hat, \ohat, \clap, \rim, \perc, \ride, \perc2].includes(role)) {
			Synth(def, ~argsFor.(role, freq, vel), ~instGrp);   // one-shot
		} {
			if((~monoFor[ch] == role) or: { ~monoDef.includes(def) }) {
				// persistent MONO voice -> portamento between notes
				node = ~mono[role];
				if(node.isNil) {
					node = Synth(def, ~argsFor.(role, freq, vel)
						++ [\gate, 1, \t_trig, 1], ~instGrp);
					~mono[role] = node;
				} {
					node.set(\freq, freq, \amp, vel, \gate, 1, \t_trig, 1);
				};
			} {
				node = Synth(def, ~argsFor.(role, freq, vel) ++ [\gate, 1], ~instGrp);
				if(~gated.includes(role)) {
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
	var role = ~chanMap[ch], def, monoRole, key, node;
	def = role.notNil.if({ ~roleMap[role] ? role });
	monoRole = nil;
	if(~monoFor[ch] == role) { monoRole = role };
	if(def.notNil and: { ~monoDef.includes(def) }) { monoRole = role };
	if(monoRole.notNil and: { ~mono[monoRole].notNil }) {
		~mono[monoRole].set(\gate, 0);       // release but KEEP node (glide cont.)
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
	// fx targets: fxDrums / fxBass / fxMel  (also accept plain "fx" -> all)
	var fxg = (synth == \fxDrums).if(\drums,
		{ (synth == \fxBass).if(\bass,
			{ (synth == \fxMel).if(\mel,
				{ (synth == \fxPerc).if(\perc, { nil }) }) }) });
	if(synth == \fx) {
		[\drums, \bass, \mel, \perc].do { |g|
			~fxParams[g][param] = value; ~fxSynths[g].set(param, value) };
	} {
		if(fxg.notNil) {
			~fxParams[fxg][param] = value;
			~fxSynths[fxg].set(param, value);
		} {
			if(~params[synth].notNil) { ~params[synth][param] = value };
		};
	};
}, '/synth/param');

// --- /synth/map  role synthDefName  : genre picks an instrument variant ---
OSCdef(\synthmap, { |msg|
	var role = msg[1].asString.asSymbol;
	var def  = msg[2].asString.asSymbol;
	if(~roleMap[role].notNil) {
		~roleMap[role] = def;
		// swap takes effect immediately for mono voices
		if(~mono[role].notNil) { ~mono[role].free; ~mono.removeAt(role) };
	};
}, '/synth/map');

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
