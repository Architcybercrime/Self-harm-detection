"""
auth.py
JWT Authentication module for Self Harm Detection API.
Handles user registration, login and token verification.
Uses bcrypt for secure password hashing.
Users stored in Supabase PostgreSQL database.
"""

from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
import bcrypt
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('D:\\selfharm-project\\backend\\.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, hashed):
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def register_user(username, password):
    """Register a new user in Supabase."""
    try:
        # Check if user exists
        existing = supabase.table("Users")\
            .select("username")\
            .eq("username", username)\
            .execute()

        if existing.data:
            return {"success": False, "error": "Username already exists"}

        # Hash password and store
        hashed = hash_password(password)
        result = supabase.table("Users").insert({
            "username": username,
            "password": hashed,
            "role":     "user"
        }).execute()

        return {"success": True, "message": f"User {username} registered successfully"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(username, password):
    """Login user and return JWT token."""
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

        token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=24)
        )

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
    """Configure JWT with the Flask app."""
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY',
        'selfharm-detection-secret-key-2026'
    )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    jwt = JWTManager(app)
    return jwt