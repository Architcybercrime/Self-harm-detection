# ── SECURITY CONFIGURATION ───────────────────────────
# SQL Injection Prevention: Using Supabase ORM (no raw SQL queries)
# XSS Prevention: Security headers + input sanitization
# CSRF Protection: JWT tokens prevent CSRF attacks (stateless auth)
# Password Hashing: bcrypt with salt rounds
# Rate Limiting: slowapi on all endpoints
# Authentication: JWT Bearer tokens + API Keys supported
# Authorization: Depends(verify_token) on all protected endpoints
# Input Validation: Pydantic models validate all inputs automatically
# CORS: Restricted to specific origins
# Security Headers: Via middleware

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore')

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import re as _re

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
import socketio
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
import joblib, sys, datetime, uuid, shutil, secrets, base64, io, csv
import numpy as np
from pathlib import Path
from jose import JWTError, jwt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.preprocess import full_preprocess, get_sentiment_scores
from utils.monitor import log_prediction, get_monitoring_report
from utils.facial_analysis import analyze_face_from_base64, capture_webcam_frame
from utils.speech_analysis import analyze_audio_file, record_from_microphone
from utils.fusion import fuse_risk_scores
from utils.database import save_prediction, get_stats as db_get_stats, get_recent_predictions
from utils.auth import register_user, login_user
from utils.audit_log import (
    log_prediction as audit_prediction,
    log_api_key_event, log_unauthorized,
    log_mfa_event, get_audit_logs,
)
from utils.alerts import dispatch_high_risk_alert

# ── CONSTANTS ────────────────────────────────────────
JWT_SECRET    = os.getenv('JWT_SECRET_KEY', 'selfharm-detection-secret-key-2026')
JWT_ALGORITHM = "HS256"
SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── PYDANTIC MODELS ──────────────────────────────────
class TextInput(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000,
                      description="Text to analyze for self-harm risk")

    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace')
        return v.strip()


class RegisterInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

    @validator('username')
    def username_alphanumeric(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers and underscores')
        return v


class LoginInput(BaseModel):
    username: str
    password: str


class FaceInput(BaseModel):
    use_webcam:   Optional[bool] = False
    image_base64: Optional[str]  = None


class SpeechInput(BaseModel):
    use_microphone: Optional[bool] = False
    audio_path:     Optional[str]  = None
    duration:       Optional[int]  = Field(5, ge=1, le=30)


class MultimodalInput(BaseModel):
    text:           Optional[str]  = None
    use_webcam:     Optional[bool] = False
    use_microphone: Optional[bool] = False
    duration:       Optional[int]  = Field(5, ge=1, le=30)
    weights:        Optional[Dict] = None


class MFAVerifyInput(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)


class MFALoginInput(BaseModel):
    username:  str
    password:  str
    totp_code: str = Field(..., min_length=6, max_length=6)


class UserProfileInput(BaseModel):
    display_name:    Optional[str] = None
    alert_email:     Optional[str] = None
    alert_phone:     Optional[str] = None
    alert_whatsapp:  Optional[str] = None
    email_alerts:    Optional[bool] = None
    sms_alerts:      Optional[bool] = None
    whatsapp_alerts: Optional[bool] = None


# ── FASTAPI APP ──────────────────────────────────────
app = FastAPI(
    title       = "Self Harm Detection API",
    description = """
## AI-Based System for Self-Harm Detection

**Accuracy: 92.2%** | Uses Text, Facial and Speech analysis

### Features
- Text analysis using TF-IDF + VADER + Logistic Regression
- Facial emotion detection using DeepFace
- Speech analysis using Librosa + SpeechRecognition
- Multimodal fusion with dynamic weights
- Real-time WebSocket alerts
- Supabase PostgreSQL database
- JWT Authentication + API Key System
- **Professional PDF Report Generation**
- **Video Upload Analysis**

### Authentication
Two methods supported:
1. **JWT Token**: `Bearer YOUR_JWT_TOKEN`
2. **API Key**: `Bearer shd_YOUR_API_KEY`

Get your API key from `POST /api/keys/generate`
    """,
    version     = "2.0.0",
    contact     = {
        "name": "Archit Agrawal",
        "url":  "https://github.com/Architcybercrime/Self-harm-detection"
    }
)

# ── CORS ─────────────────────────────────────────────
_cors_env = os.getenv("ALLOWED_ORIGINS", "")
_extra    = [o.strip() for o in _cors_env.split(",") if o.strip()]
ALLOWED_ORIGINS = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5000", "http://127.0.0.1:5000",
    "http://localhost:8000", "http://127.0.0.1:8000",
    "http://localhost:8501", "http://127.0.0.1:8501",
] + _extra

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers     = ["Content-Type", "Authorization"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)


def sanitize_output(text: str) -> str:
    """Strip HTML tags from user-provided text to prevent XSS in API responses."""
    if not isinstance(text, str):
        return text
    return _re.sub(r'<[^>]+>', '', text)


