"""
auth.py
JWT Authentication module for Self Harm Detection API.
Handles user registration, login and token verification.
Uses bcrypt for secure password hashing.
"""

from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
import bcrypt
import os

# Simple in-memory user store
users_db = {}


def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)


def verify_password(password, hashed):
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def register_user(username, password):
    """Register a new user."""
    if username in users_db:
        return {"success": False, "error": "Username already exists"}

    users_db[username] = {
        "username": username,
        "password": hash_password(password),
        "role":     "user"
    }
    return {"success": True, "message": f"User {username} registered successfully"}


def login_user(username, password):
    """Login user and return JWT token."""
    if username not in users_db:
        return {"success": False, "error": "User not found"}

    if not verify_password(password, users_db[username]['password']):
        return {"success": False, "error": "Invalid password"}

    token = create_access_token(
        identity=username,
        expires_delta=timedelta(hours=24)
    )

    return {
        "success":      True,
        "access_token": token,
        "username":     username,
        "expires_in":   "24 hours"
    }


def setup_jwt(app):
    """Configure JWT with the Flask app."""
    app.config['JWT_SECRET_KEY'] = os.getenv(
        'JWT_SECRET_KEY', 
        'selfharm-detection-secret-key-2026'
    )
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    jwt = JWTManager(app)
    return jwt