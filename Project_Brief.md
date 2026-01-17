Project: AI Workshop Attendee (MVP)
Build time target: 3 hours max
Due: Sunday night (presentation Wednesday)

Core Requirements
Build a Python application that acts as a live workshop attendee by:

Capturing screen at 2-3 fps while presenting slides
Capturing microphone audio continuously
Streaming both to Gemini 2.5 Flash Native Audio via Live API
Logging AI responses to file for post-session review
Simple CLI interface to start/stop session


Technical Stack (Pre-decided)

API: Gemini 2.5 Flash Native Audio (gemini-2.5-flash-native-audio-preview-12-2025)
SDK: google-genai Python package
Screen capture: pyautogui or mss (faster)
Audio: pyaudio for mic streaming
Python 3.10+


System Prompt for AI Attendee
You are attending a 4-hour AI workshop for small business professionals.

Your role:
- Watch slides as they change on screen
- Listen to the presenter's explanations
- Identify: unclear explanations, pacing issues, gaps between slides and narration
- Queue observations without interrupting mid-slide
- Ask clarifying questions when appropriate (as a real attendee would)
- Focus on practical clarity - will SMB owners understand this?

Output format for logged feedback:
- [TIMESTAMP] OBSERVATION: <what you noticed>
- [TIMESTAMP] QUESTION: <what needs clarification>
- [TIMESTAMP] POSITIVE: <what worked well>

Success Criteria
Must have:

✅ Runs for 60+ minutes without crashing
✅ Screen frames visible to Gemini (verify in logs)
✅ Audio streaming works (verify Gemini hears presenter)
✅ Responses logged to timestamped file
✅ Graceful start/stop via CLI

Nice to have:

Frame rate adjusts when screen changes (higher) vs static (lower)
Live console output showing Gemini's real-time reactions
Session stats at end (frames sent, audio minutes, response count)


Scope Boundaries (What NOT to Build)
❌ No GUI - CLI only
❌ No real-time voice interruption (log-only for v1)
❌ No video encoding - raw frame streaming is fine
❌ No fancy error recovery - fail fast and log errors
❌ No configuration files - hardcode for MVP
❌ No multi-session support - one rehearsal at a time

Suggested File Structure
workshop-attendee/
├── main.py              # Entry point, CLI interface
├── screen_capture.py    # Frame grabbing logic
├── audio_stream.py      # Mic audio capture
├── gemini_session.py    # Live API connection & streaming
├── logger.py            # Response logging to file
├── requirements.txt     # Dependencies
└── README.md            # How to run

Key Architecture Notes
Screen Capture Loop:

Grab frame every 300-500ms (2-3 fps)
Resize to 720p max (bandwidth/cost)
Convert to format Gemini accepts (JPEG base64 or PNG)

Audio Streaming:

16kHz, mono, 16-bit PCM (Gemini's expected input format)
Send in small chunks (1024 byte buffers typical)
Continuous stream, not chunked files

Gemini Session:

WebSocket connection via client.aio.live.connect()
Send screen frames and audio in parallel async tasks
Listen for responses in separate async task
Log responses with timestamps

Logging:

Filename: workshop_feedback_YYYYMMDD_HHMMSS.txt
Format: [HH:MM:SS] TYPE: content
Flush after each write (don't lose data on crash)


Environment Setup Needed
bashpip install google-genai pyaudio mss pillow python-dotenv

# Set API key
export GOOGLE_API_KEY="your-key-here"
# or use .env file

Testing Before Sunday
Quick validation:

Run for 5 minutes on a test slide deck
Verify log file created with timestamped responses
Confirm Gemini can "see" slide content (ask it to describe what's on screen)
Confirm Gemini can "hear" you (speak and check if it responds)

If it breaks:

Fallback plan: Record session with OBS/Loom
Upload 10-min chunks to Gemini web interface
Get async feedback (less cool, but functional)


Output Deliverable
Working Python project that:

Starts with python main.py --session-name "Workshop Rehearsal"
Streams for duration of presentation
Stops with Ctrl+C (graceful shutdown)
Produces readable feedback log
Has README with "How to Run" instructions