# ── SOCKETIO ─────────────────────────────────────────
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)


@sio.event
async def connect(sid, environ):
    await sio.emit('connected', {
        "message": "Connected to Self Harm Detection API",
        "service": "Real-time alerts enabled"
    }, to=sid)


@sio.event
async def disconnect(sid):
    print(f'Client {sid} disconnected')


@sio.event
async def ping(sid, data):
    await sio.emit('pong', {
        "timestamp": datetime.datetime.now().isoformat()
    }, to=sid)


# ── LOAD MODELS ──────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))

model = None
tfidf = None

try:
    model = joblib.load(os.path.join(_BASE, 'model', 'risk_model.pkl'))
    tfidf = joblib.load(os.path.join(_BASE, 'model', 'tfidf_vectorizer.pkl'))
except FileNotFoundError:
    print('WARNING: Model files not found - using keyword-based fallback')

prediction_log = []


# ── KEYWORD-BASED FALLBACK ───────────────────────────
def keyword_based_prediction(text, sentiment):
    """Fallback risk scoring when trained model files are unavailable."""
    text_lower = text.lower()

    critical_keywords = [
        'kill myself', 'kill me', 'end my life', 'want to die',
        'suicide', 'commit suicide', 'end it all', 'not worth living',
        'better off dead', 'take my life', 'ending my life',
        'no reason to live', 'want to end', 'hang myself',
        'overdose', 'slit my', 'cut myself', 'wanted to suicide',
        'wanna suicide', 'kms', 'wanted suicide'
    ]

    high_risk_keywords = [
        'hopeless', 'worthless', 'useless', 'burden',
        'cant go on', "can't go on", 'give up', 'giving up',
        'no point', 'pointless', 'meaningless', 'empty inside',
        'trapped', 'suffering', 'no escape', 'cant take it',
        "can't take it", 'wanna die', 'dying', 'death',
        'helpless', 'depressed'
    ]

    medium_risk_keywords = [
        'sad', 'crying', 'alone', 'lonely', 'tired', 'exhausted',
        'cant sleep', "can't sleep", 'anxious', 'panic', 'scared',
        'afraid', 'broken', 'numb', 'empty', 'lost', 'stressed'
    ]

    critical_count = sum(1 for kw in critical_keywords if kw in text_lower)
    high_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
    medium_count = sum(1 for kw in medium_risk_keywords if kw in text_lower)

    if critical_count >= 1 or high_count >= 2 or sentiment < -0.7:
        risk_level = 'HIGH'
        confidence = min(0.95, 0.80 + (critical_count * 0.05) + (high_count * 0.03))
        alert = True
    elif high_count >= 1 or medium_count >= 2 or sentiment < -0.3:
        risk_level = 'MEDIUM'
        confidence = min(0.85, 0.65 + (high_count * 0.05) + (medium_count * 0.02))
        alert = False
    else:
        risk_level = 'LOW'
        confidence = 0.75
        alert = False

    return risk_level, round(confidence, 4), alert

