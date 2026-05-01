"""Authentication router — registration, login, demo token, profile, and MFA endpoints."""
import os
import io
import base64
import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jose import jwt
from pydantic import BaseModel, Field, validator
from typing import Optional

from shared import (
    verify_token,
    get_supabase,
    JWT_SECRET,
    JWT_ALGORITHM,
    get_client_ip,
)
from utils.auth import register_user, login_user
from utils.audit_log import log_mfa_event

router = APIRouter(prefix="/api", tags=["Authentication"])


# ── PYDANTIC MODELS ──────────────────────────────────
class RegisterInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

    @validator('username')
    def username_alphanumeric(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers and underscores')
        return v


class LoginInput(BaseModel):
    username: str
    password: str


class MFAVerifyInput(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)


class MFALoginInput(BaseModel):
    username:  str
    password:  str
    totp_code: str = Field(..., min_length=6, max_length=6)


class UserProfileInput(BaseModel):
    display_name:    Optional[str] = None
    alert_email:     Optional[str] = None
    alert_phone:     Optional[str] = None
    alert_whatsapp:  Optional[str] = None
    email_alerts:    Optional[bool] = None
    sms_alerts:      Optional[bool] = None
    whatsapp_alerts: Optional[bool] = None


# ── HELPER ───────────────────────────────────────────
def _get_totp_secret(username: str):
    """Return the active TOTP row for a user, or None.

    Args:
        username: The username to look up.

    Returns:
        dict | None: Row with ``totp_secret`` and ``is_enabled``, or ``None``.
    """
    supabase = get_supabase()
    try:
        res = supabase.table("UserMFA")\
            .select("totp_secret, is_enabled")\
            .eq("username", username)\
            .execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None


# ── ENDPOINTS ────────────────────────────────────────
@router.post("/register", status_code=201)
def register(data: RegisterInput):
    """Register a new user account."""
    result = register_user(data.username, data.password)
    if result['success']:
        return result
    raise HTTPException(status_code=400, detail=result['error'])


@router.post("/login")
def login(data: LoginInput):
    """Login and get a JWT token. Returns mfa_required=true if MFA is enabled."""
    result = login_user(data.username, data.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['error'])

    row = _get_totp_secret(data.username)
    if row and row.get("is_enabled"):
        return {
            "success":      True,
            "mfa_required": True,
            "username":     data.username,
            "message":      "MFA required — call POST /api/auth/mfa/login with your TOTP code",
        }

    return result


@router.get("/demo-token")
def demo_token():
    """Issue a short-lived JWT for anonymous demo visitors. Valid for 2 hours."""
    token = jwt.encode(
        {
            "sub":  "demo_visitor",
            "role": "demo",
            "iat":  datetime.datetime.utcnow(),
            "exp":  datetime.datetime.utcnow() + datetime.timedelta(hours=2),
            "type": "demo",
            "jti":  secrets.token_hex(8),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {
        "success":      True,
        "access_token": token,
        "username":     "demo_visitor",
        "role":         "demo",
        "expires_in":   "2 hours",
        "message":      "Demo token issued. Valid for 2 hours — no account needed.",
    }


@router.get("/cors-check", tags=["Health"])
def cors_check(request: Request):
    """Explicit CORS verification endpoint — confirms CORS is active."""
    import os
    _cors_env = os.getenv("ALLOWED_ORIGINS", "")
    _allowed  = [o.strip() for o in _cors_env.split(",") if o.strip()] or ["*"]
    origin    = request.headers.get("origin", "no-origin-header")
    return JSONResponse(
        content={
            "cors":    "enabled",
            "origin":  origin,
            "allowed": _allowed,
            "headers": {
                "Access-Control-Allow-Origin":  origin if origin in _allowed else "*",
                "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        },
        headers={
            "Access-Control-Allow-Origin":  origin if origin in _allowed else "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


@router.get("/profile")
def profile(current_user: str = Depends(verify_token)):
    """Get the current user's basic profile."""
    return {
        "username": current_user,
        "message":  f"Welcome {current_user}!",
        "role":     "user"
    }


@router.get("/user/profile")
def get_user_profile(current_user: str = Depends(verify_token)):
    """Get user alert preferences and profile from the database."""
    supabase = get_supabase()
    try:
        res = supabase.table("UserProfiles")\
            .select("*").eq("username", current_user).execute()
        if res.data:
            return {"success": True, "profile": res.data[0]}
        return {"success": True, "profile": {
            "username":        current_user,
            "display_name":    None,
            "alert_email":     None,
            "alert_phone":     None,
            "alert_whatsapp":  None,
            "email_alerts":    False,
            "sms_alerts":      False,
            "whatsapp_alerts": False,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/user/profile")
def update_user_profile(data: UserProfileInput,
                        current_user: str = Depends(verify_token)):
    """Update alert preferences (email, SMS, WhatsApp)."""
    supabase = get_supabase()
    update   = {k: v for k, v in data.dict().items() if v is not None}
    if not update:
        return {"success": True, "message": "Nothing to update"}
    update["username"]   = current_user
    update["updated_at"] = datetime.datetime.now().isoformat()
    try:
        supabase.table("UserProfiles").upsert(update).execute()
        return {"success": True, "message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/risk-trend")
def user_risk_trend(days: int = 30, current_user: str = Depends(verify_token)):
    """Return daily aggregated risk scores for the last N days (longitudinal view)."""
    supabase = get_supabase()
    try:
        since = (datetime.datetime.utcnow() -
                 datetime.timedelta(days=days)).isoformat()
        rows = supabase.table("Predictions")\
            .select("risk_level,confidence,created_at")\
            .eq("username", current_user)\
            .gte("created_at", since)\
            .order("created_at")\
            .execute().data or []

        from collections import defaultdict
        daily: dict = defaultdict(lambda: {"total": 0, "high": 0, "avg_confidence": 0.0})
        for r in rows:
            day = (r.get("created_at") or "")[:10]
            if not day:
                continue
            daily[day]["total"]          += 1
            daily[day]["avg_confidence"] += r.get("confidence", 0)
            if r.get("risk_level") == "HIGH":
                daily[day]["high"] += 1

        trend = []
        for day, d in sorted(daily.items()):
            trend.append({
                "date":           day,
                "total":          d["total"],
                "high_risk":      d["high"],
                "avg_confidence": round(d["avg_confidence"] / d["total"], 4) if d["total"] else 0,
            })
        return {"success": True, "days": days, "trend": trend}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── MFA ──────────────────────────────────────────────
@router.post("/auth/mfa/setup", tags=["MFA"])
def mfa_setup(current_user: str = Depends(verify_token)):
    """Generate a new TOTP secret and return a QR-code data-URI for setup."""
    try:
        import pyotp, qrcode
    except ImportError:
        raise HTTPException(status_code=501,
                            detail="MFA dependencies not installed (pyotp, qrcode)")

    issuer = os.getenv("MFA_ISSUER", "SafeSignal")
    secret = pyotp.random_base32()
    uri    = pyotp.totp.TOTP(secret).provisioning_uri(
                 name=current_user, issuer_name=issuer)

    img    = qrcode.make(uri)
    buf    = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    supabase = get_supabase()
    supabase.table("UserMFA").upsert({
        "username":    current_user,
        "totp_secret": secret,
        "is_enabled":  False,
    }).execute()

    log_mfa_event("MFA_SETUP", current_user, success=True)
    return {
        "success":  True,
        "secret":   secret,
        "qr_code":  f"data:image/png;base64,{qr_b64}",
        "message":  "Scan the QR code in your authenticator app, then call /api/auth/mfa/verify-setup with your 6-digit code."
    }


@router.post("/auth/mfa/verify-setup", tags=["MFA"])
def mfa_verify_setup(data: MFAVerifyInput,
                     current_user: str = Depends(verify_token)):
    """Confirm the first TOTP code to activate MFA for the account."""
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    row = _get_totp_secret(current_user)
    if not row:
        raise HTTPException(status_code=400, detail="Run /api/auth/mfa/setup first")

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", current_user, success=False)
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    get_supabase().table("UserMFA")\
        .update({"is_enabled": True})\
        .eq("username", current_user)\
        .execute()

    log_mfa_event("MFA_ENABLED", current_user, success=True)
    return {"success": True, "message": "MFA enabled successfully"}


@router.post("/auth/mfa/disable", tags=["MFA"])
def mfa_disable(data: MFAVerifyInput,
                current_user: str = Depends(verify_token)):
    """Disable MFA (requires a valid TOTP code to confirm)."""
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    row = _get_totp_secret(current_user)
    if not row or not row.get("is_enabled"):
        raise HTTPException(status_code=400, detail="MFA is not enabled")

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", current_user, success=False)
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    get_supabase().table("UserMFA")\
        .update({"is_enabled": False, "totp_secret": None})\
        .eq("username", current_user)\
        .execute()

    log_mfa_event("MFA_DISABLED", current_user, success=True)
    return {"success": True, "message": "MFA disabled"}


@router.get("/auth/mfa/status", tags=["MFA"])
def mfa_status(current_user: str = Depends(verify_token)):
    """Check whether MFA is enabled for the current user."""
    row     = _get_totp_secret(current_user)
    enabled = bool(row and row.get("is_enabled"))
    return {"success": True, "mfa_enabled": enabled, "username": current_user}


@router.post("/auth/mfa/login", tags=["MFA"])
def mfa_login(data: MFALoginInput, request: Request):
    """Second step of MFA login — verify TOTP code and return JWT token."""
    try:
        import pyotp
    except ImportError:
        raise HTTPException(status_code=501, detail="pyotp not installed")

    result = login_user(data.username, data.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))

    row = _get_totp_secret(data.username)
    if not row or not row.get("is_enabled"):
        return result

    totp = pyotp.TOTP(row["totp_secret"])
    if not totp.verify(data.totp_code, valid_window=1):
        log_mfa_event("MFA_FAILURE", data.username,
                      ip=get_client_ip(request), success=False)
        raise HTTPException(status_code=401, detail="Invalid TOTP code")

    log_mfa_event("MFA_ENABLED", data.username,
                  ip=get_client_ip(request), success=True)
    return result
