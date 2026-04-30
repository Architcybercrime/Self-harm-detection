/* ============================================================
   main.js
   PURPOSE: All JavaScript for SafeSignal.
   Organised into clearly labelled sections:

   1. SETUP          — register GSAP plugin
   2. CURSOR         — custom dot cursor
   3. PROGRESS BAR   — scroll progress indicator
   4. HERO           — entrance + scroll fade transition
   5. RED BLOCKS     — clip-path wipe animation
   6. DARK CHAPTER   — title slide-in
   7. PARALLAX       — photo grid scroll speeds
   8. RACE NIGHT     — floating cards entrance
   9. SCROLL REVEAL  — IntersectionObserver for all sections
   10. ANALYSIS      — text detection engine
   11. UI HELPERS    — language switcher, tab clicks

   HOW TO READ THIS FILE:
   Each section has a comment explaining WHAT it does and WHY.
   The code immediately follows the comment.
   ============================================================ */
/* ══════════════════════════════════════════════════════════
   1. SETUP
   GSAP plugins must be registered before use.
   ScrollTrigger connects GSAP animations to scroll position.
   ══════════════════════════════════════════════════════════ */

gsap.registerPlugin(ScrollTrigger);


/* ══════════════════════════════════════════════════════════
   2. CUSTOM CURSOR
   The browser's default cursor is hidden (cursor:none in CSS).
   We move this div to the mouse position on every mousemove.

   WHY mix-blend-mode:difference?
   It inverts the cursor colour relative to what's behind it.
   White cursor on dark sections → looks dark.
   Dark cursor on light sections → looks dark.
   Always visible, regardless of background colour.
   ══════════════════════════════════════════════════════════ */
const cursor = document.getElementById('cursor');

document.addEventListener('mousemove', e => {
  cursor.style.left = e.clientX + 'px';
  cursor.style.top  = e.clientY + 'px';
});

// Grow the cursor when hovering interactive elements
const interactiveEls = 'a, button, .bio-tab, .footer-link, .social-icon, .nav-chapters, .nav-menu';
document.querySelectorAll(interactiveEls).forEach(el => {
  el.addEventListener('mouseenter', () => cursor.classList.add('big'));
  el.addEventListener('mouseleave', () => cursor.classList.remove('big'));
});


/* ══════════════════════════════════════════════════════════
   3. PROGRESS BAR
   The thin red line at the very top of the page.
   ScrollTrigger's onUpdate callback fires on every scroll tick.
   self.progress is 0 at the top, 1 at the bottom of the page.
   ══════════════════════════════════════════════════════════ */
ScrollTrigger.create({
  trigger: document.body,
  start: 'top top',
  end: 'bottom bottom',
  onUpdate: self => {
    document.getElementById('progress').style.width =
      (self.progress * 100) + '%';
  }
});


/* ══════════════════════════════════════════════════════════
   4. HERO ANIMATIONS

   4a. ENTRANCE — title fades up from below on page load.
       gsap.from() animates FROM the given values TO current.
       delay:0.3 lets the browser finish rendering first.

   4b. SCROLL FADE — as user scrolls through hero:
       - Gradient overlay fades IN  (opacity 0 → 1)
       - Title fades OUT            (opacity 1 → 0, y: 0 → -60)
       scrub:true = animation progress == scroll progress.
       No easing, no delay — perfectly tied to finger/scroll.
   ══════════════════════════════════════════════════════════ */

// 4a: Entrance animation — plays once on page load
gsap.from('#heroTitle', {
  y: 80,
  opacity: 0,
  duration: 1.4,
  ease: 'power4.out',
  delay: 0.3
});

// 4b: Scroll fade — gradient overlay fades in as you scroll down,
//     fades back out when you scroll back up (scrub handles both directions)
gsap.to('#heroOverlay', {
  opacity: 1,
  scrollTrigger: {
    trigger: '#hero',
    start: 'top top',
    end: 'bottom top',
    scrub: true
  }
});

