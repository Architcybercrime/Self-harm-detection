<div align="center">

# 🛡️ SafeSignal
### AI-Powered Self-Harm & Suicide Risk Detection System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![Tests](https://img.shields.io/badge/Tests-35%2B%20cases-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

> **2nd Year AIML Mini Project — Project #34**  
> *Avani Upadhyay · Archit Agrawal*

<br/>

**[🌐 Live Demo](https://self-harm-detection.vercel.app)** &nbsp;|&nbsp; **[📖 API Docs](https://safesignal-api-prod.onrender.com/docs)** &nbsp;|&nbsp; **[📊 Swagger UI](https://safesignal-api-prod.onrender.com/redoc)**

<br/>

*An early-warning mental health surveillance platform that fuses text, facial expression, and voice analysis to detect self-harm risk in real time — with 92.2% accuracy on 232,074 training samples.*

</div>

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [System Architecture](#-system-architecture)
4. [ML Pipeline](#-ml-pipeline)
5. [API Reference](#-api-reference)
6. [Security](#-security)
7. [Performance](#-performance)
8. [Test Coverage](#-test-coverage)
9. [Project Structure](#-project-structure)
10. [Local Setup](#-local-setup)
11. [Deployment](#-deployment)
12. [Ethical Considerations](#-ethical-considerations)
13. [Team](#-team)

---

## 🔍 Overview

SafeSignal is a full-stack, production-deployed mental health AI platform that analyses **text, facial expressions, and speech** simultaneously to compute a real-time self-harm risk score. It is designed to assist mental health professionals and crisis counsellors with an objective, explainable second opinion.

**Why SafeSignal?**

| Challenge | Our Solution |
|-----------|-------------|
| Late detection of crisis signals | Real-time multimodal analysis pipeline |
| Single-modality bias | Weighted fusion of 3 independent models |
| Black-box AI in healthcare | Explainable risk indicators + PDF reports |
| No professional oversight | High-risk WebSocket alerts + email/SMS dispatch |
| Data privacy concerns | JWT auth, Row-Level Security, audit logging |

---

## ✨ Key Features

### 🤖 AI & Analysis
- **Text Analysis** — TF-IDF vectorisation + VADER sentiment + Logistic Regression (92.2% accuracy)
- **Facial Emotion Detection** — DeepFace + OpenCV fallback; analyses 7 emotion dimensions from webcam or uploaded image
- **Voice / Speech Analysis** — Librosa acoustic feature extraction (pitch stress, tremor, speech rate, vocal energy, flat affect) + SpeechRecognition transcription
- **Multimodal Fusion** — Dynamic weighted combination of all three modalities with configurable weights
- **Batch Analysis** — CSV upload for bulk screening (up to 500 rows)
- **Video Analysis** — Frame-by-frame facial + audio extraction from uploaded video files

### 📊 Reporting & Monitoring
- **Professional PDF Reports** — ReportLab-generated clinical assessment reports with executive summary, risk indicators, recommendations, and mandatory disclaimers
- **Real-time WebSocket Alerts** — Socket.IO push notifications on HIGH risk detection
- **Email + SMS + WhatsApp Alerts** — SendGrid email and Twilio SMS/WhatsApp dispatch to registered contacts
- **Model Drift Detection** — Sliding-window trend analysis with ESCALATING_RISK / CONSECUTIVE_HIGH_RISK alerts
- **Longitudinal Risk Trends** — Per-user risk history and trend visualisation

### 🔐 Security & Auth
- JWT Bearer token authentication (24-hour expiry)
- Demo visitor tokens (2-hour short-lived JWT, no credentials required)
- Multi-Factor Authentication (TOTP/HOTP via `pyotp`, QR code setup)
- API Key system (`shd_` prefixed keys as JWT alternative)
- Bcrypt password hashing with per-user salt
- Rate limiting on all endpoints (`slowapi`)
- Structured security audit log (every auth event logged to Supabase)

### 🏗️ Infrastructure
- FastAPI 2.0 REST API with OpenAPI 3.1 (Swagger + ReDoc)
- Supabase PostgreSQL with Row-Level Security
- GitHub Actions CI (lint + 35+ pytest cases on every push to `main`)
- Deployed: Render (backend) + Vercel (frontend)

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER / VERCEL                      │
│   dashboard.html · login.html · register.html           │
│   Local JS classifier (instant offline fallback)        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS  +  JWT Bearer Token
                       │ WebSocket (Socket.IO)
┌──────────────────────▼──────────────────────────────────┐
│              RENDER  —  FastAPI 2.0 (Python 3.11)       │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  auth router│  │predict router│  │analysis router│  │
│  │  /register  │  │  /predict    │  │ /analyze-face │  │
│  │  /login     │  │  /predict-   │  │ /analyze-     │  │
│  │  /mfa/*     │  │  multimodal  │  │  speech       │  │
│  └─────────────┘  │  /predict-   │  │ /analyze-     │  │
│                   │  batch       │  │  video        │  │
│  ┌─────────────┐  │  /generate-  │  └───────────────┘  │
│  │ keys router │  │  report      │                      │
│  │ admin router│  └──────────────┘  ┌───────────────┐  │
│  │monitor router                    │  ml_engine.py │  │
│  └─────────────┘                    │  TF-IDF+VADER │  │
│                                     │  + LogReg     │  │
│  ┌──────────────────────────────┐   │  keyword fall-│  │
│  │     utils/                   │   │  back (robust)│  │
│  │  preprocess · fusion         │   └───────────────┘  │
│  │  monitor · alerts            │                      │
│  │  report_generator · audit    │  Socket.IO           │
│  │  facial_analysis · speech    │  WebSocket server    │
│  └──────────────────────────────┘                      │
└──────────────────────┬──────────────────────────────────┘
                       │ Supabase JS Client
┌──────────────────────▼──────────────────────────────────┐
│               SUPABASE  —  PostgreSQL                    │
│                                                          │
│  Users · Predictions · ApiKeys · UserMFA                │
│  UserProfiles · AuditLogs                               │
│  Row-Level Security on all tables                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🧠 ML Pipeline

The ML pipeline follows a 7-stage production-ready design:

```
Stage 1: Data Ingestion
    Kaggle "Suicide Watch" dataset — 232,074 Reddit posts
    Labels: suicide (high risk) / non-suicide (low risk)

Stage 2: Preprocessing
    clean_text()         → lowercase, strip URLs/@mentions/special chars
    remove_stopwords()   → NLTK English stopwords (keep negations: not/no/never)
    lemmatize_text()     → WordNet lemmatisation

Stage 3: Feature Extraction
    TF-IDF Vectoriser    → 10,000-feature sparse matrix
    VADER Sentiment      → compound score + neg score (2 numeric features)
    Combined Feature     → hstack([tfidf_vec, sentiment, neg_score])

Stage 4: Model Training
    Algorithm: Logistic Regression (liblinear solver, C=1.0)
    Train/Test Split: 80/20
    Cross-Validation: 5-fold stratified CV

Stage 5: Evaluation
    Accuracy:  92.2%
    Precision: 92%
    Recall:    92%
    F1-Score:  0.92
    CV F1:     0.9218 (±0.004)

Stage 6: Inference
    run_prediction(text) → risk_level + confidence + sentiment + indicators
    Fallback: keyword_based_prediction() when model unavailable

Stage 7: Monitoring
    log_prediction() → sliding-window drift detection
    get_trend_analysis() → ESCALATING_RISK / CONSECUTIVE_HIGH_RISK alerts
```

### Multimodal Fusion

When multiple modalities are active, scores are fused with configurable weights:

```python
default_weights = { "text": 0.5, "face": 0.3, "speech": 0.2 }
final_score = Σ(modality_score × weight) / Σ(active_weights)
```

Risk is escalated if any single modality exceeds the HIGH threshold.

---

## 📡 API Reference

**Base URL:** `https://safesignal-api-prod.onrender.com`

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `GET` | `/api/health` | Detailed health with CORS headers |
| `GET` | `/api/demo-token` | Issue 2-hour visitor JWT (no login needed) |
| `POST` | `/api/register` | Register new user |
| `POST` | `/api/login` | Login → 24-hour JWT |
| `POST` | `/api/auth/mfa/login` | MFA second-step verification |

### Prediction Endpoints *(JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/predict` | Text risk prediction — **92.2% accuracy** |
| `POST` | `/api/predict-multimodal` | Text + face + speech fusion |
| `POST` | `/api/predict-batch` | CSV bulk analysis (max 500 rows) |
| `POST` | `/api/generate-report` | Download PDF clinical assessment |

### Analysis Endpoints *(JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze-face` | Facial emotion from webcam/base64 image |
| `POST` | `/api/analyze-speech` | Speech analysis from microphone |
| `POST` | `/api/analyze-speech-upload` | Browser-recorded audio upload |
| `POST` | `/api/analyze-video` | Video file analysis |

### User & Monitoring *(JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Session prediction statistics |
| `GET` | `/api/history` | Prediction history from database |
| `GET` | `/api/monitor` | Drift detection + trend analysis |
| `GET` | `/api/profile` | Current user profile |
| `GET/PUT` | `/api/user/profile` | Alert preferences |
| `GET` | `/api/user/risk-trend` | Longitudinal risk trend |

### API Keys *(JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/keys/generate` | Generate personal API key |
| `GET` | `/api/keys/my-key` | View active API key |
| `DELETE` | `/api/keys/revoke` | Revoke API key |

### MFA *(JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/mfa/setup` | Setup TOTP (returns QR code) |
| `POST` | `/api/auth/mfa/verify-setup` | Activate MFA |
| `POST` | `/api/auth/mfa/disable` | Disable MFA |
| `GET` | `/api/auth/mfa/status` | Check MFA status |

### Admin *(Admin JWT required)*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/users` | List all users |
| `GET` | `/api/admin/analytics` | Aggregated risk analytics |
| `GET` | `/api/admin/audit-logs` | Security audit log |

### Example Request & Response

```bash
# Get demo token (no account needed)
curl https://safesignal-api-prod.onrender.com/api/demo-token

# Run text analysis
curl -X POST https://safesignal-api-prod.onrender.com/api/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel completely hopeless and nobody cares about me"}'
```

```json
{
  "risk_level": "HIGH",
  "confidence": 0.8940,
  "alert_triggered": true,
  "sentiment_score": -0.5574,
  "message": "High risk indicators detected. Please seek professional support immediately.",
  "modality": "text",
  "risk_indicators": {
    "text_sentiment": "negative",
    "confidence_level": "high",
    "severity": "critical"
  },
  "recommendations": {
    "immediate_action": true,
    "support_resources": [
      "iCall: 9152987821",
      "Vandrevala Foundation: 1860-2662-345",
      "AASRA: 9820466627"
    ],
    "follow_up": "Immediate professional consultation recommended"
  },
  "analysis_timestamp": "2026-05-01T10:30:00.000Z"
}
```

---

## 🔐 Security

SafeSignal implements defence-in-depth with multiple overlapping security layers:

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT Bearer tokens (24h) + API Keys (`shd_` prefix) |
| **MFA** | TOTP/HOTP via `pyotp` with QR code enrollment |
| **Password Storage** | `bcrypt` with per-user salt, never stored in plaintext |
| **Transport** | HTTPS-only; HSTS header enforced |
| **Rate Limiting** | `slowapi` on all endpoints — prevents brute force |
| **Input Validation** | Pydantic models — type checking, min/max length, regex |
| **Output Sanitization** | HTML tags stripped before inclusion in responses |
| **SQL Injection** | Supabase ORM only — zero raw SQL queries |
| **CORS** | Restricted to specific origins; explicit header enforcement |
| **Security Headers** | `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`, `HSTS` |
| **CSRF** | Stateless JWT (no cookies) — inherently CSRF-resistant |
| **Row-Level Security** | Supabase RLS policies on all database tables |
| **Audit Logging** | Every auth event → `AuditLogs` table with IP, severity, timestamp |
| **Role Enforcement** | Admin role verified in JWT payload AND database |
| **Secrets Management** | All keys via environment variables — no hardcoded credentials |

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Model Accuracy | **92.2%** |
| Precision | 92% |
| Recall | 92% |
| F1-Score | **0.92** |
| Cross-Validation F1 | 0.9218 ± 0.004 |
| Training Samples | 232,074 Reddit posts |
| Dataset | [Kaggle — Suicide Watch](https://www.kaggle.com/datasets/nikhileswarkomati/suicide-watch) |
| Inference Latency | < 200ms (warm instance) |
| Batch Capacity | 500 rows per CSV |
| API Endpoints | 25+ |

---

## 🧪 Test Coverage

```bash
cd backend
pytest tests/test_api.py -v
```

**35+ test cases** covering:

| Category | Tests |
|----------|-------|
| Health & CORS | Response body, status codes, CORS headers |
| Registration | Success, duplicate user, short username/password, invalid characters |
| Login | Valid credentials, nonexistent user, missing fields |
| Demo Token | 200 response, body fields, valid JWT structure, accepted by `/predict` |
| Prediction | Auth required, empty/short/long text, valid predictions, missing body |
| Profile | Auth required, returns correct username |
| Statistics | `/stats`, `/history`, `/monitor` response shapes |
| Admin | Non-admin rejected (403), admin accepted |
| Input Validation | Edge cases: whitespace-only, unicode, extremely long text |
| Utilities | `sanitize_output()` (strips HTML, preserves plain text) |
| Preprocessing | `full_preprocess()` pipeline correctness |
| Fusion Module | Text-only, no input, custom weights, invalid weights |

**CI:** GitHub Actions runs the full test suite on every push to `main`.

---

## 📁 Project Structure

```
Self-harm-detection/
│
├── .github/
│   └── workflows/
│       └── ci.yml                  ← GitHub Actions: lint + pytest on push
│
├── backend/
│   ├── main.py                     ← FastAPI app + Socket.IO + middleware
│   ├── ml_engine.py                ← Central ML state (model, prediction_log, run_prediction)
│   ├── shared.py                   ← JWT verification, sanitisation, Supabase client
│   ├── requirements.txt            ← Pinned dependencies (binary wheels, Python 3.11)
│   ├── render.yaml                 ← Render deployment config
│   ├── download_models.py          ← NLTK + model artifact setup
│   ├── run_migrations.py           ← Supabase table migrations
│   │
│   ├── routers/                    ← FastAPI APIRouter modules
│   │   ├── auth.py                 ← /register /login /profile /mfa/*
│   │   ├── predict.py              ← /predict /predict-multimodal /predict-batch /generate-report
│   │   ├── analysis.py             ← /analyze-face /analyze-speech /analyze-video
│   │   ├── monitoring.py           ← /stats /history /monitor /db-stats /user/*
│   │   ├── keys.py                 ← /keys/generate /keys/my-key /keys/revoke
│   │   └── admin.py                ← /admin/users /admin/analytics /admin/audit-logs
│   │
│   ├── utils/
│   │   ├── preprocess.py           ← Text cleaning, stopwords, lemmatisation, VADER
│   │   ├── fusion.py               ← Multimodal risk score fusion
│   │   ├── facial_analysis.py      ← DeepFace + OpenCV fallback
│   │   ├── speech_analysis.py      ← Librosa acoustic features + SpeechRecognition
│   │   ├── monitor.py              ← Drift detection, trend analysis
│   │   ├── database.py             ← Supabase CRUD helpers
│   │   ├── audit_log.py            ← Structured security event logging
│   │   ├── alerts.py               ← SendGrid email + Twilio SMS/WhatsApp
│   │   ├── validators.py           ← Input validation helpers
│   │   └── report_generator.py     ← ReportLab PDF clinical reports
│   │
│   ├── model/
│   │   ├── train_model.py          ← Full ML training script
│   │   ├── risk_model.pkl          ← Trained Logistic Regression (gitignored)
│   │   └── tfidf_vectorizer.pkl    ← Fitted TF-IDF vectoriser (gitignored)
│   │
│   ├── data/
│   │   └── README.md               ← Dataset download instructions
│   │
│   └── tests/
│       └── test_api.py             ← 35+ pytest test cases
│
├── frontend/
│   ├── config.js                   ← API_BASE — single source of truth for backend URL
│   ├── index.html                  ← Landing / home page
│   ├── login.html                  ← Login with cold-start retry logic
│   ├── register.html               ← Registration
│   ├── dashboard.html              ← Main analysis dashboard (text/face/voice/video)
│   └── style.css                   ← Global styles
│
└── README.md
```

---

## 🚀 Local Setup

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (free tier works)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Architcybercrime/Self-harm-detection.git
cd Self-harm-detection/backend

# 2. Install dependencies (use --prefer-binary for fast installs)
pip install --prefer-binary -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env — required keys:
#   JWT_SECRET_KEY=<any long random string>
#   SUPABASE_URL=https://xxxx.supabase.co
#   SUPABASE_KEY=eyJ...  (anon/public JWT key from Supabase → Settings → API)

# 4. Download NLTK data
python -c "
import nltk
for c in ['vader_lexicon','stopwords','wordnet','punkt','punkt_tab']:
    nltk.download(c)
"

# 5. (Optional) Train the ML model
#    First download dataset from Kaggle:
#    https://www.kaggle.com/datasets/nikhileswarkomati/suicide-watch
#    Place Suicide_Detection.csv in backend/data/
python model/train_model.py

# 6. Run database migrations
python run_migrations.py

# 7. Start the API
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**Swagger UI:** http://127.0.0.1:8000/docs

**Frontend:** Open `frontend/login.html` directly in your browser  
*(or set `API_BASE` in `frontend/config.js` to `http://127.0.0.1:8000` for local dev)*

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT signing |
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon/public JWT key |
| `SENDGRID_API_KEY` | Optional | SendGrid key for email alerts |
| `SENDGRID_FROM_EMAIL` | Optional | Sender address for alerts |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio SID for SMS/WhatsApp |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Optional | Twilio sender number |
| `ALLOWED_ORIGINS` | Optional | Comma-separated CORS origins |

---

## ☁️ Deployment

### Live URLs

| Service | URL |
|---------|-----|
| **Frontend** | https://self-harm-detection.vercel.app |
| **Backend API** | https://safesignal-api-prod.onrender.com |
| **Swagger UI** | https://safesignal-api-prod.onrender.com/docs |
| **ReDoc** | https://safesignal-api-prod.onrender.com/redoc |

### Deploy Your Own

**Backend (Render):**
1. Fork the repo
2. Create a new Render Web Service → point to `backend/` root directory
3. Build command: `pip install --prefer-binary -r requirements.txt && python download_models.py && python run_migrations.py`
4. Start command: `uvicorn main:socket_app --host 0.0.0.0 --port $PORT`
5. Set environment variables: `JWT_SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `PYTHON_VERSION=3.11.0`

**Frontend (Vercel):**
1. Connect your fork to Vercel
2. Set root directory to `frontend/`
3. Update `API_BASE` in `frontend/config.js` to your Render URL

---

## ⚖️ Ethical Considerations

SafeSignal is designed with responsible AI principles at its core:

- **Support tool, not a diagnosis** — all outputs are flagged as AI-generated indicators to be reviewed by a qualified mental health professional, never as clinical conclusions
- **Human-in-the-loop** — HIGH risk alerts require human review before any intervention is initiated
- **Privacy by design** — predictions stored with Supabase Row-Level Security; no plaintext credentials ever stored or transmitted
- **Mandatory disclaimers** — every PDF report includes a clinical disclaimer and directs to professional resources
- **Crisis resources included** — HIGH risk responses always include helpline numbers (iCall, Vandrevala Foundation, AASRA)
- **Informed consent** — users are clearly informed their text is being analysed for mental health signals
- **No profiling** — system flags risk events per-session, not used to build permanent risk profiles without user consent
- **Transparency** — open-source codebase; model type (Logistic Regression), dataset source (Kaggle), and accuracy (92.2%) are publicly documented

---

## 👥 Team

| Name | Contributions |
|------|--------------|
| **Avani Upadhyay** | Frontend Development, UI/UX Design, Dashboard, User Flows |
| **Archit Agrawal** | Backend API (FastAPI), ML Model Training, Database Design, Security Architecture, PDF Reports, Deployment, CI/CD |

---

## 📚 References

- [Kaggle — Suicide Watch Dataset](https://www.kaggle.com/datasets/nikhileswarkomati/suicide-watch) — 232,074 Reddit posts, Nikhileswar Komati
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment) — Hutto & Gilbert (2014)
- [DeepFace](https://github.com/serengil/deepface) — Facial recognition and emotion analysis
- [Supabase](https://supabase.com) — Open source Firebase alternative
- [Scikit-learn](https://scikit-learn.org) — Machine learning in Python

---

<div align="center">

*"Early detection saves lives. AI can be a compassionate tool when built responsibly."*

<br/>

Made with ❤️ for mental health awareness

</div>
