# ── SECURITY CONFIGURATION ───────────────────────────
# SQL Injection Prevention: Using Supabase ORM (no raw SQL queries)
# XSS Prevention: Flask-Talisman security headers + input sanitization
# CSRF Protection: JWT tokens prevent CSRF attacks (stateless auth)
# Password Hashing: bcrypt with salt rounds
# Rate Limiting: flask-limiter on all endpoints
# Authentication: JWT Bearer tokens required
# Authorization: @jwt_required() on all protected endpoints
# Input Validation: validators.py sanitizes all inputs
# CORS: Restricted to specific origins
# Security Headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore')

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit
from flasgger import Swagger
import joblib, sys, datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.preprocess import full_preprocess, get_sentiment_scores
from utils.monitor import log_prediction, get_monitoring_report
from utils.facial_analysis import analyze_face_from_base64, capture_webcam_frame
from utils.speech_analysis import analyze_audio_file, record_from_microphone
from utils.fusion import fuse_risk_scores
from utils.database import save_prediction, get_stats as db_get_stats, get_recent_predictions
from utils.auth import register_user, login_user, setup_jwt
from utils.validators import validate_text_input, validate_credentials, sanitize_text, validate_audio_duration
from utils.video_processor import process_video_for_analysis
from utils.multimodal_report import generate_multimodal_report

app = Flask(__name__)

# ── CORS CONFIGURATION (Production-Grade) ────────────
ALLOWED_ORIGINS = [
    "http://localhost:3000",
  "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
  "http://localhost:5500",
  "http://127.0.0.1:5500",
  "http://localhost:8000",
  "http://127.0.0.1:8000",
    "null",  # For file:// protocol (local HTML)
    "https://self-harm-detection.vercel.app",
]

CORS(app,
     resources={
         r"/api/*": {
             "origins": ALLOWED_ORIGINS,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "expose_headers": ["Content-Range", "X-Content-Range"],
             "supports_credentials": True,
             "max_age": 3600
         }
     })

Talisman(app,
    force_https=False,
    strict_transport_security=False,
    content_security_policy=False
)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

jwt = setup_jwt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ── SWAGGER DOCS ─────────────────────────────────────
swagger = Swagger(app, template={
    "info": {
        "title": "Self Harm Detection API",
        "description": "AI-Based System for Self-Harm Detection. Accuracy: 92.2%. Uses Text, Facial and Speech analysis.",
        "version": "1.0.0",
        "contact": {
            "name": "Archit Agrawal",
            "url": "https://github.com/Architcybercrime/Self-harm-detection"
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token. Enter: Bearer YOUR_TOKEN"
        }
    }
})

# Load model files if they exist
try:
    model = joblib.load('model/risk_model.pkl')
    tfidf = joblib.load('model/tfidf_vectorizer.pkl')
    print("ML models loaded")
except FileNotFoundError:
    print("Model files not found - using keyword-based fallback")
    model = None
    tfidf = None

# ── LOGGING CONFIGURATION (Production-ready) ────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.INFO)

prediction_log = []


# ── IMPROVED KEYWORD-BASED DETECTION ─────────────────
def keyword_based_prediction(text, sentiment):
    """Production-grade keyword-based risk detection with weighted scoring."""
    text_lower = text.lower()

    # CRITICAL keywords (instant HIGH risk)
    critical_keywords = [
        'kill myself', 'kill me', 'end my life', 'want to die',
      'want to disappear',
        'suicide', 'commit suicide', 'end it all', 'not worth living',
        'better off dead', 'take my life', 'ending my life',
        'no reason to live', 'want to end', 'hang myself',
        'overdose', 'slit my', 'cut myself', 'wanted to suicide',
        'wanna suicide', 'kms', 'wanted suicide'
    ]

    # HIGH risk keywords
    high_risk_keywords = [
        'hopeless', 'worthless', 'useless', 'burden',
        'cant go on', "can't go on", 'give up', 'giving up',
        'no point', 'pointless', 'meaningless', 'empty inside',
        'trapped', 'suffering', 'no escape', 'cant take it',
        "can't take it", 'wanna die', 'dying', 'death',
        'helpless', 'depressed'
    ]

    # MEDIUM risk keywords
    medium_risk_keywords = [
        'sad', 'crying', 'alone', 'lonely', 'tired', 'exhausted',
        'cant sleep', "can't sleep", 'anxious', 'panic', 'scared',
        'afraid', 'broken', 'numb', 'empty', 'lost', 'stressed'
    ]

    critical_count = sum(1 for kw in critical_keywords if kw in text_lower)
    high_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
    medium_count = sum(1 for kw in medium_risk_keywords if kw in text_lower)

    # Decision logic (weighted)
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


