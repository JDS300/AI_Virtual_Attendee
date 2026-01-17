import pyaudio
import numpy as np
from scipy import signal


class AudioStream:
    """Captures microphone audio and resamples to 16kHz/16-bit/mono PCM for Gemini Live API."""
    
    TARGET_RATE = 16000   # Gemini expects 16kHz
    CHANNELS = 1          # Mono
    FORMAT = pyaudio.paInt16  # 16-bit
    CHUNK = 1024          # Samples per chunk at native rate
    
    def __init__(self, device_index: int | None = None):
        """
        Initialize audio stream.
        
        Args:
            device_index: Audio input device index (None = default device)
        """
        self.pa = pyaudio.PyAudio()
        self.device_index = device_index
        self.stream = None
        self.running = False
        self.native_rate = None
    
    def list_devices(self) -> list[dict]:
        """List available audio input devices."""
        devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:  # Only input devices
                devices.append({
                    "index": i,
                    "name": info["name"],
                    "channels": info["maxInputChannels"],
                    "sample_rate": int(info["defaultSampleRate"])
                })
        return devices
    
    def start(self):
        """Open the audio input stream at native rate."""
        # Get native sample rate for the device
        if self.device_index is not None:
            info = self.pa.get_device_info_by_index(self.device_index)
            self.native_rate = int(info["defaultSampleRate"])
        else:
            # Default device - try common rates
            for rate in [48000, 44100, 16000]:
                try:
                    self.native_rate = rate
                    self.stream = self.pa.open(
                        format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=rate,
                        input=True,
                        input_device_index=self.device_index,
                        frames_per_buffer=self.CHUNK
                    )
                    self.running = True
                    print(f"🎤 Audio: Recording at {rate}Hz")
                    return
                except OSError:
                    continue
            raise OSError("Could not open audio stream at any sample rate")
        
        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.native_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.CHUNK
        )
        self.running = True
        print(f"🎤 Audio: Recording at {self.native_rate}Hz (device {self.device_index})")
    
    def read_chunk(self) -> bytes:
        """
        Read a chunk of audio data, resampled to 16kHz for Gemini.
        
        Returns:
            Raw PCM audio bytes at 16kHz
        """
        if not self.stream or not self.running:
            return b""
        
        # Read at native rate
        data = self.stream.read(self.CHUNK, exception_on_overflow=False)
        
        # Resample to 16kHz if needed
        if self.native_rate != self.TARGET_RATE:
            # Convert bytes to numpy array
            samples = np.frombuffer(data, dtype=np.int16)
            
            # Calculate resample ratio
            num_samples = int(len(samples) * self.TARGET_RATE / self.native_rate)
            
            # Resample using scipy
            resampled = signal.resample(samples, num_samples)
            
            # Convert back to int16 bytes
            data = resampled.astype(np.int16).tobytes()
        
        return data
    
    def stop(self):
        """Stop and close the audio stream."""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()


# Keep RATE and CHUNK as class attrs for backwards compatibility
AudioStream.RATE = AudioStream.TARGET_RATE


if __name__ == "__main__":
    # Quick test
    audio = AudioStream()
    print("Available input devices:")
    for d in audio.list_devices():
        print(f"  [{d['index']}] {d['name']} ({d['channels']}ch @ {d['sample_rate']}Hz)")
    
    print("\nCapturing 1 second of audio...")
    audio.start()
    chunks = []
    for _ in range(int(AudioStream.TARGET_RATE / AudioStream.CHUNK)):
        chunks.append(audio.read_chunk())
    audio.stop()
    
    total_bytes = sum(len(c) for c in chunks)
    print(f"Captured {total_bytes} bytes ({len(chunks)} chunks)")
