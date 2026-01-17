Handoff Package
Project: AI Workshop Attendee MVP
Timeline: 3 hours max
Delivery: Tuesday 9pm
Full Brief Above ⬆️ (includes multi-monitor requirement)

Quick Start Commands for Agents
bash# Setup
mkdir workshop-attendee && cd workshop-attendee
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install deps
pip install google-genai pyaudio mss pillow python-dotenv

# Create .env
echo "GOOGLE_API_KEY=your-key-here" > .env

# Build per file structure in brief
# Test with: python main.py --monitor 2 --session-name "Test Run"

Priority Order if Time Runs Short

Screen capture + monitor selection (30 min)
Gemini Live API connection (45 min)
Audio streaming (45 min)
Response logging (20 min)
CLI polish (20 min)
README (20 min)

If you're at 2.5 hours and audio isn't working: ship screen-only version. JD can narrate without mic capture and still get visual feedback.

Communication Back to JD
When complete, deliver:

GitHub repo link (or zipped project)
30-second video demo (optional but impressive)
List of any blockers encountered
Estimated actual build time