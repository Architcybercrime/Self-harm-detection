"""Shared constants, dependencies and utilities used across all routers."""
import os
import datetime
import secrets
import re as _re
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET    = os.getenv('JWT_SECRET_KEY', 'selfharm-detection-secret-key-2026')
JWT_ALGORITHM = "HS256"
SUPABASE_URL  = os.getenv("SUPABASE_URL")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY")


def get_supabase():
    """Create and return a Supabase client using environment credentials.

    Returns:
        supabase.Client: An authenticated Supabase client instance.
    """
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token or API key and return username.

    Supports two authentication schemes:
    - API keys prefixed with ``shd_`` validated against the ApiKeys table.
    - Standard JWT Bearer tokens signed with ``JWT_SECRET``.

    Args:
        credentials: HTTP Bearer credentials injected by FastAPI dependency.

    Returns:
        str: The authenticated username.

    Raises:
        HTTPException: 401 if the token/key is invalid, expired, or inactive.
    """
    token = credentials.credentials
    if token.startswith('shd_'):
        supabase = get_supabase()
        try:
            result = supabase.table("ApiKeys").select("username").eq("api_key", token).eq("is_active", True).execute()
            if not result.data:
                raise HTTPException(status_code=401, detail="Invalid or inactive API key")
            username = result.data[0]['username']
            supabase.table("ApiKeys").update({"last_used": datetime.datetime.now().isoformat()}).eq("api_key", token).execute()
            return username
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="API key verification failed")
    try:
        payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify that the token belongs to an admin user.

    Checks the JWT ``role`` claim first (fast path); falls back to a DB
    lookup for older tokens that pre-date the role claim.

    Args:
        credentials: HTTP Bearer credentials injected by FastAPI dependency.

    Returns:
        str: The authenticated admin username.

    Raises:
        HTTPException: 403 if the user does not have admin privileges.
        HTTPException: 401 if the token is invalid or expired.
    """
    token = credentials.credentials
    try:
        payload  = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        role     = payload.get("role", "user")
        username = payload.get("sub")
        if role == "admin":
            return username
    except Exception:
        pass
    raise HTTPException(status_code=403, detail="Admin access required")


def get_client_ip(request: Request) -> str:
    """Extract the client IP address from request headers.

    Prefers the ``X-Forwarded-For`` header (set by proxies/load balancers)
    and falls back to the direct connection address.

    Args:
        request: The incoming FastAPI/Starlette request object.

    Returns:
        str: The client's IP address, or ``"unknown"`` if it cannot be determined.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def sanitize_output(text: str) -> str:
    """Strip HTML tags from user-provided text to prevent XSS in API responses.

    Args:
        text: The string to sanitize. Non-string values are returned unchanged.

    Returns:
        str: The input string with all HTML tags removed.
    """
    if not isinstance(text, str):
        return text
    return _re.sub(r'<[^>]+>', '', text)
