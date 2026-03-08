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

   WHAT IT DOES:
   Scores text against three keyword lists (high/medium/low risk).
   Each matched keyword adds to the score (max 100).
   Determines a level: HIGH RISK / MODERATE / LOW RISK.
   Colours the result text and fills the progress bar.

   NOTE: This is a demonstration keyword matcher.
   A production system would use a trained ML model
   (e.g. Python + FastAPI — see the React+Node project).
   ══════════════════════════════════════════════════════════ */
const keywords = {
  high: [
    'suicide', 'kill myself', 'end my life', 'want to die',
    'no reason to live', 'hurting myself', 'cutting', 'overdose'
  ],
  medium: [
    'hopeless', 'worthless', 'numb', 'trapped', 'empty',
    'burden', 'disappear', 'cant go on', "can't go on", 'give up'
  ],
  low: [
    'sad', 'upset', 'crying', 'tired', 'stressed',
    'anxious', 'overwhelmed', 'alone', 'hurt'
  ]
};

const riskColours = {
  'HIGH RISK': '#E4032E',
  'MODERATE':  '#D4A017',
  'LOW RISK':  '#2A8A4A'
};

const riskNotes = {
  'HIGH RISK': 'Significant distress signals detected. This text contains language strongly associated with self-harm ideation.',
  'MODERATE':  'Several distress markers identified. Further context and professional evaluation advised.',
  'LOW RISK':  'Mild distress language detected. Continued monitoring may be appropriate.'
};

function runAnalysis() {
  const text = document.getElementById('textInput').value.trim();
  if (!text) return;

  // Show loading state
  const btn = document.getElementById('analyzeBtn');
  btn.innerHTML = 'ANALYSING...';
  btn.disabled = true;

  // Simulate async processing (800ms)
  setTimeout(() => {
    const lower = text.toLowerCase();
    let score = 0;
    const found = [];

    keywords.high.forEach(k   => { if (lower.includes(k)) { score += 28; found.push(k); } });
    keywords.medium.forEach(k => { if (lower.includes(k)) { score += 12; found.push(k); } });
    keywords.low.forEach(k    => { if (lower.includes(k)) { score += 5;  found.push(k); } });

    score = Math.min(100, score); // cap at 100
    const level  = score >= 50 ? 'HIGH RISK' : score >= 18 ? 'MODERATE' : 'LOW RISK';
    const colour = riskColours[level];

    // Update UI
    const levelEl = document.getElementById('resultLevel');
    levelEl.textContent  = level;
    levelEl.style.color  = colour;

    // Animate progress bar (reset to 0 first so transition plays)
    const bar = document.getElementById('resultBar');
    bar.style.background = colour;
    bar.style.width = '0%';
    // Double rAF ensures the browser registers the 0% before animating
    requestAnimationFrame(() => requestAnimationFrame(() => {
      bar.style.width = score + '%';
    }));

    // Render signal tags
    const signals = found.length ? found : ['no signals found'];
    document.getElementById('resultTags').innerHTML =
      signals.map(s => `<span class="result-tag">${s}</span>`).join('');

    document.getElementById('resultNote').textContent = riskNotes[level];

    // Show result panel
    const resultEl = document.getElementById('result');
    resultEl.classList.add('show');
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Reset button
    btn.innerHTML = '<span class="plus">+</span> RUN ANALYSIS';
    btn.disabled  = false;

  }, 800);
}

// Allow pressing Enter in textarea to trigger analysis
document.getElementById('textInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) runAnalysis();
});


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
        end: '+=200vh',
        pin: true,
        scrub: 3,
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
let cameraStream = null;

function startCamera() {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      cameraStream = stream;
      const video = document.getElementById('cameraFeed');
      video.srcObject = stream;
      document.getElementById('cameraWrap').classList.add('active');
      document.getElementById('cameraStatus').textContent = 'FEED ACTIVE — AWAITING MODEL';
      document.getElementById('startCameraBtn').style.display = 'none';
      document.getElementById('stopCameraBtn').style.display  = 'inline-flex';
    })
    .catch(() => {
      document.getElementById('cameraStatus').textContent = 'CAMERA ACCESS DENIED';
    });
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }
  const video = document.getElementById('cameraFeed');
  video.srcObject = null;
  document.getElementById('cameraWrap').classList.remove('active');
  document.getElementById('cameraStatus').textContent = 'AWAITING FEED';
  document.getElementById('startCameraBtn').style.display = 'inline-flex';
  document.getElementById('stopCameraBtn').style.display  = 'none';
}

/* ── Microphone (Voice tab) ── */
let micStream = null;
let micAnalyser = null;
let micAnimFrame = null;
let micTimerInterval = null;
let micSeconds = 0;

function startMic() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      micStream = stream;
      micSeconds = 0;

      // Web Audio visualiser
      const ctx     = new (window.AudioContext || window.webkitAudioContext)();
      const source  = ctx.createMediaStreamSource(stream);
      micAnalyser   = ctx.createAnalyser();
      micAnalyser.fftSize = 32;
      source.connect(micAnalyser);

      const bars    = document.querySelectorAll('.mic-bar');
      const dataArr = new Uint8Array(micAnalyser.frequencyBinCount);

      function drawBars() {
        micAnimFrame = requestAnimationFrame(drawBars);
        micAnalyser.getByteFrequencyData(dataArr);
        bars.forEach((bar, i) => {
          const val = dataArr[i] || 0;
          bar.style.height = Math.max(8, (val / 255) * 100) + '%';
        });
      }
      drawBars();

      // Timer
      micTimerInterval = setInterval(() => {
        micSeconds++;
        const m = String(Math.floor(micSeconds / 60)).padStart(2,'0');
        const s = String(micSeconds % 60).padStart(2,'0');
        document.getElementById('micTimer').textContent = m + ':' + s;
      }, 1000);

      document.getElementById('micWrap').classList.add('recording');
      document.getElementById('micStatus').textContent = 'RECORDING — AWAITING MODEL';
      document.getElementById('startMicBtn').style.display = 'none';
      document.getElementById('stopMicBtn').style.display  = 'inline-flex';
    })
    .catch(() => {
      document.getElementById('micStatus').textContent = 'MICROPHONE ACCESS DENIED';
    });
}

function stopMic() {
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  if (micAnimFrame) { cancelAnimationFrame(micAnimFrame); micAnimFrame = null; }
  if (micTimerInterval) { clearInterval(micTimerInterval); micTimerInterval = null; }

  // Reset bars to idle state
  document.querySelectorAll('.mic-bar').forEach((bar, i) => {
    const idle = [20,40,60,80,100,80,60,40,20];
    bar.style.height = idle[i] + '%';
  });

  document.getElementById('micWrap').classList.remove('recording');
  document.getElementById('micStatus').textContent  = 'READY TO RECORD';
  document.getElementById('micTimer').textContent   = '00:00';
  document.getElementById('startMicBtn').style.display = 'inline-flex';
  document.getElementById('stopMicBtn').style.display  = 'none';
}