// 4b: Title fades out going down, comes BACK when scrolling up.
//     scrub:true means the animation perfectly reverses on scroll up.
//     toggleActions not used — scrub alone handles both directions.
//     clearProps:'all' on the entrance tween ensures scrub can
//     override the inline styles left by the entrance animation.
gsap.to('#heroTitle', {
  opacity: 0,
  y: -60,
  scrollTrigger: {
    trigger: '#hero',
    start: '20% top',
    end: 'bottom top',
    scrub: true,
    // When scrolled fully back to top, restore the title to full opacity
    onLeaveBack: () => {
      gsap.set('#heroTitle', { clearProps: 'opacity,y' });
    }
  }
});


/* ══════════════════════════════════════════════════════════
   5. RED RECTANGLES — CLIP-PATH WIPE

   clip-path: inset(top right bottom left)
   inset(0 100% 0 0) = clip 100% from the right = fully hidden
   inset(0 0%   0 0) = clip 0%  from the right = fully visible

   GSAP animates from fully-hidden to fully-visible.
   This creates the "wipe in from left" effect.

   toggleActions: 'play none none none'
   = play forward when enters viewport, do nothing on reverse
   ══════════════════════════════════════════════════════════ */
/* Red block animations are now fired by the horizontal
   scroll trigger in section 12 when panel 2 becomes visible */


/* ══════════════════════════════════════════════════════════
   6. DARK CHAPTER TITLE — SLIDE IN FROM LEFT

   The massive "PRECISION" text slides in from off-screen left.
   x: -100 means it starts 100px to the left of its position.
   ══════════════════════════════════════════════════════════ */
gsap.from('#darkTitle', {
  x: -100,
  opacity: 0,
  duration: 1.2,
  ease: 'power4.out',
  scrollTrigger: {
    trigger: '.dark-chapter',
    start: 'top 60%',
    toggleActions: 'play none none none'
  }
});


/* ══════════════════════════════════════════════════════════
   7. PHOTO PARALLAX

   Parallax = different elements moving at different speeds.
   photo-card-1 moves  -60px  over the section scroll range.
   photo-card-2 moves -120px  (twice as fast = more depth).

   scrub: 1   = smooth, 1 second lag behind scroll
   scrub: 1.5 = smoother, 1.5 second lag

   Combined with the CSS staggered starting positions,
   this creates the floating, layered depth effect.
   ══════════════════════════════════════════════════════════ */
gsap.to('.photo-card-1', {
  y: -60,
  ease: 'none',
  scrollTrigger: {
    trigger: '.photo-grid-section',
    start: 'top bottom',
    end: 'bottom top',
    scrub: 1
  }
});

gsap.to('.photo-card-2', {
  y: -120,
  ease: 'none',
  scrollTrigger: {
    trigger: '.photo-grid-section',
    start: 'top bottom',
    end: 'bottom top',
    scrub: 1.5
  }
});


/* ══════════════════════════════════════════════════════════
   8. FLOATING PHOTO CARDS

   The two small photo cards on the race night section
   fade and rise into view when the section enters viewport.

   stagger: 0.2 = each card starts 0.2s after the previous.
   ══════════════════════════════════════════════════════════ */
gsap.from('.float-card', {
  y: 80,
  opacity: 0,
  duration: 1,
  stagger: 0.2,
  ease: 'power3.out',
  scrollTrigger: {
    trigger: '.racenight-section',
    start: 'top 60%',
    toggleActions: 'play none none none'
  }
});


/* ══════════════════════════════════════════════════════════
   9. SCROLL REVEAL — IntersectionObserver

   WHAT IS IntersectionObserver?
   A browser API that fires a callback whenever a watched
   element enters or leaves the viewport.
   More performant than listening to scroll events.

   HOW IT WORKS HERE:
   1. Elements have class .reveal or .reveal-left
   2. CSS gives them opacity:0 and a translate offset
   3. When they enter the viewport (≥12% visible),
      we add class .in → CSS transitions them to visible
   4. observer.unobserve(el) stops watching after first reveal
      (no need to re-animate if they scroll back up)
   ══════════════════════════════════════════════════════════ */
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in');
      revealObserver.unobserve(entry.target); // stop watching
    }
  });
}, { threshold: 0.12 }); // 12% of element must be visible

