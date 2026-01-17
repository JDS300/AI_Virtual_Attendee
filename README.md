# AI Workshop Attendee

Real-time presentation feedback tool that streams your screen and microphone to Gemini, acting as a virtual workshop attendee.

## Quick Start

```bash
cd PATH_TO_SCRIPT
source venv/bin/activate.fish (used for any OS using fish as the shell, ie CachyOS)

# Run (2>/dev/null hides audio library warnings)
python main.py --session-name "Workshop Rehearsal" 2>/dev/null
```

## Usage

```bash
# Default: full desktop + HyperX mic
python main.py --session-name "My Rehearsal" 2>/dev/null

# Specify monitor (0=all, 1-4=individual)
python main.py --monitor 1 --session-name "Practice" 2>/dev/null

# Different audio device
python main.py --audio-device 11 --session-name "Test" 2>/dev/null

# List monitors
python main.py --list-monitors
```

**Stop:** Press Ctrl+C for graceful shutdown with stats.

## What It Does

1. Captures your screen at ~2.5 fps (resized to 720p)
2. Captures microphone audio (48kHz → 16kHz resampled)
3. Streams both to Gemini Live API
4. **Displays AI feedback in real-time in terminal**
5. Logs all feedback with timestamps to file

## Real-Time Output

As you present, you'll see Gemini's feedback appear live:

```
🎬 Session started. Streaming to Gemini...
📁 Logging to: workshop_feedback_My_Rehearsal_20260116_213500.txt
🎤 Audio: Recording at 48000Hz (device 5)

💬 Gemini: OBSERVATION: The slide text is quite small and may be hard to read
💬 Gemini: POSITIVE: Clear explanation of the three-step process
💬 Gemini: QUESTION: Could you clarify what ROI means in this context?
```

## Requirements

- Python 3.10+
- Google API key with Gemini 2.5 Flash Native Audio access
- Microphone
