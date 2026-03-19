"""
test_api.py
Unit tests for Self Harm Detection API
Using pytest framework
"""

import pytest
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app
from flask_jwt_extended import create_access_token


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def token():
    """Generate JWT token for testing."""
    with app.app_context():
        return create_access_token(identity="testuser")


@pytest.fixture
def auth_headers(token):
    """Return auth headers with JWT token."""
    return {"Authorization": f"Bearer {token}"}


# ── HEALTH ENDPOINT ──────────────────────────────────
def test_health_endpoint(client):
    """Test health endpoint returns 200."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'running'
    assert data['accuracy'] == '92.2%'
    assert data['websocket'] == 'enabled'


# ── PREDICT ENDPOINT ─────────────────────────────────
def test_predict_high_risk(client, auth_headers):
    """Test prediction returns HIGH risk for distress text."""
    response = client.post('/api/predict',
        json={"text": "I feel completely hopeless and want to disappear"},
        headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['risk_level'] == 'HIGH'
    assert data['alert_triggered'] == True
    assert 'confidence' in data
    assert 'sentiment_score' in data
    assert 'risk_indicators' in data
    assert 'recommendations' in data


def test_predict_low_risk(client, auth_headers):
    """Test prediction returns LOW risk for normal text."""
    response = client.post('/api/predict',
        json={"text": "I had a great day today, feeling wonderful!"},
        headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['risk_level'] == 'LOW'
    assert data['alert_triggered'] == False


def test_predict_missing_text(client, auth_headers):
    """Test prediction returns 400 when text is missing."""
    response = client.post('/api/predict',
        json={},
        headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_predict_empty_text(client, auth_headers):
    """Test prediction returns 400 when text is empty."""
    response = client.post('/api/predict',
        json={"text": ""},
        headers=auth_headers)
    assert response.status_code == 400


def test_predict_text_too_long(client, auth_headers):
    """Test prediction returns 400 when text exceeds limit."""
    long_text = "a" * 5001
    response = client.post('/api/predict',
        json={"text": long_text},
        headers=auth_headers)
    assert response.status_code == 400


def test_predict_unauthorized(client):
    """Test prediction returns 401 without JWT token."""
    response = client.post('/api/predict',
        json={"text": "I feel hopeless"})
    assert response.status_code == 401


# ── STATS ENDPOINT ───────────────────────────────────
def test_stats_endpoint(client, auth_headers):
    """Test stats endpoint works."""
    response = client.get('/api/stats', headers=auth_headers)
    assert response.status_code == 200


# ── MONITOR ENDPOINT ─────────────────────────────────
def test_monitor_endpoint(client, auth_headers):
    """Test monitor endpoint works."""
    response = client.get('/api/monitor', headers=auth_headers)
    assert response.status_code == 200


# ── HISTORY ENDPOINT ─────────────────────────────────
def test_history_endpoint(client, auth_headers):
    """Test history endpoint returns data."""
    response = client.get('/api/history', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data


# ── DB STATS ENDPOINT ────────────────────────────────
def test_db_stats_endpoint(client, auth_headers):
    """Test db-stats endpoint returns statistics."""
    response = client.get('/api/db-stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data


# ── PREPROCESSING ────────────────────────────────────
def test_preprocessing():
    """Test text preprocessing works correctly."""
    from utils.preprocess import full_preprocess, get_sentiment_scores

    cleaned = full_preprocess("I feel VERY hopeless today!!!")
    assert isinstance(cleaned, str)
    assert len(cleaned) > 0

    scores = get_sentiment_scores("I feel hopeless")
    assert 'compound' in scores
    assert 'neg' in scores
    assert -1 <= scores['compound'] <= 1


# ── FUSION MODULE ────────────────────────────────────
def test_fusion_text_only():
    """Test fusion with text only."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores(
        text_result={"risk_level": "HIGH", "confidence": 0.9}
    )
    assert 'final_risk_score' in result
    assert 'risk_level' in result
    assert 'alert_triggered' in result
    assert 'weights_applied' in result
    assert 'weight_explanation' in result


def test_fusion_no_input():
    """Test fusion with no input returns error."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores()
    assert 'error' in result


def test_fusion_custom_weights():
    """Test fusion with custom weights."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores(
        text_result={"risk_level": "HIGH", "confidence": 0.9},
        custom_weights={"text": 1.0, "facial": 0.0, "speech": 0.0}
    )
    assert 'final_risk_score' in result


def test_fusion_invalid_weights():
    """Test fusion with invalid weights returns error."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores(
        text_result={"risk_level": "HIGH", "confidence": 0.9},
        custom_weights={"text": 0.5, "facial": 0.5, "speech": 0.5}
    )
    assert 'error' in result


# ── AUTH ENDPOINTS ───────────────────────────────────
def test_register_success(client):
    """Test successful user registration with unique username."""
    unique_user = f"testuser_{int(time.time())}"
    response = client.post('/api/register',
        json={"username": unique_user, "password": "password123"})
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] == True


def test_register_duplicate(client):
    """Test duplicate username registration fails."""
    client.post('/api/register',
        json={"username": "dupuser", "password": "password123"})
    response = client.post('/api/register',
        json={"username": "dupuser", "password": "password123"})
    assert response.status_code == 400


def test_register_short_username(client):
    """Test registration fails with short username."""
    response = client.post('/api/register',
        json={"username": "ab", "password": "password123"})
    assert response.status_code == 400


def test_register_short_password(client):
    """Test registration fails with short password."""
    response = client.post('/api/register',
        json={"username": "validuser", "password": "123"})
    assert response.status_code == 400


def test_login_nonexistent_user_returns_401(client):
    """Test login fails for nonexistent user returns 401."""
    response = client.post('/api/login',
        json={"username": "doesnotexist999", "password": "password123"})
    assert response.status_code == 401
    data = response.get_json()
    assert data['success'] == False


def test_login_missing_fields(client):
    """Test login fails when fields are missing."""
    response = client.post('/api/login', json={})
    assert response.status_code == 400


# ── VALIDATORS ───────────────────────────────────────
def test_validate_text_too_short(client, auth_headers):
    """Test prediction fails with too short text."""
    response = client.post('/api/predict',
        json={"text": "hi"},
        headers=auth_headers)
    assert response.status_code == 400


def test_validate_special_characters(client, auth_headers):
    """Test prediction works with special characters."""
    response = client.post('/api/predict',
        json={"text": "I feel very sad and hopeless today!!!"},
        headers=auth_headers)
    assert response.status_code == 200


def test_db_stats_structure(client, auth_headers):
    """Test db-stats returns correct structure."""
    response = client.get('/api/db-stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data


# ── SPEECH ANALYSIS ──────────────────────────────────
def test_speech_endpoint_no_input(client, auth_headers):
    """Test speech endpoint returns error with no input."""
    response = client.post('/api/analyze-speech',
        json={},
        headers=auth_headers)
    assert response.status_code == 400


def test_speech_endpoint_invalid_duration(client, auth_headers):
    """Test speech endpoint rejects invalid duration."""
    response = client.post('/api/analyze-speech',
        json={"use_microphone": True, "duration": 100},
        headers=auth_headers)
    assert response.status_code == 400


def test_speech_analysis_module():
    """Test speech analysis module loads correctly."""
    from utils.speech_analysis import LIBROSA_AVAILABLE, SR_AVAILABLE
    assert LIBROSA_AVAILABLE == True
    assert SR_AVAILABLE == True