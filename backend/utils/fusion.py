"""
fusion.py
Multimodal fusion module - combines text, facial and speech
risk scores into a single unified risk assessment.
"""

import numpy as np


def fuse_risk_scores(text_result=None, face_result=None, speech_result=None):
    """
    Combine risk scores from all modalities.
    Uses weighted average based on confidence.
    
    Weights (based on research):
    - Text analysis   : 50% (most reliable)
    - Facial analysis : 30% (strong indicator)
    - Speech analysis : 20% (supporting signal)
    """

    scores     = []
    weights    = []
    modalities = []

    # Text score
    if text_result and 'confidence' in text_result:
        text_score = text_result['confidence']
        if text_result.get('risk_level') == 'LOW':
            text_score = 1 - text_score
        scores.append(float(text_score))
        weights.append(0.50)
        modalities.append('text')

    # Facial score
    if face_result and 'facial_risk_score' in face_result:
        scores.append(float(face_result['facial_risk_score']))
        weights.append(0.30)
        modalities.append('facial')

    # Speech score
    if speech_result and 'speech_risk_score' in speech_result:
        scores.append(float(speech_result['speech_risk_score']))
        weights.append(0.20)
        modalities.append('speech')

    if not scores:
        return {"error": "No valid modality results provided"}

    # Normalize weights
    total_weight  = sum(weights)
    norm_weights  = [w / total_weight for w in weights]

    # Weighted average
    final_score = float(np.dot(scores, norm_weights))
    final_score = float(np.clip(final_score, 0, 1))

    # Determine final risk level
    risk_level = get_final_risk_level(final_score)
    alert      = risk_level in ['HIGH', 'CRITICAL']

    return {
        "final_risk_score":   round(final_score, 4),
        "risk_level":         risk_level,
        "alert_triggered":    alert,
        "modalities_used":    modalities,
        "individual_scores": {
            "text_score":    round(float(scores[modalities.index('text')]), 4)
                             if 'text' in modalities else None,
            "facial_score":  round(float(scores[modalities.index('facial')]), 4)
                             if 'facial' in modalities else None,
            "speech_score":  round(float(scores[modalities.index('speech')]), 4)
                             if 'speech' in modalities else None,
        },
        "message":            get_risk_message(risk_level),
        "recommendation":     get_recommendation(risk_level)
    }


def get_final_risk_level(score):
    """Convert unified score to risk level."""
    if score < 0.25:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    elif score < 0.75:
        return "HIGH"
    else:
        return "CRITICAL"


def get_risk_message(risk_level):
    """Get human readable message for risk level."""
    messages = {
        "LOW":      "No significant risk indicators detected across modalities.",
        "MEDIUM":   "Some risk indicators detected. Continued monitoring recommended.",
        "HIGH":     "Multiple risk indicators detected. Professional support recommended.",
        "CRITICAL": "Critical risk level detected. Immediate intervention required."
    }
    return messages.get(risk_level, "Unknown risk level")


def get_recommendation(risk_level):
    """Get actionable recommendation."""
    recommendations = {
        "LOW":      "Continue regular check-ins and monitoring.",
        "MEDIUM":   "Schedule a wellness check. Increase monitoring frequency.",
        "HIGH":     "Alert mental health professional. Provide support resources.",
        "CRITICAL": "Immediate alert to mental health team. Emergency support required."
    }
    return recommendations.get(risk_level, "Consult a professional.")