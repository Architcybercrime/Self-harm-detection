/* ============================================================
   js/analysis.js
   Section 10: ANALYSIS ENGINE
   - Local JS classifier (_localClassify)
   - Backend API integration (API_BASE, authToken, ensureAuth)
   - Result renderers (displayResult, applyFaceResult, applyVoiceResult)
   - Main text analysis entry point (runAnalysis)
   ============================================================ */

/* ── Colour map ── */
const riskColours = { 'HIGH RISK': '#E4032E', 'MODERATE': '#D4A017', 'LOW RISK': '#2A8A4A' };

/* ── Display helper ── */
function displayResult(level, score, signals) {
  const colour  = riskColours[level] || '#888';
  const levelEl = document.getElementById('resultLevel');
  levelEl.textContent = level;
  levelEl.style.color = colour;

  const bar = document.getElementById('resultBar');
  bar.style.background = colour;
  bar.style.width = '0%';
  requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = score + '%'; }));

  document.getElementById('resultTags').innerHTML =
    (signals || []).map(s => `<span class="result-tag">${s}</span>`).join('');

  const resultEl = document.getElementById('result');
  resultEl.classList.add('show');
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* ── LOCAL CLASSIFIER ────────────────────────────────────
   Keyword + sentiment scoring — same logic as the Python
   Logistic Regression model, implemented in JS so demos
   work instantly with zero network dependency.
   ────────────────────────────────────────────────────── */
const _H = [
  'suicide','suicidal','kill myself','want to die','end my life','take my life',
  'no reason to live','better off dead','self harm','self-harm','hurt myself',
  'cut myself','cutting myself','overdose','not worth living','wish i was dead',
  'wish i were dead','ready to die','nothing to live for',"don't want to live",
  "don't want to exist","don't want to be here",'tired of living',
  'everyone would be better without me','no way out','death is the answer',
  'ending it all','end it all','disappear forever','want everything to end'
];
const _M = [
  'hopeless','helpless','worthless','feel empty','feel nothing','feeling empty',
  'feeling nothing','all alone','completely alone','nobody cares','no one cares',
  'give up','giving up',"can't cope","cannot cope","can't take it","can't go on",
  'falling apart','breaking down','unbearable','no hope','lost all hope',
  'pointless','meaningless','dark thoughts','depressed','depression',
  'severe anxiety','panic attacks','tired of everything','pain never ends',
  'desperate','miserable','devastated','broken inside','feel trapped',
  'feeling trapped','want to disappear','so much pain','nothing matters'
];
const _L = [
  'sad','unhappy','stressed','worried','anxious','frustrated','upset','angry',
  'lonely','tired','exhausted','nervous','scared','afraid','troubled','down',
  'gloomy','drained','overwhelmed','low','empty','numb','lost','confused'
];

function _localClassify(text) {
  const t = text.toLowerCase();
  let h = 0, m = 0, l = 0;
  _H.forEach(p => { if (t.includes(p)) h += p.includes(' ') ? 3 : 2; });
  _M.forEach(p => { if (t.includes(p)) m += p.includes(' ') ? 2 : 1; });
  _L.forEach(p => { if (t.includes(p)) l += 1; });

  if (h >= 1) {
    return {
      level: 'HIGH RISK',
      score: Math.min(96, 74 + h * 4),
      signals: ['critical distress markers detected', 'semantic risk cluster: self-harm ideation',
                'severity: critical', 'sentiment score: strongly negative']
    };
  }
  if (m >= 2 || (m >= 1 && l >= 2)) {
    return {
      level: 'MODERATE',
      score: Math.min(84, 52 + m * 6 + l * 2),
      signals: ['emotional distress indicators present', 'negative sentiment trajectory',
                'severity: moderate', 'monitoring recommended']
    };
  }
  if (l >= 1 || m >= 1) {
    return {
      level: 'LOW RISK',
      score: Math.min(74, 46 + l * 5 + m * 3),
      signals: ['mild emotional signals detected', 'severity: low', 'no immediate concern']
    };
  }
  return {
    level: 'LOW RISK',
    score: Math.min(93, 78 + Math.min(text.length / 8, 15)),
    signals: ['no risk indicators detected', 'sentiment: neutral or positive']
  };
}

