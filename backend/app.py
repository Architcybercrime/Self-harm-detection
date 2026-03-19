from flask import Flask, request, jsonify
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import joblib, os, sys, datetime
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

app  = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:5000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
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

model = joblib.load('model/risk_model.pkl')
tfidf = joblib.load('model/tfidf_vectorizer.pkl')

prediction_log = []


@app.route('/api/health', methods=['GET'])
@limiter.limit("60 per minute")
def health():
    return jsonify({
        "status":    "running",
        "service":   "Self Harm Detection API",
        "accuracy":  "92.2%",
        "database":  "Supabase PostgreSQL",
        "auth":      "JWT enabled",
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

    cleaned   = full_preprocess(text)
    scores    = get_sentiment_scores(text)
    sentiment = scores['compound']
    neg_score = scores['neg']

    tfidf_vec = tfidf.transform([cleaned]).toarray()
    X = np.hstack([tfidf_vec, [[sentiment, neg_score]]])

    prediction  = model.predict(X)[0]
    probability = model.predict_proba(X)[0]
    confidence  = round(float(max(probability)), 4)

    if prediction == 'suicide':
        risk_level = 'HIGH'
        alert      = True
        message    = 'High risk indicators detected. Please seek professional support immediately.'
    else:
        risk_level = 'LOW'
        alert      = False
        message    = 'No immediate concern detected. Continue monitoring.'

    prediction_log.append({
        "timestamp":  datetime.datetime.now().isoformat(),
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
        text_input  = text,
        risk_level  = risk_level,
        confidence  = confidence,
        sentiment   = round(sentiment, 4),
        modality    = "text",
        alert       = alert
    )

    return jsonify({
        "risk_level":        risk_level,
        "confidence":        confidence,
        "alert_triggered":   alert,
        "sentiment_score":   round(sentiment, 4),
        "message":           message,
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
    }), 200


@app.route('/api/stats', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def stats():
    if not prediction_log:
        return jsonify({"message": "No predictions yet"})

    total  = len(prediction_log)
    alerts = sum(1 for p in prediction_log if p['risk_level'] == 'HIGH')

    return jsonify({
        "total_predictions": total,
        "alerts_triggered":  alerts,
        "alert_rate":        round(alerts/total, 4),
        "recent":            prediction_log[-5:]
    })


@app.route('/api/monitor', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def monitor():
    report = get_monitoring_report()
    return jsonify(report)


@app.route('/api/analyze-face', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def analyze_face():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'image_base64' in data:
        result = analyze_face_from_base64(data['image_base64'])
        return jsonify(result), 200

    if data.get('use_webcam'):
        result = capture_webcam_frame()
        return jsonify(result), 200

    return jsonify({"error": "Provide image_base64 or use_webcam:true"}), 400


@app.route('/api/analyze-speech', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def analyze_speech():
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


@app.route('/api/predict-multimodal', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def predict_multimodal():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    text_result   = None
    face_result   = None
    speech_result = None
    text          = ""

    if 'text' in data:
        text = sanitize_text(str(data['text']))
        is_valid, errors = validate_text_input(text)
        if not is_valid:
            return jsonify({"error": errors[0]}), 400
        cleaned   = full_preprocess(text)
        scores    = get_sentiment_scores(text)
        sentiment = scores['compound']
        neg_score = scores['neg']
        tfidf_vec = tfidf.transform([cleaned]).toarray()
        X = np.hstack([tfidf_vec, [[sentiment, neg_score]]])
        prediction  = model.predict(X)[0]
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
            "timestamp":  datetime.datetime.now().isoformat(),
            "risk_level": final_result['risk_level'],
            "confidence": final_result['final_risk_score'],
            "multimodal": True
        })

        save_prediction(
            text_input  = text,
            risk_level  = final_result['risk_level'],
            confidence  = final_result['final_risk_score'],
            sentiment   = 0.0,
            modality    = "multimodal",
            alert       = final_result['alert_triggered']
        )

    return jsonify(final_result), 200


@app.route('/api/history', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def history():
    result = get_recent_predictions(20)
    return jsonify(result), 200


@app.route('/api/db-stats', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def db_stats():
    result = db_get_stats()
    return jsonify(result), 200


@app.route('/api/profile', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def profile():
    current_user = get_jwt_identity()
    return jsonify({
        "username": current_user,
        "message":  f"Welcome {current_user}!",
        "role":     "user"
    }), 200


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error":       "Rate limit exceeded",
        "message":     str(e.description),
        "retry_after": "Please wait before making another request"
    }), 429


@app.errorhandler(400)
def bad_request_handler(e):
    return jsonify({
        "error":   "Bad request",
        "message": str(e)
    }), 400


if __name__ == '__main__':
    print("="*50)
    print("  Self Harm Detection API - Running")
    print("  Accuracy: 92.2%")
    print("  Rate Limiting: ENABLED")
    print("  Database: Supabase PostgreSQL")
    print("  Auth: JWT ENABLED - All endpoints protected")
    print("  Validation: ENABLED")
    print("  Dynamic Weights: ENABLED")
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
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)