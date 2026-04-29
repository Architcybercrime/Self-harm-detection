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


def analyze_text_risk_from_speech(text):
    """
    Analyze transcribed text for self-harm risk using keywords.
    Returns text-based risk score (0-1).
    """
    if not text or text.startswith("Could not") or text.startswith("Speech recognition"):
        return 0.0, "NO_TEXT", []
    
    text_lower = text.lower()
    
    # CRITICAL keywords
    critical = ['kill myself', 'kill me', 'end my life', 'want to die', 'suicide', 
                'end it all', 'not worth living', 'better off dead']
    # HIGH risk keywords
    high = ['hopeless', 'worthless', 'useless', 'burden', 'give up', 'no point', 
            'pointless', 'meaningless', 'trapped', 'suffering', 'no escape', 'helpless']
    # MEDIUM risk keywords
    medium = ['sad', 'lonely', 'tired', 'exhausted', 'anxious', 'panic', 'afraid', 
              'broken', 'numb', 'empty', 'lost', 'stressed']
    
    found_signals = []
    critical_count = sum(1 for kw in critical if kw in text_lower)
    high_count = sum(1 for kw in high if kw in text_lower)
    medium_count = sum(1 for kw in medium if kw in text_lower)
    
    if critical_count > 0:
        found_signals.extend([kw for kw in critical if kw in text_lower])
    if high_count > 0:
        found_signals.extend([kw for kw in high if kw in text_lower])
    
    # Calculate text-based risk
    if critical_count >= 1 or high_count >= 2:
        text_risk = min(0.95, 0.75 + (critical_count * 0.15))
        text_level = "HIGH"
    elif high_count >= 1 or medium_count >= 2:
        text_risk = min(0.70, 0.50 + (high_count * 0.15))
        text_level = "MEDIUM"
    else:
        text_risk = 0.2 + (medium_count * 0.08)
        text_level = "LOW"
    
    return float(np.clip(text_risk, 0, 1)), text_level, found_signals[:3]


def analyze_audio_file(audio_path, language="en-US"):
    """
    Analyze audio file for speech features AND transcribed text risk.
    Supports multilingual transcription: en-US, hi-IN (Hindi), pa-IN (Punjabi), etc.
    """
    if not LIBROSA_AVAILABLE:
        return {"error": "librosa not installed"}

    try:
        y, sample_rate = librosa.load(audio_path, sr=None)

        tempo      = extract_tempo(y, sample_rate)
        pitch      = extract_pitch(y, sample_rate)
        energy     = extract_energy(y)
        mfcc_score = extract_mfcc_features(y, sample_rate)
        acoustic_risk = calculate_speech_risk(tempo, pitch, energy)

        result = {
            "success":           True,
            "tempo_bpm":         round(float(tempo), 2),
            "avg_pitch_hz":      round(float(pitch), 2),
            "energy_level":      round(float(energy), 4),
            "mfcc_variance":     round(float(mfcc_score), 4),
            "acoustic_risk_score": round(float(acoustic_risk), 4),
            "acoustic_risk_level": get_speech_risk_level(acoustic_risk),
            "interpretation":    interpret_speech(tempo, pitch, energy),
            "language":          language
        }

        # Transcribe and analyze text in specified language
        transcription = ""
        if SR_AVAILABLE:
            transcription = transcribe_audio(audio_path, language=language)
            result["transcription"] = transcription
            
            text_risk, text_level, signals = analyze_text_risk_from_speech(transcription)
            result["text_risk_score"] = round(float(text_risk), 4)
            result["text_risk_level"] = text_level
            result["risk_signals"] = signals
            
            # Combine acoustic + text risk (60% acoustic, 40% text)
            combined_risk = (acoustic_risk * 0.6) + (text_risk * 0.4)
            result["speech_risk_score"] = round(float(combined_risk), 4)
            result["risk_level"] = get_speech_risk_level(combined_risk)
            result["risk_source"] = "acoustic + semantic"
        else:
            # Fallback: use acoustic alone
            result["speech_risk_score"] = round(float(acoustic_risk), 4)
            result["risk_level"] = get_speech_risk_level(acoustic_risk)
            result["risk_source"] = "acoustic only"

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


def transcribe_audio(audio_path, language="en-US"):
    """
    Convert speech to text using Google Speech Recognition.
    Supports multiple languages: en-US, hi-IN (Hindi), pa-IN (Punjabi), etc.
    """
    if not SR_AVAILABLE:
        return "Speech recognition not available"

    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.listen(source)
            # Google Speech Recognition API supports language codes
            text = recognizer.recognize_google(audio, language=language)
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