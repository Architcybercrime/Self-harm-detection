"""
database.py
Supabase database integration for persistent storage
of predictions and monitoring data.
"""

from supabase import create_client
import os
from dotenv import load_dotenv

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('D:\\selfharm-project\\backend\\.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_prediction(text_input, risk_level, confidence, sentiment, modality, alert):
    """Save a prediction to Supabase database."""
    try:
        data = {
            "text_input":  text_input[:500] if text_input else "",
            "risk_level":  risk_level,
            "confidence":  float(confidence),
            "sentiment":   float(sentiment),
            "modality":    modality,
            "alert":       bool(alert)
        }
        result = supabase.table("Predictions").insert(data).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_all_predictions(limit=100):
    """Get all predictions from database."""
    try:
        result = supabase.table("Predictions")\
            .select("*")\
            .order("id", desc=True)\
            .limit(limit)\
            .execute()
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_stats():
    """Get prediction statistics from database."""
    try:
        all_data = supabase.table("Predictions").select("*").execute()
        records  = all_data.data

        if not records:
            return {"success": True, "message": "No predictions yet"}

        total      = len(records)
        high_risk  = sum(1 for r in records if r['risk_level'] == 'HIGH')
        alerts     = sum(1 for r in records if r['alert'])
        avg_conf   = sum(r['confidence'] for r in records) / total

        return {
            "success":           True,
            "total_predictions": total,
            "high_risk_count":   high_risk,
            "alert_count":       alerts,
            "high_risk_rate":    round(high_risk / total, 4),
            "avg_confidence":    round(avg_conf, 4)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_recent_predictions(limit=10):
    """Get most recent predictions."""
    try:
        result = supabase.table("Predictions")\
            .select("*")\
            .order("id", desc=True)\
            .limit(limit)\
            .execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── TEST ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Supabase connection...")
    test = save_prediction(
        text_input  = "Test prediction",
        risk_level  = "LOW",
        confidence  = 0.85,
        sentiment   = 0.1,
        modality    = "text",
        alert       = False
    )
    print(f"Save result: {test}")

    stats = get_stats()
    print(f"Stats: {stats}")