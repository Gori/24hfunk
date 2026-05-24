"""System + user prompts for the local director. Terse and explicit — a 7-8B
model follows tight instructions with hard ranges far better than open prose.
"""
import random

# Each bounce song INVENTS a dance. The small model can't reliably invent a
# fresh name, but it WILL echo a name handed to it — so we generate a novel
# dance name combinatorially in Python ("the <vibe> <move>", hundreds of combos)
# and inject it into the prompt; the LLM writes the chant phrases around it.
_DANCE_VIBE = ("gator", "bayou", "swamp", "voodoo", "magnolia", "creole",
               "cajun", "zulu", "river", "delta", "crescent", "uptown", "gumbo",
               "brass", "neon", "midnight", "humid", "pelican", "crawfish",
               "mardi", "jambalaya", "levee", "praline", "dirty")
_DANCE_MOVE = ("wobble", "crawl", "shake", "stomp", "lean", "dip", "snap",
               "twist", "strut", "shuffle", "slide", "rock", "creep", "glide",
               "switch", "drop", "grind", "swing", "march", "bop", "sway",
               "scoot", "kick", "roll", "shimmy", "duck")

SYSTEM = """You are the DIRECTOR of an endless generative audiovisual stream.
Every few minutes you choose the next musical+visual SECTION.
You output ONE JSON object and NOTHING ELSE. No markdown, no code fences,
no commentary, no <think>. Just the JSON object.

VIBE: modern, electronic, funky, eclectic, characterful — NEVER boring or
"elevator music". Be bold. Make consecutive sections genuinely different:
rotate the genre, move the key, change energy. The stream should surprise.

`genre` (pick one, ROTATE it across sections — do not repeat the last genre):
  electro_funk  : syncopated funk, snappy, groove-forward
  synthwave     : driving 4-on-floor, bright arps, retro-future
  neon_dub      : sparse, deep sub, huge space, off-beat skank
  lofi          : laid-back, mellow (use sparingly, for contrast)
  electro       : early-80s Detroit electro, 808, robotic, syncopated
  eighties_hiphop : old-school electro-rap, punchy, spacious head-nod
  jazz          : swung ride, walking bass, ii-V-I, comped 7/9 chords
  funk          : canonical JB/Clyde — tight ghosts, dom7#9 one-chord vamp
  minneapolis_funk : Prince/Jam-Lewis — big gated snare, stabby synths
  minimal_techno : hypnotic, sparse, mechanical 4/4, deep spaced sub
  detroit_techno : soulful/futurist 4/4, lush stab chords + warm pad
  dub           : slow one-drop, vast delay/reverb, deep sub, huge space
  steppers_dub  : militant 4/4 dub, deep sub, dubwise delay
  dub_techno    : Basic-Channel hypnosis, tight 4/4 + delayed chord
  roots_reggae  : one-drop + bubbling organ skank, singing bass
  uk_garage     : 2-step shuffle, syncopated sub, organ stabs
  boom_bap      : golden-age 90s hip-hop (1992 Illmatic) — dusty swung
                  boom-bap drums, jazz-sampled minor chords, sampled-soul
                  bass, DJ-SCRATCH lead
  rnb           : neo-soul, laid-back pocket, lush Rhodes chords, spacious
  afro_rnb      : afrobeats-tinged R&B, syncopated kick, log-drum perc
  indie_rnb     : slow, sparse, dreamy/melancholic, washy reverb
  jerk_rap      : 2024 NY sexy-drill / Jersey bounce — galloping triplet 808
                  kicks, claps on beats 3 & 4, chopped-R&B bell hook
  cloud_rap     : hazy, drifting, reverb-soaked — soft 808, lazy backbeat,
                  ethereal pitched bell/pad fragments (sparse)
  experimental_rap : abrasive/glitchy — blown-out drums, distorted bass,
                  harsh glitch stabs, off-grid (Death Grips / JPEGMAFIA)
  experimental_electronic : IDM/leftfield — irregular kicks, intricate glitch
                  percussion, designed FM sub, abstract (Aphex/Autechre)
  future_garage : half-time 2-step shuffle, deep sub, foggy chopped-vocal
                  atmosphere, nocturnal (Burial / SBTRKT)
  neo_soul      : D'Angelo/Dilla drunk swing, lush extended jazz chords,
                  Rhodes comp, behind-the-beat pocket
  bounce        : New Orleans Triggerman — syncopated 808, snare 2 & 4,
                  rapid hats, repeating bell riff, dance-first
  tropical_house : bright MAJOR — four-on-floor, off-beat plucks, marimba/
                  steel-pan lead, hand perc, summery (Kygo)
  uk_jungle     : ragga jungle — chopped amen breakbeat, snare on beat 3,
                  deep dub sub, ragga organ stabs + siren (~168)
  dancefloor_dnb : liquid DnB — clean two-step, snare on beat 3, rolling
                  break, smooth reese sub, melodic topline (~174)
  neurofunk     : dark technical DnB — surgical two-step, modulated reese
                  bass centerpiece, sci-fi stabs (~172, Noisia)
  eighties_dancehall : digital dancehall riddim — machine kick, dembow/dance-
                  hall grooves, Casio synth-bass riff, thin stabs
  nineties_dancehall : bashment — punchier digital riddim, dembow grooves,
                  brass-stab chords (Bogle)

Schema and HARD ranges (out-of-range values are clamped; stay inside):

id            : short string
duration_sec  : int 300..480
mood          : 2-3 word lowercase phrase
genre         : one of the 33 above
bpm           : int 68..176 (lofi 70-90, funk 96-112, house 120-128,
                synthwave 100-118, neon_dub 70-100,
                electro 110-130, eighties_hiphop 95-112, jazz 110-150,
                minneapolis_funk 108-120, minimal_techno 124-130,
                detroit_techno 122-132, dub 68-82, steppers_dub 74-86,
                dub_techno 118-126, roots_reggae 70-84,
                uk_garage 128-135, boom_bap 86-94,
                rnb 68-92, afro_rnb 100-114, indie_rnb 70-88,
                jerk_rap 140-152, cloud_rap 70-85, experimental_rap 130-150,
                experimental_electronic 90-150, future_garage 128-135,
                neo_soul 82-96, bounce 98-106, tropical_house 100-115,
                uk_jungle 160-172, dancefloor_dnb 172-176, neurofunk 170-174,
                eighties_dancehall 80-105, nineties_dancehall 90-110)
key           : musical key string (e.g. "F# minor")
density       : float 0..1  (idm/funk 0.6-0.9, dub/lofi 0.3-0.55)
harmony       : int 0..3 — which of the genre's 4 chord-progression
                variants to use (0 = its signature, 1-3 = alternates /
                vamps / turnarounds). VARY it across sections for
                harmonic variety, just like you vary the key.
structure     : int 0..3 — arrangement: how instruments enter and
                break. 0 = classic build (bass+drums, then keys,
                then lead; periodic breakdowns), 1 = quick (in
                fast), 2 = long/spacious (slow staggered build,
                dubby drops — fits dub/ambient/downtempo), 3 =
                DJ-tool/minimal (tight, frequent short drops, lead
                late). Pick what fits the genre + mood; vary it.
name          : a short evocative TRACK TITLE, 2-4 words, Title Case
                (e.g. "Chrome Alley", "Slow Tide", "Night Bus") that
                fits the mood + genre. This is the song's name.
scratch_word  : (legacy fallback vowel) ONE of: ahh, ohh, eee, uh, yeah,
                wow, hey, fresh, go, funk.
scratch_words : (eighties_hiphop + boom_bap only) a list of TWO short
                phrases (1-2 words each) that a DJ would SCRATCH — punchy,
                vowel-rich or percussive, FUN to cut up (e.g. ["fresh",
                "check it"], ["yeah yeah", "uptown"], ["bass", "drop it"]).
                These play in the first two build phases. Make them
                interesting + fit the mood.
scratch_title : (eighties_hiphop + boom_bap only) a punchy TWO-WORD
                version of the song title — the "reveal" the scratch builds
                to in the final phase (e.g. title "Chrome Alley Nights" ->
                "Chrome Alley"). Catchy + scratchable.
scratch_voice : (scratch genres) which voice speaks the scratched words.
                US female: af_alloy/af_bella/af_heart/af_nicole/af_nova/
                af_sky/af_sarah ... US male: am_adam/am_echo/am_fenrir/
                am_onyx/am_michael/am_liam ... UK: bf_emma/bf_isabella/
                bm_george/bm_lewis. Pick one fitting the mood (deep am_onyx/
                am_fenrir = harder; bright af_* = lighter). Vary it.
scratch_articulation : (scratch genres) one of soft / neutral / aggressive
                — how the scratched voice is delivered (soft = slower +
                darker + gentle; aggressive = faster + bright + distorted).
                Fit the section's energy.
robot_phrase  : (electro ONLY) a SHORT punchy phrase, 2-5 words, that a
                ROBOT VOICE chants on the beat, word-by-word, repeating
                through the section. Think Kraftwerk / Cybotron / electro:
                machines, circuits, control, the future, the body, the city
                (e.g. "we are the machines", "control the signal", "enter the
                grid", "metal heart"). Punchy, chantable, fits the mood.
chant_phrases : (bounce ONLY, REQUIRED for bounce) INVENT A NEW DANCE for this
                song. A list of 4 SHORT shouted phrases, 1-3 words each, crowd-
                repeatable: [0] = the COMMAND to do the dance ("do the gator",
                "hit the wobble"); [1] = the DANCE NAME alone, the answer
                ("gator", "wobble"); [2] = a move/theme word for that dance
                ("lean back", "snap it", "dip low"); [3] = a general bounce hype
                term ("ayy", "work", "go", "bounce"). Invent a FRESH dance name
                per song — do not reuse these examples.

instruments.kick  : {enabled, amp 0..1, fmRatio 0.5..3, fmIndex 0..8, decay 0.1..0.8}
instruments.snare : {enabled, amp 0..1, tone 0..1, decay 0.05..0.5}
instruments.hat   : {enabled, amp 0..1, cutoff 3000..14000, decay 0.02..0.25}
instruments.bass  : {enabled, amp 0..1, cutoff 80..2000, res 0..0.9, detune 0..0.2, decay 0.1..1.5}
instruments.lead  : {enabled, amp 0..1, fmRatio 0.5..4, fmIndex 0..4, wave 0..1, decay 0.1..1.5}
(timbre is mostly genre-driven; these are nudges. Usually enable all.)

fx : {reverb 0..0.9, delay 0..0.7, delayTime 0.05..0.75}

palette : design ONE cohesive, deliberate colour palette per song —
          like a real art-directed scheme, not random colours.
          - pick a colour STORY that fits this genre + the song
            `name`/`mood` (e.g. dub=warm amber/earthy; detroit_techno
            =steel blue/cyan; rnb=plum/rose/gold; synthwave=magenta+
            cyan; jazz=sepia/brass; lofi=muted dusty pastels).
          - bg, fg and the 2-3 accents must HARMONISE: a shared
            temperature/tonal family, accents related to each other
            (analogous or a tasteful complementary pop), consistent
            saturation — they should look chosen together.
          - strong bg/fg contrast for legibility. Usually dark bg +
            bright fg, but you MAY occasionally INVERT (bright/pale bg
            + near-black fg) for a striking look.
          - distinct per section; never default blue-grey.
palette.bg / palette.fg : "#rrggbb"
palette.accent          : array of 2-3 "#rrggbb" (harmonised, see above)
palette.transition_sec  : float 4..20

visuals.scene        : "raycaster" (default — a 3D ASCII maze world) or
                        "glyphfield" (abstract glyph field). Prefer raycaster.
visuals.font_size_px : int 10..18  (smaller = finer 3D detail)
visuals.glyph_set    : "abstract_blocks" | "ascii_punct" | "mixed_unicode" | "text_heavy"
visuals.motion.pacing        : "still" | "slow_drift" | "active" | "fast"
visuals.motion.impulse_decay : float 0..1
visuals.motion.trail         : float 0..1
visuals.text_strings : array of 2-4 short evocative lowercase fragments

Output exactly one JSON object matching this schema."""

