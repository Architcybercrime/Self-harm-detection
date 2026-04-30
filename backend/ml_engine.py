"""
ml_engine.py
============
Central ML prediction engine — loaded once at startup.

Exports
-------
model            : trained Logistic Regression (or None if file missing)
tfidf            : fitted TF-IDF vectoriser   (or None if file missing)
prediction_log   : in-memory list of recent predictions (for /api/stats)
run_prediction() : runs text → risk prediction and returns result dict
"""

import os
import datetime
import numpy as np
import joblib

from utils.preprocess import full_preprocess, get_sentiment_scores

# ── Model paths ───────────────────────────────────────
_BASE  = os.path.dirname(os.path.abspath(__file__))
_MODEL = os.path.join(_BASE, 'model', 'risk_model.pkl')
_TFIDF = os.path.join(_BASE, 'model', 'tfidf_vectorizer.pkl')

# ── Load models once at startup ───────────────────────
model = None
tfidf = None

try:
    model = joblib.load(_MODEL)
    tfidf = joblib.load(_TFIDF)
    print("✓ ML model loaded successfully")
except FileNotFoundError:
    print("WARNING: Model files not found — using keyword-based fallback")

# ── In-memory prediction log ──────────────────────────
prediction_log: list = []


# ── Keyword fallback ──────────────────────────────────
def keyword_based_prediction(text: str, sentiment: float):
    """
    Fallback risk scorer used when trained model files are unavailable.

    Args:
        text: Raw input text.
        sentiment: VADER compound sentiment score (-1 to +1).

    Returns:
        Tuple of (risk_level, confidence, alert_triggered).
    """
    t = text.lower()

    critical = [
        'kill myself', 'kill me', 'end my life', 'want to die',
        'suicide', 'commit suicide', 'end it all', 'not worth living',
        'better off dead', 'take my life', 'ending my life',
        'no reason to live', 'want to end', 'hang myself',
        'overdose', 'slit my', 'cut myself', 'kms',
    ]
    high = [
        'hopeless', 'worthless', 'useless', 'burden',
        "can't go on", 'give up', 'giving up', 'no point',
        'pointless', 'meaningless', 'empty inside', 'trapped',
        'no escape', "can't take it", 'wanna die', 'helpless', 'depressed',
    ]
    medium = [
        'sad', 'crying', 'alone', 'lonely', 'tired', 'exhausted',
        "can't sleep", 'anxious', 'panic', 'scared', 'afraid',
        'broken', 'numb', 'empty', 'lost', 'stressed',
    ]

    cc = sum(1 for kw in critical if kw in t)
    hc = sum(1 for kw in high    if kw in t)
    mc = sum(1 for kw in medium  if kw in t)

    if cc >= 1 or hc >= 2 or sentiment < -0.7:
        return 'HIGH', min(0.95, 0.80 + cc * 0.05 + hc * 0.03), True
    if hc >= 1 or mc >= 2 or sentiment < -0.3:
        return 'MEDIUM', min(0.85, 0.65 + hc * 0.05 + mc * 0.02), False
    return 'LOW', 0.75, False


# ── Main prediction function ──────────────────────────
def run_prediction(text: str, explain: bool = False) -> dict:
    """
    Run the full ML prediction pipeline on input text.

    Args:
        text:    Raw text to analyse.
        explain: If True, include SHAP top-word explanations.

    Returns:
        Dictionary with risk_level, confidence, sentiment,
        recommendations, and optional SHAP explanation.
    """
    cleaned   = full_preprocess(text)
    scores    = get_sentiment_scores(text)
    sentiment = scores['compound']
    neg_score = scores['neg']

    def _build_result(risk_level, confidence, alert):
        message = (
            'High risk indicators detected. Please seek professional support immediately.'
            if alert else
            'No immediate concern detected. Continue monitoring.'
        )
        return {
            "risk_level":       risk_level,
            "confidence":       confidence,
            "alert_triggered":  alert,
            "sentiment_score":  round(sentiment, 4),
            "message":          message,
            "modality":         "text",
            "risk_indicators": {
                "text_sentiment":   "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive",
                "confidence_level": "high"    if confidence > 0.85 else "medium" if confidence > 0.65 else "low",
                "severity":         "critical" if confidence > 0.9  else "high"  if confidence > 0.75 else "moderate",
            },
            "recommendations": {
                "immediate_action":  alert,
                "support_resources": [
                    "iCall: 9152987821",
                    "Vandrevala Foundation: 1860-2662-345",
                    "AASRA: 9820466627",
                ] if alert else [],
                "follow_up": (
                    "Immediate professional consultation recommended"
                    if alert else "Continue regular monitoring"
                ),
            },
            "analysis_timestamp": datetime.datetime.now().isoformat(),
        }

    # ── Fallback if model unavailable ────────────────
    if model is None or tfidf is None:
        rl, conf, alert = keyword_based_prediction(text, sentiment)
        return _build_result(rl, round(conf, 4), alert)

    # ── ML model prediction ───────────────────────────
    vec        = tfidf.transform([cleaned]).toarray()
    X          = np.hstack([vec, [[sentiment, neg_score]]])
    prediction = model.predict(X)[0]
    prob       = model.predict_proba(X)[0]
    confidence = round(float(max(prob)), 4)

    risk_level = 'HIGH' if prediction == 'suicide' else 'LOW'
    alert      = risk_level == 'HIGH'
    result     = _build_result(risk_level, confidence, alert)

    # ── SHAP explanation (fast for linear models) ─────
    if explain:
        try:
            import shap
            feat_names = tfidf.get_feature_names_out().tolist() + ["sentiment", "neg_score"]
            explainer  = shap.LinearExplainer(model, X, feature_perturbation="interventional")
            shap_vals  = explainer.shap_values(X)
            vals       = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
            top_idx    = np.argsort(np.abs(vals))[::-1][:8]
            result["explanation"] = {
                "top_words": [
                    {"word": feat_names[i], "impact": round(float(vals[i]), 4)}
                    for i in top_idx if abs(vals[i]) > 1e-6
                ]
            }
        except Exception:
            pass

    return result
