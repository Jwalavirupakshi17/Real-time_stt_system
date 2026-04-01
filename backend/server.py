"""
Real-Time Speech-to-Text WebSocket Server

FastAPI server that accepts streaming audio via WebSocket,
processes chunks through Whisper, and returns live transcription.
"""

import json
import asyncio
import logging
import time
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from config import WS_HOST, WS_PORT
from audio_processor import convert_audio_to_pcm, get_audio_level
try:
    from transcriber import WhisperTranscriber
    REAL_WHISPER = True
except (ImportError, ModuleNotFoundError):
    from mock_transcriber import WhisperTranscriber
    REAL_WHISPER = False
from stream_manager import StreamManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global transcriber instance (loaded once at startup)
transcriber: WhisperTranscriber | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load Whisper model on startup."""
    global transcriber
    logger.info("=" * 60)
    logger.info("  Real-Time STT Server Starting...")
    if not REAL_WHISPER:
        logger.warning("  WARNING: Whisper dependencies not found. Using MOCK transcriber.")
    logger.info("=" * 60)
    transcriber = WhisperTranscriber()
    logger.info("Server ready! Waiting for connections...")
    yield
    logger.info("Server shutting down...")


app = FastAPI(
    title="Real-Time STT Server",
    description="WebSocket-based streaming speech-to-text using Whisper",
    lifespan=lifespan,
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": transcriber is not None and transcriber.is_loaded(),
    }


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the built-in frontend UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RealTime STT</title>
<script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0a0e1a;--card:rgba(17,24,39,.7);--txt:#f1f5f9;--txt2:#94a3b8;--muted:#64748b;--blue:#3b82f6;--cyan:#22d3ee;--violet:#8b5cf6;--rose:#f43f5e;--green:#10b981;--amber:#f59e0b;--border:rgba(148,163,184,.1);--grad:linear-gradient(135deg,#3b82f6,#8b5cf6);--gradrec:linear-gradient(135deg,#f43f5e,#f59e0b)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--txt);min-height:100vh;display:flex;justify-content:center}
.c{position:relative;z-index:1;width:100%;max-width:760px;padding:2rem 1.5rem;display:flex;flex-direction:column;gap:1.5rem}
.hdr{text-align:center}
.logo{display:flex;align-items:center;justify-content:center;gap:.75rem}
.logo-i{width:40px;height:40px;background:var(--grad);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.2rem}
.logo h1{font-size:1.8rem;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sub{color:var(--txt2);font-size:.9rem;margin-top:.5rem}
.sb{display:flex;justify-content:center;gap:.75rem;flex-wrap:wrap}
.chip{padding:.3rem .8rem;background:var(--card);border-radius:20px;font-size:.75rem;display:flex;align-items:center;gap:.5rem;border:1px solid var(--border)}
.dot{width:8px;height:8px;border-radius:50%}
.on .dot{background:var(--green);box-shadow:0 0 8px var(--green)}
.off .dot{background:var(--muted)}
.rec .dot{background:var(--rose);animation:p 1.5s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.4}}
.ctrls{display:flex;justify-content:center;gap:1rem}
.btn{padding:.7rem 1.4rem;border-radius:25px;border:none;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:.5rem;transition:.2s;font-family:inherit;font-size:.9rem}
.btn-s{background:var(--grad);color:#fff}
.btn-x{background:var(--gradrec);color:#fff}
.btn-r{background:var(--card);color:var(--txt2);border:1px solid var(--border)}
.panel{background:var(--card);border-radius:16px;border:1px solid var(--border);backdrop-filter:blur(10px);min-height:180px;padding:1.25rem}
.ph{display:flex;justify-content:space-between;margin-bottom:1rem;color:var(--txt2);font-size:.85rem}
.tt{font-size:1.05rem;line-height:1.6}
.ft{color:var(--txt2);border-left:2px solid var(--border);padding-left:10px;margin-bottom:10px}
.pt{color:var(--cyan);border-left:2px solid var(--cyan);padding-left:10px}
.err{padding:.8rem;background:rgba(244,63,94,.1);border:1px solid rgba(244,63,94,.2);border-radius:8px;color:#fda4af;text-align:center;font-size:.85rem}
.logs{margin-top:1rem;padding:1rem;background:rgba(0,0,0,.3);border-radius:8px;font-size:.72rem;font-family:monospace;border:1px solid var(--border)}
.logs-h{margin-bottom:.5rem;color:var(--muted);text-transform:uppercase}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const{useState,useEffect,useRef,useCallback}=React;

function App(){
  const[rec,setRec]=useState(false);
  const[conn,setConn]=useState(false);
  const[partial,setPartial]=useState('');
  const[full,setFull]=useState('');
  const[err,setErr]=useState(null);
  const[log,setLog]=useState([]);
  const ws=useRef(null);
  const mr=useRef(null);
  const sr=useRef(null);

  const addLog=(m)=>{console.log('[STT]',m);setLog(p=>[`[${new Date().toLocaleTimeString()}] ${m}`,...p].slice(0,10))};

  const wsUrl=`ws://${window.location.host}/ws/transcribe`;

  const connect=useCallback(()=>{
    return new Promise((ok,fail)=>{
      addLog(`Connecting to ${wsUrl}...`);
      const s=new WebSocket(wsUrl);
      s.onopen=()=>{addLog('WebSocket OPEN');};
      s.onmessage=(e)=>{
        const d=JSON.parse(e.data);
        if(d.type==='connected'){addLog('Server handshake OK!');setConn(true);setErr(null);ok(s);}
        if(d.type==='transcription'||d.type==='final'){
          if(d.partial!==undefined)setPartial(d.partial);
          if(d.full!==undefined)setFull(d.full);
        }
        if(d.type==='error'){setErr(d.message);addLog('Error: '+d.message);}
      };
      s.onerror=(e)=>{addLog('Connection FAILED');setErr('WebSocket connection failed');setConn(false);fail(e);};
      s.onclose=(e)=>{setConn(false);addLog(`Closed (code:${e.code})`);};
      ws.current=s;
    });
  },[wsUrl]);

  useEffect(()=>{connect().catch(()=>{});},[connect]);

  const start=async()=>{
    try{
      setErr(null);setPartial('');setFull('');
      if(!conn)await connect();
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      sr.current=stream;
      const m=new MediaRecorder(stream);
      mr.current=m;
      m.ondataavailable=(e)=>{if(e.data.size>0&&ws.current?.readyState===WebSocket.OPEN)ws.current.send(e.data);};
      m.start(500);
      setRec(true);
      addLog('Recording started (500ms chunks)');
    }catch(e){setErr('Mic access denied or connection failed: '+e.message);}
  };

  const stop=()=>{
    if(ws.current?.readyState===WebSocket.OPEN)ws.current.send(JSON.stringify({action:'stop'}));
    mr.current?.stop();
    sr.current?.getTracks().forEach(t=>t.stop());
    setRec(false);
    addLog('Recording stopped');
    setTimeout(()=>{ws.current?.close();},1000);
  };

  const reset=()=>{setFull('');setPartial('');
    if(ws.current?.readyState===WebSocket.OPEN)ws.current.send(JSON.stringify({action:'reset'}));
  };

  return(
    <div className="c">
      <header className="hdr">
        <div className="logo"><div className="logo-i">&#127908;</div><h1>RealTime STT</h1></div>
        <p className="sub">Live speech-to-text &bull; Powered by Whisper</p>
      </header>
      <div className="sb">
        <div className={`chip ${conn?'on':'off'}`}><span className="dot"></span>{conn?'Server Connected':'Server Offline'}</div>
        {rec&&<div className="chip rec"><span className="dot"></span>Recording Live</div>}
      </div>
      {err&&<div className="err">{err}</div>}
      <div className="ctrls">
        {!rec?<button className="btn btn-s" onClick={start}>&#127908; Start Recording</button>
              :<button className="btn btn-x" onClick={stop}>&#9632; Stop Recording</button>}
        <button className="btn btn-r" onClick={reset}>Clear</button>
      </div>
      <div className="panel">
        <div className="ph"><span>Live Transcription</span>{rec&&<span style={{color:'var(--rose)'}}>&#9679; LIVE</span>}</div>
        <div className="tt">
          {full&&<div className="ft">{full}</div>}
          {partial&&<div className="pt">{partial}</div>}
          {!full&&!partial&&<div style={{color:'var(--muted)',fontStyle:'italic'}}>Click Start Recording to begin...</div>}
        </div>
      </div>
      <div className="logs">
        <div className="logs-h">Connection Logs:</div>
        {log.map((l,i)=><div key={i} style={{color:i===0?'var(--cyan)':'var(--muted)',marginBottom:'2px'}}>&gt; {l}</div>)}
      </div>
    </div>
  );
}
const root=ReactDOM.createRoot(document.getElementById('root'));
root.render(<App/>);
</script>
</body>
</html>"""

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    headers = dict(websocket.headers)
    origin = headers.get("origin", "no origin")
    
    logger.info(f"Incoming WebSocket connection: host={client_host}, origin={origin}")
    
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"[Client {client_id}] Connection Accepted")

    # Create a stream manager for this session
    stream = StreamManager()

    # Lock to prevent overlapping transcription calls
    transcription_lock = asyncio.Lock()

    # Track timing for smart transcription intervals
    last_transcription_time = 0.0
    min_transcription_interval = 0.8  # Don't transcribe more often than every 800ms
    pending_audio = False

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to STT server. Start sending audio.",
        })

        while True:
            # Receive data from client
            data = await websocket.receive()

            # Handle text messages (control commands)
            if "text" in data:
                try:
                    message = json.loads(data["text"])
                    action = message.get("action", "")

                    if action == "reset":
                        stream.reset()
                        logger.info(f"[Client {client_id}] Stream reset")
                        await websocket.send_json({
                            "type": "reset",
                            "message": "Stream reset",
                        })
                        continue

                    elif action == "stop":
                        # Final transcription of remaining buffer
                        if len(stream.audio_buffer) > 0:
                            context_audio = stream.get_context_audio()
                            loop = asyncio.get_event_loop()
                            final_text = await loop.run_in_executor(
                                None, transcriber.transcribe, context_audio
                            )
                            if final_text:
                                stream.append_transcript(final_text)
                            await websocket.send_json({
                                "type": "final",
                                "partial": final_text or "",
                                "full": stream.get_full_transcript(),
                                "stats": stream.get_stats(),
                            })
                        continue

                except json.JSONDecodeError:
                    pass
                continue

            # Handle binary audio data
            if "bytes" in data:
                audio_bytes = data["bytes"]

                if not audio_bytes:
                    continue

                # Add chunk to RAW stream buffer (WebM fragments)
                stream.add_raw_chunk(audio_bytes)

                # Convert CUMULATIVE raw buffer to PCM
                # This ensures FFmpeg always has the WebM header it needs to decode.
                pcm_audio = convert_audio_to_pcm(stream.get_raw_buffer())

                if pcm_audio is None or len(pcm_audio) == 0:
                    continue

                # Update the processed PCM buffer
                stream.set_audio_buffer(pcm_audio)
                pending_audio = True

                # Calculate audio level from the LATEST chunk for visualization
                # Note: convert_audio_to_pcm(audio_bytes) would fail here, 
                # so we take the last part of pcm_audio.
                latest_samples = int(0.5 * 16000) # Last 500ms
                audio_level = get_audio_level(pcm_audio[-latest_samples:] if len(pcm_audio) > latest_samples else pcm_audio)

                # Smart transcription: throttle to avoid overwhelming the model
                now = time.time()
                time_since_last = now - last_transcription_time

                if time_since_last >= min_transcription_interval and pending_audio:
                    # Log audio level to help verify mic input
                    logger.info(f"[Client {client_id}] Audio Level: {audio_level:.4f} (Buffer: {stream.get_buffer_duration():.2f}s)")

                    # Get context audio for transcription
                    context_audio = stream.get_context_audio()

                    # Run Whisper with a lock to prevent overlapping calls
                    async with transcription_lock:
                        # Run Whisper in executor to prevent blocking the event loop
                        loop = asyncio.get_event_loop()
                        partial_text = await loop.run_in_executor(
                            None, transcriber.transcribe, context_audio
                        )

                    last_transcription_time = time.time()
                    pending_audio = False

                    # Send transcription result
                    await websocket.send_json({
                        "type": "transcription",
                        "partial": partial_text,
                        "full": stream.get_full_transcript(),
                        "audio_level": round(audio_level, 4),
                        "buffer_duration": stream.get_buffer_duration(),
                    })

                    logger.info(
                        f"[Client {client_id}] Chunk #{stream.chunk_count}: "
                        f"'{partial_text[:60]}...'" if len(partial_text) > 60
                        else f"[Client {client_id}] Chunk #{stream.chunk_count}: "
                        f"'{partial_text}'"
                    )
                else:
                    # Send audio level update even when not transcribing
                    await websocket.send_json({
                        "type": "audio_level",
                        "audio_level": round(audio_level, 4),
                    })

    except WebSocketDisconnect:
        logger.info(f"[Client {client_id}] Disconnected")
    except Exception as e:
        logger.error(f"[Client {client_id}] Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        stats = stream.get_stats()
        logger.info(f"[Client {client_id}] Session stats: {stats}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {WS_HOST}:{WS_PORT}")
    uvicorn.run(
        "server:app",
        host=WS_HOST,
        port=WS_PORT,
        reload=False,
        log_level="info",
    )
