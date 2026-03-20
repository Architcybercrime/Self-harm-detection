# 🧠 Self-Harm Detection System
### AI-Based Detection Using Behavioral & Physiological Indicators

> **Project 34 | 2nd Year AIML Mini Project**  
> **Team:** Avani Upadhyay | Archit Agrawal

---

## 📌 Problem Statement
Self-harm is a critical mental health concern that often remains undetected due to stigma, lack of visible symptoms, and limited access to timely support. This system uses **multimodal AI** to analyze behavioral and physiological signals to identify at-risk individuals and trigger timely alerts.

---

## 🎯 Key Objectives
- Detect early indicators of self-harm risk using AI/ML
- Enable timely intervention by mental health professionals
- Preserve user privacy and confidentiality
- Support caregivers and mental health support systems

---

## ⚙️ System Architecture & Workflow
```
Data Collection → Preprocessing → Feature Extraction → 
Model Training → Evaluation → FastAPI → Alert Generation → PDF Report
```
```
Self-harm-detection/
│
├── backend/
│   ├── app.py                  ← Flask REST API (port 5000)
│   ├── main.py                 ← FastAPI v2.0 (port 8000) ← PRIMARY
│   ├── model/
│   │   └── train_model.py      ← ML model training
│   ├── utils/
│   │   ├── preprocess.py       ← Text preprocessing
│   │   ├── facial_analysis.py  ← DeepFace real-time webcam
│   │   ├── speech_analysis.py  ← Librosa audio analysis
│   │   ├── fusion.py           ← Multimodal risk fusion
│   │   ├── monitor.py          ← Trend-based drift detection
│   │   ├── database.py         ← Supabase integration
│   │   ├── auth.py             ← JWT authentication
│   │   ├── validators.py       ← Input validation
│   │   └── report_generator.py ← Professional PDF reports
│   ├── tests/
│   │   └── test_api.py         ← 28 pytest test cases
│   └── data/
│       └── README.md           ← Dataset instructions
│
├── streamlit_app.py            ← Interactive dashboard
├── frontend/
│   ├── index.html              ← Main UI
│   ├── style.css               ← Styling
│   └── scripts.js              ← Frontend logic
│
├── docs/
│   └── confusion_matrix.png    ← Model evaluation chart
│
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Primary API | Python, **FastAPI** v2.0 |
| Backup API | Python, Flask |
| Machine Learning | Scikit-learn, NLTK |
| Text Analysis | TF-IDF, VADER Sentiment |
| Facial Analysis | DeepFace, OpenCV (Real-time webcam) |
| Speech Analysis | Librosa, SpeechRecognition, PyAudio |
| Data Processing | Pandas, NumPy |
| Database | Supabase PostgreSQL |
| Authentication | JWT + Bcrypt |
| Security | Rate Limiting, CORS, Security Headers |
| Real-time | WebSocket (Socket.IO) |
| PDF Reports | ReportLab |
| Dashboard | Streamlit |
| Testing | Pytest (28 test cases) |
| Frontend | HTML5, CSS3, JavaScript |
| Visualization | Matplotlib, Seaborn |
| Model Persistence | Joblib |

---

## 🤖 ML Model Performance

| Metric | Score |
|---|---|
| Accuracy | **92.2%** |
| Precision | 92% |
| Recall | 92% |
| F1-Score | 0.92 |
| CV F1 Score | 0.9218 |
| Training Samples | 50,000 |
| Dataset | Kaggle Suicide Detection (232,074 posts) |

### Confusion Matrix
![Confusion Matrix](docs/confusion_matrix.png)

---

## 📡 API Endpoints (FastAPI v2.0)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/health` | Public | Check API status |
| POST | `/api/register` | Public | Register new user |
| POST | `/api/login` | Public | Login and get JWT token |
| GET | `/api/profile` | JWT | Get user profile |
| POST | `/api/predict` | JWT | Predict risk from text |
| POST | `/api/generate-report` | JWT | **Download professional PDF report** |
| POST | `/api/analyze-face` | JWT | Real-time webcam emotion analysis |
| POST | `/api/analyze-speech` | JWT | Live microphone speech analysis |
| POST | `/api/predict-multimodal` | JWT | Combined text+face+speech prediction |
| GET | `/api/stats` | JWT | Session statistics |
| GET | `/api/monitor` | JWT | Trend-based drift detection |
| GET | `/api/history` | JWT | Prediction history from DB |
| GET | `/api/db-stats` | JWT | Database statistics |

### Swagger UI
```
FastAPI Docs : http://127.0.0.1:8000/docs
FastAPI ReDoc: http://127.0.0.1:8000/redoc
Flask Docs   : http://127.0.0.1:5000/apidocs
```

