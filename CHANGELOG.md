# Changelog

All notable changes to the **Self-Harm Detection System** are documented here.

---

## [2026-03-19]

### Added
- `feat: WebSocket real-time alerts` — high-risk predictions trigger instant notifications (`adbd66f`)
- `feat: JWT protection on all endpoints` — 28 tests passing including auth tests (`bad6fe1`)
- `feat: users stored in Supabase PostgreSQL` — RLS enabled for security (`26a9859`)
- `feat: sophisticated trend-based alerting system` — escalating risk, consecutive alerts, sentiment trends (`b10684f`)
- `feat: dynamic weight adjustment in multimodal fusion` — weight explanation added (`c9c6e81`)
- `feat: speech analysis tests added` — 25 pytest cases all passing (`ca23786`)
- `feat: enhanced prediction output` — risk indicators, severity and support resources (`91253e6`)
- `feat: expanded unit tests to 22 cases` — all passing, warnings suppressed (`d99dc62`)
- `feat: input validation and sanitization` — all endpoints protected against malicious input (`486bb89`)
- `feat: CORS configuration hardened` — restricted to specific origins and methods (`7972854`)
- `feat: bcrypt password hashing` — upgraded from SHA-256 to industry-standard bcrypt (`95d4583`)
- `feat: JWT authentication added` — register, login and protected profile endpoint (`e56f620`)
- `feat: security headers added` — flask-talisman for XSS and clickjacking protection (`94f74c4`)
- `feat: unit tests added` — 13 pytest test cases all passing (`39f4202`)
- `feat: Supabase PostgreSQL database integration` — credentials secured via env file (`577920512`, `e3f6361`)
- `feat: rate limiting added` — API protection with per-endpoint limits (`3010bc5`)

### Fixed
- `fix: suppressed TensorFlow deprecation warnings` — cleaner output (`0d4af4b`)

### Changed
- `feat: 28 unit tests all passing` — fixed unique username test for Supabase (`c37bf90`)
- `feat: hardened security` — error handlers, suppressed TF warnings, JWT secret in env (`872ccb0`)

### Docs
- `docs: added security configuration comments` — SQL injection, XSS, CSRF prevention documented (`c4e0184`)
- `docs: documented real-time webcam and microphone analysis` — with example requests (`a4232b8`)
- `docs: updated README` — JWT, Supabase, 12 endpoints, 22 tests (`762d069`)
- `docs: added .env.example` — environment variable setup guide (`642a3d0`)
- `Restore System Architecture section in README` (`a6cca9b`)

### Chore
- `chore: updated requirements.txt` — all new dependencies (`01b9872`)

---

## [2026-03-08]

### Added
- `Added Facial and Voice Analysis` — frontend facial and voice analysis modules (`629fb58`)
- `Added Translation feature` — multilingual UI support (`f1d7f4f`)

### Changed
- `Basic/Minute Improvements` — minor UI and UX improvements (`d918e55`)

---

## [2026-03-06]

### Improved
- `improvement: retrained on 50k dataset` — accuracy improved from 91.8% to 92.2% (`9a9bd8a`)

### Docs
- `docs: updated accuracy to 92.2%` — after retraining on 50k dataset (`b5d9ae9`)

---

## [2026-03-05]

### Added
- `feat: multimodal fusion endpoint complete` — text + face + speech unified risk scoring (`190251c`)
- `feat: speech analysis module complete` — librosa and SpeechRecognition both working (`a208bf3`)
- `Added transitions` — animated page transitions (`e085263`)
- `Added intro section image and styling fixes` (`02b3d09`)

### Fixed
- `fix: microphone recording working` — PyAudio installed, speech transcription tested (`cb27181`)

---

## [2026-03-03]

### Added
- `feat: DeepFace facial expression analysis working` — webcam emotion detection tested (`d7f80d8`)
- `feat: added monitoring and drift detection module` — Stage 7 ML pipeline complete (`70541c4`)
- `feat: Flask REST API live` — health, predict and stats endpoints working (`11b52ef`)
- `feat: ML model training complete` — Logistic Regression 91.8% accuracy with confusion matrix (`f28402b`)
- `feat: text preprocessing module with VADER sentiment analysis` (`3808f8c`)
- `init: backend folder structure created` (`dffda65`)
- `Complete mental health frontend with quiz` (`5591ad1`)

### Fixed
- `fix: removed large CSV from tracking` — added to .gitignore (`0c5c8d6`)

### Docs
- `docs: added system architecture documentation` — all 7 ML pipeline stages documented (`ba963d5`)
- `docs: complete project README` — architecture, API docs and model performance (`54258e1`)

### Other
- `Merge branch 'main'` (`a3c1ba1`)
- `Your descriptive commit message` (`3460cda`)
