import { useAudioStream } from './hooks/useAudioStream';
import './App.css';

function App() {
  const {
    isRecording,
    isConnected,
    partialText,
    fullText,
    audioLevel,
    error,
    stats,
    startRecording,
    stopRecording,
    resetTranscription,
  } = useAudioStream();

  return (
    <div className="app">
      {/* Background animated gradient */}
      <div className="bg-gradient" />

      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="logo">
            <div className="logo-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </div>
            <h1>RealTime STT</h1>
          </div>
          <p className="subtitle">
            Live speech-to-text powered by Whisper &bull; Streaming architecture
          </p>
        </header>

        {/* Status Indicators */}
        <div className="status-bar">
          <div className={`status-chip ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot" />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          {isRecording && (
            <div className="status-chip recording">
              <span className="status-dot pulse" />
              Recording
            </div>
          )}
          {stats && (
            <div className="status-chip stats">
              Chunks: {stats.chunks_received} &bull; Audio: {stats.total_audio_s}s
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-banner">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            {error}
          </div>
        )}

        {/* Audio Level Visualizer */}
        {isRecording && (
          <div className="audio-visualizer">
            <div className="level-bars">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className={`level-bar ${audioLevel * 20 > i ? 'active' : ''}`}
                  style={{
                    height: `${20 + Math.random() * (audioLevel * 100)}%`,
                    animationDelay: `${i * 0.05}s`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="controls">
          {!isRecording ? (
            <button
              id="btn-start"
              className="btn btn-start"
              onClick={startRecording}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
              Start Recording
            </button>
          ) : (
            <button
              id="btn-stop"
              className="btn btn-stop"
              onClick={stopRecording}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              Stop Recording
            </button>
          )}

          <button
            id="btn-reset"
            className="btn btn-reset"
            onClick={resetTranscription}
            disabled={!partialText && !fullText}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            Clear
          </button>
        </div>

        {/* Transcription Display */}
        <div className="transcription-panel">
          <div className="panel-header">
            <h2>Live Transcription</h2>
            {isRecording && <div className="live-badge">LIVE</div>}
          </div>

          <div className="transcription-content">
            {!partialText && !fullText ? (
              <div className="placeholder">
                {isRecording
                  ? 'Listening... Start speaking to see transcription.'
                  : 'Click "Start Recording" to begin live transcription.'}
              </div>
            ) : (
              <>
                {fullText && (
                  <div className="transcript-section">
                    <span className="section-label">Accumulated</span>
                    <p className="transcript-text full-text">{fullText}</p>
                  </div>
                )}
                {partialText && (
                  <div className="transcript-section">
                    <span className="section-label">Current Window</span>
                    <p className="transcript-text partial-text">{partialText}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="footer">
          <p>
            Powered by <strong>OpenAI Whisper</strong> &bull; WebSocket Streaming
            &bull; Inspired by NVIDIA NeMo
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
