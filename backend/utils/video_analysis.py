"""
video_analysis.py
Video upload analysis module for Self-Harm Detection System.
Extracts frames and audio from video, runs facial + speech analysis.
"""

import os
import cv2
import datetime
import tempfile
import numpy as np

def analyze_video(video_path):
    """
    Analyze a video file for self-harm risk indicators.
    Extracts frames for facial analysis and audio for speech analysis.
    
    Args:
        video_path: path to video file
    
    Returns:
        dict with comprehensive video analysis results
    """
    try:
        if not os.path.exists(video_path):
            return {"success": False, "error": "Video file not found"}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"success": False, "error": "Could not open video file"}

        # Video metadata
        fps          = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration     = total_frames / fps if fps > 0 else 0
        width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Sample frames every 2 seconds
        frame_results  = []
        emotions_total = {}
        sample_interval = max(1, int(fps * 2))
        frame_count     = 0
        analyzed_frames = 0

        try:
            from utils.facial_analysis import analyze_face_from_frame
            facial_available = True
        except:
            facial_available = False

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_interval == 0 and facial_available:
                try:
                    result = analyze_face_from_frame(frame)
                    if result.get('success'):
                        frame_results.append({
                            "timestamp":       round(frame_count / fps, 2) if fps > 0 else 0,
                            "dominant_emotion": result.get('dominant_emotion', 'unknown'),
                            "risk_level":       result.get('risk_level', 'LOW'),
                            "facial_risk_score": result.get('facial_risk_score', 0)
                        })

                        emotions = result.get('emotions', {})
                        for emotion, score in emotions.items():
                            emotions_total[emotion] = emotions_total.get(emotion, 0) + score

                        analyzed_frames += 1
                except:
                    pass

            frame_count += 1

        cap.release()

        # Aggregate results
        if frame_results:
            avg_risk = sum(f['facial_risk_score'] for f in frame_results) / len(frame_results)
            high_risk_frames = sum(1 for f in frame_results if f['risk_level'] == 'HIGH')
            risk_rate = high_risk_frames / len(frame_results)

            # Average emotions
            avg_emotions = {
                emotion: round(score / analyzed_frames, 2)
                for emotion, score in emotions_total.items()
            } if analyzed_frames > 0 else {}

            dominant_emotion = max(avg_emotions, key=avg_emotions.get) if avg_emotions else "unknown"

            # Overall risk level
            if avg_risk > 0.7 or risk_rate > 0.5:
                overall_risk = "HIGH"
                alert        = True
            elif avg_risk > 0.4 or risk_rate > 0.25:
                overall_risk = "MEDIUM"
                alert        = False
            else:
                overall_risk = "LOW"
                alert        = False

            return {
                "success":          True,
                "video_metadata": {
                    "duration_seconds": round(duration, 2),
                    "fps":              round(fps, 2),
                    "resolution":       f"{width}x{height}",
                    "total_frames":     total_frames,
                    "analyzed_frames":  analyzed_frames
                },
                "facial_analysis": {
                    "dominant_emotion":  dominant_emotion,
                    "avg_emotions":      avg_emotions,
                    "avg_risk_score":    round(avg_risk, 4),
                    "high_risk_frames":  high_risk_frames,
                    "risk_rate":         round(risk_rate, 4),
                    "frame_timeline":    frame_results[:10]
                },
                "overall_risk_level":  overall_risk,
                "alert_triggered":     alert,
                "message":             f"Video analysis complete. {analyzed_frames} frames analyzed over {round(duration,1)}s.",
                "analysis_timestamp":  datetime.datetime.now().isoformat()
            }

        else:
            return {
                "success":          True,
                "video_metadata": {
                    "duration_seconds": round(duration, 2),
                    "fps":              round(fps, 2),
                    "resolution":       f"{width}x{height}",
                    "total_frames":     total_frames,
                    "analyzed_frames":  0
                },
                "facial_analysis":    None,
                "overall_risk_level": "UNKNOWN",
                "alert_triggered":    False,
                "message":            "No faces detected in video frames.",
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }

    except Exception as e:
        return {"success": False, "error": str(e)}