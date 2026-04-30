"""Prediction router — text analysis, multimodal fusion, report generation, and batch CSV."""
import os
import io
import csv
import uuid
import shutil
import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict

from shared import verify_token, sanitize_output, get_client_ip, get_supabase
from utils.monitor import log_prediction
from utils.database import save_prediction
from utils.audit_log import log_prediction as audit_prediction
from utils.alerts import dispatch_high_risk_alert
from utils.fusion import fuse_risk_scores
from utils.facial_analysis import capture_webcam_frame
from utils.speech_analysis import record_from_microphone

router = APIRouter(prefix="/api", tags=["Prediction"])

# Injected by main.py after sio is created
sio = None


# ── PYDANTIC MODELS ──────────────────────────────────
class TextInput(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000,
                      description="Text to analyze for self-harm risk")

    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace')
        return v.strip()


class MultimodalInput(BaseModel):
    text:           Optional[str]  = None
    use_webcam:     Optional[bool] = False
    use_microphone: Optional[bool] = False
    duration:       Optional[int]  = Field(5, ge=1, le=30)
    weights:        Optional[Dict] = None


# ── ENDPOINTS ────────────────────────────────────────
@router.post("/predict")
async def predict(data: TextInput, request: Request,
                  current_user: str = Depends(verify_token)):
    """Predict self-harm risk from text (92.2% accuracy)."""
    from main import run_prediction, prediction_log
    result = run_prediction(data.text)
    ip     = get_client_ip(request)

    prediction_log.append({
        "timestamp":  datetime.datetime.now().isoformat(),
        "risk_level": result['risk_level'],
        "confidence": result['confidence']
    })

    log_prediction(len(data.text.split()), result['risk_level'],
                   result['confidence'], result['sentiment_score'])
    save_prediction(data.text, result['risk_level'], result['confidence'],
                    result['sentiment_score'], "text", result['alert_triggered'])
    audit_prediction(current_user, result['risk_level'], "text",
                     result['confidence'], ip=ip)

    result["text"] = sanitize_output(data.text)

    if result['alert_triggered']:
        if sio:
            await sio.emit('high_risk_alert', {
                "risk_level": result['risk_level'],
                "confidence": result['confidence'],
                "message":    result['message'],
                "timestamp":  datetime.datetime.now().isoformat()
            })
        try:
            supabase  = get_supabase()
            prof_res  = supabase.table("UserProfiles")\
                .select("*").eq("username", current_user).execute()
            profile   = prof_res.data[0] if prof_res.data else None
            dispatch_high_risk_alert(
                username=current_user,
                confidence=result['confidence'],
                modality="text",
                text_snippet=data.text[:200],
                profile=profile,
            )
        except Exception:
            pass

    return result


@router.post("/generate-report", tags=["Report"])
async def generate_report_endpoint(data: TextInput,
                                    current_user: str = Depends(verify_token)):
    """Generate a professional psychological risk assessment PDF report."""
    from utils.report_generator import generate_report as gen_report
    from main import run_prediction

    prediction_data = run_prediction(data.text)
    prediction_data['analysis_timestamp'] = datetime.datetime.now().isoformat()

    report_id = str(uuid.uuid4())[:8].upper()
    filepath  = gen_report(prediction_data,
                            username=current_user,
                            report_id=report_id)

    return FileResponse(
        filepath,
        media_type = "application/pdf",
        filename   = f"risk_assessment_{report_id}.pdf",
        headers    = {
            "Content-Disposition": f"attachment; filename=risk_assessment_{report_id}.pdf"
        }
    )


@router.post("/predict-multimodal")
async def predict_multimodal(data: MultimodalInput,
                              current_user: str = Depends(verify_token)):
    """Combined multimodal risk prediction (text + face + speech)."""
    from main import run_prediction, prediction_log
    text_result = face_result = speech_result = None
    text = ""

    if data.text:
        text        = data.text.strip()
        text_result = run_prediction(text)
        text_result = {
            "risk_level": text_result['risk_level'],
            "confidence": text_result['confidence']
        }

    if data.use_webcam:
        face_result = capture_webcam_frame()

    if data.use_microphone:
        speech_result = record_from_microphone(data.duration)

    final_result = fuse_risk_scores(
        text_result=text_result,
        face_result=face_result,
        speech_result=speech_result,
        custom_weights=data.weights
    )

    if 'risk_level' in final_result:
        prediction_log.append({
            "timestamp":  datetime.datetime.now().isoformat(),
            "risk_level": final_result['risk_level'],
            "confidence": final_result['final_risk_score'],
            "multimodal": True
        })
        save_prediction(text, final_result['risk_level'],
                        final_result['final_risk_score'], 0.0,
                        "multimodal", final_result['alert_triggered'])

        if final_result['alert_triggered'] and sio:
            await sio.emit('high_risk_alert', {
                "risk_level": final_result['risk_level'],
                "confidence": final_result['final_risk_score'],
                "modality":   "multimodal",
                "timestamp":  datetime.datetime.now().isoformat()
            })

    return final_result


@router.post("/predict-batch")
async def predict_batch(
    current_user: str = Depends(verify_token),
    file: UploadFile = File(...),
):
    """Batch risk analysis from a CSV file (max 500 rows). CSV must have a 'text' column."""
    from main import run_prediction

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        decoded = content.decode('latin-1')

    reader     = csv.DictReader(io.StringIO(decoded))
    fieldnames = reader.fieldnames or []
    text_col   = 'text' if 'text' in fieldnames else (fieldnames[0] if fieldnames else None)

    if not text_col:
        raise HTTPException(status_code=400, detail="CSV must have at least one column")

    results = []
    for i, row in enumerate(reader):
        if i >= 500:
            break
        text = (row.get(text_col) or "").strip()
        if not text:
            results.append({"row": i + 1, "text": "", "error": "empty"})
            continue
        try:
            r = run_prediction(text)
            results.append({
                "row":        i + 1,
                "text":       text[:100],
                "risk_level": r["risk_level"],
                "confidence": r["confidence"],
                "alert":      r["alert_triggered"],
            })
        except Exception as e:
            results.append({"row": i + 1, "text": text[:100], "error": str(e)})

    high_count = sum(1 for r in results if r.get("risk_level") == "HIGH")
    return {
        "success":        True,
        "total_rows":     len(results),
        "high_risk_rows": high_count,
        "results":        results,
    }
