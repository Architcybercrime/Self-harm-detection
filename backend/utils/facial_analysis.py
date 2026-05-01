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


def analyze_face_fallback(image_path):
    """Lightweight fallback when DeepFace is unavailable."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Could not read image", "success": False}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

        roi = gray
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            roi = gray[y:y + h, x:x + w]

        brightness = float(np.mean(roi))
        contrast = float(np.std(roi))
        edges = cv2.Canny(roi, 80, 160)
        edge_density = float(np.count_nonzero(edges)) / float(roi.size or 1)

        emotions = {
            "neutral": 35.0,
            "sad": 15.0 + max(0.0, (120.0 - brightness) / 4.0),
            "fear": 10.0 + max(0.0, contrast / 3.0),
            "angry": 8.0 + max(0.0, edge_density * 120.0),
            "disgust": 5.0,
            "surprise": 8.0,
            "happy": max(5.0, 28.0 - max(0.0, (120.0 - brightness) / 5.0)),
        }

        total = sum(emotions.values()) or 1.0
        emotions = {key: round((value / total) * 100.0, 2) for key, value in emotions.items()}
        dominant = max(emotions, key=emotions.get)
        risk_score = calculate_facial_risk(emotions)

        return {
            "success": True,
            "dominant_emotion": dominant,
            "emotions": emotions,
            "facial_risk_score": round(float(risk_score), 4),
            "risk_level": get_facial_risk_level(risk_score),
            "fallback": True,
        }

    except Exception as e:
        return {"error": str(e), "success": False}


def analyze_face_from_file(image_path):
    """Analyze facial expressions from an image file."""
    if not DEEPFACE_AVAILABLE:
        return analyze_face_fallback(image_path)

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

    except Exception:
        return analyze_face_fallback(image_path)


def analyze_face_from_base64(base64_string):
    """Analyze facial expressions from base64 encoded image."""
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