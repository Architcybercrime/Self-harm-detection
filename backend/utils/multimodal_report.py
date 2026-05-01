"""
multimodal_report.py
Comprehensive therapist-style report generation combining facial, voice, and text analysis.
Generates professional assessment with concerns, improvements, and action items.
"""

import json
import datetime


def generate_multimodal_report(facial_data, voice_data, text_data):
    """
    Generate comprehensive therapeutic report from multimodal analysis.
    
    Args:
        facial_data: dict with emotions, dominant_emotion, facial_risk_score, risk_level
        voice_data: dict with tempo, pitch, energy, text_risk_score, acoustic_risk_score, transcription
        text_data: dict with risk_level, confidence, risk_indicators (optional)
    
    Returns:
        dict with comprehensive report structure
    """
    
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "analysis_type": "MULTIMODAL_VIDEO_ANALYSIS",
        "overall_risk_assessment": None,
        "executive_summary": None,
        "findings": {},
        "concerns": [],
        "areas_for_improvement": [],
        "strengths": [],
        "recommendations": [],
        "actionable_insights": [],
        "therapist_notes": None,
        "next_steps": []
    }
    
    # Calculate overall risk from all modalities
    facial_risk = float(facial_data.get('facial_risk_score', 0.2))
    voice_risk = float(voice_data.get('speech_risk_score', 0.2))
    text_risk = float(voice_data.get('text_risk_score', 0.2))
    
    # Weighted overall risk: 30% facial, 40% voice/acoustic+text, 30% text-semantic
    overall_risk = (facial_risk * 0.3) + (voice_risk * 0.4) + (text_risk * 0.3)
    report["overall_risk_score"] = round(overall_risk, 4)
    report["overall_risk_level"] = get_risk_level(overall_risk)
    
    # ═══════════════════════════════════════════════════════════
    # FACIAL ANALYSIS FINDINGS
    # ═══════════════════════════════════════════════════════════
    report["findings"]["facial_analysis"] = {
        "dominant_emotion": facial_data.get('dominant_emotion', 'UNKNOWN'),
        "emotions_breakdown": facial_data.get('emotions', {}),
        "risk_score": facial_risk,
        "risk_level": facial_data.get('risk_level', 'LOW'),
        "interpretation": analyze_facial_patterns(facial_data)
    }
    
    # ═══════════════════════════════════════════════════════════
    # VOICE/SPEECH ANALYSIS FINDINGS
    # ═══════════════════════════════════════════════════════════
    report["findings"]["voice_analysis"] = {
        "acoustic_features": {
            "tempo_bpm": voice_data.get('tempo_bpm', 0),
            "pitch_hz": voice_data.get('avg_pitch_hz', 0),
            "energy_level": voice_data.get('energy_level', 0),
            "interpretation": voice_data.get('interpretation', '')
        },
        "transcription": voice_data.get('transcription', 'No transcription available'),
        "language": voice_data.get('language', 'en-US'),
        "acoustic_risk_score": voice_data.get('acoustic_risk_score', 0),
        "text_risk_score": voice_data.get('text_risk_score', 0),
        "combined_risk_score": voice_data.get('speech_risk_score', 0),
        "risk_signals": voice_data.get('risk_signals', [])
    }
    
    # ═══════════════════════════════════════════════════════════
    # IDENTIFY CONCERNS
    # ═══════════════════════════════════════════════════════════
    concerns = identify_concerns(facial_data, voice_data)
    report["concerns"] = concerns
    
    # ═══════════════════════════════════════════════════════════
    # IDENTIFY AREAS FOR IMPROVEMENT
    # ═══════════════════════════════════════════════════════════
    improvements = identify_improvements(facial_data, voice_data)
    report["areas_for_improvement"] = improvements
    
    # ═══════════════════════════════════════════════════════════
    # IDENTIFY STRENGTHS
    # ═══════════════════════════════════════════════════════════
    strengths = identify_strengths(facial_data, voice_data)
    report["strengths"] = strengths
    
    # ═══════════════════════════════════════════════════════════
    # GENERATE RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════
    recommendations = generate_recommendations(facial_data, voice_data, concerns, improvements)
    report["recommendations"] = recommendations
    
    # ═══════════════════════════════════════════════════════════
    # ACTIONABLE INSIGHTS
    # ═══════════════════════════════════════════════════════════
    insights = generate_actionable_insights(facial_data, voice_data, concerns)
    report["actionable_insights"] = insights
    
    # ═══════════════════════════════════════════════════════════
    # THERAPIST NOTES
    # ═══════════════════════════════════════════════════════════
    report["therapist_notes"] = generate_therapist_notes(facial_data, voice_data, report)
    
    # ═══════════════════════════════════════════════════════════
    # NEXT STEPS
    # ═══════════════════════════════════════════════════════════
    report["next_steps"] = generate_next_steps(report["overall_risk_level"], concerns)
    
    # ═══════════════════════════════════════════════════════════
    # EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════
    report["executive_summary"] = generate_executive_summary(report)
    
    return report


