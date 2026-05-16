"""MIDI-LLM source: slseanwu/MIDI-LLM_Llama-3.2-1B (AMT arrival-time tokens,
decoded via the `anticipation` library). Text-conditioned; emits a flat chunk
that we decode to timed notes and route to our drums/bass/lead channels.

Not a streaming model — we generate a chunk and play it via the worker's
look-ahead buffer while the next chunk generates. Any failure (load, generate,
decode, empty output) transparently delegates to CannedSource so the stream
never stops.
"""
from __future__ import annotations

import os

from midi.canned import CannedSource
from midi.source import CH_BASS, CH_DRUMS, CH_LEAD, Note, Phrase

MODEL_ID = os.environ.get("STR_MIDILLM_MODEL", "slseanwu/MIDI-LLM_Llama-3.2-1B")
_PROMPT = ("You are a world-class composer. Please compose some music "
           "according to the following description: ")


class MidiLLMSource:
    name = "midillm"
    min_buffer = 16.0  # generation is slow; keep a deep buffer

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "mps"
        self.midi_base = 0
        self.desc = "calm minimal lofi with soft drums, warm bass and a sparse chill lead"
        self._fallback = CannedSource()
        self._degraded = False
        self._fail = 0

    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import anticipation.vocab as V

        if not torch.backends.mps.is_available():
            raise RuntimeError("MPS not available")
        print(f"[midillm] loading {MODEL_ID} (fp16/MPS) …")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, torch_dtype=torch.float16
        ).to(self.device).eval()
        # anticipation MIDI tokens are appended after the Llama text vocab
        self.midi_base = self.model.config.vocab_size - V.VOCAB_SIZE
        if self.midi_base <= 0:
            raise RuntimeError(f"unexpected vocab layout (base={self.midi_base})")
        print(f"[midillm] loaded; midi_base={self.midi_base}")

    def prime(self, section: dict) -> None:
        self._fallback.prime(section)
        mood = section.get("mood", "calm")
        key = section.get("key", "C minor")
        bpm = section.get("bpm") or section.get("tempo") or 78
        dens = section.get("density", 0.5)
        tex = "sparse and minimal" if dens < 0.5 else "flowing"
        self.desc = (f"{mood} lofi in {key} around {int(bpm)} bpm, {tex}, "
                     f"soft digital drums, warm bass, gentle chill lead")

    def next_phrase(self) -> Phrase:
        if self._degraded:
            return self._fallback.next_phrase()
        try:
            ph = self._generate()
            if not ph.notes:
                raise RuntimeError("decoded zero notes")
            self._fail = 0
            return ph
        except Exception as e:  # noqa: BLE001
            self._fail += 1
            print(f"[midillm] generation failed ({self._fail}): {e}")
            if self._fail >= 3:
                print("[midillm] degraded -> permanent canned fallback")
                self._degraded = True
            return self._fallback.next_phrase()

    def _generate(self) -> Phrase:
        import torch
        import anticipation.vocab as V
        from anticipation.convert import events_to_midi

        enc = self.tokenizer(_PROMPT + self.desc, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **enc,
                max_new_tokens=1024,
                do_sample=True,
                temperature=1.0,
                top_p=0.98,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        gen = out[0][enc.input_ids.shape[1]:].tolist()

        # back to anticipation token space, keep only valid MIDI-vocab tokens
        toks = [t - self.midi_base for t in gen
                if self.midi_base <= t < self.midi_base + V.VOCAB_SIZE]
        toks = [t for t in toks if t != V.SEPARATOR]
        toks = toks[: (len(toks) // 3) * 3]  # whole (time,dur,note) triplets
        if len(toks) < 3:
            raise RuntimeError("too few MIDI tokens")

        mf = events_to_midi(toks)
        return self._midi_to_phrase(mf)

    @staticmethod
    def _midi_to_phrase(mf) -> Phrase:
        import mido

        tempo = 500000
        notes = []
        for track in mf.tracks:
            abs_tick = 0
            pending = {}  # (chan,note) -> (onset_s, vel)
            for msg in track:
                abs_tick += msg.time
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    continue
                if msg.type not in ("note_on", "note_off"):
                    continue
                t_s = mido.tick2second(abs_tick, mf.ticks_per_beat, tempo)
                key = (msg.channel, msg.note)
                if msg.type == "note_on" and msg.velocity > 0:
                    pending[key] = (t_s, msg.velocity / 127.0)
                else:
                    if key in pending:
                        on_s, vel = pending.pop(key)
                        dur = max(0.05, t_s - on_s)
                        if msg.channel == 9:
                            ch, pitch = CH_DRUMS, msg.note
                        elif msg.note < 52:
                            ch, pitch = CH_BASS, msg.note
                        else:
                            ch, pitch = CH_LEAD, msg.note
                        notes.append(Note(on_s, dur, pitch, max(0.2, vel), ch))

        if not notes:
            return Phrase(notes=[], length=0.0)
        notes.sort(key=lambda n: n.t)
        t0 = notes[0].t
        for n in notes:
            n.t -= t0
        length = max(n.t + n.dur for n in notes)
        return Phrase(notes=notes, length=length)
