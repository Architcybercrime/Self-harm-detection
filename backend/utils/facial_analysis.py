"""
facial_analysis.py
Facial expression analysis using DeepFace.
Extracts emotion scores from images/webcam frames.
"""

import numpy as np
import cv2
import base64
import os

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("DeepFace not available")


def analyze_face_from_file(image_path):
    """Analyze facial expressions from an image file."""
    if not DEEPFACE_AVAILABLE:
        return {"error": "DeepFace not installed"}

    try:
        result = DeepFace.analyze(
            image_path,
            actions=['emotion'],
            enforce_detection=False
        )

        emotions = result[0]['emotion']
        dominant = result[0]['dominant_emotion']

        risk_score = calculate_facial_risk(emotions)

        return {
            "success":           True,
            "dominant_emotion":  dominant,
            "emotions":          {k: round(float(v), 2) for k, v in emotions.items()},
            "facial_risk_score": round(float(risk_score), 4),
            "risk_level":        get_facial_risk_level(risk_score)
        }

    except Exception as e:
        return {"error": str(e), "success": False}


def analyze_face_from_base64(base64_string):
    """Analyze facial expressions from base64 encoded image."""
    if not DEEPFACE_AVAILABLE:
        return {"error": "DeepFace not installed"}

    try:
        img_data = base64.b64decode(base64_string)
        nparr    = np.frombuffer(img_data, np.uint8)
        img      = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        temp_path = 'temp_face.jpg'
        cv2.imwrite(temp_path, img)

        result = analyze_face_from_file(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result

    except Exception as e:
        return {"error": str(e), "success": False}


def calculate_facial_risk(emotions):
    """
    Calculate risk score from emotion probabilities.
    Higher sad + fear + disgust = higher risk.
    """
    risk_weights = {
        'sad':      0.35,
        'fear':     0.25,
        'angry':    0.15,
        'disgust':  0.10,
        'neutral':  0.05,
        'surprise': 0.05,
        'happy':   -0.30
    }

    score = 0
    for emotion, weight in risk_weights.items():
        score += (float(emotions.get(emotion, 0)) / 100) * weight

    return float(np.clip(score, 0, 1))


def get_facial_risk_level(score):
    """Convert facial risk score to risk level."""
    if score < 0.2:
        return "LOW"
    elif score < 0.4:
        return "MEDIUM"
    elif score < 0.6:
        return "HIGH"
    else:
        return "CRITICAL"


def capture_webcam_frame():
    """Capture a single frame from webcam and analyze it."""
    if not DEEPFACE_AVAILABLE:
        return {"error": "DeepFace not installed"}

    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"error": "Could not access webcam"}

        temp_path = 'temp_webcam.jpg'
        cv2.imwrite(temp_path, frame)

        result = analyze_face_from_file(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result

    except Exception as e:
        return {"error": str(e), "success": False}


# ── TEST ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing facial analysis module...")
    print(f"DeepFace available: {DEEPFACE_AVAILABLE}")

    test_image = "test_face.jpg"
    if os.path.exists(test_image):
        result = analyze_face_from_file(test_image)
        print(f"Result: {result}")
    else:
        print("No test image found.")
        print("To test: place a face image as 'test_face.jpg' and run again")
        print("Module loaded successfully!")