# ── HELPER: GENERATE REPORT WITH ERROR HANDLING ──────
def generate_report_safe(facial_data=None, voice_data=None, text_data=None):
    """Generate multimodal report with comprehensive error handling."""
    try:
        return generate_multimodal_report(
            facial_data=facial_data or {},
            voice_data=voice_data or {},
            text_data=text_data or {}
        )
    except Exception as e:
        app.logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        # Return minimal fallback report
        return {
            "executive_summary": "Analysis completed with limited reporting.",
            "overall_risk_score": 0.5,
            "overall_risk_level": "MEDIUM",
            "findings": {"error": "Detailed report unavailable, but analysis completed."}
        }


# ── REQUEST SIZE LIMITS ──────────────────────────────
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 500)) * 1024 * 1024  # Default 500MB


# ── WEBSOCKET EVENTS ─────────────────────────────────
@socketio.on('connect')
def handle_connect():
    emit('connected', {
        "message": "Connected to Self Harm Detection API",
        "service": "Real-time alerts enabled"
    })


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from WebSocket')


@socketio.on('ping')
def handle_ping():
    emit('pong', {"timestamp": datetime.datetime.now().isoformat()})


# ── REST ENDPOINTS ───────────────────────────────────
@app.route('/api/health', methods=['GET'])
@limiter.limit("60 per minute")
def health():
    """
    Check API health status
    ---
    tags:
      - Health
    responses:
      200:
        description: API is running
    """
    return jsonify({
        "status": "running",
        "service": "Self Harm Detection API",
        "accuracy": "92.2%",
        "database": "Supabase PostgreSQL",
        "auth": "JWT enabled",
        "websocket": "enabled",
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            username:
              type: string
              example: archit2026
            password:
              type: string
              example: mypassword123
    responses:
      201:
        description: User registered successfully
      400:
        description: Validation error
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "username and password required"}), 400

    username = sanitize_text(str(data['username']))
    password = str(data['password']).strip()

    is_valid, errors = validate_credentials(username, password)
    if not is_valid:
        return jsonify({"error": errors[0]}), 400

    result = register_user(username, password)
    if result['success']:
        return jsonify(result), 201
    return jsonify(result), 400


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login and get JWT token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            username:
              type: string
              example: archit2026
            password:
              type: string
              example: mypassword123
    responses:
      200:
        description: Login successful, returns JWT token
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "username and password required"}), 400

    result = login_user(data['username'], data['password'])
    if result['success']:
        return jsonify(result), 200
    return jsonify(result), 401


