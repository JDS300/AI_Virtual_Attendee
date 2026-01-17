# AI Workshop Attendee - Build Challenges

This document details the technical challenges encountered while building the AI Workshop Attendee MVP, their root causes, and the solutions implemented.

---

## 1. Screen Capture Failure on Multi-Monitor X11

**Issue:** `mss` library threw `XGetImage() failed` error when trying to capture any monitor.

**Cause:** The `mss` library uses X11's `XGetImage` directly, which has issues with complex multi-monitor setups involving different DPIs or HiDPI scaling (the system had 5 monitors with 1.25x scaling on some).

**Fix:** Switched to `pyscreenshot` library which uses the XDG Desktop Portal and handles multi-monitor setups more gracefully. Used `mss` only for monitor detection (listing works even when capture fails).

```python
# Before (failed)
screenshot = self.sct.grab(monitor)

# After (works)
img = pyscreenshot.grab(bbox=(left, top, right, bottom))
```

---

## 2. RGBA to RGB Conversion for JPEG

**Issue:** `OSError: cannot write mode RGBA as JPEG` when saving captured frames.

**Cause:** `pyscreenshot` returns RGBA images (with alpha channel), but JPEG format doesn't support transparency.

**Fix:** Convert RGBA to RGB before encoding:
```python
if img.mode == 'RGBA':
    img = img.convert('RGB')
```

---

## 3. API Key Not Loading from .env

**Issue:** `ValueError: GOOGLE_API_KEY environment variable not set` despite `.env` file existing.

**Cause:** `load_dotenv()` was called inside `main()` function, but `GeminiSession` was instantiated before environment variables were loaded into `os.environ`.

**Fix:** Moved `load_dotenv()` to module level, before any imports that need the API key:
```python
from dotenv import load_dotenv
load_dotenv()  # Must be before importing gemini_session

from gemini_session import GeminiSession
```

---

## 4. Wrong Gemini Model Name

**Issue:** `ConnectionClosedError: models/gemini-2.5-flash-preview-native-audio-dialog is not found`

**Cause:** Initial model name from project brief was incorrect/outdated.

**Fix:** Updated to correct model name: `gemini-2.5-flash-native-audio-preview-12-2025`

---

## 5. Async Context Manager Handling

**Issue:** `TypeError: '_AsyncGeneratorContextManager' object can't be awaited`

**Cause:** `client.aio.live.connect()` returns an async context manager, not a coroutine. Using `await` directly doesn't work.

**Fix:** Manually enter the context manager:
```python
# Before (failed)
self.session = await self.client.aio.live.connect(...)

# After (works)
self._session_ctx = self.client.aio.live.connect(...)
self.session = await self._session_ctx.__aenter__()
```

---

## 6. Native Audio Model Configuration

**Issue:** `ConnectionClosedError: Cannot extract voices from a non-audio request`

**Cause:** The native audio model requires `response_modalities=["AUDIO"]`. Using `["TEXT"]` or `["AUDIO", "TEXT"]` is not supported.

**Fix:** Set AUDIO-only modality with transcription for text output:
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    speech_config=types.SpeechConfig(...)
)
```

---

## 7. Microphone Sample Rate Mismatch

**Issue:** `OSError: [Errno -9997] Invalid sample rate` when opening HyperX mic at 16kHz.

**Cause:** HyperX Cloud Alpha Wireless only supports 48kHz sample rate, but Gemini requires 16kHz audio input.

**Fix:** Record at native 48kHz rate, resample to 16kHz using scipy:
```python
self.native_rate = 48000  # Record at native rate
# Resample to 16kHz
resampled = signal.resample(samples, num_samples)
```

---

## 8. audioop Module Removed in Python 3.14

**Issue:** `ModuleNotFoundError: No module named 'audioop'`

**Cause:** Python 3.14 removed the deprecated `audioop` module which was initially used for sample rate conversion.

**Fix:** Replaced `audioop.ratecv()` with `scipy.signal.resample()`:
```python
# Before (Python < 3.13)
import audioop
data, state = audioop.ratecv(data, 2, 1, 48000, 16000, state)

# After (Python 3.14+)
from scipy import signal
resampled = signal.resample(samples, num_samples).astype(np.int16)
```

---

## 9. Response Parsing for Audio Transcription

**Issue:** 0 responses logged despite Gemini being connected and active.

**Cause:** Native audio model returns responses differently - text comes via `output_transcription` attribute rather than direct `response.text`.

**Fix:** Handle multiple response formats:
```python
# Check for output_transcription (native audio model)
if hasattr(sc, 'output_transcription') and sc.output_transcription:
    text = sc.output_transcription.text

# Also check server_content.model_turn.parts
if hasattr(sc, 'model_turn') and sc.model_turn:
    for part in sc.model_turn.parts:
        if hasattr(part, 'text') and part.text:
            text = part.text
```

---

## Summary

| Challenge | Root Cause | Solution |
|-----------|-----------|----------|
| Screen capture fails | mss + X11 multi-monitor | Use pyscreenshot |
| JPEG encoding fails | RGBA images | Convert to RGB |
| API key not found | load_dotenv() timing | Move to module level |
| Model not found | Wrong model name | Use correct 12-2025 model |
| Await fails | Async context manager | Use __aenter__() |
| Audio request error | Wrong modality | Use AUDIO + transcription |
| Sample rate error | HyperX needs 48kHz | Resample with scipy |
| audioop missing | Python 3.14 removal | Use scipy.signal |
| No responses | Wrong attribute | Parse transcription |
