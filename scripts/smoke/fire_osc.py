"""Fire test MIDI OSC at the SuperCollider router.

Usage:
  python scripts/smoke/fire_osc.py kick
  python scripts/smoke/fire_osc.py seq 16 0.2     # 16 notes, 0.2s apart
"""
import os
import sys
import time

from pythonosc.udp_client import SimpleUDPClient

HOST = "127.0.0.1"
PORT = int(os.environ.get("SC_OSC_PORT", "57120"))
client = SimpleUDPClient(HOST, PORT)


def noteon(ch, pitch, vel=0.8):
    client.send_message("/midi/noteon", [int(ch), int(pitch), float(vel), 0.0])


def noteoff(ch, pitch):
    client.send_message("/midi/noteoff", [int(ch), int(pitch), 0.0])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "kick"
    if cmd == "kick":
        noteon(9, 36)
    elif cmd == "snare":
        noteon(9, 38)
    elif cmd == "hat":
        noteon(9, 42)
    elif cmd == "bass":
        noteon(0, 36, 0.9); time.sleep(0.6); noteoff(0, 36)
    elif cmd == "lead":
        noteon(1, 64, 0.7); time.sleep(0.6); noteoff(1, 64)
    elif cmd == "seq":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 16
        gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
        pattern = [(9, 36), (9, 42), (0, 40), (9, 38), (9, 42), (1, 64), (0, 43), (9, 42)]
        held = []  # (ch, pitch, steps_remaining) for sustained voices
        for i in range(n):
            # release sustained notes whose hold elapsed
            still = []
            for ch, p, rem in held:
                if rem <= 0:
                    noteoff(ch, p)
                else:
                    still.append((ch, p, rem - 1))
            held = still
            ch, p = pattern[i % len(pattern)]
            noteon(ch, p, 0.8)
            if ch in (0, 1):  # bass/lead are gated — must be released
                held.append((ch, p, 2))
            time.sleep(gap)
        for ch, p, _ in held:  # flush
            noteoff(ch, p)
    else:
        print(f"unknown command: {cmd}")
        sys.exit(2)
    print(f"sent '{cmd}' to {HOST}:{PORT}")


if __name__ == "__main__":
    main()
