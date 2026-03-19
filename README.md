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
Model Training → Evaluation → Flask API → Alert Generation
```
```
Self-harm-detection/
│
├── backend/
│   ├── app.py                  ← Flask REST API (12 endpoints)
│   ├── model/
│   │   └── train_model.py      ← ML model training
│   ├── utils/
│   │   ├── preprocess.py       ← Text preprocessing
│   │   ├── facial_analysis.py  ← DeepFace real-time webcam detection
│   │   ├── speech_analysis.py  ← Librosa audio analysis
│   │   ├── fusion.py           ← Multimodal risk fusion
│   │   ├── monitor.py          ← Drift detection
│   │   ├── database.py         ← Supabase integration
│   │   ├── auth.py             ← JWT authentication
│   │   └── validators.py       ← Input validation
│   ├── tests/
│   │   └── test_api.py         ← 22 pytest test cases
│   └── data/
│       └── README.md           ← Dataset instructions
│
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
| Backend API | Python, Flask |
| Machine Learning | Scikit-learn, NLTK |
| Text Analysis | TF-IDF, VADER Sentiment |
| Facial Analysis | DeepFace, OpenCV (Real-time webcam) |
| Speech Analysis | Librosa, SpeechRecognition, PyAudio |
| Data Processing | Pandas, NumPy |
| Database | Supabase PostgreSQL |
| Authentication | JWT + Bcrypt |
| Security | Flask-Talisman, Rate Limiting, CORS |
| Testing | Pytest (22 test cases) |
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

### Confusion Matrix
![Confusion Matrix](docs/confusion_matrix.png)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check API status |
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login and get JWT token |
| GET | `/api/profile` | Get user profile [JWT] |
| POST | `/api/predict` | Predict risk from text |
| POST | `/api/analyze-face` | Real-time webcam emotion analysis |
| POST | `/api/analyze-speech` | Live microphone speech analysis |
| POST | `/api/predict-multimodal` | Combined text+face+speech prediction |
| GET | `/api/stats` | Session statistics |
| GET | `/api/monitor` | Drift detection report |
| GET | `/api/history` | Prediction history from DB |
| GET | `/api/db-stats` | Database statistics |

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
    "severity": "high"
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

### Real-time Webcam Analysis ✅ WORKING
```json
POST /api/analyze-face
{
  "use_webcam": true
}
```
**Response:**
```json
{
  "dominant_emotion": "neutral",
  "emotions": {
    "angry": 3.36,
    "disgust": 0.0,
    "fear": 0.23,
    "happy": 0.84,
    "neutral": 88.16,
    "sad": 7.39,
    "surprise": 0.02
  },
  "facial_risk_score": 0.1342,
  "risk_level": "LOW"
}
```

### Live Microphone Analysis ✅ WORKING
```json
POST /api/analyze-speech
{
  "use_microphone": true,
  "duration": 5
}
```

### Multimodal Analysis (Text + Webcam + Mic) ✅ WORKING
```json
POST /api/predict-multimodal
{
  "text": "I feel hopeless",
  "use_webcam": true,
  "use_microphone": true,
  "duration": 5
}
```

---

## 🔐 Security Features

- ✅ JWT Authentication with 24hr token expiry
- ✅ Bcrypt password hashing
- ✅ Rate limiting on all endpoints
- ✅ Security headers (XSS, Clickjacking protection)
- ✅ CORS configuration
- ✅ Input validation and sanitization
- ✅ Environment variables for secrets

---

## 🧪 Testing
```bash
cd backend
python -m pytest tests/test_api.py -v
```

**22 test cases covering:**
- Health endpoint
- Prediction (high risk, low risk, validation)
- Authentication (register, login)
- Database endpoints
- Preprocessing pipeline
- Multimodal fusion

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

### Step 6: Run the API
```bash
python app.py
```

### Step 7: Open Frontend
Open `frontend/index.html` in browser with API running.

---

## 🗺️ Future Enhancements
- [ ] Cloud deployment on Render.com
- [ ] Docker containerization
- [ ] Real-time WebSocket alerts
- [ ] Arduino heart rate sensor integration
- [ ] Mobile PWA application

---

## ⚠️ Ethical Considerations
- This system is a **support tool only** — not a replacement for professional diagnosis
- Predictions are stored securely in cloud database
- Alert system involves human-in-the-loop decision making
- All passwords are hashed using bcrypt

---

## 👥 Team

| Name | Role |
|---|---|
| Avani Upadhyay | Frontend Development, UI/UX |
| Archit Agrawal | Backend API, ML Model, Database, Security |

---

> *"Early detection saves lives. AI can be a compassionate tool when built responsibly."*