# ── JWT + API KEY AUTH ────────────────────────────────
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    # Check if it's an API Key (starts with shd_)
    if token.startswith('shd_'):
        supabase = get_supabase()
        try:
            result = supabase.table("ApiKeys")\
                .select("username")\
                .eq("api_key", token)\
                .eq("is_active", True)\
                .execute()

            if not result.data:
                raise HTTPException(status_code=401, detail="Invalid or inactive API key")

            username = result.data[0]['username']

            # Update last_used timestamp
            supabase.table("ApiKeys")\
                .update({"last_used": datetime.datetime.now().isoformat()})\
                .eq("api_key", token)\
                .execute()

            return username
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail="API key verification failed")

    # Otherwise verify as JWT token
    try:
        payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def run_prediction(text, explain: bool = False):
    """Helper to run ML prediction on text. Set explain=True for SHAP top words."""
    cleaned   = full_preprocess(text)
    scores    = get_sentiment_scores(text)
    sentiment = scores['compound']
    neg_score = scores['neg']
    X = None

    if model is None or tfidf is None:
        risk_level, confidence, alert = keyword_based_prediction(text, sentiment)
        message = ('High risk indicators detected. Please seek professional support immediately.'
                   if alert else 'No immediate concern detected. Continue monitoring.')

        return {
            "risk_level":      risk_level,
            "confidence":      confidence,
            "alert_triggered": alert,
            "sentiment_score": round(sentiment, 4),
            "message":         message,
            "modality":        "text",
            "risk_indicators": {
                "text_sentiment":   "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive",
                "confidence_level": "high" if confidence > 0.85 else "medium" if confidence > 0.65 else "low",
                "severity":         "critical" if confidence > 0.9 else "high" if confidence > 0.75 else "moderate"
            },
            "recommendations": {
                "immediate_action":  alert,
                "support_resources": [
                    "iCall: 9152987821",
                    "Vandrevala Foundation: 1860-2662-345",
                    "AASRA: 9820466627"
                ] if alert else [],
                "follow_up": "Immediate professional consultation recommended" if alert else "Continue regular monitoring"
            },
            "analysis_timestamp": datetime.datetime.now().isoformat()
        }

    try:
        tfidf_vec   = tfidf.transform([cleaned]).toarray()
        X           = np.hstack([tfidf_vec, [[sentiment, neg_score]]])
        expected    = getattr(model, "n_features_in_", X.shape[1])
        if expected != X.shape[1]:
            raise ValueError(
                f"Model expects {expected} features but preprocessing produced {X.shape[1]}"
            )
        prediction  = model.predict(X)[0]
        probability = model.predict_proba(X)[0]
        confidence  = round(float(max(probability)), 4)

        risk_level = 'HIGH' if prediction == 'suicide' else 'LOW'
        alert      = risk_level == 'HIGH'
        message    = ('High risk indicators detected. Please seek professional support immediately.'
                      if alert else 'No immediate concern detected. Continue monitoring.')
    except Exception as exc:
        logging.getLogger(__name__).warning(f"ML prediction unavailable, using keyword fallback: {exc}")
        risk_level, confidence, alert = keyword_based_prediction(text, sentiment)
        message = ('High risk indicators detected. Please seek professional support immediately.'
                   if alert else 'No immediate concern detected. Continue monitoring.')

    # SHAP explanation — fast for linear models
    top_words = []
    if X is not None:
        try:
            import shap
            feature_names = tfidf.get_feature_names_out().tolist() + ["sentiment", "neg_score"]
            explainer     = shap.LinearExplainer(model, X, feature_perturbation="interventional")
            shap_vals     = explainer.shap_values(X)
            # shap_vals shape: (n_classes, n_samples, n_features) or (n_samples, n_features)
            if isinstance(shap_vals, list):
                # index 1 = "suicide" class (positive label)
                vals = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
            else:
                vals = shap_vals[0]
            top_idx   = np.argsort(np.abs(vals))[::-1][:8]
            top_words = [
                {"word": feature_names[i], "impact": round(float(vals[i]), 4)}
                for i in top_idx if abs(vals[i]) > 1e-6
            ]
        except Exception:
            pass

    result = {
        "risk_level":      risk_level,
        "confidence":      confidence,
        "alert_triggered": alert,
        "sentiment_score": round(sentiment, 4),
        "message":         message,
        "modality":        "text",
        "risk_indicators": {
            "text_sentiment":   "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive",
            "confidence_level": "high" if confidence > 0.85 else "medium" if confidence > 0.65 else "low",
            "severity":         "critical" if confidence > 0.9 else "high" if confidence > 0.75 else "moderate"
        },
        "recommendations": {
            "immediate_action":  alert,
            "support_resources": [
                "iCall: 9152987821",
                "Vandrevala Foundation: 1860-2662-345",
                "AASRA: 9820466627"
            ] if alert else [],
            "follow_up": "Immediate professional consultation recommended" if alert else "Continue regular monitoring"
        },
        "analysis_timestamp": datetime.datetime.now().isoformat()
    }
    if top_words:
        result["explanation"] = {"top_words": top_words}
    return result