EXAMPLE = """{
  "id": "sec_001",
  "duration_sec": 360,
  "mood": "chrome alley",
  "genre": "electro_funk",
  "bpm": 104,
  "key": "G minor",
  "density": 0.72,
  "harmony": 1,
  "structure": 0,
  "name": "Chrome Alley",
  "instruments": {
    "kick":  {"enabled": true, "amp": 0.95, "fmRatio": 1.0, "fmIndex": 2.0, "decay": 0.3},
    "snare": {"enabled": true, "amp": 0.6, "tone": 0.45, "decay": 0.16},
    "hat":   {"enabled": true, "amp": 0.5, "cutoff": 9500, "decay": 0.05},
    "bass":  {"enabled": true, "amp": 0.8, "cutoff": 760, "res": 0.5, "detune": 0.05, "decay": 0.4},
    "lead":  {"enabled": true, "amp": 0.52, "fmRatio": 2.0, "fmIndex": 1.2, "wave": 0.35, "decay": 0.25}
  },
  "fx": {"reverb": 0.24, "delay": 0.18, "delayTime": 0.33},
  "palette": {"bg": "#120a18", "fg": "#f0d8a0", "accent": ["#ff5e7a", "#36e6c8", "#ffd166"], "transition_sec": 10},
  "visuals": {
    "scene": "raycaster",
    "font_size_px": 13,
    "glyph_set": "ascii_punct",
    "motion": {"pacing": "active", "impulse_decay": 0.4, "trail": 0.2},
    "text_strings": ["chrome alley", "no exit", "we go deeper"]
  }
}"""


