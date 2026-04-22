# Data Flow Diagram (DFD)

```mermaid
flowchart TD
    Mic["🎤 Browser Microphone"] -->|Captures raw audio| MediaRecorder["MediaRecorder (500ms WebM chunks)"]
    MediaRecorder -->|Binary WebSocket message| FastAPI["FastAPI WebSocket Server"]
    FastAPI -->|Raw WebM bytes| FFmpeg["Audio Processor (FFmpeg)"]
    FFmpeg -->|16kHz mono PCM float32 array| StreamMgr["Stream Manager (rolling buffer)"]
    StreamMgr -->|Context audio window (last 10s)| QwenASR["Qwen3-ASR-0.6B Model"]
    QwenASR -->|Transcribed text| StreamMgr
    StreamMgr -->|Accumulated transcript history| FastAPI
    StreamMgr -->|Saves timestamped text| TranscriptFile[("📄 transcripts/*.txt")]
    FastAPI -->|JSON response (partial + history)| ReactUI["React Frontend UI"]
    ReactUI -->|Displays scrollable transcript| User["👤 User"]
    FastAPI -->|Events, metrics, errors| Logger["App Logger"]
    FFmpeg -->|Conversion time, I/O sizes| Logger
    QwenASR -->|Inference time, memory usage| Logger
    Logger -->|Structured logs| LogFile[("📋 performance.log")]
```
