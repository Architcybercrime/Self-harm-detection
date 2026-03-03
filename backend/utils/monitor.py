"""
monitor.py
Monitors model predictions for drift and logs all activity.
Stage 7 of ML Pipeline - Monitoring & Maintenance
"""

import json
import datetime
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'predictions.json')


def setup_logs():
    """Create logs directory if not exists."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            json.dump([], f)


def log_prediction(text_length, risk_level, confidence, sentiment_score):
    """Log every prediction for monitoring."""
    setup_logs()

    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        logs = []

    entry = {
        "timestamp":     datetime.datetime.now().isoformat(),
        "text_length":   text_length,
        "risk_level":    risk_level,
        "confidence":    confidence,
        "sentiment":     sentiment_score
    }
    logs.append(entry)

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)


def get_monitoring_report():
    """Generate monitoring report to detect model drift."""
    setup_logs()

    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        return {"error": "No logs found"}

    if len(logs) < 5:
        return {
            "status": "insufficient_data",
            "message": f"Only {len(logs)} predictions logged. Need at least 5.",
            "total_predictions": len(logs)
        }

    total  = len(logs)
    high   = sum(1 for l in logs if l['risk_level'] == 'HIGH')
    low    = sum(1 for l in logs if l['risk_level'] == 'LOW')
    avg_conf = sum(l['confidence'] for l in logs) / total
    avg_sent = sum(l['sentiment'] for l in logs) / total

    # Drift detection
    high_rate = high / total
    drift_warning = None
    if high_rate > 0.7:
        drift_warning = "⚠️ HIGH RISK rate above 70% - possible data drift or misuse"
    elif high_rate < 0.05:
        drift_warning = "⚠️ HIGH RISK rate very low - model may be underperforming"

    return {
        "status":              "healthy" if not drift_warning else "warning",
        "total_predictions":   total,
        "high_risk_count":     high,
        "low_risk_count":      low,
        "high_risk_rate":      round(high_rate, 4),
        "avg_confidence":      round(avg_conf, 4),
        "avg_sentiment":       round(avg_sent, 4),
        "drift_warning":       drift_warning,
        "last_prediction":     logs[-1]['timestamp'],
        "monitoring_message":  drift_warning or "✅ Model performing within expected parameters"
    }