"""
Stream Manager
Maintains a rolling audio buffer per session for context-aware transcription.
Inspired by NVIDIA NeMo's streaming approach.
"""

import numpy as np
import logging
from config import SAMPLE_RATE, CONTEXT_WINDOW_SECONDS, MAX_BUFFER_SECONDS

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages the audio stream for a single WebSocket session.
    
    - Maintains a rolling buffer of recent audio for context
    - Tracks the full transcript accumulated over the session
    - Provides context-aware audio windows for Whisper transcription
    """

    def __init__(self):
        self.audio_buffer = np.array([], dtype=np.float32)
        self.raw_buffer = b""  # Store raw WebM bytes
        self.full_transcript = ""
        self.chunk_count = 0
        self.total_audio_seconds = 0.0

        # Context window sizes in samples
        self._context_samples = CONTEXT_WINDOW_SECONDS * SAMPLE_RATE
        self._max_samples = MAX_BUFFER_SECONDS * SAMPLE_RATE

    def add_chunk(self, chunk: np.ndarray) -> None:
        """
        Add a new audio chunk to the rolling buffer.
        """
        if chunk is None or len(chunk) == 0:
            return

        self.audio_buffer = np.concatenate([self.audio_buffer, chunk])
        self.chunk_count += 1
        self.total_audio_seconds += len(chunk) / SAMPLE_RATE

        # Trim buffer if it exceeds max size
        if len(self.audio_buffer) > self._max_samples:
            overflow = len(self.audio_buffer) - self._context_samples
            self.audio_buffer = self.audio_buffer[overflow:]

    def add_raw_chunk(self, chunk: bytes) -> None:
        """Add raw WebM bytes to the buffer."""
        if chunk:
            self.raw_buffer += chunk

    def set_audio_buffer(self, audio: np.ndarray) -> None:
        """Replace the PCM buffer with newly converted audio."""
        if audio is not None:
            self.audio_buffer = audio
            # Update chunk count and total time
            self.chunk_count += 1
            self.total_audio_seconds = len(audio) / SAMPLE_RATE

    def get_raw_buffer(self) -> bytes:
        """Get the accumulated raw WebM bytes."""
        return self.raw_buffer

    def get_context_audio(self) -> np.ndarray:
        """
        Get the current audio context window for transcription.
        Returns the last CONTEXT_WINDOW_SECONDS of audio.

        Returns:
            numpy float32 array of recent audio
        """
        if len(self.audio_buffer) <= self._context_samples:
            return self.audio_buffer.copy()
        return self.audio_buffer[-self._context_samples:].copy()

    def get_latest_chunk_audio(self) -> np.ndarray:
        """
        Get just the audio from the most recent few seconds 
        for quick partial transcription.
        """
        # Return last 3 seconds or full buffer if shorter
        quick_window = 3 * SAMPLE_RATE
        if len(self.audio_buffer) <= quick_window:
            return self.audio_buffer.copy()
        return self.audio_buffer[-quick_window:].copy()

    def append_transcript(self, text: str) -> None:
        """Append finalized text to the full transcript."""
        if text:
            if self.full_transcript:
                self.full_transcript += " " + text
            else:
                self.full_transcript = text

    def get_full_transcript(self) -> str:
        """Get the accumulated full transcript."""
        return self.full_transcript

    def get_buffer_duration(self) -> float:
        """Get the current buffer duration in seconds."""
        return len(self.audio_buffer) / SAMPLE_RATE

    def reset(self) -> None:
        """Reset the stream manager state."""
        self.audio_buffer = np.array([], dtype=np.float32)
        self.full_transcript = ""
        self.chunk_count = 0
        self.total_audio_seconds = 0.0

    def get_stats(self) -> dict:
        """Get current stream statistics."""
        return {
            "chunks_received": self.chunk_count,
            "buffer_duration_s": round(self.get_buffer_duration(), 2),
            "total_audio_s": round(self.total_audio_seconds, 2),
            "transcript_length": len(self.full_transcript),
        }