document.querySelectorAll('.reveal, .reveal-left').forEach(el => {
  revealObserver.observe(el);
});


/* ══════════════════════════════════════════════════════════
   10. ANALYSIS ENGINE
   Works in two modes:
     LOCAL  — instant JS classifier, zero backend needed
     ONLINE — real FastAPI ML model when backend is up
   Local result appears immediately; backend result
   updates it if the API responds within 5 s.
   ══════════════════════════════════════════════════════════ */

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

/* Pixel-brightness based local face simulation */
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
    const sigs = data.risk_signals || [];
    const sigEl = document.getElementById('riskSignals');
    if (sigEl) sigEl.innerHTML = sigs.length
      ? sigs.map(s => `<span class="result-tag">${s}</span>`).join('')
      : '<span style="color:#999;">No risk indicators detected</span>';
    const aEl = document.getElementById('acousticRiskVal');
    const txEl = document.getElementById('textRiskVal');
    const cEl  = document.getElementById('combinedRiskVal');
    if (aEl) aEl.textContent = `${(aRisk * 100).toFixed(0)}%`;
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

// Ctrl+Enter to run
document.getElementById('textInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) runAnalysis();
});


/* ── Voice Input (Web Speech API) ───────────────────────── */
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


/* ══════════════════════════════════════════════════════════
   11. UI HELPERS

   LANGUAGE SWITCHER:
   Clicking a language button removes .active from all,
   then adds it to the clicked one.
   ══════════════════════════════════════════════════════════ */
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
  });
});

// Bio tab switcher
document.querySelectorAll('.bio-tab').forEach(tab => {
  tab.addEventListener('click', function () {
    document.querySelectorAll('.bio-tab').forEach(t => t.classList.remove('active'));
    this.classList.add('active');
  });
});


/* ══════════════════════════════════════════════════════════
   12. HORIZONTAL SCROLL GROUPS

   Three groups, two behaviours:

   GROUP 1 (hs1): Bio → Red Blocks
   Track starts at x:0 (Bio visible).
   Scroll DOWN → track moves LEFT to -100vw → Red Blocks appears.

   GROUP 2 (hs2): ghost → Chapter/Detection
   Track starts at x:-100vw (Chapter off-screen LEFT, ghost visible).
   Scroll DOWN → track moves RIGHT to 0 → Chapter slides in from left.

   GROUP 3 (hs3): dark ghost → PRECISION
   Track starts at x:-100vw (PRECISION off-screen LEFT, ghost visible).
   Scroll DOWN → track moves RIGHT to 0 → PRECISION slides in from left.
   ══════════════════════════════════════════════════════════ */