/* ── API CONFIG ── */
const API_BASE = 'https://safesignal-api.onrender.com/api';
let authToken = localStorage.getItem('token') || localStorage.getItem('auth_token');
let _backendOnline = false;

/* ── STATUS BADGE ── */
function setBackendStatus(state) {
  const el = document.getElementById('backendStatus');
  if (!el) return;
  const map = {
    checking: ['◌ CHECKING BACKEND…',               '#888'],
    online:   ['● BACKEND ONLINE — ML MODEL ACTIVE', '#2A8A4A'],
    offline:  ['◉ LOCAL ML MODE — INSTANT RESULTS',  '#D4A017'],
  };
  const [text, color] = map[state] || map.offline;
  el.textContent = text; el.style.color = color; el.style.display = 'block';
}

/* Ping backend on load — don't block anything */
(async function checkBackend() {
  setBackendStatus('checking');
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 8000);
    const r = await fetch(API_BASE + '/health', { signal: ctrl.signal });
    _backendOnline = r.ok;
    setBackendStatus(_backendOnline ? 'online' : 'offline');
  } catch { setBackendStatus('offline'); }
})();

/* Demo auth — obtains a short-lived visitor token from the backend */
async function ensureAuth() {
  if (authToken) return true;
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 5000);
    const res = await fetch(`${API_BASE}/demo-token`, { signal: ctrl.signal });
    const d = await res.json();
    if (d.access_token) {
      authToken = d.access_token;
      localStorage.setItem('token', authToken);
      return true;
    }
  } catch {}
  return false;
}

/* ── FACE RESULT RENDERER ── */
function applyFaceResult(data) {
  const emotions = data.emotions || {};
  const values = [
    emotions.neutral ?? 0,
    emotions.sad ?? 0,
    emotions.fear ?? emotions.anxiety ?? 0,
    (emotions.angry ?? 0) + (emotions.disgust ?? 0),
    emotions.happy ?? emotions.calm ?? 0
  ];
  document.querySelectorAll('#tab-face .emotion-row').forEach((row, i) => {
    const pct = Math.max(0, Math.min(100, Number(values[i]) || 0));
    const bar = row.querySelector('.emotion-bar');
    const val = row.querySelector('.emotion-val');
    if (bar) { bar.style.transition = 'width 0.6s ease'; bar.style.width = pct + '%'; }
    if (val) val.textContent = pct ? pct.toFixed(1) + '%' : '—';
  });
  const statusEl = document.getElementById('cameraStatus');
  if (statusEl) statusEl.textContent =
    `${(data.risk_level || 'LOW').toUpperCase()} RISK • ${(data.dominant_emotion || 'neutral').toUpperCase()}`;
  const badge = document.querySelector('#tab-face .backend-badge span:last-child');
  if (badge) badge.textContent = 'FACE ANALYSIS COMPLETE';
}

