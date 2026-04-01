"""
Whisper Transcription Engine
Loads and manages the Whisper model for speech-to-text inference.
"""

import whisper
import numpy as np
import logging
import time
from config import WHISPER_MODEL_SIZE

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Manages the Whisper model and provides transcription capabilities.
    The model is loaded once and reused for all transcription requests.
    """

    def __init__(self, model_size: str = WHISPER_MODEL_SIZE):
        """
        Initialize the transcriber and load the Whisper model.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the Whisper model into memory."""
        logger.info(f"Loading Whisper model '{self.model_size}'...")
        start = time.time()
        self.model = whisper.load_model(self.model_size)
        elapsed = time.time() - start
        logger.info(f"Whisper model '{self.model_size}' loaded in {elapsed:.2f}s")

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe audio data using Whisper.

        Args:
            audio: numpy float32 array of audio samples at 16kHz

        Returns:
            Transcribed text string
        """
        if audio is None or len(audio) == 0:
            return ""

        # Ensure audio is float32 as Whisper expects
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        try:
            start = time.time()

            # Transcribe with Whisper
            # fp16=False for CPU compatibility; set to True if using CUDA
            result = self.model.transcribe(
                audio,
                fp16=False,
                language=None,             # Auto-detect language
                no_speech_threshold=0.1,    # Extremely sensitive to quiet speech
                condition_on_previous_text=False,
            )

            text = result.get("text", "").strip()
            elapsed = time.time() - start

            logger.debug(
                f"Transcription: {len(audio)/16000:.2f}s audio -> "
                f"'{text[:80]}...' in {elapsed:.2f}s"
            )

            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def is_loaded(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.model is not None