def get_risk_level(score):
    """Convert numerical risk score to risk level."""
    if score >= 0.7:
        return "CRITICAL"
    elif score >= 0.5:
        return "HIGH"
    elif score >= 0.3:
        return "MEDIUM"
    else:
        return "LOW"


def analyze_facial_patterns(facial_data):
    """Generate interpretation of facial emotional patterns."""
    dominant = facial_data.get('dominant_emotion', 'UNKNOWN').lower()
    emotions = facial_data.get('emotions', {})
    
    interpretations = {
        'sad': "Facial expression indicates prolonged sadness or melancholy. The person may be experiencing depressed mood.",
        'angry': "Facial expression shows signs of anger or irritability. This may indicate frustration or emotional dysregulation.",
        'fear': "Facial expression displays fear or anxiety markers. The person may be experiencing worry or apprehension.",
        'neutral': "Facial expression is relatively neutral. The person appears emotionally restrained or composed.",
        'happy': "Facial expression shows signs of positive emotion. The person appears to be in better emotional state.",
        'disgust': "Facial expression indicates disgust or rejection. May reflect negative self-perception or dismissiveness.",
        'surprise': "Facial expression shows surprise. May indicate emotional reactivity or unexpected thoughts/realization."
    }
    
    base_interp = interpretations.get(dominant, f"Facial analysis shows {dominant} emotional state.")
    
    # Add additional context from emotion probabilities
    if emotions.get('sad', 0) > 30:
        base_interp += " Notably elevated sadness markers detected."
    if emotions.get('angry', 0) > 30:
        base_interp += " Elevated anger/irritability markers present."
    if emotions.get('fear', 0) > 30:
        base_interp += " Significant anxiety/fear indicators observed."
    
    return base_interp


def identify_concerns(facial_data, voice_data):
    """Identify clinical concerns from multimodal analysis."""
    concerns = []
    
    # Facial concerns
    facial_risk = float(facial_data.get('facial_risk_score', 0))
    dominant_emotion = facial_data.get('dominant_emotion', '').lower()
    
    if facial_risk > 0.5:
        concerns.append({
            "area": "Facial Expression",
            "concern": f"Elevated emotional distress indicators in facial expressions",
            "severity": "HIGH" if facial_risk > 0.7 else "MEDIUM",
            "details": f"Dominant emotion: {dominant_emotion.title()}. Risk score: {facial_risk:.2%}"
        })
    
    # Voice concerns
    voice_risk = float(voice_data.get('speech_risk_score', 0))
    text_risk = float(voice_data.get('text_risk_score', 0))
    
    if text_risk > 0.6:
        risk_signals = voice_data.get('risk_signals', [])
        signal_text = ", ".join(risk_signals) if risk_signals else "High-risk language patterns"
        concerns.append({
            "area": "Speech Content",
            "concern": f"High-risk language patterns detected in speech",
            "severity": "HIGH" if text_risk > 0.8 else "MEDIUM",
            "details": f"Risk indicators: {signal_text}. Text risk score: {text_risk:.2%}"
        })
    
    # Acoustic concerns
    acoustic_risk = float(voice_data.get('acoustic_risk_score', 0))
    tempo = float(voice_data.get('tempo_bpm', 0))
    pitch = float(voice_data.get('avg_pitch_hz', 0))
    energy = float(voice_data.get('energy_level', 0))
    
    if acoustic_risk > 0.5:
        acoustic_interpretation = voice_data.get('interpretation', '')
        concerns.append({
            "area": "Vocal Characteristics",
            "concern": "Vocal features suggest emotional distress",
            "severity": "HIGH" if acoustic_risk > 0.7 else "MEDIUM",
            "details": f"{acoustic_interpretation}. Acoustic risk: {acoustic_risk:.2%}"
        })
    
    return concerns if concerns else [{"area": "Overall", "concern": "No significant concerns detected", "severity": "LOW", "details": "Behavioral patterns within normal range"}]