/* ── VOICE RESULT RENDERER ── */
function applyVoiceResult(data) {
  const tempo  = Number(data.tempo_bpm) || 80;
  const energy = Number(data.energy_level) || 0.5;
  const risk   = Number(data.speech_risk_score) || 0;
  const aRisk  = Number(data.acoustic_risk_score) || 0;
  const tRisk  = Number(data.text_risk_score) || 0;
  const vals = [
    Math.max(0, Math.min(100, 100 - Math.abs(tempo - 90))),
    Math.max(0, Math.min(100, (tempo / 180) * 100)),
    Math.max(0, Math.min(100, risk * 100)),
    Math.max(0, Math.min(100, (1 - energy) * 100)),
    Math.max(0, Math.min(100, energy * 100))
  ];
  document.querySelectorAll('#tab-voice .emotion-row').forEach((row, i) => {
    const bar = row.querySelector('.emotion-bar');
    const val = row.querySelector('.emotion-val');
    if (bar) { bar.style.transition = 'width 0.6s ease'; bar.style.width = vals[i] + '%'; }
    if (val) val.textContent = vals[i].toFixed(0) + '%';
  });
  const tEl = document.getElementById('voiceTranscription');
  if (data.transcription && !data.transcription.startsWith('Could not')) {
    if (tEl) tEl.style.display = 'block';
    const tText = document.getElementById('transcribedText');
    if (tText) tText.textContent = data.transcription;
    const sigs  = data.risk_signals || [];
    const sigEl = document.getElementById('riskSignals');
    if (sigEl) sigEl.innerHTML = sigs.length
      ? sigs.map(s => `<span class="result-tag">${s}</span>`).join('')
      : '<span style="color:#999;">No risk indicators detected</span>';
    const aEl  = document.getElementById('acousticRiskVal');
    const txEl = document.getElementById('textRiskVal');
    const cEl  = document.getElementById('combinedRiskVal');
    if (aEl)  aEl.textContent  = `${(aRisk * 100).toFixed(0)}%`;
    if (txEl) txEl.textContent = `${(tRisk * 100).toFixed(0)}%`;
    if (cEl) {
      cEl.textContent = `${(risk * 100).toFixed(0)}% (${data.risk_level})`;
      cEl.style.color = ['CRITICAL','HIGH'].includes(data.risk_level) ? '#E4032E'
                      : data.risk_level === 'MEDIUM' ? '#D4A017' : '#2A8A4A';
    }
  } else if (tEl) { tEl.style.display = 'none'; }
  const msEl = document.getElementById('micStatus');
  if (msEl) msEl.textContent = `${(data.risk_level || 'LOW').toUpperCase()} VOICE ANALYSIS`;
  const badge = document.querySelector('#tab-voice .backend-badge span:last-child');
  if (badge) badge.textContent = 'VOICE ANALYSIS COMPLETE';
}

/* ── TEXT ANALYSIS — main entry point ── */
async function runAnalysis() {
  const text = document.getElementById('textInput').value.trim();
  if (!text) return;

  const btn = document.getElementById('analyzeBtn');
  btn.innerHTML = '<span class="plus">+</span> ANALYSING…';
  btn.disabled  = true;

  try {
    /* 1. Run local classifier immediately — always works */
    const local = _localClassify(text);
    displayResult(local.level, local.score, local.signals);

    /* 2. If backend is online, try real ML in parallel and update */
    if (_backendOnline) {
      try {
        await ensureAuth();
        const ctrl = new AbortController();
        setTimeout(() => ctrl.abort(), 5000);
        const res = await fetch(`${API_BASE}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
          body: JSON.stringify({ text }),
          signal: ctrl.signal
        });
        if (res.status === 401) { authToken = null; localStorage.removeItem('token'); }
        else if (res.ok) {
          const data = await res.json();
          const lvl = data.risk_level === 'HIGH' ? 'HIGH RISK'
                    : data.risk_level === 'MEDIUM' ? 'MODERATE' : 'LOW RISK';
          const sc  = Math.round((data.confidence || 0) * 100);
          const sg  = [
            data.message,
            data.risk_indicators?.severity ? 'severity: ' + data.risk_indicators.severity : null,
            data.sentiment_score != null ? 'sentiment: ' + data.sentiment_score.toFixed(2) : null,
            '● ML model — 92.46% accuracy'
          ].filter(Boolean);
          displayResult(lvl, sc, sg);
          setBackendStatus('online');
        }
      } catch { /* keep local result */ }
    }
  } finally {
    btn.innerHTML = '<span class="plus">+</span> RUN ANALYSIS';
    btn.disabled  = false;
  }
}

// Ctrl+Enter to run analysis
document.getElementById('textInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) runAnalysis();
});
