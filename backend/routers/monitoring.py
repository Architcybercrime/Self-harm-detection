"""Monitoring router — stats, history, monitoring report, DB stats, and alerts."""
import datetime

from fastapi import APIRouter, Depends, HTTPException

from shared import verify_token
from utils.monitor import get_monitoring_report
from utils.database import get_stats as db_get_stats, get_recent_predictions

router = APIRouter(prefix="/api", tags=["Monitoring"])


# ── ENDPOINTS ────────────────────────────────────────
@router.get("/stats", tags=["Statistics"])
def stats(current_user: str = Depends(verify_token)):
    """Get session-level prediction statistics from the in-memory log."""
    from ml_engine import prediction_log
    if not prediction_log:
        return {"message": "No predictions yet"}

    total  = len(prediction_log)
    alerts = sum(1 for p in prediction_log if p['risk_level'] == 'HIGH')
    return {
        "total_predictions": total,
        "alerts_triggered":  alerts,
        "alert_rate":        round(alerts / total, 4),
        "recent":            prediction_log[-5:]
    }


@router.get("/history", tags=["Database"])
def history(current_user: str = Depends(verify_token)):
    """Get the 20 most recent predictions from the Supabase database."""
    return get_recent_predictions(20)


@router.get("/monitor")
def monitor(current_user: str = Depends(verify_token)):
    """Get the model monitoring and drift detection report."""
    return get_monitoring_report()


@router.get("/db-stats", tags=["Database"])
def db_stats(current_user: str = Depends(verify_token)):
    """Get aggregated database statistics from Supabase."""
    return db_get_stats()
