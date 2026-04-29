"""
auth.py
JWT Authentication module for Self Harm Detection API.
Handles user registration, login and token verification.
Uses bcrypt for secure password hashing.
Users stored in Supabase PostgreSQL database.
Works with both Flask and FastAPI.
"""

from datetime import timedelta, datetime
import bcrypt
import os
from dotenv import load_dotenv
from supabase import create_client
from jose import jwt

load_dotenv()

SUPABASE_URL  = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY", "")

# IMPORTANT: JWT_SECRET MUST be set in production environment
# For development only: if not set, use a warning fallback (insecure!)
JWT_SECRET = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET:
    import warnings
    warnings.warn("JWT_SECRET_KEY not set in environment. Using insecure development default.", stacklevel=2)
    JWT_SECRET = 'selfharm-detection-secret-key-2026'  # ONLY for development

JWT_ALGORITHM = "HS256"

# Gracefully handle missing credentials
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        supabase = None
else:
    supabase = None

# In-memory mock user store for test/dev when Supabase not configured
_mock_users = {}


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, hashed):
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def register_user(username, password):
    """Register a new user in Supabase."""
    if supabase is None:
        # Use in-memory store for mock mode (supports duplicate checks)
        if username in _mock_users:
            return {"success": False, "error": "Username already exists"}
        hashed = hash_password(password)
        _mock_users[username] = {"password": hashed, "role": "user"}
        return {"success": True, "message": f"User {username} registered successfully (mock)"}
    
    try:
        existing = supabase.table("Users")\
            .select("username")\
            .eq("username", username)\
            .execute()

        if existing.data:
            return {"success": False, "error": "Username already exists"}

        hashed = hash_password(password)
        supabase.table("Users").insert({
            "username": username,
            "password": hashed,
            "role":     "user"
        }).execute()

        return {"success": True, "message": f"User {username} registered successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """Login user and return JWT token. Works with Flask and FastAPI."""
    if supabase is None:
        # Mock login checks in-memory store
        user = _mock_users.get(username)
        if not user:
            return {"success": False, "error": "User not found"}
        if not verify_password(password, user['password']):
            return {"success": False, "error": "Invalid password"}
        token = jwt.encode({
            "sub":   username,
            "fresh": False,
            "iat":   datetime.utcnow(),
            "exp":   datetime.utcnow() + timedelta(hours=24),
            "type":  "access"
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "success":      True,
            "access_token": token,
            "username":     username,
            "role":         user.get('role', 'user'),
            "expires_in":   "24 hours"
        }
    
    try:
        result = supabase.table("Users")\
            .select("*")\
            .eq("username", username)\
            .execute()

        if not result.data:
            return {"success": False, "error": "User not found"}

        user = result.data[0]

        if not verify_password(password, user['password']):
            return {"success": False, "error": "Invalid password"}

        token = jwt.encode({
            "sub":   username,
            "fresh": False,
            "iat":   datetime.utcnow(),
            "exp":   datetime.utcnow() + timedelta(hours=24),
            "type":  "access"
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "success":      True,
            "access_token": token,
            "username":     username,
            "role":         user['role'],
            "expires_in":   "24 hours"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def setup_jwt(app):
    """Configure JWT with the Flask app (Flask only)."""
    from flask_jwt_extended import JWTManager
    app.config['JWT_SECRET_KEY']              = JWT_SECRET
    app.config['JWT_ACCESS_TOKEN_EXPIRES']    = timedelta(hours=24)
    return JWTManager(app)