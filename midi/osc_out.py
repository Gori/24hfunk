"""OSC out from the MIDI worker to the SuperCollider router (UDP 57120)."""
from __future__ import annotations

import os

from pythonosc.udp_client import SimpleUDPClient

SC_HOST = "127.0.0.1"
SC_PORT = int(os.environ.get("SC_OSC_PORT", "57120"))


class ScSender:
    def __init__(self, host: str = SC_HOST, port: int = SC_PORT):
        self.client = SimpleUDPClient(host, port)

    def note_on(self, ch: int, pitch: int, vel: float, t_ms: float = 0.0) -> None:
        self.client.send_message(
            "/midi/noteon", [int(ch), int(pitch), float(vel), float(t_ms)]
        )

    def note_off(self, ch: int, pitch: int, t_ms: float = 0.0) -> None:
        self.client.send_message(
            "/midi/noteoff", [int(ch), int(pitch), float(t_ms)]
        )

    def param(self, synth: str, name: str, value: float) -> None:
        self.client.send_message(
            "/synth/param", [str(synth), str(name), float(value)]
        )

    def select(self, role: str, synthdef: str) -> None:
        """Pick a per-genre instrument variant for a role."""
        self.client.send_message("/synth/map", [str(role), str(synthdef)])

    def tempo(self, bpm: float) -> None:
        self.client.send_message("/midi/tempo", [float(bpm)])

    def bar(self, idx: int) -> None:
        self.client.send_message("/midi/bar", [int(idx)])

    def panic(self) -> None:
        """Hard-stop all sounding instrument nodes (used at re-prime)."""
        self.client.send_message("/panic", [1])
