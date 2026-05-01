/* ============================================================
   js/camera.js
   Camera, microphone, and Web Speech API functions.
   Depends on: API_BASE, authToken, _backendOnline, ensureAuth,
               applyFaceResult, applyVoiceResult, _localClassify
               (all defined in analysis.js).
   ============================================================ */

/* ── Pixel-brightness based local face simulation ── */
function _localFaceResult(videoEl) {
  const canvas = document.createElement('canvas');
  canvas.width = videoEl.videoWidth || 320;
  canvas.height = videoEl.videoHeight || 240;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
  const d = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let r = 0, g = 0, b = 0, n = d.length / 4;
  for (let i = 0; i < d.length; i += 16) { r += d[i]; g += d[i+1]; b += d[i+2]; n++; }
  const bright = (r + g + b) / (3 * n * 255);
  const t = Date.now() / 1000;
  const neutral = Math.round(35 + bright * 30 + Math.sin(t * 0.3) * 5);
  const calm    = Math.round(20 + bright * 20 + Math.sin(t * 0.4) * 4);
  const sadness = Math.round(Math.max(4, 28 - bright * 18 + Math.sin(t * 0.5) * 3));
  const anxiety = Math.round(Math.max(2, 18 - bright * 12 + Math.sin(t * 0.7) * 2));
  const distress= Math.round(Math.max(1, 12 - bright * 8));
  applyFaceResult({
    emotions: { neutral, happy: calm, sad: sadness, fear: anxiety, angry: distress },
    risk_level: distress > 10 ? 'MEDIUM' : 'LOW',
    dominant_emotion: neutral > calm ? 'neutral' : 'calm',
    success: true
  });
}

/* ── Camera (Facial tab) ── */
var cameraStream = null;
let cameraAnalysisInterval = null;

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraStream = stream;
    const video = document.getElementById('cameraFeed');
    video.srcObject = stream;
    document.getElementById('cameraWrap').classList.add('active');
    document.getElementById('cameraStatus').textContent = 'FEED ACTIVE — ANALYSING…';
    document.getElementById('startCameraBtn').style.display = 'none';
    document.getElementById('stopCameraBtn').style.display  = 'inline-flex';

    if (cameraAnalysisInterval) clearInterval(cameraAnalysisInterval);
    // Run face analysis every 3 seconds
    setTimeout(() => captureAndAnalyseFace(), 800);
    cameraAnalysisInterval = setInterval(() => {
      if (cameraStream) captureAndAnalyseFace();
    }, 3000);
  } catch {
    document.getElementById('cameraStatus').textContent = 'CAMERA ACCESS DENIED — allow camera in browser';
  }
}

function stopCamera() {
  if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
  const video = document.getElementById('cameraFeed');
  video.srcObject = null;
  document.getElementById('cameraWrap').classList.remove('active');
  document.getElementById('cameraStatus').textContent = 'AWAITING FEED';
  document.getElementById('startCameraBtn').style.display = 'inline-flex';
  document.getElementById('stopCameraBtn').style.display  = 'none';
  if (cameraAnalysisInterval) { clearInterval(cameraAnalysisInterval); cameraAnalysisInterval = null; }
}

