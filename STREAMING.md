# Streaming `str` to YouTube 24/7

The generative engine runs locally; OBS captures the browser + audio and pushes
RTMP to YouTube. The agent automated everything it can — these steps need your
machine/account and OBS's GUI, so they're yours. Do them once.

## 0. Run the stream engine

```bash
./scripts/start-stream.sh        # one-off: hybrid director, ~60s rotation
# …or, for 24/7 with auto-restart of any crashed part:
./scripts/supervise.sh           # bootstraps + watchdogs everything; leave running
open http://localhost:8080       # confirm visuals + audio before going live
```

## 1. Audio routing (so OBS can capture SC, and you can still hear it)

1. `brew install --cask blackhole-16ch` then run the installer it downloaded
   (needs your password — Homebrew can't do that headless) and **reboot**.
2. Open **Audio MIDI Setup** → **+** → **Create Multi-Output Device**.
   Tick **BlackHole 16ch** *and* your speakers/headphones. Name it `STR Out`.
   (This sends audio to BlackHole *and* your ears simultaneously.)
3. Point SuperCollider at it (no code edit needed):
   ```bash
   export STR_AUDIO_DEVICE="STR Out"     # exact device name
   ./scripts/start-stream.sh             # (or supervise.sh) — re-launch
   ```
   The synth log prints `[synth] output device -> STR Out`.

## 2. OBS Studio

1. Install OBS. Add a **Scene**.
2. **+ Source → Browser**: URL `http://localhost:8080`, **1920 × 1080**,
   FPS **30**, untick "Shutdown source when not visible". Size it full-canvas.
3. **+ Source → Audio Input Capture** → device **BlackHole 16ch**
   (this is the stream's audio).
4. **Settings → Output**: Output Mode *Advanced*; Encoder
   **Apple VT H264 Hardware**; Bitrate **~5000 Kbps** (1080p30);
   Keyframe interval **2 s**.
5. **Settings → Advanced → Network**: enable **Automatically reconnect**
   (essential for 24/7).
6. **Settings → Stream**: Service **YouTube – RTMPS**, then **Connect account**
   *or* paste your **Stream key** (Settings won't be shown here — get it in
   step 3 below). Never share/commit this key.

## 3. YouTube

1. youtube.com → **Create → Go live**. First time, live access can take ~24 h
   to enable — do this a day early.
2. Create a stream. Title/description it. **IMPORTANT:** in the content
   settings toggle **"Altered or synthetic content"** — this stream is
   AI-generated audio + visuals; YouTube policy requires disclosure.
3. Copy the **Stream key** into OBS (step 2.6). Set visibility (Public/Unlisted).
4. In OBS click **Start Streaming**. YouTube Live Control Room shows it within
   ~10–30 s; then **Go Live**.

## 4. 24/7 reliability

- Keep `./scripts/supervise.sh` running (tmux/screen). It restarts any crashed
  engine component automatically.
- OBS "Automatically reconnect" handles RTMP drops.
- Optional autostart on login — sample launchd agent
  (`~/Library/LaunchAgents/co.str.stream.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>co.str.stream</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string>
   <string>/Users/oskarsundberg/Dropbox/wrk/str/scripts/supervise.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>STR_AUDIO_DEVICE</key><string>STR Out</string></dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>WorkingDirectory</key>
  <string>/Users/oskarsundberg/Dropbox/wrk/str</string>
</dict></plist>
```
`launchctl load ~/Library/LaunchAgents/co.str.stream.plist`
(OBS itself you start manually, or add it to Login Items.)

## Notes / limits

- 16 GB M1 Pro: director + scribe are the 4B model (defaults) — comfortable.
  Close other heavy apps. Don't set `STR_MIDI_SOURCE=midillm` (extra ~3.5 GB).
- The browser tab must stay open & not be minimised (Browser Source keeps it
  rendering even if hidden, but don't quit Chrome/OBS).
- Power: set the Mac to never sleep (System Settings → Lock Screen / Energy)
  while streaming.