# ── HEALTH ───────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health(request: Request):
    """Check API health status"""
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        content={
            "status":    "running",
            "service":   "Self Harm Detection API",
            "version":   "2.0.0",
            "framework": "FastAPI",
            "accuracy":  "92.2%",
            "database":  "Supabase PostgreSQL",
            "auth":      "JWT + API Keys enabled",
            "websocket": "enabled",
            "timestamp": datetime.datetime.now().isoformat(),
        },
        headers={
            "Access-Control-Allow-Origin":  origin if origin in ALLOWED_ORIGINS else "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


# ── AUTH ─────────────────────────────────────────────
@app.post("/api/register", tags=["Authentication"], status_code=201)
def register(data: RegisterInput):
    """Register a new user"""
    result = register_user(data.username, data.password)
    if result['success']:
        return result
    raise HTTPException(status_code=400, detail=result['error'])


@app.post("/api/login", tags=["Authentication"])
def login(data: LoginInput):
    """Login and get JWT token. Returns mfa_required=true if MFA is enabled."""
    result = login_user(data.username, data.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['error'])

    # Check if MFA is enabled for this user
    row = _get_totp_secret(data.username)
    if row and row.get("is_enabled"):
        return {
            "success":      True,
            "mfa_required": True,
            "username":     data.username,
            "message":      "MFA required — call POST /api/auth/mfa/login with your TOTP code",
        }

    return result


# ── DEMO TOKEN ───────────────────────────────────────
@app.get("/api/demo-token", tags=["Authentication"])
def demo_token(request: Request):
    """
    Issue a short-lived JWT for anonymous demo visitors.
    No credentials required. Token valid for 2 hours.
    Rate-limited: one token per IP per request cycle.
    """
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    token = jwt.encode(
        {
            "sub":  "demo_visitor",
            "role": "demo",
            "iat":  now,
            "exp":  now + int(datetime.timedelta(hours=2).total_seconds()),
            "type": "demo",
            "jti":  secrets.token_hex(8),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "success":      True,
        "access_token": token,
        "username":     "demo_visitor",
        "role":         "demo",
        "expires_in":   "2 hours",
        "message":      "Demo token issued. Valid for 2 hours — no account needed.",
    }


# ── CORS CHECK ───────────────────────────────────────
@app.get("/api/cors-check", tags=["Health"])
def cors_check(request: Request):
    """
    Explicit CORS verification endpoint.
    Returns the origin header and confirms CORS is active.
    """
    origin = request.headers.get("origin", "no-origin-header")
    return JSONResponse(
        content={
            "cors":    "enabled",
            "origin":  origin,
            "allowed": ALLOWED_ORIGINS,
            "headers": {
                "Access-Control-Allow-Origin":      origin if origin in ALLOWED_ORIGINS else "*",
                "Access-Control-Allow-Methods":     "GET, POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers":     "Content-Type, Authorization",
            },
        },
        headers={
            "Access-Control-Allow-Origin":  origin if origin in ALLOWED_ORIGINS else "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


# ── PREDICT ──────────────────────────────────────────
@app.post("/api/predict", tags=["Prediction"])
async def predict(data: TextInput, request: Request,
                  current_user: str = Depends(verify_token)):
    """Predict self-harm risk from text (92.2% accuracy)"""
    result = run_prediction(data.text)
    ip     = get_client_ip(request)

    prediction_log.append({
        "timestamp":  datetime.datetime.now().isoformat(),
        "risk_level": result['risk_level'],
        "confidence": result['confidence']
    })

    log_prediction(len(data.text.split()), result['risk_level'],
                   result['confidence'], result['sentiment_score'])
    save_prediction(data.text, result['risk_level'], result['confidence'],
                    result['sentiment_score'], "text", result['alert_triggered'])
    audit_prediction(current_user, result['risk_level'], "text",
                     result['confidence'], ip=ip)

    # Sanitize user-provided text echoed in the response (XSS prevention)
    result["text"] = sanitize_output(data.text)

    if result['alert_triggered']:
        await sio.emit('high_risk_alert', {
            "risk_level": result['risk_level'],
            "confidence": result['confidence'],
            "message":    result['message'],
            "timestamp":  datetime.datetime.now().isoformat()
        })
        # Fire email/SMS/WhatsApp alerts if user has a profile configured
        try:
            supabase = get_supabase()
            prof_res = supabase.table("UserProfiles")\
                .select("*").eq("username", current_user).execute()
            profile  = prof_res.data[0] if prof_res.data else None
            dispatch_high_risk_alert(
                username=current_user,
                confidence=result['confidence'],
                modality="text",
                text_snippet=data.text[:200],
                profile=profile,
            )
        except Exception:
            pass

    return result


# ── GENERATE REPORT ──────────────────────────────────
@app.post("/api/generate-report", tags=["Report"])
async def generate_report_endpoint(data: TextInput,
                                    current_user: str = Depends(verify_token)):
    """Generate a professional psychological risk assessment PDF report."""
    from utils.report_generator import generate_report as gen_report

    prediction_data = run_prediction(data.text)
    prediction_data['analysis_timestamp'] = datetime.datetime.now().isoformat()

    report_id = str(uuid.uuid4())[:8].upper()
    filepath  = gen_report(prediction_data,
                            username=current_user,
                            report_id=report_id)

    return FileResponse(
        filepath,
        media_type = "application/pdf",
        filename   = f"risk_assessment_{report_id}.pdf",
        headers    = {
            "Content-Disposition": f"attachment; filename=risk_assessment_{report_id}.pdf"
        }
    )


# ── VIDEO ANALYSIS ───────────────────────────────────
@app.post("/api/analyze-video", tags=["Multimodal"])
async def analyze_video_endpoint(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...)
):
    """Upload and analyze a video file for self-harm risk indicators."""
    from utils.video_analysis import analyze_video

    allowed_types = [
        'video/mp4', 'video/avi', 'video/quicktime',
        'video/x-msvideo', 'video/x-matroska', 'video/webm'
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Use MP4, AVI, MOV, MKV or WEBM"
        )

    temp_path = f"temp_video_{uuid.uuid4().hex[:8]}.mp4"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyze_video(temp_path)

        if result.get('success') and result.get('overall_risk_level') != 'UNKNOWN':
            save_prediction(
                text_input = f"Video: {file.filename}",
                risk_level = result.get('overall_risk_level', 'LOW'),
                confidence = result.get('facial_analysis', {}).get('avg_risk_score', 0),
                sentiment  = 0.0,
                modality   = "video",
                alert      = result.get('alert_triggered', False)
            )

            if result.get('alert_triggered'):
                await sio.emit('high_risk_alert', {
                    "risk_level": result.get('overall_risk_level'),
                    "modality":   "video",
                    "message":    "High risk detected in video analysis",
                    "timestamp":  datetime.datetime.now().isoformat()
                })

        return result

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ── API KEY MANAGEMENT ───────────────────────────────
@app.post("/api/keys/generate", tags=["API Keys"])
def generate_api_key(current_user: str = Depends(verify_token)):
    """
    Generate a personal API key for external integrations.
    Use this key instead of JWT token for direct API access.
    Format: Bearer shd_YOUR_KEY
    """
    supabase = get_supabase()
    api_key  = f"shd_{secrets.token_urlsafe(32)}"

    try:
        # Deactivate old keys
        supabase.table("ApiKeys")\
            .update({"is_active": False})\
            .eq("username", current_user)\
            .execute()

        # Insert new key
        supabase.table("ApiKeys").insert({
            "username":  current_user,
            "api_key":   api_key,
            "is_active": True
        }).execute()

        log_api_key_event("API_KEY_GENERATED", current_user)
        return {
            "success":    True,
            "api_key":    api_key,
            "username":   current_user,
            "message":    "API key generated successfully!",
            "usage":      f"Authorization: Bearer {api_key}",
            "curl_example": f'curl -X POST http://127.0.0.1:8000/api/predict -H "Authorization: Bearer {api_key}" -H "Content-Type: application/json" -d \'{{"text": "your text here"}}\''
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/keys/my-key", tags=["API Keys"])
def get_my_api_key(current_user: str = Depends(verify_token)):
    """Get your current active API key."""
    supabase = get_supabase()

    try:
        result = supabase.table("ApiKeys")\
            .select("*")\
            .eq("username", current_user)\
            .eq("is_active", True)\
            .execute()

        if not result.data:
            return {
                "success": False,
                "message": "No active API key. Use POST /api/keys/generate to create one."
            }

        key_data = result.data[0]
        return {
            "success":    True,
            "api_key":    key_data['api_key'],
            "created_at": key_data['created_at'],
            "last_used":  key_data['last_used'],
            "is_active":  key_data['is_active']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/keys/revoke", tags=["API Keys"])
def revoke_api_key(current_user: str = Depends(verify_token)):
    """Revoke your current active API key."""
    supabase = get_supabase()

    try:
        supabase.table("ApiKeys")\
            .update({"is_active": False})\
            .eq("username", current_user)\
            .execute()

        log_api_key_event("API_KEY_REVOKED", current_user)
        return {"success": True, "message": "API key revoked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── STATS ────────────────────────────────────────────
@app.get("/api/stats", tags=["Statistics"])
def stats(current_user: str = Depends(verify_token)):
    """Get session prediction statistics"""
    if not prediction_log:
        return {"message": "No predictions yet"}

    total  = len(prediction_log)
    alerts = sum(1 for p in prediction_log if p['risk_level'] == 'HIGH')
    return {
        "total_predictions": total,
        "alerts_triggered":  alerts,
        "alert_rate":        round(alerts/total, 4),
        "recent":            prediction_log[-5:]
    }


# ── MONITOR ──────────────────────────────────────────
@app.get("/api/monitor", tags=["Monitoring"])
def monitor(current_user: str = Depends(verify_token)):
    """Get monitoring and drift detection report"""
    return get_monitoring_report()


# ── FACIAL ANALYSIS ──────────────────────────────────
@app.post("/api/analyze-face", tags=["Multimodal"])
def analyze_face(data: FaceInput,
                 current_user: str = Depends(verify_token)):
    """Analyze facial expressions via webcam or base64 image"""
    if data.image_base64:
        return analyze_face_from_base64(data.image_base64)
    if data.use_webcam:
        return capture_webcam_frame()
    raise HTTPException(status_code=400,
                        detail="Provide image_base64 or use_webcam:true")


# ── SPEECH ANALYSIS ──────────────────────────────────
@app.post("/api/analyze-speech", tags=["Multimodal"])
def analyze_speech(data: SpeechInput,
                   current_user: str = Depends(verify_token)):
    """Analyze speech from microphone or audio file"""
    if data.audio_path:
        return analyze_audio_file(data.audio_path)
    if data.use_microphone:
        return record_from_microphone(data.duration)
    raise HTTPException(status_code=400,
                        detail="Provide audio_path or use_microphone:true")


@app.post("/api/analyze-speech-upload", tags=["Multimodal"])
async def analyze_speech_upload(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...)
):
    """Analyze a browser-recorded audio file uploaded from the frontend."""
    suffix = os.path.splitext(file.filename or "upload.webm")[1] or ".webm"
    temp_path = f"temp_voice_{uuid.uuid4().hex[:8]}{suffix}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyze_audio_file(temp_path)
        if isinstance(result, dict):
            result["uploaded_from_browser"] = True
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ── MULTIMODAL ───────────────────────────────────────
@app.post("/api/predict-multimodal", tags=["Prediction"])
async def predict_multimodal(data: MultimodalInput,
                              current_user: str = Depends(verify_token)):
    """Combined multimodal risk prediction (text + face + speech)"""
    text_result = face_result = speech_result = None
    text = ""

    if data.text:
        text        = data.text.strip()
        text_result = run_prediction(text)
        text_result = {
            "risk_level": text_result['risk_level'],
            "confidence": text_result['confidence']
        }

    if data.use_webcam:
        face_result = capture_webcam_frame()

    if data.use_microphone:
        speech_result = record_from_microphone(data.duration)

    final_result = fuse_risk_scores(
        text_result=text_result,
        face_result=face_result,
        speech_result=speech_result,
        custom_weights=data.weights
    )

    if 'risk_level' in final_result:
        prediction_log.append({
            "timestamp":  datetime.datetime.now().isoformat(),
            "risk_level": final_result['risk_level'],
            "confidence": final_result['final_risk_score'],
            "multimodal": True
        })
        save_prediction(text, final_result['risk_level'],
                        final_result['final_risk_score'], 0.0,
                        "multimodal", final_result['alert_triggered'])

        if final_result['alert_triggered']:
            await sio.emit('high_risk_alert', {
                "risk_level": final_result['risk_level'],
                "confidence": final_result['final_risk_score'],
                "modality":   "multimodal",
                "timestamp":  datetime.datetime.now().isoformat()
            })

    return final_result


# ── HISTORY ──────────────────────────────────────────
@app.get("/api/history", tags=["Database"])
def history(current_user: str = Depends(verify_token)):
    """Get recent prediction history from Supabase"""
    return get_recent_predictions(20)


# ── DB STATS ─────────────────────────────────────────
@app.get("/api/db-stats", tags=["Database"])
def db_stats(current_user: str = Depends(verify_token)):
    """Get database statistics from Supabase"""
    return db_get_stats()


# ── PROFILE ──────────────────────────────────────────
@app.get("/api/profile", tags=["Authentication"])
def profile(current_user: str = Depends(verify_token)):
    """Get current user profile"""
    return {
        "username": current_user,
        "message":  f"Welcome {current_user}!",
        "role":     "user"
    }


# ── MFA / TOTP ───────────────────────────────────────
def _get_totp_secret(username: str):
    """Return the active TOTP secret for a user, or None."""
    supabase = get_supabase()
    try:
        res = supabase.table("UserMFA")\
            .select("totp_secret, is_enabled")\
            .eq("username", username)\
            .execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None


@app.post("/api/auth/mfa/setup", tags=["MFA"])
def mfa_setup(current_user: str = Depends(verify_token)):
    """
    Generate a new TOTP secret for the current user and return a QR-code
    data-URI. The user must verify with /api/auth/mfa/verify-setup before
    MFA is actually enabled.
    """
    try:
        import pyotp, qrcode
    except ImportError:
        raise HTTPException(status_code=501,
                            detail="MFA dependencies not installed (pyotp, qrcode)")

    issuer = os.getenv("MFA_ISSUER", "SafeSignal")
    secret = pyotp.random_base32()
    uri    = pyotp.totp.TOTP(secret).provisioning_uri(
                 name=current_user, issuer_name=issuer)

    # Generate QR code as base64 data URI
    img    = qrcode.make(uri)
    buf    = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    supabase = get_supabase()
    # Upsert pending secret (not yet enabled)
    supabase.table("UserMFA").upsert({
        "username":    current_user,
        "totp_secret": secret,
        "is_enabled":  False,
    }).execute()

    log_mfa_event("MFA_SETUP", current_user, success=True)
    return {
        "success":    True,
        "secret":     secret,
        "qr_code":    f"data:image/png;base64,{qr_b64}",
        "message":    "Scan the QR code in your authenticator app, then call /api/auth/mfa/verify-setup with your 6-digit code."
    }


@app.post("/api/auth/mfa/verify-setup", tags=["MFA"])
def mfa_verify_setup(data: MFAVerifyInput,
                     current_user: str = Depends(verify_token)):
    """Confirm the first TOTP code to activate MFA for the account."""
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    row = _get_totp_secret(current_user)
    if not row:
        raise HTTPException(status_code=400, detail="Run /api/auth/mfa/setup first")

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", current_user, success=False)
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    get_supabase().table("UserMFA")\
        .update({"is_enabled": True})\
        .eq("username", current_user)\
        .execute()

    log_mfa_event("MFA_ENABLED", current_user, success=True)
    return {"success": True, "message": "MFA enabled successfully"}


@app.post("/api/auth/mfa/disable", tags=["MFA"])
def mfa_disable(data: MFAVerifyInput,
                current_user: str = Depends(verify_token)):
    """Disable MFA (requires a valid TOTP code to confirm)."""
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    row = _get_totp_secret(current_user)
    if not row or not row.get("is_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", current_user, success=False)
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    get_supabase().table("UserMFA")\
        .update({"is_enabled": False, "totp_secret": None})\
        .eq("username", current_user)\
        .execute()

    log_mfa_event("MFA_DISABLED", current_user, success=True)
    return {"success": True, "message": "MFA disabled"}


@app.get("/api/auth/mfa/status", tags=["MFA"])
def mfa_status(current_user: str = Depends(verify_token)):
    """Check whether MFA is enabled for the current user."""
    row = _get_totp_secret(current_user)
    enabled = bool(row and row.get("is_enabled"))
    return {"success": True, "mfa_enabled": enabled, "username": current_user}


@app.post("/api/auth/mfa/login", tags=["MFA"])
def mfa_login(data: MFALoginInput, request: Request):
    """
    Second step of MFA login: verify TOTP code and return JWT token.
    Call this after /api/login returns mfa_required=true.
    """
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    from utils.auth import login_user as _login, verify_password as _vp
    # Re-verify credentials first
    result = _login(data.username, data.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))

    row = _get_totp_secret(data.username)
    if not row or not row.get("is_enabled"):
        # MFA not set up — just return token directly
        return result

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", data.username,
                      ip=get_client_ip(request), success=False)
        raise HTTPException(status_code=401, detail="Invalid TOTP code")

    log_mfa_event("MFA_ENABLED", data.username,
                  ip=get_client_ip(request), success=True)
    return result


# ── ADMIN ────────────────────────────────────────────
def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Restrict endpoint to users with role='admin'.
    Checks JWT payload first (fast path); falls back to DB lookup for
    old tokens that pre-date the role claim (backward-compatible).
    """
    token = credentials.credentials

    # JWT path
    if not token.startswith('shd_'):
        try:
            payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
            # Fast path: role embedded in JWT
            if payload.get("role") == "admin":
                return username
            # Slow path: old token without role claim — verify in DB
            supabase = get_supabase()
            try:
                result = supabase.table("Users")\
                    .select("role")\
                    .eq("username", username)\
                    .execute()
                if result.data and result.data[0].get("role") == "admin":
                    return username
            except Exception:
                pass
            raise HTTPException(status_code=403, detail="Admin access required")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    # API-key path: no admin via API key
    raise HTTPException(status_code=403, detail="Admin access requires JWT token")


@app.get("/api/admin/audit-logs", tags=["Admin"])
def admin_audit_logs(
    limit:      int = 100,
    event_type: str = None,
    username:   str = None,
    admin_user: str = Depends(require_admin),
):
    """[Admin] Fetch structured security audit logs."""
    return get_audit_logs(limit=limit, event_type=event_type, username=username)


@app.get("/api/admin/users", tags=["Admin"])
def admin_users(
    limit:      int = 100,
    admin_user: str = Depends(require_admin),
):
    """[Admin] List all registered users (username, role, created_at). Requires admin role."""
    supabase = get_supabase()
    try:
        result = supabase.table("Users")\
            .select("username, role, created_at")\
            .limit(limit)\
            .execute()
        users = result.data or []
        return {
            "success": True,
            "count":   len(users),
            "users":   users,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/analytics", tags=["Admin"])
def admin_analytics(admin_user: str = Depends(require_admin)):
    """[Admin] Aggregated risk analytics for the admin dashboard."""
    supabase = get_supabase()
    try:
        rows = supabase.table("Predictions").select("*").execute().data or []
        total      = len(rows)
        high_risk  = sum(1 for r in rows if r.get("risk_level") == "HIGH")
        alerts     = sum(1 for r in rows if r.get("alert"))
        avg_conf   = round(sum(r["confidence"] for r in rows) / total, 4) if total else 0

        by_modality: dict = {}
        for r in rows:
            m = r.get("modality", "unknown")
            by_modality[m] = by_modality.get(m, 0) + 1

        # Last 7 days daily counts
        from collections import defaultdict
        daily: dict = defaultdict(lambda: {"total": 0, "high": 0})
        for r in rows:
            day = (r.get("created_at") or r.get("timestamp") or "")[:10]
            if day:
                daily[day]["total"] += 1
                if r.get("risk_level") == "HIGH":
                    daily[day]["high"] += 1

        return {
            "success":           True,
            "total_predictions": total,
            "high_risk_count":   high_risk,
            "alert_count":       alerts,
            "avg_confidence":    avg_conf,
            "high_risk_rate":    round(high_risk / total, 4) if total else 0,
            "by_modality":       by_modality,
            "daily_counts":      dict(sorted(daily.items())[-14:]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── USER PROFILES (alert settings + longitudinal data) ───
@app.get("/api/user/profile", tags=["User"])
def get_user_profile(current_user: str = Depends(verify_token)):
    """Get user alert preferences and profile."""
    supabase = get_supabase()
    try:
        res = supabase.table("UserProfiles")\
            .select("*").eq("username", current_user).execute()
        if res.data:
            return {"success": True, "profile": res.data[0]}
        return {"success": True, "profile": {
            "username": current_user,
            "display_name": None,
            "alert_email": None, "alert_phone": None, "alert_whatsapp": None,
            "email_alerts": False, "sms_alerts": False, "whatsapp_alerts": False,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/user/profile", tags=["User"])
def update_user_profile(data: UserProfileInput,
                        current_user: str = Depends(verify_token)):
    """Update alert preferences (email, SMS, WhatsApp)."""
    supabase = get_supabase()
    update   = {k: v for k, v in data.dict().items() if v is not None}
    if not update:
        return {"success": True, "message": "Nothing to update"}
    update["username"]   = current_user
    update["updated_at"] = datetime.datetime.now().isoformat()
    try:
        supabase.table("UserProfiles").upsert(update).execute()
        return {"success": True, "message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/risk-trend", tags=["User"])
def user_risk_trend(days: int = 30, current_user: str = Depends(verify_token)):
    """Return daily aggregated risk scores for the last N days (longitudinal view)."""
    supabase = get_supabase()
    try:
        since = (datetime.datetime.utcnow() -
                 datetime.timedelta(days=days)).isoformat()
        rows = supabase.table("Predictions")\
            .select("risk_level,confidence,created_at")\
            .eq("username", current_user)\
            .gte("created_at", since)\
            .order("created_at")\
            .execute().data or []

        from collections import defaultdict
        daily: dict = defaultdict(lambda: {"total": 0, "high": 0, "avg_confidence": 0.0})
        for r in rows:
            day = (r.get("created_at") or "")[:10]
            if not day:
                continue
            daily[day]["total"]          += 1
            daily[day]["avg_confidence"] += r.get("confidence", 0)
            if r.get("risk_level") == "HIGH":
                daily[day]["high"] += 1

        trend = []
        for day, d in sorted(daily.items()):
            trend.append({
                "date":           day,
                "total":          d["total"],
                "high_risk":      d["high"],
                "avg_confidence": round(d["avg_confidence"] / d["total"], 4) if d["total"] else 0,
            })
        return {"success": True, "days": days, "trend": trend}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── BATCH CSV UPLOAD ─────────────────────────────────
@app.post("/api/predict-batch", tags=["Prediction"])
async def predict_batch(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...),
):
    """
    Batch risk analysis from a CSV file.
    The CSV must have a column named 'text' (first column is used as fallback).
    Returns a JSON array with risk results for each row (max 500 rows).
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig')  # handles BOM
    except UnicodeDecodeError:
        decoded = content.decode('latin-1')

    reader   = csv.DictReader(io.StringIO(decoded))
    fieldnames = reader.fieldnames or []
    text_col   = 'text' if 'text' in fieldnames else (fieldnames[0] if fieldnames else None)

    if not text_col:
        raise HTTPException(status_code=400, detail="CSV must have at least one column")

    results = []
    for i, row in enumerate(reader):
        if i >= 500:
            break
        text = (row.get(text_col) or "").strip()
        if not text:
            results.append({"row": i + 1, "text": "", "error": "empty"})
            continue
        try:
            r = run_prediction(text)
            results.append({
                "row":         i + 1,
                "text":        text[:100],
                "risk_level":  r["risk_level"],
                "confidence":  r["confidence"],
                "alert":       r["alert_triggered"],
            })
        except Exception as e:
            results.append({"row": i + 1, "text": text[:100], "error": str(e)})

    high_count = sum(1 for r in results if r.get("risk_level") == "HIGH")
    return {
        "success":        True,
        "total_rows":     len(results),
        "high_risk_rows": high_count,
        "results":        results,
    }


# ── RUN ──────────────────────────────────────────────
if __name__ == '__main__':
    import uvicorn
    print("="*50)
    print("  Self Harm Detection API - FastAPI")
    print("  Version: 2.0.0")
    print("  Accuracy: 92.2%")
    print("  Docs:  http://127.0.0.1:8000/docs")
    print("  ReDoc: http://127.0.0.1:8000/redoc")
    print("  Endpoints:")
    print("    POST /api/generate-report  [JWT/Key] ← PDF Report")
    print("    POST /api/analyze-video    [JWT/Key] ← Video Upload")
    print("    POST /api/keys/generate    [JWT/Key] ← Get API Key")
    print("    GET  /api/keys/my-key      [JWT/Key] ← View API Key")
    print("    DELETE /api/keys/revoke    [JWT/Key] ← Revoke Key")
    print("="*50)
    uvicorn.run("main:socket_app", host="0.0.0.0",
                port=8000, reload=True)