def identify_improvements(facial_data, voice_data):
    """Identify areas where person could improve emotional wellbeing."""
    improvements = []
    
    # Facial pattern improvements
    emotions = facial_data.get('emotions', {})
    if emotions.get('sad', 0) > 40:
        improvements.append({
            "area": "Emotional Expression",
            "suggestion": "Work on increasing positive emotional expression and facial engagement",
            "why": "High levels of sadness in facial expression suggest potential mood disturbance that could benefit from emotional regulation techniques.",
            "actions": ["Practice smiling or positive facial expressions", "Engage in mood-lifting activities", "Consider mindfulness or face-based emotion regulation"]
        })
    
    # Speech pattern improvements
    tempo = float(voice_data.get('tempo_bpm', 0))
    pitch = float(voice_data.get('avg_pitch_hz', 0))
    
    if tempo < 100:
        improvements.append({
            "area": "Speech Pace",
            "suggestion": "Work on speaking with more consistent and natural pace",
            "why": "Slower speech patterns can indicate depression, fatigue, or lack of engagement. Speaking at a normal pace can improve communication effectiveness.",
            "actions": ["Practice speaking exercises", "Record yourself speaking and review", "Engage in conversations with varied topics"]
        })
    
    if pitch < 100 and float(voice_data.get('energy_level', 0)) < 0.5:
        improvements.append({
            "area": "Vocal Engagement",
            "suggestion": "Increase vocal energy and pitch variation in speech",
            "why": "Low pitch and energy can indicate depression, low mood, or disengagement. Vocal variation improves communication and reflects better emotional state.",
            "actions": ["Practice vocal exercises", "Engage in group conversations", "Work with speech coach if needed"]
        })
    
    return improvements if improvements else [{"area": "Overall", "suggestion": "Continue positive emotional patterns", "why": "Current patterns are healthy", "actions": ["Maintain current wellness routines"]}]


def identify_strengths(facial_data, voice_data):
    """Identify positive patterns and strengths."""
    strengths = []
    
    facial_risk = float(facial_data.get('facial_risk_score', 0))
    voice_risk = float(voice_data.get('speech_risk_score', 0))
    
    if facial_risk < 0.3:
        strengths.append({
            "area": "Emotional Regulation",
            "strength": "Relatively stable and regulated emotional expressions",
            "importance": "This indicates good emotional control and resilience."
        })
    
    if voice_risk < 0.3:
        strengths.append({
            "area": "Communication",
            "strength": "Clear and stable vocal patterns without distress indicators",
            "importance": "This shows healthy emotional expression through speech."
        })
    
    emotions = facial_data.get('emotions', {})
    if emotions.get('happy', 0) > 20:
        strengths.append({
            "area": "Positive Affect",
            "strength": "Presence of positive emotional expression",
            "importance": "This indicates capacity for positive emotions and resilience."
        })
    
    return strengths if strengths else []


def generate_recommendations(facial_data, voice_data, concerns, improvements):
    """Generate professional recommendations."""
    recommendations = []
    
    overall_risk = float(facial_data.get('facial_risk_score', 0.2)) * 0.3 + float(voice_data.get('speech_risk_score', 0.2)) * 0.7
    
    if overall_risk > 0.7:
        recommendations.append({
            "priority": "URGENT",
            "recommendation": "Professional mental health evaluation recommended",
            "rationale": "Multimodal analysis indicates significant distress indicators. Professional assessment is strongly recommended to rule out serious conditions.",
            "action_items": ["Schedule appointment with mental health professional", "Share this report with healthcare provider", "Consider crisis resources if in immediate danger"]
        })
    
    if len(concerns) > 2:
        recommendations.append({
            "priority": "HIGH",
            "recommendation": "Comprehensive therapeutic assessment suggested",
            "rationale": f"Multiple areas of concern identified ({len(concerns)} concern areas). Structured therapy could help address these patterns.",
            "action_items": ["Consult with therapist", "Develop personalized coping strategies", "Regular check-ins recommended"]
        })
    
    recommendations.append({
        "priority": "MEDIUM",
        "recommendation": "Regular emotional wellness monitoring",
        "rationale": "Ongoing monitoring helps track progress and identify emerging concerns early.",
        "action_items": ["Schedule regular self-assessments", "Maintain wellness journal", "Practice recommended emotional regulation techniques"]
    })
    
    return recommendations


def generate_actionable_insights(facial_data, voice_data, concerns):
    """Generate specific actionable insights."""
    insights = []
    
    # If sad emotion detected
    if facial_data.get('emotions', {}).get('sad', 0) > 35:
        insights.append({
            "insight": "Elevated sadness detected",
            "action": "Engage in mood-lifting activities like exercise, social interaction, or hobbies",
            "timeline": "Implement immediately and practice daily for 2-4 weeks"
        })
    
    # If fast/stressed speech
    tempo = float(voice_data.get('tempo_bpm', 0))
    if tempo > 130:
        insights.append({
            "insight": "Rapid speech pattern detected (possibly stress-related)",
            "action": "Practice deep breathing and deliberate speech pacing",
            "timeline": "Implement during conversations for 1-2 weeks to build habit"
        })
    
    # If low energy
    if float(voice_data.get('energy_level', 0)) < 0.4:
        insights.append({
            "insight": "Low vocal energy indicates possible fatigue or depression",
            "action": "Ensure adequate sleep (7-9 hours), exercise regularly, and maintain social engagement",
            "timeline": "Establish routine for next 2 weeks"
        })
    
    # If risk signals in speech
    if voice_data.get('risk_signals'):
        signals = voice_data.get('risk_signals', [])
        insights.append({
            "insight": f"Self-harm related language detected: {', '.join(signals[:3])}",
            "action": "Reach out to mental health professional or crisis hotline immediately",
            "timeline": "DO THIS NOW if experiencing crisis"
        })
    
    return insights if insights else [{"insight": "Overall stable patterns", "action": "Continue current wellness practices", "timeline": "Ongoing"}]


