from datetime import datetime
from pathlib import Path


class FeedbackLogger:
    """Logs timestamped feedback to file with immediate flush for crash protection."""
    
    def __init__(self, session_name: str, output_dir: Path | None = None):
        """
        Initialize feedback logger.
        
        Args:
            session_name: Name for this session (used in filename)
            output_dir: Directory for log files (default: current directory)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = session_name.replace(" ", "_")
        
        if output_dir is None:
            output_dir = Path.cwd()
        
        self.filepath = output_dir / f"workshop_feedback_{safe_name}_{timestamp}.txt"
        self.file = open(self.filepath, "w", encoding="utf-8")
        self.response_count = 0
        self._log(f"Session started: {session_name}")
    
    def _log(self, message: str):
        """Write a timestamped line and flush immediately."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.file.write(f"[{timestamp}] {message}\n")
        self.file.flush()
    
    def log_response(self, text: str):
        """
        Log a Gemini response.
        
        Args:
            text: Response text from Gemini
        """
        self.response_count += 1
        for line in text.strip().split("\n"):
            if line.strip():  # Skip empty lines
                self._log(line)
    
    def log_stats(self, frames_sent: int, audio_seconds: float):
        """
        Log session statistics.
        
        Args:
            frames_sent: Number of screen frames sent
            audio_seconds: Duration of audio captured in seconds
        """
        self._log("--- SESSION STATS ---")
        self._log(f"Frames sent: {frames_sent}")
        self._log(f"Audio duration: {audio_seconds:.1f}s")
        self._log(f"Responses received: {self.response_count}")
    
    def close(self):
        """Close the log file."""
        self.file.close()


if __name__ == "__main__":
    # Quick test
    logger = FeedbackLogger("Test Session")
    logger.log_response("OBSERVATION: This is a test observation")
    logger.log_response("QUESTION: Is this working correctly?")
    logger.log_stats(frames_sent=10, audio_seconds=5.5)
    logger.close()
    print(f"Log written to: {logger.filepath}")
