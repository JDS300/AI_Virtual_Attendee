import asyncio
import os
from typing import Callable
from google import genai
from google.genai import types


SYSTEM_PROMPT = """You are attending a 4-hour AI workshop for small business professionals.

Your role:
- Watch slides as they change on screen
- Listen to the presenter's explanations
- Identify: unclear explanations, pacing issues, gaps between slides and narration
- Queue observations without interrupting mid-slide
- Ask clarifying questions when appropriate (as a real attendee would)
- Focus on practical clarity - will SMB owners understand this?

Output format for feedback:
- OBSERVATION: <what you noticed>
- QUESTION: <what needs clarification>
- POSITIVE: <what worked well>
"""


class GeminiSession:
    """Manages Live API WebSocket connection for multimodal streaming."""
    
    # Model with native audio support for Live API
    MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
    
    def __init__(self, on_response_callback: Callable[[str], None]):
        """
        Initialize Gemini session.
        
        Args:
            on_response_callback: Function to call with each text response
        """
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set. Check your .env file.")
        self.client = genai.Client(api_key=api_key)
        self.session = None
        self.on_response = on_response_callback
        self.running = False
    
    async def connect(self):
        """Establish Live API WebSocket connection."""
        # Native audio model requires AUDIO modality only
        # Use output_audio_transcription to get text transcripts for logging
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],  # Native audio models require AUDIO
            output_audio_transcription=types.AudioTranscriptionConfig(),  # Get text transcripts
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=SYSTEM_PROMPT)]
            ),
        )
        # live.connect() returns an async context manager, so we enter it manually
        self._session_ctx = self.client.aio.live.connect(
            model=self.MODEL,
            config=config
        )
        self.session = await self._session_ctx.__aenter__()
        self.running = True
    
    async def send_frame(self, base64_jpeg: str):
        """
        Send a screen frame to Gemini.
        
        Args:
            base64_jpeg: Base64-encoded JPEG image data
        """
        if self.session and self.running:
            await self.session.send_realtime_input(
                media=types.Blob(mime_type="image/jpeg", data=base64_jpeg)
            )
    
    async def send_audio(self, pcm_data: bytes):
        """
        Send audio chunk to Gemini.
        
        Args:
            pcm_data: Raw 16-bit PCM audio at 16kHz
        """
        if self.session and self.running:
            await self.session.send_realtime_input(
                media=types.Blob(mime_type="audio/pcm", data=pcm_data)
            )
    
    async def listen_for_responses(self):
        """Listen for Gemini responses and pass to callback."""
        try:
            async for response in self.session.receive():
                # Handle different response types
                text = None
                
                # Check for direct text
                if hasattr(response, 'text') and response.text:
                    text = response.text
                
                # Check for server_content with model_turn parts
                elif hasattr(response, 'server_content') and response.server_content:
                    sc = response.server_content
                    if hasattr(sc, 'model_turn') and sc.model_turn:
                        for part in sc.model_turn.parts:
                            if hasattr(part, 'text') and part.text:
                                text = part.text
                                break
                    # Check for output_transcription
                    if hasattr(sc, 'output_transcription') and sc.output_transcription:
                        text = sc.output_transcription.text
                
                if text:
                    self.on_response(text)
                    print(f"💬 Gemini: {text}")
        except Exception as e:
            if self.running:  # Only log if not intentionally stopped
                print(f"Response listener error: {e}")
    
    async def disconnect(self):
        """Close the session."""
        self.running = False
        if hasattr(self, '_session_ctx') and self._session_ctx:
            try:
                await self._session_ctx.__aexit__(None, None, None)
            except Exception:
                pass  # Ignore errors during cleanup
