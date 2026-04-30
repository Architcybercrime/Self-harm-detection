"""API key management router — generate, retrieve, and revoke personal API keys."""
import secrets

from fastapi import APIRouter, Depends, HTTPException

from shared import verify_token, get_supabase
from utils.audit_log import log_api_key_event

router = APIRouter(prefix="/api", tags=["API Keys"])


# ── ENDPOINTS ────────────────────────────────────────
@router.post("/keys/generate")
def generate_api_key(current_user: str = Depends(verify_token)):
    """Generate a personal API key for external integrations.

    Any existing active key for the user is deactivated before issuing the new one.
    Use the returned key as ``Bearer shd_YOUR_KEY`` in the Authorization header.
    """
    supabase = get_supabase()
    api_key  = f"shd_{secrets.token_urlsafe(32)}"

    try:
        supabase.table("ApiKeys")\
            .update({"is_active": False})\
            .eq("username", current_user)\
            .execute()

        supabase.table("ApiKeys").insert({
            "username":  current_user,
            "api_key":   api_key,
            "is_active": True
        }).execute()

        log_api_key_event("API_KEY_GENERATED", current_user)
        return {
            "success":      True,
            "api_key":      api_key,
            "username":     current_user,
            "message":      "API key generated successfully!",
            "usage":        f"Authorization: Bearer {api_key}",
            "curl_example": (
                f'curl -X POST http://127.0.0.1:8000/api/predict '
                f'-H "Authorization: Bearer {api_key}" '
                f'-H "Content-Type: application/json" '
                f'-d \'{{"text": "your text here"}}\''
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/my-key")
def get_my_api_key(current_user: str = Depends(verify_token)):
    """Retrieve the current active API key for the authenticated user."""
    supabase = get_supabase()

    try:
        result = supabase.table("ApiKeys")\
            .select("*")\
            .eq("username", current_user)\
            .eq("is_active", True)\
            .execute()

        if not result.data:
            return {
                "success": False,
                "message": "No active API key. Use POST /api/keys/generate to create one."
            }

        key_data = result.data[0]
        return {
            "success":    True,
            "api_key":    key_data['api_key'],
            "created_at": key_data['created_at'],
            "last_used":  key_data['last_used'],
            "is_active":  key_data['is_active']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keys/revoke")
def revoke_api_key(current_user: str = Depends(verify_token)):
    """Revoke the current active API key for the authenticated user."""
    supabase = get_supabase()

    try:
        supabase.table("ApiKeys")\
            .update({"is_active": False})\
            .eq("username", current_user)\
            .execute()

        log_api_key_event("API_KEY_REVOKED", current_user)
        return {"success": True, "message": "API key revoked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