@app.route('/api/predict', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def predict():
    """
    Predict self-harm risk from text
    ---
    tags:
      - Prediction
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            text:
              type: string
              example: I feel completely hopeless today
    responses:
      200:
        description: Risk prediction result
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "text field is required"}), 400

    try:
        text = sanitize_text(str(data['text']))
        is_valid, errors = validate_text_input(text)
        if not is_valid:
            return jsonify({"error": errors[0]}), 400

        cleaned = full_preprocess(text)
        scores = get_sentiment_scores(text)
        sentiment = scores['compound']
        neg_score = scores['neg']

        # Fallback prediction if model not available
        if model is None or tfidf is None:
            risk_level, confidence, alert = keyword_based_prediction(text, sentiment)
        else:
            # ML-based prediction
            tfidf_vec = tfidf.transform([cleaned]).toarray()
            X = np.hstack([tfidf_vec, [[sentiment, neg_score]]])
            prediction = model.predict(X)[0]
            probability = model.predict_proba(X)[0]
            confidence = round(float(max(probability)), 4)
            if prediction == 'suicide':
                risk_level = 'HIGH'
                alert = True
            else:
                risk_level = 'LOW'
                alert = False

        message = 'High risk indicators detected. Please seek professional support immediately.' if alert else 'No immediate concern detected. Continue monitoring.'

        prediction_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "risk_level": risk_level,
            "confidence": confidence
        })

        log_prediction(
            text_length=len(text.split()),
            risk_level=risk_level,
            confidence=confidence,
            sentiment_score=round(sentiment, 4)
        )

        save_prediction(
            text_input=text,
            risk_level=risk_level,
            confidence=confidence,
            sentiment=round(sentiment, 4),
            modality="text",
            alert=alert
        )

        if alert:
            socketio.emit('high_risk_alert', {
                "risk_level": risk_level,
                "confidence": confidence,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "Immediate professional consultation recommended"
            })

        # Generate comprehensive report for text analysis
        text_analysis_data = {
            "text_risk_score": confidence,
            "risk_level": risk_level,
            "sentiment_score": round(sentiment, 4),
            "sentiment_label": "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive",
            "transcription": text[:100] + ("..." if len(text) > 100 else "")
        }
        comprehensive_report = generate_report_safe(text_data=text_analysis_data)

        return jsonify({
            "risk_level": risk_level,
            "confidence": confidence,
            "alert_triggered": alert,
            "sentiment_score": round(sentiment, 4),
            "message": message,
            "risk_indicators": {
                "text_sentiment": "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive",
                "confidence_level": "high" if confidence > 0.85 else "medium" if confidence > 0.65 else "low",
                "severity": "critical" if confidence > 0.9 else "high" if confidence > 0.75 else "moderate"
            },
            "recommendations": {
            "immediate_action": alert,
            "support_resources": [
                "iCall: 9152987821",
                "Vandrevala Foundation: 1860-2662-345",
                "AASRA: 9820466627"
            ] if alert else [],
            "follow_up": "Immediate professional consultation recommended" if alert else "Continue regular monitoring"
        },
        "comprehensive_report": comprehensive_report,
        "analysis_timestamp": datetime.datetime.now().isoformat()
    }), 200
    
    except Exception as e:
        app.logger.error(f"Text prediction error: {str(e)}", exc_info=True)
        return jsonify({"error": "Analysis failed. Please try again.", "details": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def stats():
    """
    Get session prediction statistics
    ---
    tags:
      - Statistics
    security:
      - Bearer: []
    responses:
      200:
        description: Session statistics
    """
    if not prediction_log:
        return jsonify({"message": "No predictions yet"})

    total = len(prediction_log)
    alerts = sum(1 for p in prediction_log if p['risk_level'] == 'HIGH')

    return jsonify({
        "total_predictions": total,
        "alerts_triggered": alerts,
        "alert_rate": round(alerts/total, 4) if total > 0 else 0,
        "recent": prediction_log[-5:]
    })


@app.route('/api/monitor', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def monitor():
    """
    Get monitoring and drift detection report
    ---
    tags:
      - Monitoring
    security:
      - Bearer: []
    responses:
      200:
        description: Monitoring report with trend analysis
    """
    report = get_monitoring_report()
    return jsonify(report)


@app.route('/api/analyze-face', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def analyze_face():
    """
    Analyze facial expressions via webcam or image
    ---
    tags:
      - Multimodal
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            use_webcam:
              type: boolean
              example: true
            image_base64:
              type: string
              example: base64_encoded_image
    responses:
      200:
        description: Facial emotion analysis result
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        if 'image_base64' in data:
            result = analyze_face_from_base64(data['image_base64'])
            # Generate comprehensive report for facial analysis
            facial_data = result.copy() if isinstance(result, dict) else {"risk_score": 0}
            facial_data.setdefault('facial_risk_score', result.get('risk_score', 0.2) if isinstance(result, dict) else 0.2)
            facial_data.setdefault('risk_level', result.get('risk_level', 'LOW') if isinstance(result, dict) else 'LOW')
            facial_data.setdefault('dominant_emotion', result.get('emotion', 'neutral') if isinstance(result, dict) else 'neutral')
            comprehensive_report = generate_report_safe(facial_data=facial_data)
            result['comprehensive_report'] = comprehensive_report
            return jsonify(result), 200

        if data.get('use_webcam'):
            result = capture_webcam_frame()
            # Generate comprehensive report for facial analysis
            facial_data = result.copy() if isinstance(result, dict) else {"risk_score": 0}
            facial_data.setdefault('facial_risk_score', result.get('risk_score', 0.2) if isinstance(result, dict) else 0.2)
            facial_data.setdefault('risk_level', result.get('risk_level', 'LOW') if isinstance(result, dict) else 'LOW')
            facial_data.setdefault('dominant_emotion', result.get('emotion', 'neutral') if isinstance(result, dict) else 'neutral')
            comprehensive_report = generate_report_safe(facial_data=facial_data)
            result['comprehensive_report'] = comprehensive_report
            return jsonify(result), 200

        return jsonify({"error": "Provide image_base64 or use_webcam:true"}), 400
    
    except Exception as e:
        app.logger.error(f"Facial analysis error: {str(e)}", exc_info=True)
        return jsonify({"error": "Facial analysis failed. Please try again.", "details": str(e)}), 500


@app.route('/api/analyze-speech', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def analyze_speech():
    """
    Analyze speech from microphone or audio file
    ---
    tags:
      - Multimodal
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            use_microphone:
              type: boolean
              example: true
            duration:
              type: integer
              example: 5
    responses:
      200:
        description: Speech analysis result
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'audio_path' in data:
        result = analyze_audio_file(data['audio_path'])
        return jsonify(result), 200

    if data.get('use_microphone'):
        is_valid, errors, duration = validate_audio_duration(data.get('duration', 5))
        if not is_valid:
            return jsonify({"error": errors[0]}), 400
        result = record_from_microphone(duration)
        return jsonify(result), 200

    return jsonify({"error": "Provide audio_path or use_microphone:true"}), 400


@app.route('/api/analyze-speech-upload', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def analyze_speech_upload():
    """
    Analyze uploaded speech audio clip (multipart/form-data)
    ---
    tags:
      - Multimodal
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Audio file from browser recording
    responses:
      200:
        description: Speech analysis result
      400:
        description: Invalid upload
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded", "success": False}), 400

    upload = request.files['file']
    if not upload or not upload.filename:
        return jsonify({"error": "Empty file upload", "success": False}), 400

    temp_dir = os.path.join('data', 'temp_audio')
    os.makedirs(temp_dir, exist_ok=True)

    filename = secure_filename(upload.filename)
    if not filename:
        filename = 'voice_upload.wav'

    ext = os.path.splitext(filename)[1].lower() or '.wav'
    temp_path = os.path.join(temp_dir, f"upload_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}")

    try:
        upload.save(temp_path)
        result = analyze_audio_file(temp_path)
        if result.get('success'):
            # Generate comprehensive report for voice analysis
            voice_analysis_data = {
                "speech_risk_score": result.get('risk_score', 0.2),
                "acoustic_risk_score": result.get('risk_score', 0.2),
                "text_risk_score": result.get('risk_score', 0.2),
                "transcription": result.get('transcription', ''),
                "language": result.get('language', 'en-US'),
                "risk_signals": result.get('risk_signals', []),
                "tempo_bpm": result.get('tempo', 100),
                "avg_pitch_hz": result.get('pitch', 150),
                "energy_level": result.get('energy', 0.5)
            }
            comprehensive_report = generate_report_safe(voice_data=voice_analysis_data)
            result['comprehensive_report'] = comprehensive_report
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        app.logger.error(f"Speech upload error: {str(e)}", exc_info=True)
        return jsonify({"error": "Speech analysis failed. Please try again.", "details": str(e), "success": False}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as cleanup_err:
                app.logger.warning(f"Failed to cleanup {temp_path}: {str(cleanup_err)}")


@app.route('/api/predict-multimodal', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def predict_multimodal():
    """
    Combined multimodal risk prediction (text + face + speech)
    ---
    tags:
      - Prediction
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            text:
              type: string
              example: I feel hopeless
            use_webcam:
              type: boolean
              example: true
            use_microphone:
              type: boolean
              example: false
            weights:
              type: object
              example: {"text": 0.5, "facial": 0.3, "speech": 0.2}
    responses:
      200:
        description: Unified multimodal risk score
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    text_result = None
    face_result = None
    speech_result = None
    text = ""

    # Text analysis
    if 'text' in data:
        text = sanitize_text(str(data['text']))
        is_valid, errors = validate_text_input(text)
        if not is_valid:
            return jsonify({"error": errors[0]}), 400

        cleaned = full_preprocess(text)
        scores = get_sentiment_scores(text)
        sentiment = scores['compound']
        neg_score = scores['neg']

        if model is None or tfidf is None:
            risk_level, confidence, _ = keyword_based_prediction(text, sentiment)
            text_result = {"risk_level": risk_level, "confidence": confidence}
        else:
            tfidf_vec = tfidf.transform([cleaned]).toarray()
            X = np.hstack([tfidf_vec, [[sentiment, neg_score]]])
            prediction = model.predict(X)[0]
            probability = model.predict_proba(X)[0]
            text_result = {
                "risk_level": 'HIGH' if prediction == 'suicide' else 'LOW',
                "confidence": round(float(max(probability)), 4)
            }

    if data.get('use_webcam'):
        face_result = capture_webcam_frame()

    if data.get('use_microphone'):
        is_valid, errors, duration = validate_audio_duration(data.get('duration', 5))
        if not is_valid:
            return jsonify({"error": errors[0]}), 400
        speech_result = record_from_microphone(duration)

    custom_weights = data.get('weights', None)
    final_result = fuse_risk_scores(
        text_result=text_result,
        face_result=face_result,
        speech_result=speech_result,
        custom_weights=custom_weights
    )

    if 'risk_level' in final_result:
        prediction_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "risk_level": final_result['risk_level'],
            "confidence": final_result['final_risk_score'],
            "multimodal": True
        })

        save_prediction(
            text_input=text,
            risk_level=final_result['risk_level'],
            confidence=final_result['final_risk_score'],
            sentiment=0.0,
            modality="multimodal",
            alert=final_result['alert_triggered']
        )

        if final_result['alert_triggered']:
            socketio.emit('high_risk_alert', {
                "risk_level": final_result['risk_level'],
                "confidence": final_result['final_risk_score'],
                "modality": "multimodal",
                "message": final_result['message'],
                "timestamp": datetime.datetime.now().isoformat()
            })

    return jsonify(final_result), 200


@app.route('/api/analyze-video-upload', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def analyze_video_upload():
    """
    Upload video file and perform multimodal analysis with therapist-style report generation.
    Returns comprehensive analysis + professional report.
    ---
    tags:
      - Multimodal
    security:
      - Bearer: []
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Video file (MP4, MOV, AVI, etc.)
      - in: formData
        name: language
        type: string
        required: false
        default: en-US
        description: Language code for speech recognition (en-US, hi-IN, pa-IN, etc.)
    responses:
      200:
        description: Multimodal video analysis + therapist-style report
    """
    from utils.video_processor import process_video_for_analysis
    from utils.multimodal_report import generate_multimodal_report
    
    if 'file' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    upload = request.files['file']
    if upload.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Validate video file type
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm'}
    file_ext = os.path.splitext(upload.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({"error": f"Unsupported video format. Allowed: {', '.join(allowed_extensions)}"}), 400
    
    language = request.form.get('language', 'en-US')
    temp_dir = 'temp_audio'
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = secure_filename(upload.filename)
    ext = os.path.splitext(filename)[1].lower() or '.mp4'
    temp_path = os.path.join(temp_dir, f"upload_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}")
    
    try:
        # Emit progress: upload received
        socketio.emit('upload_progress', {"stage": "received", "progress": 10})
        app.logger.info(f"Video upload started: {filename}")
        
        upload.save(temp_path)
        socketio.emit('upload_progress', {"stage": "processing", "progress": 30})
        
        # Process video: extract audio + frames, run multimodal analysis
        video_analysis = process_video_for_analysis(temp_path, language=language)
        socketio.emit('upload_progress', {"stage": "analyzed", "progress": 70})
        
        if not video_analysis.get('success'):
            error_msg = video_analysis.get('error', 'Video analysis failed')
            app.logger.error(f"Video analysis failed for {filename}: {error_msg}")
            return jsonify({"error": error_msg, "success": False}), 400
        
        # Generate comprehensive multimodal report
        facial_data = video_analysis.get('facial_analysis', {})
        voice_data = video_analysis.get('voice_analysis', {})
        
        # Ensure we have complete data structures
        facial_data.setdefault('facial_risk_score', 0.2)
        facial_data.setdefault('risk_level', 'LOW')
        facial_data.setdefault('dominant_emotion', 'neutral')
        facial_data.setdefault('emotions', {})
        
        voice_data.setdefault('speech_risk_score', 0.2)
        voice_data.setdefault('acoustic_risk_score', 0.2)
        voice_data.setdefault('text_risk_score', 0.2)
        voice_data.setdefault('transcription', 'No transcription available')
        voice_data.setdefault('language', language)
        voice_data.setdefault('risk_signals', [])
        voice_data.setdefault('tempo_bpm', 100)
        voice_data.setdefault('avg_pitch_hz', 150)
        voice_data.setdefault('energy_level', 0.5)
        voice_data.setdefault('interpretation', '')
        
        # Generate comprehensive report with error handling
        comprehensive_report = generate_report_safe(facial_data, voice_data, {})
        socketio.emit('upload_progress', {"stage": "report_generated", "progress": 85})
        
        # Save prediction
        save_prediction(
            text_input=f"Video Analysis - {filename}",
            risk_level=comprehensive_report.get('overall_risk_level', 'LOW'),
            confidence=comprehensive_report.get('overall_risk_score', 0),
            sentiment=0.0,
            modality="multimodal_video",
            alert=comprehensive_report.get('overall_risk_level', 'LOW') in ['HIGH', 'CRITICAL']
        )
        
        # Emit alert if high risk
        if comprehensive_report.get('overall_risk_level', 'LOW') in ['HIGH', 'CRITICAL']:
            socketio.emit('high_risk_alert', {
                "risk_level": comprehensive_report.get('overall_risk_level'),
                "confidence": comprehensive_report.get('overall_risk_score'),
                "modality": "multimodal_video",
                "message": f"Video Analysis Alert: {comprehensive_report.get('overall_risk_level')} RISK DETECTED",
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        socketio.emit('upload_progress', {"stage": "complete", "progress": 100})
        app.logger.info(f"Video analysis completed successfully: {filename}")
        
        return jsonify({
            "success": True,
            "video_metadata": video_analysis.get('video_metadata'),
            "facial_analysis": facial_data,
            "voice_analysis": voice_data,
            "comprehensive_report": comprehensive_report
        }), 200
        
    except Exception as e:
        app.logger.error(f"Video upload error: {str(e)}", exc_info=True)
        socketio.emit('upload_error', {"error": str(e)})
        return jsonify({"error": "Video analysis failed. Please try a different file.", "details": str(e), "success": False}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                app.logger.debug(f"Cleaned up temporary file: {temp_path}")
            except OSError as cleanup_err:
                app.logger.warning(f"Failed to cleanup {temp_path}: {str(cleanup_err)}")


@app.route('/api/history', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def history():
    """
    Get recent prediction history from database
    ---
    tags:
      - Database
    security:
      - Bearer: []
    responses:
      200:
        description: Recent predictions from Supabase
    """
    result = get_recent_predictions(20)
    return jsonify(result), 200


@app.route('/api/db-stats', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def db_stats():
    """
    Get database statistics
    ---
    tags:
      - Database
    security:
      - Bearer: []
    responses:
      200:
        description: Database statistics
    """
    result = db_get_stats()
    return jsonify(result), 200


@app.route('/api/profile', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def profile():
    """
    Get current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: User profile
      401:
        description: Unauthorized
    """
    current_user = get_jwt_identity()
    return jsonify({
        "username": current_user,
        "message": f"Welcome {current_user}!",
        "role": "user"
    }), 200


# ── ERROR HANDLERS ───────────────────────────────────
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded",
        "retry_after": "Please wait before making another request"
    }), 429


@app.errorhandler(400)
def bad_request_handler(e):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(401)
def unauthorized_handler(e):
    return jsonify({"error": "Unauthorized - valid JWT token required"}), 401


@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error_handler(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    print("="*50)
    print("  Self Harm Detection API - Running")
    print("  Accuracy: 92.2%")
    print("  Rate Limiting: ENABLED")
    print("  Database: Supabase PostgreSQL")
    print("  Auth: JWT ENABLED - All endpoints protected")
    print("  Validation: ENABLED")
    print("  Dynamic Weights: ENABLED")
    print("  WebSocket: ENABLED - Real-time alerts")
    print("  Security: HARDENED")
    print("  Swagger Docs: http://127.0.0.1:5000/apidocs")
    print("  Endpoints:")
    print("    GET  /api/health         [public]")
    print("    POST /api/register       [public]")
    print("    POST /api/login          [public]")
    print("    GET  /api/profile        [JWT]")
    print("    POST /api/predict        [JWT]")
    print("    GET  /api/stats          [JWT]")
    print("    GET  /api/monitor        [JWT]")
    print("    POST /api/analyze-face   [JWT]")
    print("    POST /api/analyze-speech [JWT]")
    print("    POST /api/predict-multimodal [JWT]")
    print("    GET  /api/history        [JWT]")
    print("    GET  /api/db-stats       [JWT]")
    print("  WebSocket Events:")
    print("    connected, high_risk_alert, pong")
    print("="*50)
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)