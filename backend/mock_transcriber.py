import random
import time

class WhisperTranscriber:
    """Mock Whisper transcriber for development/testing."""
    
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self._is_loaded = True
        print(f"DEBUG: Initialized Mock WhisperTranscriber ({model_size})")

    def is_loaded(self) -> bool:
        return self._is_loaded

    def transcribe(self, audio_data) -> str:
        """Simulate transcription with random words or phrases."""
        if audio_data is None or len(audio_data) == 0:
            return ""
        
        # Simulate processing time
        time.sleep(0.1)
        
        phrases = [
            "The quick brown fox",
            "jumps over the lazy dog",
            "Real-time speech to text is working",
            "Whisper model is amazing",
            "Low latency transcription",
            "Streaming audio chunks",
            "Python backend is ready",
            "React frontend is connected"
        ]
        
        # Return a random phrase if there's enough audio
        if len(audio_data) > 1000:
            return random.choice(phrases)
        return ""
