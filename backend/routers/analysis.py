"""Analysis router — facial, speech, and video analysis endpoints."""
import os
import uuid
import shutil
import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional

from shared import verify_token, get_supabase
from utils.facial_analysis import analyze_face_from_base64, capture_webcam_frame
from utils.speech_analysis import analyze_audio_file, record_from_microphone
from utils.database import save_prediction

router = APIRouter(prefix="/api", tags=["Multimodal"])

# Injected by main.py after sio is created
sio = None


# ── PYDANTIC MODELS ──────────────────────────────────
class FaceInput(BaseModel):
    use_webcam:   Optional[bool] = False
    image_base64: Optional[str]  = None


class SpeechInput(BaseModel):
    use_microphone: Optional[bool] = False
    audio_path:     Optional[str]  = None
    duration:       Optional[int]  = Field(5, ge=1, le=30)


# ── ENDPOINTS ────────────────────────────────────────
@router.post("/analyze-face")
def analyze_face(data: FaceInput,
                 current_user: str = Depends(verify_token)):
    """Analyze facial expressions via webcam capture or a base64-encoded image."""
    if data.image_base64:
        return analyze_face_from_base64(data.image_base64)
    if data.use_webcam:
        return capture_webcam_frame()
    raise HTTPException(status_code=400,
                        detail="Provide image_base64 or use_webcam:true")


@router.post("/analyze-speech")
def analyze_speech(data: SpeechInput,
                   current_user: str = Depends(verify_token)):
    """Analyze speech risk from a local audio file path or live microphone recording."""
    if data.audio_path:
        return analyze_audio_file(data.audio_path)
    if data.use_microphone:
        return record_from_microphone(data.duration)
    raise HTTPException(status_code=400,
                        detail="Provide audio_path or use_microphone:true")


@router.post("/analyze-speech-upload")
async def analyze_speech_upload(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...)
):
    """Analyze a browser-recorded audio file uploaded from the frontend."""
    suffix    = os.path.splitext(file.filename or "upload.webm")[1] or ".webm"
    temp_path = f"temp_voice_{uuid.uuid4().hex[:8]}{suffix}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyze_audio_file(temp_path)
        if isinstance(result, dict):
            result["uploaded_from_browser"] = True
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/analyze-video")
async def analyze_video_endpoint(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...)
):
    """Upload and analyze a video file for self-harm risk indicators."""
    from utils.video_analysis import analyze_video

    allowed_types = [
        'video/mp4', 'video/avi', 'video/quicktime',
        'video/x-msvideo', 'video/x-matroska', 'video/webm'
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Use MP4, AVI, MOV, MKV or WEBM"
        )

    temp_path = f"temp_video_{uuid.uuid4().hex[:8]}.mp4"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = analyze_video(temp_path)

        if result.get('success') and result.get('overall_risk_level') != 'UNKNOWN':
            save_prediction(
                text_input = f"Video: {file.filename}",
                risk_level = result.get('overall_risk_level', 'LOW'),
                confidence = result.get('facial_analysis', {}).get('avg_risk_score', 0),
                sentiment  = 0.0,
                modality   = "video",
                alert      = result.get('alert_triggered', False)
            )

            if result.get('alert_triggered') and sio:
                await sio.emit('high_risk_alert', {
                    "risk_level": result.get('overall_risk_level'),
                    "modality":   "video",
                    "message":    "High risk detected in video analysis",
                    "timestamp":  datetime.datetime.now().isoformat()
                })

        return result

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
