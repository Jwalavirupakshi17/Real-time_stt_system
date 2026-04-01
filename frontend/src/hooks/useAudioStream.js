import { useState, useRef, useCallback, useEffect } from 'react';

const WS_URL = 'ws://localhost:8000/ws/transcribe';

/**
 * Custom hook for managing audio capture and WebSocket streaming.
 * Handles microphone access, MediaRecorder chunks, and WS communication.
 */
export function useAudioStream() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [partialText, setPartialText] = useState('');
  const [fullText, setFullText] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const connectWebSocket = useCallback(() => {
    return new Promise((resolve, reject) => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[WS] Connected');
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            switch (data.type) {
              case 'connected':
                console.log('[WS]', data.message);
                resolve(ws);
                break;

              case 'transcription':
                if (data.partial !== undefined) setPartialText(data.partial);
                if (data.full !== undefined) setFullText(data.full);
                if (data.audio_level !== undefined) setAudioLevel(data.audio_level);
                break;

              case 'audio_level':
                if (data.audio_level !== undefined) setAudioLevel(data.audio_level);
                break;

              case 'final':
                if (data.partial !== undefined) setPartialText(data.partial);
                if (data.full !== undefined) setFullText(data.full);
                if (data.stats) setStats(data.stats);
                break;

              case 'reset':
                setPartialText('');
                setFullText('');
                setAudioLevel(0);
                break;

              case 'error':
                setError(data.message);
                break;

              default:
                console.log('[WS] Unknown message type:', data.type);
            }
          } catch (e) {
            console.error('[WS] Parse error:', e);
          }
        };

        ws.onerror = (e) => {
          console.error('[WS] Error:', e);
          setError('WebSocket connection error. Is the backend running?');
          setIsConnected(false);
          reject(e);
        };

        ws.onclose = () => {
          console.log('[WS] Disconnected');
          setIsConnected(false);
        };
      } catch (e) {
        reject(e);
      }
    });
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setPartialText('');
      setFullText('');
      setAudioLevel(0);
      setStats(null);

      // Connect WebSocket first
      await connectWebSocket();

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
        video: false,
      });
      streamRef.current = stream;

      // Create MediaRecorder with WebM/Opus format
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (
          event.data.size > 0 &&
          wsRef.current &&
          wsRef.current.readyState === WebSocket.OPEN
        ) {
          wsRef.current.send(event.data);
        }
      };

      mediaRecorder.onerror = (e) => {
        console.error('[MediaRecorder] Error:', e);
        setError('Microphone recording error');
      };

      // Start recording with 500ms timeslice for chunk-based streaming
      mediaRecorder.start(500);
      setIsRecording(true);
      console.log('[Recorder] Started with 500ms chunks');
    } catch (e) {
      console.error('Start recording error:', e);
      if (e.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone access.');
      } else if (e.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone.');
      } else {
        setError(`Failed to start recording: ${e.message}`);
      }
    }
  }, [connectWebSocket]);

  const stopRecording = useCallback(() => {
    // Send stop signal to server
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
    }

    // Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;

    // Stop media stream tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    streamRef.current = null;

    // Close WebSocket after a short delay to receive final transcription
    setTimeout(() => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }, 1500);

    setIsRecording(false);
    setAudioLevel(0);
    console.log('[Recorder] Stopped');
  }, []);

  const resetTranscription = useCallback(() => {
    setPartialText('');
    setFullText('');
    setAudioLevel(0);
    setStats(null);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'reset' }));
    }
  }, []);

  return {
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
  };
}
