"""
speech_analysis.py
Speech and audio analysis for self-harm risk detection.
Analyzes tone, pitch, speaking speed from audio input.
"""

import os
import numpy as np

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


def analyze_audio_file(audio_path):
    """Analyze audio file for speech features."""
    if not LIBROSA_AVAILABLE:
        return {"error": "librosa not installed"}

    try:
        y, sample_rate = librosa.load(audio_path, sr=None)

        tempo      = extract_tempo(y, sample_rate)
        pitch      = extract_pitch(y, sample_rate)
        energy     = extract_energy(y)
        mfcc_score = extract_mfcc_features(y, sample_rate)
        risk_score = calculate_speech_risk(tempo, pitch, energy)

        result = {
            "success":           True,
            "tempo_bpm":         round(float(tempo), 2),
            "avg_pitch_hz":      round(float(pitch), 2),
            "energy_level":      round(float(energy), 4),
            "mfcc_variance":     round(float(mfcc_score), 4),
            "speech_risk_score": round(float(risk_score), 4),
            "risk_level":        get_speech_risk_level(risk_score),
            "interpretation":    interpret_speech(tempo, pitch, energy)
        }

        if SR_AVAILABLE:
            transcription = transcribe_audio(audio_path)
            result["transcription"] = transcription

        return result

    except Exception as e:
        return {"error": str(e), "success": False}


def extract_tempo(y, sr):
    """Extract speaking tempo/pace."""
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return float(tempo) if tempo else 0.0
    except:
        return 0.0


def extract_pitch(y, sr):
    """Extract average pitch frequency."""
    try:
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        if len(pitch_values) > 0:
            return float(np.mean(pitch_values[pitch_values > 0]))
        return 0.0
    except:
        return 0.0


def extract_energy(y):
    """Extract RMS energy (volume/intensity)."""
    try:
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    except:
        return 0.0


def extract_mfcc_features(y, sr):
    """Extract MFCC variance — measures emotional expressiveness."""
    try:
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        return float(np.mean(np.var(mfccs, axis=1)))
    except:
        return 0.0


def calculate_speech_risk(tempo, pitch, energy):
    """
    Calculate speech-based risk score.
    Clinical indicators:
    - Very slow tempo = flat affect
    - Low pitch = monotone voice
    - Low energy = withdrawn
    """
    risk = 0.0

    if tempo < 60:
        risk += 0.35
    elif tempo < 80:
        risk += 0.20
    elif tempo > 140:
        risk += 0.10

    if pitch < 100:
        risk += 0.30
    elif pitch < 150:
        risk += 0.15

    if energy < 0.01:
        risk += 0.35
    elif energy < 0.03:
        risk += 0.20

    return float(np.clip(risk, 0, 1))


def get_speech_risk_level(score):
    """Convert speech risk score to risk level."""
    if score < 0.2:
        return "LOW"
    elif score < 0.4:
        return "MEDIUM"
    elif score < 0.6:
        return "HIGH"
    else:
        return "CRITICAL"


def interpret_speech(tempo, pitch, energy):
    """Generate human readable interpretation."""
    notes = []

    if tempo < 60:
        notes.append("Very slow speaking pace detected")
    elif tempo > 140:
        notes.append("Rapid speaking pace detected")
    else:
        notes.append("Normal speaking pace")

    if pitch < 100:
        notes.append("Monotone/flat voice detected")
    else:
        notes.append("Normal pitch variation")

    if energy < 0.01:
        notes.append("Very low vocal energy - withdrawn pattern")
    elif energy < 0.03:
        notes.append("Below average vocal energy")
    else:
        notes.append("Normal vocal energy")

    return " | ".join(notes)


def transcribe_audio(audio_path):
    """Convert speech to text using Google Speech Recognition."""
    if not SR_AVAILABLE:
        return "Speech recognition not available"

    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Speech recognition service unavailable"
    except Exception as e:
        return f"Transcription error: {str(e)}"


def record_from_microphone(duration=5):
    """Record audio from microphone for given duration."""
    if not SR_AVAILABLE:
        return {"error": "SpeechRecognition not installed"}

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Recording for {duration} seconds... SPEAK NOW!")
            audio = recognizer.record(source, duration=duration)

        print("Recording done! Analyzing...")

        # Save to temp file
        temp_path = "temp_audio.wav"
        with open(temp_path, "wb") as f:
            f.write(audio.get_wav_data())

        # Analyze with librosa
        result = analyze_audio_file(temp_path)

        # Try transcription
        try:
            text = recognizer.recognize_google(audio)
            result["transcription"] = text
        except:
            result["transcription"] = "Could not transcribe"

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result

    except Exception as e:
        return {"error": str(e), "success": False}


# ── TEST ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Speech Analysis Module")
    print(f"Librosa available          : {LIBROSA_AVAILABLE}")
    print(f"SpeechRecognition available: {SR_AVAILABLE}")
    print("\nModule loaded successfully!")
    print("To test: call record_from_microphone() or analyze_audio_file('audio.wav')")