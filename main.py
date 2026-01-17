#!/usr/bin/env python3
"""
AI Workshop Attendee - Real-time presentation feedback using Gemini Live API.

Streams screen and microphone to Gemini 2.5 Flash Native Audio, acting as a 
virtual workshop attendee that observes and provides feedback.
"""

import asyncio
import argparse
import signal
import sys

# Load .env BEFORE importing modules that need GOOGLE_API_KEY
from dotenv import load_dotenv
load_dotenv()

from screen_capture import ScreenCapture
from audio_stream import AudioStream
from gemini_session import GeminiSession
from logger import FeedbackLogger


class WorkshopAttendee:
    """Orchestrates screen capture, audio streaming, and Gemini feedback."""
    
    FRAME_INTERVAL = 0.4  # ~2.5 fps
    
    def __init__(self, session_name: str, monitor: int, audio_device: int | None = None):
        """
        Initialize the workshop attendee.
        
        Args:
            session_name: Name for this session (used in logs)
            monitor: Monitor index to capture (0=all, 1+=individual)
            audio_device: Audio input device index (None=default, 5=HyperX)
        """
        self.logger = FeedbackLogger(session_name)
        self.screen = ScreenCapture(monitor_index=monitor)
        self.audio = AudioStream(device_index=audio_device)
        self.gemini = GeminiSession(on_response_callback=self.logger.log_response)
        
        self.running = False
        self.frames_sent = 0
        self.audio_chunks_sent = 0
    
    async def run(self):
        """Main run loop - streams screen and audio to Gemini."""
        await self.gemini.connect()
        self.audio.start()
        self.running = True
        
        print(f"🎬 Session started. Streaming to Gemini...")
        print(f"📁 Logging to: {self.logger.filepath}")
        print("Press Ctrl+C to stop.\n")
        
        # Run tasks concurrently
        try:
            await asyncio.gather(
                self._screen_loop(),
                self._audio_loop(),
                self.gemini.listen_for_responses(),
            )
        except asyncio.CancelledError:
            pass  # Expected on shutdown
    
    async def _screen_loop(self):
        """Capture and send screen frames."""
        while self.running:
            try:
                frame = self.screen.capture_frame()
                await self.gemini.send_frame(frame)
                self.frames_sent += 1
                if self.frames_sent % 10 == 0:
                    print(f"📷 Frames sent: {self.frames_sent}", end="\r")
                await asyncio.sleep(self.FRAME_INTERVAL)
            except Exception as e:
                print(f"Screen error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    async def _audio_loop(self):
        """Capture and send audio chunks."""
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                # Run blocking read in executor to avoid blocking the event loop
                chunk = await loop.run_in_executor(None, self.audio.read_chunk)
                if chunk:
                    await self.gemini.send_audio(chunk)
                    self.audio_chunks_sent += 1
            except Exception as e:
                print(f"Audio error: {e}")
                await asyncio.sleep(0.1)
    
    async def shutdown(self):
        """Graceful shutdown with stats."""
        print("\n⏹️  Stopping session...")
        self.running = False
        
        self.audio.stop()
        await self.gemini.disconnect()
        
        # Calculate audio duration: chunks * bytes_per_chunk / (sample_rate * bytes_per_sample)
        audio_seconds = (self.audio_chunks_sent * AudioStream.CHUNK) / (AudioStream.RATE * 2)
        
        self.logger.log_stats(self.frames_sent, audio_seconds)
        self.logger.close()
        
        print(f"\n✅ Session complete!")
        print(f"   📷 Frames: {self.frames_sent}")
        print(f"   🎤 Audio: {audio_seconds:.1f}s")
        print(f"   📝 Log: {self.logger.filepath}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Workshop Attendee - Real-time presentation feedback"
    )
    parser.add_argument(
        "--session-name", 
        default="Workshop Rehearsal",
        help="Name for this session (default: 'Workshop Rehearsal')"
    )
    parser.add_argument(
        "--monitor", 
        type=int, 
        default=0,
        help="Monitor index to capture (0=all, 1+=individual, default: 0)"
    )
    parser.add_argument(
        "--audio-device",
        type=int,
        default=5,
        help="Audio input device index (default: 5=HyperX)"
    )
    parser.add_argument(
        "--list-monitors",
        action="store_true",
        help="List available monitors and exit"
    )
    args = parser.parse_args()
    
    # List monitors if requested
    if args.list_monitors:
        sc = ScreenCapture()
        print("Available monitors:")
        for i, m in enumerate(sc.list_monitors()):
            print(f"  [{i}] {m}")
        return
    
    attendee = WorkshopAttendee(args.session_name, args.monitor, args.audio_device)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal...")
        asyncio.get_event_loop().create_task(attendee.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(attendee.run())
    except KeyboardInterrupt:
        # Fallback if signal handler didn't catch it
        asyncio.run(attendee.shutdown())


if __name__ == "__main__":
    main()
