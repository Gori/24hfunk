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
// Synth defs in this set get the persistent-voice (glide) path. Glide
// adds liveness even on a "horn-section" line. Sustained-type leads work
// here; Pluck/Bell/Glitch/Siren stay voice-stealing because their
// character depends on per-note attacks/decay/whoop fired by initial
// gate, which persistent-mono only fires once.
~monoDef = Set[\leadMoog, \leadHyper];
// VOICE-STEALING mono channels: only one note at a time on this channel.
// New noteon releases the previous note's gate before starting the new
// synth (each note still gets a fresh envelope — no glide). Use this when
// you want strict mono behavior across DIFFERENT synth defs without
// needing each synth to support t_trig retriggering.
~monoCh = Set[1];                            // CH_LEAD = mono (all lead defs)

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
	var def = ~roleMap[role] ? role;             // genre-chosen variant
	var p   = ~params[role];                     // params are keyed by ROLE
	// section amp (from the director). For the LEAD it is an instrument-level
	// SCALER that the per-note velocity multiplies (so scratch/lead volume +
	// dynamics actually respond); drums/bass/keys keep amp = section amp as
	// before. (Was: params \amp appended last -> clobbered \amp=vel for
	// everything, so per-note lead volume changes had NO effect.)
	var hasAmp = (p.notNil and: { p[\amp].notNil });
	var perNoteVol = (def == \leadScratch) or: { def == \leadVox };  // buffer-vocal leads
	var amp = perNoteVol.if(
		{ vel * (hasAmp.if({ p[\amp] }, { 1.0 })) },   // per-note velocity controls volume
		{ hasAmp.if({ p[\amp] }, { vel }) }            // everything else: UNCHANGED
	);
	var a = [\freq, freq, \amp, amp, \out, ~fxBuses[grp].index];
	if(p.notNil) { p.keysValuesDo { |k, v| if(k != \amp) { a = a ++ [k, v] } } };
	// leadScratch: the note PITCH encodes the build phase in its octave
	// (60-71 = phase 1 / slot 0, 72-83 = phase 2 / slot 1, 84+ = phase 3 /
	// slot 2) so each phase scratches a DIFFERENT word/title buffer. Also
	// needs the tempo for rhythmic-division hand motion.
	if((def == \leadScratch) and: { ~scratchBufs.notNil }) {
		var bidx = ((freq.cpsmidi - 60) / 12).floor.clip(0, 5).asInteger;
		a = a ++ [\buf, ~scratchBufs[bidx].bufnum, \beatHz, (~bpm ? 120) / 60,
			\drive, (~scratchDrive ? 1.0), \cutoff, (~scratchCutoff ? 3600)];
	};
	// leadVox (electro robot vocal): same word-slot-in-octave buffer pick +
	// tempo. drive/cutoff come from the genre lead params (not the scratch artic).
	if((def == \leadVox) and: { ~scratchBufs.notNil }) {
		var bidx = ((freq.cpsmidi - 60) / 12).floor.clip(0, 5).asInteger;
		a = a ++ [\buf, ~scratchBufs[bidx].bufnum, \beatHz, (~bpm ? 120) / 60];
	};
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
					// clear the ref when the node frees (e.g. the maxSustain
					// safety fires during a long rest between solos) so the
					// NEXT note recreates a live voice instead of .set()'ing a
					// dead node -> silence.
					node.onFree({ if(~mono[role] == node) { ~mono[role] = nil } });
				} {
					node.set(\freq, freq, \amp, vel, \gate, 1, \t_trig, 1);
				};
			} {
				// VOICE-STEALING mono: release any active note on this channel
				// before creating the new one (only one synth at a time).
				if(~monoCh.includes(ch)) {
					~active.keysValuesDo { |k, n|
						if(k.asString.beginsWith(ch.asString ++ "_")) {
							n.set(\gate, 0);
							~active.removeAt(k);
						};
					};
				};
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

// --- scratch vocal WORD recipes -> re-render ~scratchBuf -------------------
// each word = 3 formant frames (F1/F2/F3 glide start->mid->end) + head/tail
// consonant noise (0 none, 1 f/s hiss, 2 g/k burst, 3 sh). See _vocalRender.
~scratchWords = (
	ahh:   (dur: 0.42, f1: [700,700,700],  f2: [1100,1100,1100], f3: [2600,2600,2600], head: 0, tail: 0),
	ohh:   (dur: 0.42, f1: [450,450,450],  f2: [800,800,800],    f3: [2600,2600,2600], head: 0, tail: 0),
	eee:   (dur: 0.40, f1: [300,300,300],  f2: [2300,2300,2300], f3: [3000,3000,3000], head: 0, tail: 0),
	uh:    (dur: 0.28, f1: [600,600,600],  f2: [1000,1000,1000], f3: [2400,2400,2400], head: 0, tail: 0),
	yeah:  (dur: 0.46, f1: [300,500,750],  f2: [2300,1700,1100], f3: [3000,2700,2600], head: 0, tail: 0),
	wow:   (dur: 0.46, f1: [350,650,350],  f2: [750,1100,750],   f3: [2400,2500,2400], head: 0, tail: 0),
	hey:   (dur: 0.42, f1: [600,500,300],  f2: [1500,1900,2300], f3: [2600,2800,3000], head: 1, tail: 0),
	fresh: (dur: 0.52, f1: [500,550,550],  f2: [1400,1700,1700], f3: [2500,2600,2600], head: 1, tail: 3),
	go:    (dur: 0.40, f1: [450,450,450],  f2: [900,800,800],    f3: [2400,2400,2400], head: 2, tail: 0),
	funk:  (dur: 0.44, f1: [600,600,500],  f2: [1000,1000,900],  f3: [2400,2400,2400], head: 1, tail: 2),
);
~renderWord = { |w|
	var r = ~scratchWords[w] ? ~scratchWords[\ahh];
	if(~scratchBuf.notNil) {
		Synth(\_vocalRender, [\buf, ~scratchBuf, \dur, r[\dur],
			\f1a, r[\f1][0], \f1b, r[\f1][1], \f1c, r[\f1][2],
			\f2a, r[\f2][0], \f2b, r[\f2][1], \f2c, r[\f2][2],
			\f3a, r[\f3][0], \f3b, r[\f3][1], \f3c, r[\f3][2],
			\head, r[\head], \tail, r[\tail]]);
	};
};
// scratch articulation: drive (aggression) + cutoff (brightness), set per
// section by the director from the LLM's articulation choice.
~scratchDrive = 1.0;
~scratchCutoff = 3600;
OSCdef(\scratchartic, { |msg|
	~scratchDrive  = msg[1].asFloat;
	~scratchCutoff = msg[2].asFloat;
}, '/scratch/artic');

OSCdef(\scratchword, { |msg| ~renderWord.(msg[1].asString.asSymbol); }, '/scratch/word');
~renderWord.(\ahh);                       // initial buffer content (procedural fallback)
// SIX scratch buffer slots — one per WORD (2 words x 3 build phases):
// 0/1 = phase-1 phrase words, 2/3 = phase-2 phrase words, 4/5 = title words.
// Each word is its own sample so multi-word phrases scratch SEPARATELY.
// All start on the procedural vowel; /scratch/load swaps slots in per render.
~scratchBufs = Array.fill(6, { ~scratchBuf });

// --- /scratch/load  idx path  : load a TTS wav into scratch buffer slot idx
// (0..5). Frees the previous (non-procedural) buffer after a short delay so
// an in-flight scratch note finishes reading it first.
OSCdef(\scratchload, { |msg|
	var idx  = msg[1].asInteger;
	var path = msg[2].asString;
	if((idx >= 0) and: { idx < 6 } and: { File.exists(path) }) {
		Buffer.read(Server.default, path, action: { |b|
			var old = ~scratchBufs[idx];
			~scratchBufs[idx] = b;
			if(old.notNil and: { old != b } and: { old != ~scratchBuf }) {
				SystemClock.sched(2.0, { old.free; nil });
			};
		});
	};
}, '/scratch/load');

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