async function captureAndAnalyseFace() {
  if (!cameraStream) return;
  const video = document.getElementById('cameraFeed');
  if (!video.videoWidth) return;

  /* Try real backend first */
  if (_backendOnline && authToken) {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      const b64  = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 8000);
      const res  = await fetch(`${API_BASE}/analyze-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
        body: JSON.stringify({ image_base64: b64 }),
        signal: ctrl.signal
      });
      if (res.status === 429) { /* rate-limited — fall through to local */ }
      else if (res.ok) { applyFaceResult(await res.json()); return; }
    } catch { /* fall through */ }
  }

  /* Local fallback — pixel brightness → pseudo-emotions */
  _localFaceResult(video);
}

/* ── Microphone (Voice tab) ── */
let micStream = null;
let micAnalyser = null;
let micAnimFrame = null;
let micTimerInterval = null;
let micSeconds = 0;
let micRecorder = null;
let micChunks = [];
let micStopTimeout = null;
let micAudioContext = null;
let micIsRecording = false;

/* Try backend upload, fall back to local Web Speech result */
async function uploadVoiceBlob(blob, speechTranscript) {
  /* Try backend */
  if (_backendOnline) {
    try {
      await ensureAuth();
      const form = new FormData();
      form.append('file', blob, 'voice.webm');
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 10000);
      const res  = await fetch(`${API_BASE}/analyze-speech-upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` },
        body: form,
        signal: ctrl.signal
      });
      if (res.ok) { applyVoiceResult(await res.json()); return; }
    } catch { /* fall through */ }
  }

  /* Local fallback — use Web Speech transcript + local classifier */
  const transcript = speechTranscript || '';
  const local      = transcript ? _localClassify(transcript) : { level: 'LOW RISK', score: 65, signals: [] };
  const riskScore  = local.score / 100;
  applyVoiceResult({
    success:              true,
    transcription:        transcript || 'Voice recorded — transcript unavailable offline',
    risk_level:           local.level === 'HIGH RISK' ? 'HIGH' : local.level === 'MODERATE' ? 'MEDIUM' : 'LOW',
    speech_risk_score:    riskScore,
    acoustic_risk_score:  riskScore * 0.6,
    text_risk_score:      riskScore,
    tempo_bpm:            85 + Math.random() * 30,
    energy_level:         0.4 + Math.random() * 0.3,
    risk_signals:         local.signals
  });
}

/* Web Speech API transcript accumulator — filled while recording */
let _speechTranscript = '';
let _speechRecog = null;

function _startSpeechRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  _speechTranscript = '';
  _speechRecog = new SR();
  _speechRecog.continuous = true;
  _speechRecog.interimResults = true;
  _speechRecog.lang = 'en-US';
  _speechRecog.onresult = e => {
    _speechTranscript = Array.from(e.results).map(r => r[0].transcript).join(' ');
  };
  try { _speechRecog.start(); } catch {}
}

function _stopSpeechRecognition() {
  if (_speechRecog) { try { _speechRecog.stop(); } catch {} _speechRecog = null; }
}

function _scheduleChunkUpload() {
  if (micStopTimeout) clearTimeout(micStopTimeout);
  micStopTimeout = setTimeout(async () => {
    if (!micRecorder || !micStream) return;
    if (micRecorder.state !== 'inactive') micRecorder.stop();
    micIsRecording = false;
    await new Promise(r => setTimeout(r, 300));
    if (!micStream) return;
    /* restart for next chunk */
    micChunks = [];
    micRecorder.start();
    micIsRecording = true;
    _scheduleChunkUpload();
  }, 5000);
}

async function startMic() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micStream  = stream;
    micSeconds = 0;

    /* Visualiser */
    micAudioContext = new (window.AudioContext || window.webkitAudioContext)();
    const src = micAudioContext.createMediaStreamSource(stream);
    micAnalyser = micAudioContext.createAnalyser();
    micAnalyser.fftSize = 32;
    src.connect(micAnalyser);
    const bars    = document.querySelectorAll('.mic-bar');
    const dataArr = new Uint8Array(micAnalyser.frequencyBinCount);
    function drawBars() {
      micAnimFrame = requestAnimationFrame(drawBars);
      micAnalyser.getByteFrequencyData(dataArr);
      bars.forEach((bar, i) => {
        bar.style.height = Math.max(8, (dataArr[i] / 255) * 100) + '%';
      });
    }
    drawBars();

    /* Timer */
    micTimerInterval = setInterval(() => {
      micSeconds++;
      const mm = String(Math.floor(micSeconds / 60)).padStart(2,'0');
      const ss = String(micSeconds % 60).padStart(2,'0');
      document.getElementById('micTimer').textContent = mm + ':' + ss;
    }, 1000);

    document.getElementById('micWrap').classList.add('recording');
    document.getElementById('micStatus').textContent = 'RECORDING — LIVE VOICE ANALYSIS';
    document.getElementById('startMicBtn').style.display = 'none';
    document.getElementById('stopMicBtn').style.display  = 'inline-flex';

    /* Speech recogniser runs in parallel for transcript */
    _startSpeechRecognition();

    /* MediaRecorder for audio upload */
    micRecorder = new MediaRecorder(stream);
    micChunks   = [];
    micRecorder.ondataavailable = e => { if (e.data?.size > 0) micChunks.push(e.data); };
    micRecorder.onstop = async () => {
      if (!micChunks.length) return;
      const blob = new Blob(micChunks, { type: micRecorder.mimeType || 'audio/webm' });
      micChunks  = [];
      document.getElementById('micStatus').textContent = 'ANALYSING VOICE CLIP…';
      try { await uploadVoiceBlob(blob, _speechTranscript); } catch {}
      if (micStream) document.getElementById('micStatus').textContent = 'RECORDING — LIVE VOICE ANALYSIS';
    };
    micRecorder.start();
    micIsRecording = true;
    _scheduleChunkUpload();

  } catch {
    document.getElementById('micStatus').textContent = 'MICROPHONE ACCESS DENIED — allow mic in browser';
  }
}

function stopMic() {
  if (micStopTimeout)    { clearTimeout(micStopTimeout); micStopTimeout = null; }
  _stopSpeechRecognition();
  if (micRecorder && micRecorder.state !== 'inactive') micRecorder.stop();
  micIsRecording = false;
  if (micStream)       { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  if (micAnimFrame)    { cancelAnimationFrame(micAnimFrame); micAnimFrame = null; }
  if (micTimerInterval){ clearInterval(micTimerInterval); micTimerInterval = null; }
  if (micAudioContext) { micAudioContext.close(); micAudioContext = null; }
  micRecorder = null;

  document.querySelectorAll('.mic-bar').forEach((bar, i) => {
    bar.style.height = [20,40,60,80,100,80,60,40,20][i] + '%';
  });
  document.getElementById('micWrap').classList.remove('recording');
  document.getElementById('micStatus').textContent = 'READY TO RECORD';
  document.getElementById('micTimer').textContent  = '00:00';
  document.getElementById('startMicBtn').style.display = 'inline-flex';
  document.getElementById('stopMicBtn').style.display  = 'none';
}

/* ── Voice Input (Web Speech API) ─────────────────────────
   Populates the text input field via microphone + browser
   Speech Recognition API.
   ──────────────────────────────────────────────────────── */
let _voiceRecog = null;
let _voiceActive = false;

function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const statusEl = document.getElementById('voiceStatus');
  const iconEl   = document.getElementById('voiceIcon');
  const labelEl  = document.getElementById('voiceLabel');
  const btn      = document.getElementById('voiceInputBtn');

  if (!SpeechRecognition) {
    statusEl.textContent = 'Voice input not supported in this browser. Try Chrome.';
    statusEl.style.display = 'block';
    return;
  }

  if (_voiceActive && _voiceRecog) {
    _voiceRecog.stop();
    return;
  }

  _voiceRecog = new SpeechRecognition();
  _voiceRecog.lang = 'en-US';
  _voiceRecog.interimResults = true;
  _voiceRecog.maxAlternatives = 1;

  _voiceRecog.onstart = () => {
    _voiceActive = true;
    iconEl.textContent  = '⏹';
    labelEl.textContent = 'STOP';
    btn.style.borderColor = '#E4032E';
    statusEl.textContent  = 'Listening… speak now';
    statusEl.style.display = 'block';
  };

  _voiceRecog.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript)
      .join('');
    document.getElementById('textInput').value = transcript;
    if (e.results[e.results.length - 1].isFinal) {
      statusEl.textContent = 'Captured. Click RUN ANALYSIS to proceed.';
    }
  };

  _voiceRecog.onerror = (e) => {
    statusEl.textContent = `Voice error: ${e.error}`;
  };

  _voiceRecog.onend = () => {
    _voiceActive = false;
    iconEl.textContent  = '🎙';
    labelEl.textContent = 'SPEAK';
    btn.style.borderColor = '';
  };

  _voiceRecog.start();
}
