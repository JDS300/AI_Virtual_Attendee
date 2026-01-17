import pyscreenshot
import base64
from PIL import Image
from io import BytesIO


class ScreenCapture:
    """Captures screen frames, resizes to 720p, encodes to base64 JPEG.
    
    Uses pyscreenshot for better Linux multi-monitor compatibility.
    """
    
    # Define monitor regions (left, top, right, bottom) - will be auto-detected
    _monitors = None
    
    def __init__(self, monitor_index: int = 0, max_height: int = 720):
        """
        Initialize screen capture.
        
        Args:
            monitor_index: Monitor to capture (0=full desktop, or specify region index)
            max_height: Maximum height in pixels (frames will be resized proportionally)
        """
        self.monitor_index = monitor_index
        self.max_height = max_height
        
        # Auto-detect monitors on first init
        if ScreenCapture._monitors is None:
            self._detect_monitors()
    
    def _detect_monitors(self):
        """Detect available monitors by grabbing full screen and inspecting."""
        # Try to get monitor info from mss (even if capture fails, listing works)
        try:
            import mss
            with mss.mss() as sct:
                # Monitors: [0] is combined, [1+] are individual
                ScreenCapture._monitors = []
                for m in sct.monitors[1:]:  # Skip combined monitor [0]
                    # pyscreenshot uses (left, top, right, bottom)
                    ScreenCapture._monitors.append({
                        'left': m['left'],
                        'top': m['top'],
                        'right': m['left'] + m['width'],
                        'bottom': m['top'] + m['height'],
                        'width': m['width'],
                        'height': m['height']
                    })
        except Exception:
            # Fallback: just use full screen
            ScreenCapture._monitors = []
    
    def list_monitors(self) -> list[dict]:
        """Return available monitors as regions."""
        return [{"index": 0, "description": "Full desktop (all monitors)"}] + [
            {"index": i+1, **m} for i, m in enumerate(ScreenCapture._monitors)
        ]
    
    def capture_frame(self) -> str:
        """
        Capture frame, resize to max_height, return as base64 JPEG.
        
        Returns:
            Base64-encoded JPEG string
        """
        if self.monitor_index == 0 or not ScreenCapture._monitors:
            # Capture full desktop
            img = pyscreenshot.grab()
        else:
            # Capture specific monitor region
            try:
                m = ScreenCapture._monitors[self.monitor_index - 1]
                bbox = (m['left'], m['top'], m['right'], m['bottom'])
                img = pyscreenshot.grab(bbox=bbox)
            except IndexError:
                # Fallback to full desktop
                img = pyscreenshot.grab()
        
        # Resize if height exceeds max
        if img.height > self.max_height:
            ratio = self.max_height / img.height
            new_size = (int(img.width * ratio), self.max_height)
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert RGBA to RGB (JPEG doesn't support alpha)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Encode to base64 JPEG
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


if __name__ == "__main__":
    # Quick test
    sc = ScreenCapture(monitor_index=0)
    print("Available monitors:")
    for m in sc.list_monitors():
        print(f"  {m}")
    
    print("\nCapturing full desktop (index 0)...")
    frame = sc.capture_frame()
    print(f"Captured frame: {len(frame)} bytes (base64)")
    
    # Test individual monitors
    if len(sc.list_monitors()) > 1:
        print("\nTesting monitor 1...")
        sc.monitor_index = 1
        frame = sc.capture_frame()
        print(f"Monitor 1 frame: {len(frame)} bytes (base64)")