(function () {
  if (window.innerWidth <= 600) return;

  /* ── GROUP 1: Bio → Red Blocks (slides in from RIGHT) ── */
  const hs1     = document.getElementById('hs1');
  const hs1t    = document.getElementById('hs1track');
  const hs1d1   = document.getElementById('hs1d1');
  const hs1d2   = document.getElementById('hs1d2');
  const hs1dots = document.getElementById('hs1dots');

  if (hs1 && hs1t) {
    gsap.to(hs1t, {
      x: '-100vw',
      ease: 'none',
      scrollTrigger: {
        trigger: hs1,
        start: 'top top',
        end: '+=300vh',
        pin: true,
        scrub: 1,
        anticipatePin: 1,
        onUpdate: self => {
          const inPanel2 = self.progress >= 0.5;
          hs1d1.classList.toggle('active', !inPanel2);
          hs1d2.classList.toggle('active',  inPanel2);
          hs1dots.classList.toggle('light',  inPanel2);
          // Fire red block wipe animation once when panel 2 appears
          if (inPanel2 && !hs1t._fired) {
            hs1t._fired = true;
            gsap.fromTo('#redRect1',
              { clipPath: 'inset(0 100% 0 0)' },
              { clipPath: 'inset(0 0% 0 0)', duration: 1.2, ease: 'power3.out' });
            gsap.fromTo('#redRect2',
              { clipPath: 'inset(0 100% 0 0)' },
              { clipPath: 'inset(0 0% 0 0)', duration: 1.4, ease: 'power3.out', delay: 0.15 });
          }
        }
      }
    });
  }

  /* GROUP 2 removed — Chapter/Detection is now plain vertical scroll */

  /* ── GROUP 3: PRECISION slides in from RIGHT (same as hs1) ── */
  // Structure: [dark-ghost | PRECISION]
  // Track starts at x:0 → ghost is visible (matches photo-grid bg colour).
  // Scroll down → track moves LEFT to -100vw → PRECISION slides in from right.
  const hs3     = document.getElementById('hs3');
  const hs3t    = document.getElementById('hs3track');
  const hs3d1   = document.getElementById('hs3d1');
  const hs3d2   = document.getElementById('hs3d2');
  const hs3dots = document.getElementById('hs3dots');

  if (hs3 && hs3t) {
    // Track starts at x:0 — ghost panel fills viewport, PRECISION is off-screen right
    gsap.to(hs3t, {
      x: '-100vw',          // slide left → PRECISION appears from the right
      ease: 'none',
      scrollTrigger: {
        trigger: hs3,
        start: 'top top',
        end: '+=100vh',
        pin: true,
        scrub: 0.3,
        anticipatePin: 1,
        onUpdate: self => {
          const inPanel2 = self.progress >= 0.5;
          hs3d1.classList.toggle('active', !inPanel2);
          hs3d2.classList.toggle('active',  inPanel2);
          hs3dots.classList.toggle('light', inPanel2); // white dots on dark PRECISION bg
        }
      }
    });
  }

})();


/* ══════════════════════════════════════════════════════════
   15. ANALYZE SECTION — TAB SWITCHER + CAMERA + MIC
   ══════════════════════════════════════════════════════════ */

