import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore')

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from flask import Flask, request, jsonify
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

app = Flask(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "null",
    "https://self-harm-detection.vercel.app",
]

CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

Talisman(app, force_https=False, strict_transport_security=False, content_security_policy=False)

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")

jwt = setup_jwt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

swagger = Swagger(app)

try:
    model = joblib.load('model/risk_model.pkl')
    tfidf = joblib.load('model/tfidf_vectorizer.pkl')
    print("✓ ML models loaded")
except FileNotFoundError:
    print("⚠️  Model files not found - using keyword-based fallback")
    model = None
    tfidf = None

prediction_log = []


def keyword_based_prediction(text, sentiment):
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
        'anxious', 'panic', 'scared', 'afraid',
        'broken', 'numb', 'empty', 'lost', 'stressed'
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


@socketio.on('connect')
def handle_connect():
    emit('connected', {"message": "Connected to Self Harm Detection API"})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from WebSocket')


@socketio.on('ping')
def handle_ping():
    emit('pong', {"timestamp": datetime.datetime.now().isoformat()})


@app.route('/api/health', methods=['GET'])
@limiter.limit("60 per minute")
def health():
    return jsonify({
        "status": "running",
        "service": "Self Harm Detection API",
        "accuracy": "92.2%",
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
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
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "text field is required"}), 400

    text = sanitize_text(str(data['text']))
    is_valid, errors = validate_text_input(text)
    if not is_valid:
        return jsonify({"error": errors[0]}), 400

    cleaned = full_preprocess(text)
    scores = get_sentiment_scores(text)
    sentiment = scores['compound']
    neg_score = scores['neg']

    if model is None or tfidf is None:
        risk_level, confidence, alert = keyword_based_prediction(text, sentiment)
    else:
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

    log_prediction(text_length=len(text.split()), risk_level=risk_level, confidence=confidence, sentiment_score=round(sentiment, 4))
    save_prediction(text_input=text, risk_level=risk_level, confidence=confidence, sentiment=round(sentiment, 4), modality="text", alert=alert)

    if alert:
        socketio.emit('high_risk_alert', {
            "risk_level": risk_level, "confidence": confidence, "message": message,
            "timestamp": datetime.datetime.now().isoformat()
        })

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
            "support_resources": ["iCall: 9152987821", "Vandrevala Foundation: 1860-2662-345", "AASRA: 9820466627"] if alert else [],
            "follow_up": "Immediate professional consultation recommended" if alert else "Continue regular monitoring"
        },
        "analysis_timestamp": datetime.datetime.now().isoformat()
    }), 200


@app.route('/api/stats', methods=['GET'])
@jwt_required()
def stats():
    if not prediction_log:
        return jsonify({"message": "No predictions yet"})
    total = len(prediction_log)
    alerts = sum(1 for p in prediction_log if p['risk_level'] == 'HIGH')
    return jsonify({"total_predictions": total, "alerts_triggered": alerts, "alert_rate": round(alerts/total, 4), "recent": prediction_log[-5:]})


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"username": current_user, "role": "user"}), 200


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429


if __name__ == '__main__':
    print("="*50)
    print("  Self Harm Detection API - Running")
    print("="*50)
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)