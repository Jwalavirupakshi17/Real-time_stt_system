# Real-Time Speech-to-Text Streaming System

A real-time live transcription system where speech is converted to text **continuously while speaking** — not after completion. Built with a **Python WebSocket backend** using **Whisper** and a **React frontend**.

## Architecture

```
┌─────────────────────┐     WebSocket (binary audio)     ┌──────────────────────────┐
│   React Frontend    │  ───────────────────────────────► │   FastAPI Backend        │
│                     │                                   │                          │
│  MediaRecorder      │     WebSocket (JSON text)         │  Audio Processor (FFmpeg)│
│  (500ms chunks)     │  ◄─────────────────────────────── │  Whisper Transcriber     │
│  Live Transcript UI │                                   │  Stream Manager (buffer) │
└─────────────────────┘                                   └──────────────────────────┘
```

**Streaming flow:**
1. Browser captures mic audio → MediaRecorder produces 500ms WebM/Opus chunks
2. Chunks sent as binary over WebSocket
3. Backend converts to WAV via FFmpeg → feeds to Whisper with rolling context buffer
4. Partial transcription returned as JSON → UI updates live

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm
- **FFmpeg** installed and on PATH ([download](https://ffmpeg.org/download.html))
- ~500MB disk for Whisper `base` model (auto-downloads on first run)

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** If you have a CUDA GPU, install PyTorch with CUDA support for faster inference:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cu121
> ```

### Frontend

```bash
cd frontend
npm install
```

## Running

### 1. Start the Backend

```bash
cd backend
python server.py
```

The server starts on `http://localhost:8000`. On first run, Whisper downloads the `base` model (~140MB).

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

Opens at `http://localhost:5173`.

### 3. Use the App

1. Open `http://localhost:5173` in your browser
2. Click **Start Recording** — allow microphone access when prompted
3. Speak — text appears live as you talk
4. Click **Stop Recording** to end the session

## Project Structure

```
realtime-stt-system/
├── backend/
│   ├── config.py            # Configuration (model size, sample rate, ports)
│   ├── audio_processor.py   # FFmpeg audio conversion (WebM → WAV PCM)
│   ├── transcriber.py       # Whisper model loading & inference
│   ├── stream_manager.py    # Rolling audio buffer & session state
│   ├── server.py            # FastAPI WebSocket server
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main UI component
│   │   ├── App.css          # Styling (dark theme, glassmorphism)
│   │   ├── hooks/
│   │   │   └── useAudioStream.js  # Audio capture & WS hook
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Configuration

Edit `backend/config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `WHISPER_MODEL_SIZE` | `"base"` | Model: `tiny`, `base`, `small`, `medium`, `large` |
| `SAMPLE_RATE` | `16000` | Audio sample rate (Whisper requires 16kHz) |
| `CONTEXT_WINDOW_SECONDS` | `10` | Rolling buffer for context-aware transcription |
| `WS_PORT` | `8000` | WebSocket server port |

## Notes on Streaming & Chunk Handling

- **Not batch processing:** Audio is processed incrementally as 500ms chunks arrive, not after the full recording completes.
- **Context buffer:** A rolling 10-second audio buffer provides context so Whisper can produce coherent output rather than isolated word fragments.
- **Throttled inference:** Transcriptions run at most every 800ms to balance latency vs CPU load.
- **Whisper limitation:** Whisper is designed for batch transcription, not true streaming. This system simulates streaming by re-transcribing the context window on each chunk. For production, consider `faster-whisper` or `whisper.cpp` for lower latency.
- **Inspired by NeMo:** The chunk-based inference and rolling buffer approach mirrors NVIDIA NeMo's streaming ASR architecture.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "WebSocket connection error" | Ensure backend is running on port 8000 |
| "Microphone access denied" | Allow mic access in browser permissions |
| FFmpeg errors | Verify `ffmpeg` is installed: `ffmpeg -version` |
| Slow transcription | Use `tiny` model in `config.py` or use GPU |
| No text appears | Check browser console + backend terminal for errors |
