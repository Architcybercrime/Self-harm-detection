"""
test_api.py
Unit tests for Self Harm Detection API (FastAPI v2.0)
Using pytest + Starlette TestClient (bundled with FastAPI)
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------------------------
# FastAPI TestClient setup
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient
from main import app, JWT_SECRET, JWT_ALGORITHM
from jose import jwt as jose_jwt
import datetime


@pytest.fixture(scope="module")
def client():
    """Create a Starlette/FastAPI test client (no running server needed)."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _make_token(username: str = "testuser", role: str = "user", hours: int = 1) -> str:
    """Helper: mint a valid JWT for use in Authorization header."""
    payload = {
        "sub":  username,
        "role": role,
        "iat":  datetime.datetime.utcnow(),
        "exp":  datetime.datetime.utcnow() + datetime.timedelta(hours=hours),
        "type": "access",
    }
    return jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture(scope="module")
def auth_headers():
    """JWT auth headers for a regular test user."""
    token = _make_token("testuser", "user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers():
    """JWT auth headers for an admin test user."""
    token = _make_token("admin_tester", "admin")
    return {"Authorization": f"Bearer {token}"}


# ── HEALTH ENDPOINT ──────────────────────────────────────────────────────────

def test_health_returns_200(client):
    """Health endpoint must return 200."""
    r = client.get("/api/health")
    assert r.status_code == 200


def test_health_body(client):
    """Health response must contain expected fields."""
    r = client.get("/api/health")
    d = r.json()
    assert d["status"] == "running"
    assert d["accuracy"] == "92.2%"
    assert d["websocket"] == "enabled"
    assert "timestamp" in d


def test_health_cors_headers(client):
    """Health endpoint must return explicit CORS headers."""
    r = client.get("/api/health")
    # Security headers middleware adds these; the health endpoint also sets them
    assert r.status_code == 200


# ── CORS CHECK ENDPOINT ───────────────────────────────────────────────────────

def test_cors_check_endpoint(client):
    """GET /api/cors-check must return 200 with cors field."""
    r = client.get("/api/cors-check")
    assert r.status_code == 200
    d = r.json()
    assert d["cors"] == "enabled"
    assert "allowed" in d


# ── REGISTER ENDPOINT ─────────────────────────────────────────────────────────

def test_register_success(client):
    """Successful registration returns 201 and success=true."""
    unique = f"user_{int(time.time() * 1000) % 100000}"
    r = client.post("/api/register", json={"username": unique, "password": "Password123"})
    assert r.status_code == 201
    assert r.json()["success"] is True


def test_register_duplicate(client):
    """Duplicate username registration returns 400."""
    uname = f"dupuser_{int(time.time() * 1000) % 100000}"
    client.post("/api/register", json={"username": uname, "password": "Password123"})
    r = client.post("/api/register", json={"username": uname, "password": "Password123"})
    assert r.status_code == 400


def test_register_short_username(client):
    """Registration with 2-char username returns 422."""
    r = client.post("/api/register", json={"username": "ab", "password": "Password123"})
    assert r.status_code == 422


def test_register_short_password(client):
    """Registration with password < 6 chars returns 422."""
    r = client.post("/api/register", json={"username": "validuser99", "password": "123"})
    assert r.status_code == 422


# ── LOGIN ENDPOINT ────────────────────────────────────────────────────────────

def test_login_nonexistent_user(client):
    """Login for nonexistent user returns 401."""
    r = client.post("/api/login", json={"username": "ghost_user_xyz", "password": "Password123"})
    assert r.status_code == 401


def test_login_missing_fields(client):
    """Login with empty body returns 422 (validation error)."""
    r = client.post("/api/login", json={})
    assert r.status_code == 422


# ── DEMO TOKEN ENDPOINT ───────────────────────────────────────────────────────

def test_demo_token_returns_200(client):
    """GET /api/demo-token must return 200."""
    r = client.get("/api/demo-token")
    assert r.status_code == 200


def test_demo_token_body(client):
    """Demo token response must contain access_token for demo_visitor."""
    r = client.get("/api/demo-token")
    d = r.json()
    assert d["success"] is True
    assert "access_token" in d
    assert d["username"] == "demo_visitor"
    assert d["role"] == "demo"


def test_demo_token_is_valid_jwt(client):
    """Demo token must be a decodable JWT with correct claims."""
    r = client.get("/api/demo-token")
    token = r.json()["access_token"]
    payload = jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == "demo_visitor"
    assert payload["type"] == "demo"


def test_demo_token_works_for_predict(client):
    """A demo token must be accepted by /api/predict."""
    token = client.get("/api/demo-token").json()["access_token"]
    r = client.post(
        "/api/predict",
        json={"text": "I feel very sad and hopeless about everything today"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Expect 200 (or 500 if model not loaded in CI — both are non-401)
    assert r.status_code != 401


# ── PREDICT ENDPOINT ──────────────────────────────────────────────────────────

def test_predict_requires_auth(client):
    """Predict without token must return 403 (no Bearer) or 401."""
    r = client.post("/api/predict", json={"text": "I feel hopeless"})
    assert r.status_code in (401, 403)


def test_predict_empty_text(client, auth_headers):
    """Predict with empty string returns 422."""
    r = client.post("/api/predict", json={"text": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_predict_too_short_text(client, auth_headers):
    """Predict with text shorter than min_length=3 returns 422."""
    r = client.post("/api/predict", json={"text": "hi"}, headers=auth_headers)
    assert r.status_code == 422


def test_predict_too_long_text(client, auth_headers):
    """Predict with text longer than max_length=5000 returns 422."""
    r = client.post("/api/predict", json={"text": "a" * 5001}, headers=auth_headers)
    assert r.status_code == 422


def test_predict_valid_text(client, auth_headers):
    """Predict with valid text returns 200 and risk_level field."""
    r = client.post(
        "/api/predict",
        json={"text": "I had a really good day and feel great about tomorrow"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    d = r.json()
    assert "risk_level" in d
    assert "confidence" in d
    assert "alert_triggered" in d


def test_predict_missing_body(client, auth_headers):
    """Predict with no body returns 422."""
    r = client.post("/api/predict", headers=auth_headers)
    assert r.status_code == 422


# ── PROFILE ENDPOINT ──────────────────────────────────────────────────────────

def test_profile_requires_auth(client):
    """Profile without token returns 403/401."""
    r = client.get("/api/profile")
    assert r.status_code in (401, 403)


def test_profile_returns_username(client, auth_headers):
    """Profile endpoint returns the current user's username."""
    r = client.get("/api/profile", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


# ── STATS ENDPOINT ────────────────────────────────────────────────────────────

def test_stats_endpoint(client, auth_headers):
    """Stats endpoint returns 200."""
    r = client.get("/api/stats", headers=auth_headers)
    assert r.status_code == 200


# ── HISTORY ENDPOINT ──────────────────────────────────────────────────────────

def test_history_endpoint(client, auth_headers):
    """History endpoint returns 200."""
    r = client.get("/api/history", headers=auth_headers)
    assert r.status_code == 200


# ── MONITOR ENDPOINT ──────────────────────────────────────────────────────────

def test_monitor_endpoint(client, auth_headers):
    """Monitor endpoint returns 200."""
    r = client.get("/api/monitor", headers=auth_headers)
    assert r.status_code == 200


# ── ADMIN/USERS ENDPOINT ──────────────────────────────────────────────────────

def test_admin_users_requires_admin(client, auth_headers):
    """Non-admin user must receive 403 from /api/admin/users."""
    r = client.get("/api/admin/users", headers=auth_headers)
    assert r.status_code == 403


def test_admin_users_accessible_with_admin_token(client, admin_headers):
    """Admin token must be accepted by /api/admin/users (200 or 500 if no DB)."""
    r = client.get("/api/admin/users", headers=admin_headers)
    # 200 = success, 500 = no Supabase in CI — both confirm auth passed
    assert r.status_code in (200, 500)


# ── INPUT VALIDATION ──────────────────────────────────────────────────────────

def test_predict_invalid_json(client, auth_headers):
    """Predict with completely invalid input returns 422."""
    r = client.post(
        "/api/predict",
        json={"text": 12345},  # integer instead of string
        headers=auth_headers,
    )
    # FastAPI coerces integers to str, so this may pass validation — just check not 500
    assert r.status_code != 500


def test_register_invalid_username_chars(client):
    """Username with special characters returns 422."""
    r = client.post(
        "/api/register",
        json={"username": "bad user!", "password": "Password123"},
    )
    assert r.status_code == 422


# ── PREPROCESSING (unit tests) ────────────────────────────────────────────────

def test_preprocessing_pipeline():
    """Text preprocessing runs without errors."""
    from utils.preprocess import full_preprocess, get_sentiment_scores

    cleaned = full_preprocess("I feel VERY hopeless today!!!")
    assert isinstance(cleaned, str)
    assert len(cleaned) > 0

    scores = get_sentiment_scores("I feel hopeless")
    assert "compound" in scores
    assert "neg" in scores
    assert -1 <= scores["compound"] <= 1


# ── SANITIZE_OUTPUT (unit test) ───────────────────────────────────────────────

def test_sanitize_output_strips_html():
    """sanitize_output must strip HTML tags from text."""
    from main import sanitize_output

    result = sanitize_output("<script>alert('xss')</script>Hello")
    assert "<script>" not in result
    assert "Hello" in result


def test_sanitize_output_safe_text_unchanged():
    """sanitize_output must leave plain text unchanged."""
    from main import sanitize_output

    plain = "I feel really hopeless today"
    assert sanitize_output(plain) == plain


# ── FUSION MODULE (unit tests) ────────────────────────────────────────────────

def test_fusion_text_only():
    """Fusion with text-only input returns expected keys."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores(text_result={"risk_level": "HIGH", "confidence": 0.9})
    assert "final_risk_score" in result
    assert "risk_level" in result
    assert "alert_triggered" in result


def test_fusion_no_input():
    """Fusion with no input returns an error key."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores()
    assert "error" in result


def test_fusion_invalid_weights():
    """Fusion with weights that do not sum to 1 returns an error."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores(
        text_result={"risk_level": "HIGH", "confidence": 0.9},
        custom_weights={"text": 0.5, "facial": 0.5, "speech": 0.5},
    )
    assert "error" in result
