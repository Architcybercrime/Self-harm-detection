# SafeSignal — Self-Harm Detection System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Pytest](https://img.shields.io/badge/Tests-35%2B%20cases-brightgreen?logo=pytest)
![Deploy](https://img.shields.io/badge/Backend-Render-blueviolet?logo=render)
![Frontend](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> **Project 34 — 2nd Year AIML Mini Project**
> Team: Avani Upadhyay | Archit Agrawal

AI-based multimodal system for self-harm risk detection using text, facial expressions, and speech analysis. Accuracy: **92.2%**.

---

## Architecture

```
Browser / Vercel Frontend
        |
        | HTTPS (JWT Bearer token)
        v
Render Backend  ──────────────  Supabase PostgreSQL
(FastAPI 2.0)                   (Users, Predictions,
        |                        ApiKeys, UserMFA,
        |                        UserProfiles, AuditLog)
        |
   ┌────┴──────────────────────────────────┐
   │              ML Pipeline              │
   │  TF-IDF + VADER + Logistic Regression │
   │  DeepFace (facial emotion)            │
   │  Librosa + SpeechRecognition (audio)  │
   │  Multimodal Fusion (dynamic weights)  │
   └───────────────────────────────────────┘
        |
   Real-time WebSocket (Socket.IO)
   PDF Report Generator (ReportLab)
```

```
Self-harm-detection/
├── .github/
│   └── workflows/
│       └── ci.yml              <- GitHub Actions: pytest on push to main
├── backend/
│   ├── main.py                 <- FastAPI v2.0 (PRIMARY, port 8000)
│   ├── app.py                  <- Flask backup API (port 5000)
│   ├── .env.example            <- Template for environment variables
│   ├── model/
│   │   └── train_model.py      <- ML model training script
│   ├── utils/
│   │   ├── auth.py             <- JWT + bcrypt authentication
│   │   ├── preprocess.py       <- Text preprocessing pipeline
│   │   ├── facial_analysis.py  <- DeepFace webcam/image analysis
│   │   ├── speech_analysis.py  <- Librosa + SpeechRecognition
│   │   ├── fusion.py           <- Multimodal risk score fusion
│   │   ├── monitor.py          <- Drift detection & monitoring
│   │   ├── database.py         <- Supabase helpers
│   │   ├── alerts.py           <- Email / SMS / WhatsApp alerts
│   │   ├── audit_log.py        <- Structured security audit log
│   │   ├── validators.py       <- Input validation helpers
│   │   └── report_generator.py <- Professional PDF reports
│   └── tests/
│       └── test_api.py         <- 35+ pytest test cases
├── frontend/
│   ├── index.html              <- Main UI (deployed to Vercel)
│   ├── style.css               <- Styling
│   └── main.js                 <- Frontend logic
├── streamlit_app.py            <- Interactive Streamlit dashboard
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | Public | Health check with CORS headers |
| GET | `/api/cors-check` | Public | CORS verification endpoint |
| GET | `/api/demo-token` | Public | Issue 2-hour visitor JWT (no credentials) |
| POST | `/api/register` | Public | Register new user |
| POST | `/api/login` | Public | Login and get 24-hour JWT |
| POST | `/api/auth/mfa/login` | Public | MFA second-step login |
| GET | `/api/profile` | JWT | Get current user's profile |
| POST | `/api/predict` | JWT | Predict self-harm risk from text (92.2% accuracy) |
| POST | `/api/generate-report` | JWT | Download professional PDF risk report |
| POST | `/api/analyze-face` | JWT | Facial emotion detection (webcam or base64) |
| POST | `/api/analyze-speech` | JWT | Speech analysis (microphone or audio file) |
| POST | `/api/analyze-speech-upload` | JWT | Browser-recorded audio upload |
| POST | `/api/predict-multimodal` | JWT | Combined text + face + speech prediction |
| POST | `/api/predict-batch` | JWT | Batch CSV analysis (max 500 rows) |
| POST | `/api/analyze-video` | JWT | Video file analysis |
| GET | `/api/stats` | JWT | Session prediction statistics |
| GET | `/api/monitor` | JWT | Monitoring and drift detection report |
| GET | `/api/history` | JWT | Recent prediction history from DB |
| GET | `/api/db-stats` | JWT | Database statistics |
| GET | `/api/user/profile` | JWT | Alert preferences and user profile |
| PUT | `/api/user/profile` | JWT | Update alert preferences |
| GET | `/api/user/risk-trend` | JWT | Longitudinal risk trend (last N days) |
| POST | `/api/keys/generate` | JWT | Generate personal API key |
| GET | `/api/keys/my-key` | JWT | View your active API key |
| DELETE | `/api/keys/revoke` | JWT | Revoke your API key |
| POST | `/api/auth/mfa/setup` | JWT | Set up TOTP MFA (returns QR code) |
| POST | `/api/auth/mfa/verify-setup` | JWT | Confirm and activate MFA |
| POST | `/api/auth/mfa/disable` | JWT | Disable MFA |
| GET | `/api/auth/mfa/status` | JWT | Check MFA status |
| GET | `/api/admin/users` | Admin JWT | List all users |
| GET | `/api/admin/analytics` | Admin JWT | Aggregated risk analytics |
| GET | `/api/admin/audit-logs` | Admin JWT | Security audit log |

Interactive docs:
- Swagger UI: `https://safesignal-api.onrender.com/docs`
- ReDoc: `https://safesignal-api.onrender.com/redoc`

---

## ML Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | **92.2%** |
| Precision | 92% |
| Recall | 92% |
| F1-Score | 0.92 |
| CV F1 Score | 0.9218 |
| Training Samples | 50,000 |
| Dataset | Kaggle Suicide Detection (232,074 posts) |

---

## Security Features

- JWT authentication with role claim (user / admin / demo) — 24-hour expiry
- Demo visitor tokens — 2-hour short-lived JWT, no credentials required
- Bcrypt password hashing with per-user salt
- Rate limiting via `slowapi` on all endpoints
- Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`
- Explicit CORS header enforcement on health and cors-check endpoints
- Output sanitization — HTML tags stripped from user text before inclusion in API responses
- Admin role enforced in JWT payload and verified against DB (backward-compatible)
- SQL injection prevention (Supabase ORM — no raw SQL)
- Input validation with Pydantic models (types, min/max length, regex)
- CSRF protection (stateless JWT — no cookies)
- Multi-factor authentication (TOTP/HOTP via pyotp)
- Structured security audit log for all auth events
- Environment variables for all secrets (no hardcoded credentials)
- Row Level Security on Supabase tables

---

## Test Coverage

```bash
cd backend
pytest tests/test_api.py -v
```

35+ test cases covering:
- Health endpoint response body and CORS headers
- CORS check endpoint
- Register (success, duplicate, short username, short password, invalid characters)
- Login (nonexistent user, missing fields)
- Demo token (200 response, body fields, valid JWT, accepted by predict)
- Predict (requires auth, empty/too-short/too-long text, valid text, missing body)
- Profile endpoint (requires auth, returns username)
- Stats, History, Monitor endpoints
- Admin/users (non-admin rejected, admin accepted)
- Input validation edge cases
- `sanitize_output` helper (strips HTML, leaves plain text unchanged)
- Text preprocessing pipeline
- Multimodal fusion module (text-only, no input, invalid weights)

---

## Setup — Local

### Prerequisites
- Python 3.11+
- A Supabase project (free tier works)

### Steps

```bash
# 1. Clone
git clone https://github.com/Architcybercrime/Self-harm-detection.git
cd Self-harm-detection

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in JWT_SECRET_KEY, SUPABASE_URL, SUPABASE_KEY

# 4. Download NLTK data
python -c "import nltk; nltk.download('vader_lexicon')"

# 5. (Optional) Download dataset and train the model
#    Dataset: https://www.kaggle.com/datasets/nikhileswarkomati/suicide-watch
#    Place Suicide_Detection.csv in backend/data/
python model/train_model.py

# 6. Start FastAPI
python main.py
# Swagger UI: http://127.0.0.1:8000/docs

# 7. (Optional) Start Streamlit dashboard in another terminal
cd ..
streamlit run streamlit_app.py
```

---

## Setup — Docker

```bash
# Build and start both API and any supporting services
docker-compose up --build

# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

---

## Setup — Deployed

| Service | URL |
|---------|-----|
| Frontend | Vercel — deploys automatically from `frontend/` folder |
| Backend | `https://safesignal-api.onrender.com` |
| Swagger | `https://safesignal-api.onrender.com/docs` |

The frontend uses `/api/demo-token` to obtain a short-lived visitor JWT — no account required for demo use.

---

## Sample API Usage

### Get a demo token (no login needed)
```bash
curl https://safesignal-api.onrender.com/api/demo-token
```

### Text prediction
```bash
curl -X POST https://safesignal-api.onrender.com/api/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel completely hopeless and nobody cares"}'
```

Response:
```json
{
  "risk_level": "HIGH",
  "confidence": 0.894,
  "alert_triggered": true,
  "sentiment_score": -0.5574,
  "risk_indicators": {
    "text_sentiment": "negative",
    "confidence_level": "high",
    "severity": "critical"
  },
  "recommendations": {
    "support_resources": [
      "iCall: 9152987821",
      "Vandrevala Foundation: 1860-2662-345",
      "AASRA: 9820466627"
    ]
  }
}
```

---

## Screenshots

_Screenshots placeholder — add frontend and dashboard images here._

---

## Ethical Considerations

- This system is a **support tool only** — not a replacement for professional clinical diagnosis.
- All predictions are stored securely with Supabase Row Level Security.
- Alert system involves human-in-the-loop decision making.
- Passwords hashed using bcrypt; no plaintext credentials stored or transmitted.
- PDF reports include a mandatory clinical disclaimer.

---

## Team

| Name | Role |
|------|------|
| Avani Upadhyay | Frontend Development, UI/UX |
| Archit Agrawal | Backend API, ML Model, FastAPI, Database, Security, PDF Reports |

---

> *"Early detection saves lives. AI can be a compassionate tool when built responsibly."*
