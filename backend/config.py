"""
Configuration for the Real-Time STT System.
"""

# Whisper model configuration
WHISPER_MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large

# Audio configuration
SAMPLE_RATE = 16000  # 16kHz - required by Whisper
CHANNELS = 1  # Mono audio
DTYPE = "float32"
AUDIO_GAIN = 5.0  # Software volume boost multiplier

# Streaming configuration
CHUNK_DURATION_MS = 500  # Expected chunk duration from client (ms)
CONTEXT_WINDOW_SECONDS = 10  # Rolling audio buffer duration for context
MAX_BUFFER_SECONDS = 30  # Maximum buffer before forced reset

# WebSocket server configuration
WS_HOST = "0.0.0.0"
WS_PORT = 8000

# FFmpeg configuration
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except (ImportError, AttributeError):
    FFMPEG_PATH = "ffmpeg"  # Fallback to system path
