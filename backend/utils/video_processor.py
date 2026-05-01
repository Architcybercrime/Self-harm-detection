"""
video_processor.py
Extract audio and frames from video, run multimodal analysis, generate therapist report.
"""

import os
import cv2
import tempfile
import numpy as np
from datetime import datetime

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


def extract_audio_from_video(video_path):
    """
    Extract audio from video file.
    Returns path to extracted audio file (.wav)
    """
    if not os.path.exists(video_path):
        return None, "Video file not found"
    
    temp_audio_path = os.path.join(tempfile.gettempdir(), f"extracted_audio_{int(datetime.now().timestamp())}.wav")
    
    try:
        if MOVIEPY_AVAILABLE:
            video = VideoFileClip(video_path)
            if video.audio is None:
                return None, "Video has no audio track"
            video.audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
            video.close()
            return temp_audio_path, None
        else:
            return None, "moviepy not available - cannot extract audio"
    except Exception as e:
        return None, f"Audio extraction failed: {str(e)}"


def extract_frames_from_video(video_path, sample_interval=2):
    """
    Extract frames from video at regular intervals.
    
    Args:
        video_path: path to video
        sample_interval: seconds between frame samples
    
    Returns:
        list of (frame, timestamp) tuples
    """
    frames = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return [], "Could not open video"
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        sample_frame_interval = max(1, int(fps * sample_interval))
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % sample_frame_interval == 0:
                timestamp = frame_count / fps
                frames.append({
                    'frame': frame,
                    'timestamp': timestamp,
                    'frame_number': frame_count
                })
            
            frame_count += 1
        
        cap.release()
        return frames, None
        
    except Exception as e:
        return [], f"Frame extraction failed: {str(e)}"


def process_video_for_analysis(video_path, language="en-US"):
    """
    Full video processing pipeline: extract audio + frames, run multimodal analysis.
    
    Args:
        video_path: path to video file
        language: language code for speech recognition (e.g., 'en-US', 'hi-IN', 'pa-IN')
    
    Returns:
        dict with comprehensive multimodal analysis results
    """
    
    result = {
        "success": False,
        "video_metadata": {},
        "facial_analysis": None,
        "voice_analysis": None,
        "transcript": None,
        "error": None
    }
    
    # Validate video exists
    if not os.path.exists(video_path):
        result["error"] = "Video file not found"
        return result
    
    # Get video metadata
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        result["video_metadata"] = {
            "duration_seconds": round(duration, 2),
            "fps": round(fps, 2),
            "frame_count": total_frames,
            "resolution": f"{width}x{height}"
        }
    except Exception as e:
        result["error"] = f"Could not read video metadata: {str(e)}"
        return result
    
    # Extract audio
    audio_path, audio_error = extract_audio_from_video(video_path)
    if audio_error:
        result["error"] = f"Audio extraction failed: {audio_error}"
        return result
    
    # Analyze audio (voice analysis)
    try:
        from utils.speech_analysis import analyze_audio_file
        voice_analysis = analyze_audio_file(audio_path, language=language)
        result["voice_analysis"] = voice_analysis
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        result["error"] = f"Voice analysis failed: {str(e)}"
        return result
    
    # Extract frames and analyze faces
    frames, frame_error = extract_frames_from_video(video_path, sample_interval=2)
    if frame_error:
        result["error"] = f"Frame extraction failed: {frame_error}"
        return result
    
    # Analyze facial expressions from sampled frames
    facial_results = []
    emotions_aggregate = {}
    
    try:
        from utils.facial_analysis import analyze_face_from_file
        import base64
        
        for i, frame_data in enumerate(frames[:10]):  # Analyze up to 10 frames to save time
            # Save frame temporarily
            temp_frame_path = os.path.join(tempfile.gettempdir(), f"frame_{i}_{int(datetime.now().timestamp())}.jpg")
            cv2.imwrite(temp_frame_path, frame_data['frame'])
            
            # Analyze face
            facial_result = analyze_face_from_file(temp_frame_path)
            if facial_result.get('success'):
                facial_results.append({
                    'timestamp': frame_data['timestamp'],
                    'dominant_emotion': facial_result.get('dominant_emotion'),
                    'emotions': facial_result.get('emotions'),
                    'facial_risk_score': facial_result.get('facial_risk_score')
                })
                
                # Aggregate emotions
                for emotion, score in facial_result.get('emotions', {}).items():
                    emotions_aggregate[emotion] = emotions_aggregate.get(emotion, 0) + score
            
            # Clean up
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
        
        # Average emotions
        if facial_results:
            for emotion in emotions_aggregate:
                emotions_aggregate[emotion] /= len(facial_results)
        
        # Determine dominant emotion
        dominant_emotion = max(emotions_aggregate, key=emotions_aggregate.get) if emotions_aggregate else "neutral"
        
        # Calculate average facial risk
        avg_facial_risk = np.mean([f.get('facial_risk_score', 0) for f in facial_results]) if facial_results else 0.2
        
        result["facial_analysis"] = {
            "frames_analyzed": len(facial_results),
            "dominant_emotion": dominant_emotion,
            "emotions_average": emotions_aggregate,
            "facial_risk_score": float(avg_facial_risk),
            "risk_level": get_facial_risk_level(avg_facial_risk),
            "frame_details": facial_results
        }
        
    except Exception as e:
        result["error"] = f"Facial analysis failed: {str(e)}"
        return result
    
    result["success"] = True
    return result


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
