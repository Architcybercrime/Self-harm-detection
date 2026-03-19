from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import joblib, os, sys, datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.preprocess import full_preprocess, get_sentiment_scores
from utils.monitor import log_prediction, get_monitoring_report
from utils.facial_analysis import analyze_face_from_base64, capture_webcam_frame
from utils.speech_analysis import analyze_audio_file, record_from_microphone
from utils.fusion import fuse_risk_scores
from utils.database import save_prediction, get_stats as db_get_stats, get_recent_predictions

app  = Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route('/api/predict', methods=['POST'])
@limiter.limit("30 per minute")
def predict():
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "text field is required"}), 400

    text = str(data['text']).strip()
    if not text:
        return jsonify({"error": "text cannot be empty"}), 400

    if len(text) > 5000:
        return jsonify({"error": "text too long. Maximum 5000 characters"}), 400

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

    # Save to Supabase
    save_prediction(
        text_input  = text,
        risk_level  = risk_level,
        confidence  = confidence,
        sentiment   = round(sentiment, 4),
        modality    = "text",
        alert       = alert
    )

    return jsonify({
        "risk_level":      risk_level,
        "confidence":      confidence,
        "alert_triggered": alert,
        "sentiment_score": round(sentiment, 4),
        "message":         message
    }), 200


@app.route('/api/stats', methods=['GET'])
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
@limiter.limit("30 per minute")
def monitor():
    report = get_monitoring_report()
    return jsonify(report)


@app.route('/api/analyze-face', methods=['POST'])
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
@limiter.limit("20 per minute")
def analyze_speech():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'audio_path' in data:
        result = analyze_audio_file(data['audio_path'])
        return jsonify(result), 200

    if data.get('use_microphone'):
        duration = int(data.get('duration', 5))
        if duration > 30:
            return jsonify({"error": "Maximum duration is 30 seconds"}), 400
        result   = record_from_microphone(duration)
        return jsonify(result), 200

    return jsonify({"error": "Provide audio_path or use_microphone:true"}), 400


@app.route('/api/predict-multimodal', methods=['POST'])
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
        text = str(data['text']).strip()
        if len(text) > 5000:
            return jsonify({"error": "text too long. Maximum 5000 characters"}), 400
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
        duration      = int(data.get('duration', 5))
        speech_result = record_from_microphone(duration)

    final_result = fuse_risk_scores(
        text_result=text_result,
        face_result=face_result,
        speech_result=speech_result
    )

    if 'risk_level' in final_result:
        prediction_log.append({
            "timestamp":  datetime.datetime.now().isoformat(),
            "risk_level": final_result['risk_level'],
            "confidence": final_result['final_risk_score'],
            "multimodal": True
        })

        # Save to Supabase
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
@limiter.limit("30 per minute")
def history():
    result = get_recent_predictions(20)
    return jsonify(result), 200


@app.route('/api/db-stats', methods=['GET'])
@limiter.limit("30 per minute")
def db_stats():
    result = db_get_stats()
    return jsonify(result), 200


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
    print("  Endpoints:")
    print("    GET  /api/health")
    print("    POST /api/predict        [30/min]")
    print("    GET  /api/stats          [30/min]")
    print("    GET  /api/monitor        [30/min]")
    print("    POST /api/analyze-face   [20/min]")
    print("    POST /api/analyze-speech [20/min]")
    print("    POST /api/predict-multimodal [10/min]")
    print("    GET  /api/history        [30/min]")
    print("    GET  /api/db-stats       [30/min]")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)