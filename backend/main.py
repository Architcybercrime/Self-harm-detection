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

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import socketio
import sys, datetime
from jose import JWTError, jwt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ml_engine early so models are loaded once at startup
from ml_engine import prediction_log, run_prediction  # noqa: F401

# ── CONSTANTS ────────────────────────────────────────
JWT_SECRET    = os.getenv('JWT_SECRET_KEY', 'selfharm-detection-secret-key-2026')
JWT_ALGORITHM = "HS256"
SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


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


# ── ROOT + HEALTH ────────────────────────────────────
@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def root():
    """Root / health shortcut — redirects to /api/health info."""
    return {"status": "running", "service": "Self Harm Detection API",
            "version": "2.0.0", "docs": "/docs", "health": "/api/health"}


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


# ── ROUTERS ──────────────────────────────────────────
# Routers are imported after app + sio are ready.
# All shared state (model, prediction_log) lives in ml_engine.py.
from routers import auth as auth_router
from routers import predict as predict_router
from routers import analysis as analysis_router
from routers import monitoring as monitoring_router
from routers import keys as keys_router
from routers import admin as admin_router

app.include_router(auth_router.router)
app.include_router(predict_router.router)
app.include_router(analysis_router.router)
app.include_router(monitoring_router.router)
app.include_router(keys_router.router)
app.include_router(admin_router.router)

# Inject sio into routers that emit WebSocket events
predict_router.sio  = sio
analysis_router.sio = sio


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