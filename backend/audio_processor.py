"""
Audio Processing Module
Handles conversion of incoming WebM/Opus audio to WAV PCM format using FFmpeg.
"""

import subprocess
import numpy as np
import logging
from config import SAMPLE_RATE, CHANNELS, FFMPEG_PATH, AUDIO_GAIN

logger = logging.getLogger(__name__)


def convert_audio_to_pcm(audio_bytes: bytes) -> np.ndarray | None:
    """
    Convert incoming audio bytes (WebM/Opus or any format FFmpeg supports)
    to a 16kHz mono float32 numpy array suitable for Whisper.

    Args:
        audio_bytes: Raw audio data from the client

    Returns:
        numpy array of float32 PCM samples, or None if conversion fails
    """
    if not audio_bytes or len(audio_bytes) < 100:
        logger.warning("Received empty or too-small audio chunk, skipping")
        return None

    try:
        # Use FFmpeg to convert any input format to raw PCM float32
        process = subprocess.run(
            [
                FFMPEG_PATH,
                "-i", "pipe:0",          # Read from stdin
                "-f", "f32le",            # Output format: raw 32-bit float little-endian
                "-acodec", "pcm_f32le",   # PCM float32
                "-ar", str(SAMPLE_RATE),  # Resample to 16kHz
                "-ac", str(CHANNELS),     # Mono
                "-v", "error",            # Only show errors
                "pipe:1"                  # Write to stdout
            ],
            input=audio_bytes,
            capture_output=True,
            timeout=10
        )

        if process.returncode != 0:
            stderr = process.stderr.decode("utf-8", errors="replace")
            logger.error(f"FFmpeg conversion failed: {stderr}")
            return None

        raw_pcm = process.stdout

        if len(raw_pcm) == 0:
            logger.warning("FFmpeg produced empty output")
            return None

        # Convert raw bytes to numpy float32 array
        audio_array = np.frombuffer(raw_pcm, dtype=np.float32)

        # Apply software gain boost
        if AUDIO_GAIN != 1.0:
            audio_array = audio_array * AUDIO_GAIN

        # Validate the audio data
        if np.any(np.isnan(audio_array)) or np.any(np.isinf(audio_array)):
            logger.warning("Audio contains NaN or Inf values, cleaning up")
            audio_array = np.nan_to_num(audio_array, nan=0.0, posinf=1.0, neginf=-1.0)

        # Clip to valid range [-1.0, 1.0] after gain
        audio_array = np.clip(audio_array, -1.0, 1.0)

        logger.debug(
            f"Converted audio: {len(audio_bytes)} bytes -> "
            f"{len(audio_array)} samples ({len(audio_array)/SAMPLE_RATE:.2f}s, Gain={AUDIO_GAIN}x)"
        )

        return audio_array

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        return None
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return None


def get_audio_level(audio: np.ndarray) -> float:
    """
    Calculate the RMS audio level (0.0 to 1.0) for visualization.
    """
    if audio is None or len(audio) == 0:
        return 0.0
    rms = np.sqrt(np.mean(audio ** 2))
    return min(float(rms), 1.0)