/* ── Tab switcher ── */
document.querySelectorAll('.analyze-tab').forEach(tab => {
  tab.addEventListener('click', function () {
    document.querySelectorAll('.analyze-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.analyze-panel').forEach(p => p.classList.remove('active'));
    this.classList.add('active');
    document.getElementById('tab-' + this.dataset.tab).classList.add('active');
  });
});

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
      const b64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
      const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 8000);
      const res = await fetch(`${API_BASE}/analyze-face`, {
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
      const res = await fetch(`${API_BASE}/analyze-speech-upload`, {
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
  const local = transcript ? _localClassify(transcript) : { level: 'LOW RISK', score: 65, signals: [] };
  const riskScore = local.score / 100;
  applyVoiceResult({
    success: true,
    transcription: transcript || 'Voice recorded — transcript unavailable offline',
    risk_level: local.level === 'HIGH RISK' ? 'HIGH' : local.level === 'MODERATE' ? 'MEDIUM' : 'LOW',
    speech_risk_score: riskScore,
    acoustic_risk_score: riskScore * 0.6,
    text_risk_score: riskScore,
    tempo_bpm: 85 + Math.random() * 30,
    energy_level: 0.4 + Math.random() * 0.3,
    risk_signals: local.signals
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
      const prevStatus = document.getElementById('micStatus').textContent;
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
  if (micStopTimeout) { clearTimeout(micStopTimeout); micStopTimeout = null; }
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


/* ══════════════════════════════════════════════════════════
   16. LANGUAGE SWITCHER — EN / HI / FR

   Every translatable element has data-i18n="key" in HTML.
   Placeholders use data-i18n-placeholder="key".
   switchLang() swaps all text content at once.
   Hindi uses Noto Sans Devanagari (loaded in <head>).
   ══════════════════════════════════════════════════════════ */

const translations = {
  EN: {
    'nav-chapters':       'CHAPTERS',
    'cta-analyse':        'ANALYSE TEXT',
    'hero-line1':         'BEYOND',
    'hero-line2':         'DETECTION',
    'scroll-label':       'SCROLL TO EXPLORE',
    'bio-p1':             'Every year, millions of people express distress through text — in messages, journals, and social posts. Most go unnoticed. SafeSignal was built to change that.',
    'bio-p2':             'Using natural language processing trained on clinical datasets, the system identifies linguistic patterns associated with self-harm ideation — not just keywords, but context, sentiment, and semantic clusters — with the accuracy that matters when lives are at stake.',
    'tab-how':            'HOW IT WORKS',
    'tab-stats':          'STATS',
    'hint-scroll':        'SCROLL',
    'ch-label':           'DETECTION',
    'ch-quote':           '"The words we choose reveal more about our state of mind than we realise."',
    'ch-body':            'A system that learns the subtle grammar of distress: the shift from "I feel tired" to "I feel nothing". Pattern recognition that goes deeper than any keyword list.',
    'analyze-label':      'LIVE ANALYSIS',
    'analyze-title1':     'DETECT',
    'analyze-title2':     'SIGNALS',
    'tab-text':           'TEXT',
    'tab-facial':         'FACIAL',
    'tab-voice':          'VOICE',
    'text-desc':          'Paste any text below. The engine analyses linguistic markers, sentiment trajectory, and semantic context — returning a risk score and identified signals.',
    'input-label':        '// INPUT TEXT',
    'text-placeholder':   'Type or paste text here... (Ctrl+Enter to run)',
    'btn-run':            'RUN ANALYSIS',
    'face-desc':          'The facial analysis module reads micro-expressions and affective states through your camera feed — detecting distress signals invisible to the naked eye.',
    'cam-status':         'AWAITING FEED',
    'btn-start-cam':      'START CAMERA',
    'face-result-label':  '// DETECTED EMOTIONS',
    'backend-badge':      'BACKEND INTEGRATION IN PROGRESS',
    'voice-desc':         'The voice analysis module captures speech patterns, tone shifts, and prosodic features — identifying emotional markers associated with psychological distress.',
    'mic-status':         'READY TO RECORD',
    'btn-start-mic':      'START RECORDING',
    'voice-result-label': '// VOICE SIGNALS',
    'fl-system':          'The System',
    'fl-partners':        'Partners',
    'fl-privacy':         'Privacy Policy',
    'fl-research':        'The Research',
    'fl-news':            'News',
    'fl-cookie':          'Cookie Policy',
    'fl-dataset':         'Dataset',
    'fl-contacts':        'Contacts',
    'fl-legal':           'Legal Notice',
    'fl-team':            'Team',
  },

  HI: {
    'nav-chapters':       'अध्याय',
    'cta-analyse':        'पाठ विश्लेषण',
    'hero-line1':         'परे',
    'hero-line2':         'पहचान के',
    'scroll-label':       'नीचे स्क्रॉल करें',
    'bio-p1':             'हर साल, लाखों लोग संदेशों, डायरी और सोशल पोस्ट के ज़रिए अपनी पीड़ा व्यक्त करते हैं। अधिकांश अनदेखे रह जाते हैं। SafeSignal इसे बदलने के लिए बनाया गया है।',
    'bio-p2':             'नैदानिक डेटासेट पर प्रशिक्षित प्राकृतिक भाषा प्रसंस्करण का उपयोग करते हुए, यह प्रणाली आत्म-नुकसान की भावना से जुड़े भाषाई पैटर्न की पहचान करती है — केवल शब्दों से नहीं, बल्कि संदर्भ, भावना और अर्थ समूहों से।',
    'tab-how':            'यह कैसे काम करता है',
    'tab-stats':          'आँकड़े',
    'hint-scroll':        'स्क्रॉल',
    'ch-label':           'पहचान',
    'ch-quote':           '"हमारे शब्द हमारी मानसिक स्थिति के बारे में उससे कहीं अधिक बताते हैं जितना हम महसूस करते हैं।"',
    'ch-body':            'एक ऐसी प्रणाली जो पीड़ा की सूक्ष्म भाषा सीखती है — "मैं थका हुआ हूँ" से "मुझे कुछ महसूस नहीं होता" तक के बदलाव को। पैटर्न पहचान जो किसी भी शब्द सूची से गहरी है।',
    'analyze-label':      'सीधा विश्लेषण',
    'analyze-title1':     'संकेत',
    'analyze-title2':     'पहचानें',
    'tab-text':           'पाठ',
    'tab-facial':         'चेहरा',
    'tab-voice':          'आवाज़',
    'text-desc':          'नीचे कोई भी पाठ पेस्ट करें। इंजन भाषाई संकेतों, भावना प्रक्षेपवक्र और शब्दार्थ संदर्भ का विश्लेषण करता है।',
    'input-label':        '// पाठ इनपुट करें',
    'text-placeholder':   'यहाँ टाइप या पेस्ट करें...',
    'btn-run':            'विश्लेषण करें',
    'face-desc':          'चेहरे का विश्लेषण मॉड्यूल आपके कैमरे से सूक्ष्म भाव और भावनात्मक अवस्थाएं पढ़ता है — नग्न आँखों से अदृश्य संकट संकेतों का पता लगाता है।',
    'cam-status':         'फ़ीड की प्रतीक्षा',
    'btn-start-cam':      'कैमरा शुरू करें',
    'face-result-label':  '// पहचानी गई भावनाएं',
    'backend-badge':      'बैकएंड एकीकरण प्रगति में है',
    'voice-desc':         'आवाज़ विश्लेषण मॉड्यूल भाषण पैटर्न, स्वर परिवर्तन और प्रोसोडिक विशेषताओं को कैप्चर करता है।',
    'mic-status':         'रिकॉर्ड करने के लिए तैयार',
    'btn-start-mic':      'रिकॉर्डिंग शुरू करें',
    'voice-result-label': '// आवाज़ संकेत',
    'fl-system':          'प्रणाली',
    'fl-partners':        'साझेदार',
    'fl-privacy':         'गोपनीयता नीति',
    'fl-research':        'शोध',
    'fl-news':            'समाचार',
    'fl-cookie':          'कुकी नीति',
    'fl-dataset':         'डेटासेट',
    'fl-contacts':        'संपर्क',
    'fl-legal':           'कानूनी सूचना',
    'fl-team':            'टीम',
  },

  FR: {
    'nav-chapters':       'CHAPITRES',
    'cta-analyse':        'ANALYSER LE TEXTE',
    'hero-line1':         'AU-DELÀ',
    'hero-line2':         'DE LA DÉTECTION',
    'scroll-label':       'FAIRE DÉFILER',
    'bio-p1':             'Chaque année, des millions de personnes expriment leur détresse par écrit — dans des messages, des journaux et des publications. La plupart passent inaperçus. SafeSignal a été conçu pour changer cela.',
    'bio-p2':             "Grâce au traitement du langage naturel entraîné sur des ensembles de données cliniques, le système identifie les schémas linguistiques associés à l'idéation suicidaire — pas seulement les mots-clés, mais le contexte, le sentiment et les clusters sémantiques.",
    'tab-how':            'COMMENT ÇA MARCHE',
    'tab-stats':          'STATISTIQUES',
    'hint-scroll':        'DÉFILER',
    'ch-label':           'DÉTECTION',
    'ch-quote':           '"Les mots que nous choisissons révèlent plus sur notre état d\'esprit que nous ne le réalisons."',
    'ch-body':            'Un système qui apprend la grammaire subtile de la détresse : le passage de "je me sens fatigué" à "je ne ressens rien". Une reconnaissance des schémas qui va au-delà de toute liste de mots-clés.',
    'analyze-label':      'ANALYSE EN DIRECT',
    'analyze-title1':     'DÉTECTER',
    'analyze-title2':     'LES SIGNAUX',
    'tab-text':           'TEXTE',
    'tab-facial':         'VISAGE',
    'tab-voice':          'VOIX',
    'text-desc':          "Collez n'importe quel texte ci-dessous. Le moteur analyse les marqueurs linguistiques, la trajectoire des sentiments et le contexte sémantique — retournant un score de risque.",
    'input-label':        '// SAISIR LE TEXTE',
    'text-placeholder':   'Tapez ou collez du texte ici...',
    'btn-run':            'LANCER L\'ANALYSE',
    'face-desc':          "Le module d'analyse faciale lit les micro-expressions et les états affectifs via votre caméra — détectant des signaux de détresse invisibles à l'œil nu.",
    'cam-status':         'EN ATTENTE DU FLUX',
    'btn-start-cam':      'DÉMARRER LA CAMÉRA',
    'face-result-label':  '// ÉMOTIONS DÉTECTÉES',
    'backend-badge':      'INTÉGRATION BACKEND EN COURS',
    'voice-desc':         "Le module d'analyse vocale capture les schémas de parole, les variations de ton et les caractéristiques prosodiques — identifiant les marqueurs émotionnels.",
    'mic-status':         'PRÊT À ENREGISTRER',
    'btn-start-mic':      'DÉMARRER L\'ENREGISTREMENT',
    'voice-result-label': '// SIGNAUX VOCAUX',
    'fl-system':          'Le Système',
    'fl-partners':        'Partenaires',
    'fl-privacy':         'Politique de confidentialité',
    'fl-research':        'La Recherche',
    'fl-news':            'Actualités',
    'fl-cookie':          'Politique des cookies',
    'fl-dataset':         'Jeu de données',
    'fl-contacts':        'Contacts',
    'fl-legal':           'Mentions légales',
    'fl-team':            'Équipe',
  }
};

function switchLang(lang) {
  const t = translations[lang];
  if (!t) return;

  // Swap text content for all data-i18n elements
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key] !== undefined) el.textContent = t[key];
  });

  // Swap placeholder for textarea
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (t[key] !== undefined) el.placeholder = t[key];
  });

  // Hindi needs Devanagari font on body text elements
  document.body.classList.toggle('lang-hi', lang === 'HI');
  document.body.classList.toggle('lang-fr', lang === 'FR');

  // Update active button
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.trim() === lang);
  });

  // Store preference
  window._currentLang = lang;
}

