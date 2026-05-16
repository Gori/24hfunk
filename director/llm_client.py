"""Local director LLM (mlx-lm, Qwen3-8B-4bit by default).

No constrained decoding in mlx_lm 0.31 without `outlines`, so we use the
planned fallback: strict prompt -> Pydantic validate -> one retry -> safe
default. The stream must never die because of a bad generation.
"""
from __future__ import annotations

import json
import os
import re
import time

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

from director.prompts import SYSTEM, build_user_prompt
from director.schema import SectionState

MODEL_ID = os.environ.get("STR_DIRECTOR_MODEL", "mlx-community/Qwen3-8B-4bit")
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _first_json_object(text: str) -> dict | None:
    """Extract the first balanced {...} block and json.loads it."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break
        start = text.find("{", start + 1)
    return None


class Director:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.sampler = make_sampler(temp=0.6, top_p=0.9)

    def load(self) -> None:
        t0 = time.time()
        print(f"[director] loading {self.model_id} …")
        self.model, self.tokenizer = load(self.model_id)
        print(f"[director] loaded in {time.time() - t0:.1f}s")

    def _format(self, messages) -> str:
        tok = self.tokenizer
        try:
            return tok.apply_chat_template(
                messages, add_generation_prompt=True, enable_thinking=False
            )
        except TypeError:
            return tok.apply_chat_template(messages, add_generation_prompt=True)

    def _generate(self, user: str, max_tokens: int = 850) -> str:
        prompt = self._format(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": user}]
        )
        out = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=self.sampler,
            verbose=False,
        )
        return _THINK_RE.sub("", out).strip()

    def next_section(self, history: list[str]) -> tuple[SectionState, float]:
        """Returns (section, latency_sec). Never raises."""
        t0 = time.time()
        user = build_user_prompt(history)
        for attempt in (1, 2):
            try:
                raw = self._generate(user)
                data = _first_json_object(raw)
                if data is None:
                    raise ValueError("no JSON object in output")
                section = SectionState(**data)
                return section, time.time() - t0
            except Exception as e:  # noqa: BLE001 - resilience is the point
                print(f"[director] attempt {attempt} failed: {e}")
                user = (
                    build_user_prompt(history)
                    + "\n\nYour previous reply was invalid. Output ONLY one "
                    "valid JSON object, no other text."
                )
        print("[director] falling back to safe default section")
        return SectionState(id=f"fallback_{int(time.time())}"), time.time() - t0


def summarize(s: SectionState) -> str:
    return (
        f"{s.mood} | genre {s.genre} | {s.bpm}bpm {s.key} | "
        f"density {s.density:.2f} | scene {s.visuals.scene} | "
        f"pacing {s.visuals.motion.pacing} | bg {s.palette.bg}"
    )