def generate_therapist_notes(facial_data, voice_data, report):
    """Generate professional therapist-style notes."""
    notes = f"""
CLINICAL ASSESSMENT SUMMARY

Date of Assessment: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
Overall Risk Level: {report.get('overall_risk_level', 'UNKNOWN')}
Overall Risk Score: {report.get('overall_risk_score', 0):.2%}

PRESENTATION:
The client's multimodal analysis reveals the following presentation:

Facial Expression Analysis:
- Dominant emotion: {facial_data.get('dominant_emotion', 'Not detected')}
- Emotional risk indicators: {get_risk_level(float(facial_data.get('facial_risk_score', 0)))}
- The facial expressions indicate emotional state consistent with {facial_data.get('dominant_emotion', 'variable emotional presentation')}

Vocal Analysis:
- Speech tempo: {voice_data.get('tempo_bpm', 'N/A')} BPM
- Vocal pitch: {voice_data.get('avg_pitch_hz', 'N/A')} Hz
- Energy level: {voice_data.get('energy_level', 'N/A')}
- The vocal characteristics suggest {voice_data.get('interpretation', 'variable emotional state')}

Speech Content:
- Transcription: {voice_data.get('transcription', 'No transcription available')[:100]}...
- Language: {voice_data.get('language', 'en-US')}
- Risk indicators in speech: {', '.join(voice_data.get('risk_signals', ['None detected']))}

CLINICAL IMPRESSION:
Based on the multimodal analysis, {report.get('executive_summary', 'further assessment is recommended')}

CONCERNS AND OBSERVATIONS:
{chr(10).join([f"- {c.get('concern', '')}" for c in report.get('concerns', [])[:3]])}

RECOMMENDATIONS:
{chr(10).join([f"- {r.get('recommendation', '')}" for r in report.get('recommendations', [])[:3]])}

NOTE: This is an AI-generated assessment and does NOT replace professional psychological evaluation. 
Always consult with licensed mental health professionals for diagnosis and treatment.
"""
    
    return notes.strip()


def generate_executive_summary(report):
    """Generate executive summary of the report."""
    risk_level = report.get('overall_risk_level', 'UNKNOWN')
    concerns_count = len(report.get('concerns', []))
    
    if risk_level == 'CRITICAL':
        summary = f"This assessment indicates CRITICAL LEVEL CONCERNS requiring immediate professional intervention. {concerns_count} significant areas of concern identified. The individual should seek immediate mental health support."
    elif risk_level == 'HIGH':
        summary = f"This assessment indicates HIGH LEVEL CONCERNS requiring professional evaluation. {concerns_count} areas of concern identified. Recommend scheduling mental health assessment soon."
    elif risk_level == 'MEDIUM':
        summary = f"This assessment indicates MODERATE LEVEL CONCERNS. {concerns_count} areas for attention identified. Regular monitoring and self-care strategies recommended."
    else:
        summary = f"This assessment indicates LOW LEVEL CONCERNS. Current emotional and behavioral patterns appear within normal range. Continue wellness practices and regular monitoring."
    
    return summary


def generate_next_steps(risk_level, concerns):
    """Generate specific next steps based on risk level."""
    steps = []
    
    if risk_level in ['CRITICAL', 'HIGH']:
        steps = [
            "Schedule mental health professional consultation within 48-72 hours",
            "Reach out to trusted family member or friend for support",
            "If in crisis, contact national crisis hotline (US: 988 or text 'HELLO' to 741741)",
            "Prepare this report to share with healthcare provider",
            "Avoid isolation - engage in social activities or support groups"
        ]
    elif risk_level == 'MEDIUM':
        steps = [
            "Schedule mental health professional consultation within 1-2 weeks",
            "Implement recommended emotional regulation techniques",
            "Maintain daily wellness practices and monitoring",
            "Share this report with healthcare provider if available",
            "Practice self-care and social engagement regularly"
        ]
    else:
        steps = [
            "Continue current wellness practices",
            "Schedule regular self-assessments (monthly recommended)",
            "Maintain healthy lifestyle habits",
            "Reach out for support if any concerning changes occur",
            "Consider preventive mental health check-ups annually"
        ]
    
    return steps
