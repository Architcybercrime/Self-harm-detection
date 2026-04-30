"""
audit_log.py
Structured security-event audit logging to Supabase.

Events logged:
  LOGIN_SUCCESS, LOGIN_FAILURE, REGISTER_SUCCESS, REGISTER_FAILURE,
  LOGOUT, MFA_SETUP, MFA_ENABLED, MFA_DISABLED, MFA_FAILURE,
  API_KEY_GENERATED, API_KEY_REVOKED,
  PREDICTION_MADE, HIGH_RISK_ALERT,
  ADMIN_ACCESS, UNAUTHORIZED_ACCESS
"""

import os
import datetime
import traceback
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        _supabase = None
else:
    _supabase = None


def log_event(
    event_type: str,
    username: str = None,
    ip_address: str = None,
    details: dict = None,
    success: bool = True,
    severity: str = "INFO",
):
    """
    Write one audit-log row to Supabase AuditLogs table.

    severity: INFO | WARNING | CRITICAL
    """
    entry = {
        "event_type":  event_type,
        "username":    username,
        "ip_address":  ip_address,
        "details":     details or {},
        "success":     success,
        "severity":    severity,
        "timestamp":   datetime.datetime.utcnow().isoformat(),
    }

    if _supabase:
        try:
            _supabase.table("AuditLogs").insert(entry).execute()
        except Exception:
            # Never let audit-log failure crash the main request
            pass

    return entry


# ── Convenience wrappers ──────────────────────────────

def log_login_success(username: str, ip: str = None):
    log_event("LOGIN_SUCCESS", username=username, ip_address=ip, success=True)


def log_login_failure(username: str, ip: str = None, reason: str = "bad credentials"):
    log_event("LOGIN_FAILURE", username=username, ip_address=ip,
              details={"reason": reason}, success=False, severity="WARNING")


def log_register(username: str, ip: str = None, success: bool = True, reason: str = None):
    event = "REGISTER_SUCCESS" if success else "REGISTER_FAILURE"
    log_event(event, username=username, ip_address=ip,
              details={"reason": reason} if reason else {},
              success=success,
              severity="INFO" if success else "WARNING")


def log_mfa_event(event_type: str, username: str, ip: str = None, success: bool = True):
    severity = "INFO" if success else "WARNING"
    log_event(event_type, username=username, ip_address=ip,
              success=success, severity=severity)


def log_prediction(username: str, risk_level: str, modality: str,
                   confidence: float, ip: str = None):
    severity = "CRITICAL" if risk_level == "HIGH" else "INFO"
    event    = "HIGH_RISK_ALERT" if risk_level == "HIGH" else "PREDICTION_MADE"
    log_event(event, username=username, ip_address=ip,
              details={"risk_level": risk_level, "modality": modality,
                       "confidence": confidence},
              success=True, severity=severity)


def log_api_key_event(event_type: str, username: str, ip: str = None):
    log_event(event_type, username=username, ip_address=ip, success=True)


def log_unauthorized(username: str = None, ip: str = None, endpoint: str = None):
    log_event("UNAUTHORIZED_ACCESS", username=username, ip_address=ip,
              details={"endpoint": endpoint}, success=False, severity="WARNING")


def get_audit_logs(limit: int = 100, event_type: str = None, username: str = None):
    """Fetch audit logs from Supabase (admin use)."""
    if not _supabase:
        return {"success": True, "data": [], "count": 0}
    try:
        q = _supabase.table("AuditLogs").select("*").order("timestamp", desc=True)
        if event_type:
            q = q.eq("event_type", event_type)
        if username:
            q = q.eq("username", username)
        result = q.limit(limit).execute()
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        return {"success": False, "error": str(e)}