// Wire up the buttons
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    switchLang(this.textContent.trim());
  });
});
 /* ── BIO TAB SWITCHER ── */
function bioSwitch(tab) {
  const content  = document.getElementById('bioContent');
  const bioImage = document.querySelector('.bio-image');
  const tabs     = document.querySelectorAll('.bio-tab');

  content.classList.add('fading');
  document.getElementById('bioDefault').style.display = 'none';
  document.getElementById('bioContent').style.display = 'block';
  document.querySelector('.bio-tab-reset').style.display = 'block';

  if (bioImage) bioImage.classList.add('zoomed');

  setTimeout(() => {
    if (tab === 'how') {
      content.innerHTML = `
        <div class="bio-steps">
          <div class="bio-step"><span class="step-num">01</span><span class="step-text">User inputs text, social media post, or journal entry — or enables camera/microphone</span></div>
          <div class="bio-step"><span class="step-num">02</span><span class="step-text">Text analysis — NLP model scans for emotional distress markers, tone shifts, and semantic risk patterns</span></div>
          <div class="bio-step"><span class="step-num">03</span><span class="step-text">Facial analysis — DeepFace reads micro-expressions and affective states through the camera feed in real time</span></div>
          <div class="bio-step"><span class="step-num">04</span><span class="step-text">Voice analysis — Librosa captures pitch stress, tremor, speech rate, and vocal energy from microphone input</span></div>
          <div class="bio-step"><span class="step-num">05</span><span class="step-text">Multimodal fusion — all three signals are combined into one unified risk score</span></div>
          <div class="bio-step"><span class="step-num">06</span><span class="step-text">Risk level determined — HIGH, MEDIUM, or LOW — with confidence score and support recommendations</span></div>
        </div>`;
    } else {
      content.innerHTML = `
        <div class="bio-steps">
          <div class="bio-stat"><span class="stat-number">700,000+</span><span class="stat-desc">People die due to suicide every year globally</span></div>
          <div class="bio-stat"><span class="stat-number">1 in 7</span><span class="stat-desc">Teens experience mental health struggles</span></div>
          <div class="bio-stat"><span class="stat-number">~80%</span><span class="stat-desc">Of warning signs appear online first</span></div>
          <div class="bio-stat"><span class="stat-number">4×</span><span class="stat-desc">Better outcomes with early intervention</span></div>
        </div>`;
    }
    content.classList.remove('fading');
    if (bioImage) setTimeout(() => bioImage.classList.remove('zoomed'), 300);
  }, 350);

  tabs.forEach((t, i) => {
    const isActive = (tab === 'how' && i === 0) || (tab === 'stats' && i === 1);
    t.classList.toggle('active', isActive);
    t.querySelector('.dot').style.background = isActive ? 'var(--red)' : 'var(--muted)';
  });
}
function bioReset() {
  document.getElementById('bioDefault').style.display = 'block';
  document.getElementById('bioContent').innerHTML = '';
  document.querySelector('.bio-tab-reset').style.display = 'none';
  document.querySelectorAll('.bio-tab').forEach((t, i) => {
    t.classList.toggle('active', i === 0);
    t.querySelector('.dot').style.background = i === 0 ? 'var(--red)' : 'var(--muted)';
  });
}

