from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib, os, sys, datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.preprocess import full_preprocess, get_sentiment_scores
from utils.monitor import log_prediction, get_monitoring_report
from utils.facial_analysis import analyze_face_from_base64, capture_webcam_frame

app  = Flask(__name__)
CORS(app)

model = joblib.load('model/risk_model.pkl')
tfidf = joblib.load('model/tfidf_vectorizer.pkl')

prediction_log = []


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status":    "running",
        "service":   "Self Harm Detection API",
        "accuracy":  "91.8%",
        "timestamp": datetime.datetime.now().isoformat()
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "text field is required"}), 400

    text = str(data['text']).strip()
    if not text:
        return jsonify({"error": "text cannot be empty"}), 400

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

    return jsonify({
        "risk_level":      risk_level,
        "confidence":      confidence,
        "alert_triggered": alert,
        "sentiment_score": round(sentiment, 4),
        "message":         message
    }), 200


@app.route('/api/stats', methods=['GET'])
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
def monitor():
    report = get_monitoring_report()
    return jsonify(report)


@app.route('/api/analyze-face', methods=['POST'])
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


if __name__ == '__main__':
    print("="*50)
    print("  Self Harm Detection API - Running")
    print("  Accuracy: 91.8%")
    print("  Endpoints:")
    print("    GET  /api/health")
    print("    POST /api/predict")
    print("    GET  /api/stats")
    print("    GET  /api/monitor")
    print("    POST /api/analyze-face")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)