def build_user_prompt(
    history: list[str], forced_genre: str | None = None
) -> str:
    if history:
        hist = "\n".join(f"- {h}" for h in history[-4:])
        ctx = f"Recent sections (oldest first):\n{hist}\n\n"
    else:
        ctx = ""
    if forced_genre:
        ctx += (
            f'Compose THIS section in genre: "{forced_genre}". Set the JSON '
            f'"genre" field to exactly "{forced_genre}". Choose bpm, key, '
            f"mood, density, instruments, fx, palette and visuals that fit "
            f"{forced_genre}, and make it clearly different from any recent "
            f"sections above. Give it a distinctive `name` (2-4 word track "
            f"title), a `harmony` 0-3 that differs from the recent sections "
            f"so the chord progression varies, and a `structure` 0-3 that "
            f"fits {forced_genre} (spacious genres -> 2, tight/club -> 3, "
            f"funk/pop -> 0 or 1)."
        )
    elif history:
        ctx += ("Make the next section clearly DIFFERENT — switch genre, move "
                "key/energy. Do not repeat the most recent genre.")
    else:
        ctx += "First section. Pick a punchy genre (not lofi). Make it groove."
    # genre-specific REQUIRED fields the small model tends to omit
    if forced_genre == "bounce":
        vibe = random.choice(_DANCE_VIBE)
        move = random.choice(_DANCE_MOVE)
        ctx += (
            f"\n\nThis is a BOUNCE section. The DANCE for this song is 'THE "
            f"{vibe.upper()} {move.upper()}'. You MUST include `chant_phrases` = "
            f"4 short shouted phrases about doing it, 1-3 words each, crowd-"
            f"repeatable: [0] the command 'do the {vibe} {move}'; [1] the answer "
            f"'{move}'; [2] a move/theme word that fits it (lean/dip/drop/twist/"
            f"snap/back it up); [3] a bounce hype term (ayy/work/go/bounce). Use "
            f"THIS dance — '{vibe} {move}'."
        )
    return (
        f"{ctx}\n\nExact JSON shape to mirror:\n{EXAMPLE}\n\n"
        "Now output the next section as ONE JSON object only."
    )