---

## 📄 Professional PDF Report

The system generates clinical-style psychological assessment reports including:
- **Overall Risk Level** with confidence score
- **Behavioral Tendencies** identified through AI analysis
- **Possible Underlying Conditions** with likelihood assessment
- **Professional Recommendations** (CBT, DBT, crisis support)
- **Emergency Support Resources** (iCall, Vandrevala, AASRA)
```json
POST /api/generate-report
{
  "text": "I feel completely hopeless and want to disappear"
}
```
Returns: Downloadable PDF file

---

## 🎯 Sample API Usage

### Text Prediction
```json
POST /api/predict
{
  "text": "I feel completely hopeless and nobody cares"
}
```
**Response:**
```json
{
  "alert_triggered": true,
  "confidence": 0.894,
  "risk_level": "HIGH",
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

### Multimodal with Custom Weights
```json
POST /api/predict-multimodal
{
  "text": "I feel hopeless",
  "use_webcam": true,
  "use_microphone": false,
  "weights": {"text": 0.6, "facial": 0.4, "speech": 0.0}
}
```

---

## 🔐 Security Features

- ✅ JWT Authentication with 24hr token expiry
- ✅ Bcrypt password hashing (industry standard)
- ✅ Rate limiting on all endpoints
- ✅ Security headers (XSS, Clickjacking protection)
- ✅ CORS configuration (restricted origins)
- ✅ Input validation with Pydantic models
- ✅ SQL injection prevention (Supabase ORM)
- ✅ CSRF protection (JWT stateless)
- ✅ Environment variables for all secrets
- ✅ Row Level Security on Supabase tables

---

## 🧪 Testing
```bash
cd backend
python -m pytest tests/test_api.py -v
```

**28 test cases covering:**
- Health endpoint + WebSocket status
- Prediction (high risk, low risk, validation, unauthorized)
- Authentication (register, login, duplicate, missing fields)
- Database endpoints (stats, history, structure)
- Preprocessing pipeline
- Multimodal fusion (custom weights, invalid weights)
- Speech analysis module

---

## 🖥️ Streamlit Dashboard

Interactive dashboard for testing all features:
```bash
# Terminal 1 - Start FastAPI
cd backend
python main.py

# Terminal 2 - Start Streamlit
streamlit run streamlit_app.py
```

**Dashboard Pages:**
- 🏠 Dashboard — stats + quick analysis + PDF download
- 📝 Text Analysis — full analysis + PDF report
- 📷 Facial Analysis — webcam + image upload
- 🎤 Speech Analysis — microphone recording
- 🔀 Multimodal — combined analysis
- 📊 Monitoring — trend alerts, drift detection
- 📈 History — all predictions from database

---

## 🚀 Setup & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/Architcybercrime/Self-harm-detection.git
cd Self-harm-detection
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Setup Environment Variables
```bash
cp backend/.env.example backend/.env
# Fill in your Supabase and JWT credentials
```

### Step 4: Download Dataset
Download from Kaggle and place in `backend/data/`:
- Link: https://www.kaggle.com/datasets/nikhileswarkomati/suicide-watch
- Filename: `Suicide_Detection.csv`

### Step 5: Train the Model
```bash
cd backend
python model/train_model.py
```

### Step 6: Run FastAPI (Primary)
```bash
cd backend
python main.py
# Swagger UI: http://127.0.0.1:8000/docs
```

### Step 7: Run Streamlit Dashboard
```bash
streamlit run streamlit_app.py
# Dashboard: http://localhost:8501
```

### Step 8: Run Flask (Backup)
```bash
cd backend
python app.py
# Swagger UI: http://127.0.0.1:5000/apidocs
```

---

## 🗺️ Future Enhancements
- [ ] Cloud deployment on Render.com
- [ ] Docker containerization
- [ ] Arduino heart rate sensor integration
- [ ] Mobile PWA application
- [ ] Google OAuth authentication
- [ ] Video upload analysis

---

## ⚠️ Ethical Considerations
- This system is a **support tool only** — not a replacement for professional diagnosis
- All predictions stored securely in cloud database with RLS
- Alert system involves human-in-the-loop decision making
- All passwords hashed using bcrypt
- PDF reports include mandatory clinical disclaimer

---

## 👥 Team

| Name | Role |
|---|---|
| Avani Upadhyay | Frontend Development, UI/UX |
| Archit Agrawal | Backend API, ML Model, FastAPI, Database, Security, PDF Reports |

---

> *"Early detection saves lives. AI can be a compassionate tool when built responsibly."*