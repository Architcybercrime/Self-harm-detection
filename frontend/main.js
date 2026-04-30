/* ============================================================
   main.js
   Remaining UI sections (animations, analysis and camera are
   now in js/animations.js, js/analysis.js, js/camera.js):

   11. UI HELPERS    — language switcher, bio tab switcher
   12. HORIZONTAL SCROLL GROUPS
   15. ANALYZE SECTION — tab switcher
   16. LANGUAGE SWITCHER — EN / HI / FR
       PRECISION BARS, TYPEWRITER MOCKUP
   ============================================================ */


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

   GROUP 1 (hs1): Bio → Red Blocks
   GROUP 3 (hs3): dark ghost → PRECISION
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

  /* ── GROUP 3: PRECISION slides in from RIGHT ── */
  const hs3     = document.getElementById('hs3');
  const hs3t    = document.getElementById('hs3track');
  const hs3d1   = document.getElementById('hs3d1');
  const hs3d2   = document.getElementById('hs3d2');
  const hs3dots = document.getElementById('hs3dots');

  if (hs3 && hs3t) {
    gsap.to(hs3t, {
      x: '-100vw',
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
          hs3dots.classList.toggle('light', inPanel2);
        }
      }
    });
  }

})();


/* ══════════════════════════════════════════════════════════
   15. ANALYZE SECTION — TAB SWITCHER
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


/* ══════════════════════════════════════════════════════════
   16. LANGUAGE SWITCHER — EN / HI / FR
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
    const inputEl  = document.getElementById('mockupInput');
    const riskEl   = document.getElementById('mockupRisk');
    const scoreBar = document.getElementById('mockupScoreBar');
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
