"""
monitor.py
Monitors model predictions for drift and logs all activity.
Stage 7 of ML Pipeline - Monitoring & Maintenance
Enhanced with trend-based alerting system.
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
        "timestamp":   datetime.datetime.now().isoformat(),
        "text_length": text_length,
        "risk_level":  risk_level,
        "confidence":  confidence,
        "sentiment":   sentiment_score
    }
    logs.append(entry)

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)


def get_trend_analysis(logs, window=10):
    """
    Analyze prediction trends over a sliding window.
    Detects escalating risk patterns.
    """
    if len(logs) < window:
        window = len(logs)

    recent = logs[-window:]

    high_count   = sum(1 for l in recent if l['risk_level'] == 'HIGH')
    high_rate    = high_count / window
    avg_conf     = sum(l['confidence'] for l in recent) / window
    avg_sent     = sum(l['sentiment'] for l in recent) / window

    # Trend detection - compare first half vs second half
    alerts = []
    if window >= 4:
        half      = window // 2
        first     = recent[:half]
        second    = recent[half:]
        first_hr  = sum(1 for l in first if l['risk_level'] == 'HIGH') / half
        second_hr = sum(1 for l in second if l['risk_level'] == 'HIGH') / half

        if second_hr > first_hr + 0.3:
            alerts.append({
                "type":     "ESCALATING_RISK",
                "severity": "HIGH",
                "message":  f"Risk rate increased from {first_hr:.0%} to {second_hr:.0%} in recent predictions",
                "action":   "Immediate review recommended"
            })

        if second_hr < first_hr - 0.3:
            alerts.append({
                "type":     "IMPROVING_TREND",
                "severity": "LOW",
                "message":  f"Risk rate decreased from {first_hr:.0%} to {second_hr:.0%}",
                "action":   "Continue monitoring"
            })

    # Consecutive HIGH risk alert
    consecutive = 0
    for l in reversed(recent):
        if l['risk_level'] == 'HIGH':
            consecutive += 1
        else:
            break

    if consecutive >= 3:
        alerts.append({
            "type":     "CONSECUTIVE_HIGH_RISK",
            "severity": "CRITICAL",
            "message":  f"{consecutive} consecutive HIGH risk predictions detected",
            "action":   "Immediate intervention required"
        })

    # Sentiment deterioration
    if avg_sent < -0.5:
        alerts.append({
            "type":     "NEGATIVE_SENTIMENT_TREND",
            "severity": "MEDIUM",
            "message":  f"Average sentiment critically negative ({avg_sent:.2f})",
            "action":   "Mental health check recommended"
        })

    return {
        "window_size":        window,
        "high_risk_rate":     round(high_rate, 4),
        "avg_confidence":     round(avg_conf, 4),
        "avg_sentiment":      round(avg_sent, 4),
        "consecutive_high":   consecutive,
        "trend_alerts":       alerts,
        "alert_count":        len(alerts),
        "trend_status":       "CRITICAL" if any(a['severity'] == 'CRITICAL' for a in alerts)
                              else "WARNING" if any(a['severity'] == 'HIGH' for a in alerts)
                              else "NORMAL"
    }


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
            "status":            "insufficient_data",
            "message":           f"Only {len(logs)} predictions logged. Need at least 5.",
            "total_predictions": len(logs)
        }

    total    = len(logs)
    high     = sum(1 for l in logs if l['risk_level'] == 'HIGH')
    low      = sum(1 for l in logs if l['risk_level'] == 'LOW')
    avg_conf = sum(l['confidence'] for l in logs) / total
    avg_sent = sum(l['sentiment'] for l in logs) / total

    # Drift detection
    high_rate     = high / total
    drift_warning = None
    if high_rate > 0.7:
        drift_warning = "HIGH RISK rate above 70% - possible data drift or misuse"
    elif high_rate < 0.05:
        drift_warning = "HIGH RISK rate very low - model may be underperforming"

    # Trend analysis
    trend = get_trend_analysis(logs)

    return {
        "status":              "healthy" if not drift_warning and trend['trend_status'] == 'NORMAL' else "warning",
        "total_predictions":   total,
        "high_risk_count":     high,
        "low_risk_count":      low,
        "high_risk_rate":      round(high_rate, 4),
        "avg_confidence":      round(avg_conf, 4),
        "avg_sentiment":       round(avg_sent, 4),
        "drift_warning":       drift_warning,
        "last_prediction":     logs[-1]['timestamp'],
        "trend_analysis":      trend,
        "monitoring_message":  drift_warning or "Model performing within expected parameters"
    }