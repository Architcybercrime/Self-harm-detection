"""Admin router — user management and audit log endpoints (admin-only)."""
from fastapi import APIRouter, Depends, HTTPException

from shared import require_admin, get_supabase
from utils.audit_log import get_audit_logs

router = APIRouter(prefix="/api", tags=["Admin"])


# ── ENDPOINTS ────────────────────────────────────────
@router.get("/admin/audit-logs")
def admin_audit_logs(
    limit:      int = 100,
    event_type: str = None,
    username:   str = None,
    admin_user: str = Depends(require_admin),
):
    """[Admin] Fetch structured security audit logs with optional filters."""
    return get_audit_logs(limit=limit, event_type=event_type, username=username)


@router.get("/admin/users")
def admin_users(
    limit:      int = 100,
    admin_user: str = Depends(require_admin),
):
    """[Admin] List all registered users (username, role, created_at)."""
    supabase = get_supabase()
    try:
        result = supabase.table("Users")\
            .select("username, role, created_at")\
            .limit(limit)\
            .execute()
        users = result.data or []
        return {
            "success": True,
            "count":   len(users),
            "users":   users,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/analytics")
def admin_analytics(admin_user: str = Depends(require_admin)):
    """[Admin] Aggregated risk analytics for the admin dashboard."""
    supabase = get_supabase()
    try:
        rows = supabase.table("Predictions").select("*").execute().data or []
        total     = len(rows)
        high_risk = sum(1 for r in rows if r.get("risk_level") == "HIGH")
        alerts    = sum(1 for r in rows if r.get("alert"))
        avg_conf  = round(sum(r["confidence"] for r in rows) / total, 4) if total else 0

        by_modality: dict = {}
        for r in rows:
            m = r.get("modality", "unknown")
            by_modality[m] = by_modality.get(m, 0) + 1

        from collections import defaultdict
        daily: dict = defaultdict(lambda: {"total": 0, "high": 0})
        for r in rows:
            day = (r.get("created_at") or r.get("timestamp") or "")[:10]
            if day:
                daily[day]["total"] += 1
                if r.get("risk_level") == "HIGH":
                    daily[day]["high"] += 1

        return {
            "success":           True,
            "total_predictions": total,
            "high_risk_count":   high_risk,
            "alert_count":       alerts,
            "avg_confidence":    avg_conf,
            "high_risk_rate":    round(high_risk / total, 4) if total else 0,
            "by_modality":       by_modality,
            "daily_counts":      dict(sorted(daily.items())[-14:]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