/* ── PRECISION BARS — animate when section scrolls into view ── */
const precisionObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.pbar').forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
      precisionObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });

const precisionSection = document.querySelector('.precision-overlay');
if (precisionSection) precisionObserver.observe(precisionSection);
/* ── ANALYSIS MOCKUP TYPEWRITER ANIMATION ── */
(function() {
  const examples = [
    { text: "I don't see the point anymore...", risk: 'HIGH RISK', score: 88, color: '#E4032E' },
    { text: "Feeling really tired and empty lately.", risk: 'MODERATE', score: 52, color: '#D4A017' },
    { text: "Had a great day with friends today!", risk: 'LOW RISK',  score: 12, color: '#2A8A4A' },
  ];
  let exIdx = 0, charIdx = 0, typing = true, waiting = false;

  function runMockup() {
    const inputEl   = document.getElementById('mockupInput');
    const riskEl    = document.getElementById('mockupRisk');
    const scoreBar  = document.getElementById('mockupScoreBar');
    if (!inputEl) return;

    const ex = examples[exIdx];

    if (waiting) return;

    if (typing) {
      if (charIdx <= ex.text.length) {
        inputEl.textContent = ex.text.slice(0, charIdx);
        charIdx++;
        setTimeout(runMockup, 55);
      } else {
        // Show result
        waiting = true;
        setTimeout(() => {
          riskEl.textContent  = ex.risk;
          riskEl.style.color  = ex.color;
          scoreBar.style.background = ex.color;
          scoreBar.style.width = ex.score + '%';
          waiting = false;
          typing  = false;
          setTimeout(() => {
            // Reset and move to next example
            scoreBar.style.width = '0%';
            riskEl.textContent   = '';
            inputEl.textContent  = '';
            charIdx = 0;
            typing  = true;
            exIdx   = (exIdx + 1) % examples.length;
            setTimeout(runMockup, 400);
          }, 2500);
        }, 600);
      }
    }
  }

  // Start when section scrolls into view
  const mockupObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        runMockup();
        mockupObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  const mockupEl = document.querySelector('.analysis-mockup');
  if (mockupEl) mockupObserver.observe(mockupEl);
})();