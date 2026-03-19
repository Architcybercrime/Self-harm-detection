"""
test_api.py
Unit tests for Self Harm Detection API
Using pytest framework
"""

import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ── HEALTH ENDPOINT ──────────────────────────────────
def test_health_endpoint(client):
    """Test health endpoint returns 200."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'running'
    assert data['accuracy'] == '92.2%'


# ── PREDICT ENDPOINT ─────────────────────────────────
def test_predict_high_risk(client):
    """Test prediction returns HIGH risk for distress text."""
    response = client.post('/api/predict',
        json={"text": "I feel completely hopeless and want to disappear"})
    assert response.status_code == 200
    data = response.get_json()
    assert data['risk_level'] == 'HIGH'
    assert data['alert_triggered'] == True
    assert 'confidence' in data
    assert 'sentiment_score' in data


def test_predict_low_risk(client):
    """Test prediction returns LOW risk for normal text."""
    response = client.post('/api/predict',
        json={"text": "I had a great day today, feeling wonderful!"})
    assert response.status_code == 200
    data = response.get_json()
    assert data['risk_level'] == 'LOW'
    assert data['alert_triggered'] == False


def test_predict_missing_text(client):
    """Test prediction returns 400 when text is missing."""
    response = client.post('/api/predict', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_predict_empty_text(client):
    """Test prediction returns 400 when text is empty."""
    response = client.post('/api/predict', json={"text": ""})
    assert response.status_code == 400


def test_predict_text_too_long(client):
    """Test prediction returns 400 when text exceeds limit."""
    long_text = "a" * 5001
    response = client.post('/api/predict', json={"text": long_text})
    assert response.status_code == 400


# ── STATS ENDPOINT ───────────────────────────────────
def test_stats_endpoint(client):
    """Test stats endpoint works."""
    response = client.get('/api/stats')
    assert response.status_code == 200


# ── MONITOR ENDPOINT ─────────────────────────────────
def test_monitor_endpoint(client):
    """Test monitor endpoint works."""
    response = client.get('/api/monitor')
    assert response.status_code == 200


# ── HISTORY ENDPOINT ─────────────────────────────────
def test_history_endpoint(client):
    """Test history endpoint returns data."""
    response = client.get('/api/history')
    assert response.status_code == 200
    data = response.get_json()
    assert 'success' in data


# ── DB STATS ENDPOINT ────────────────────────────────
def test_db_stats_endpoint(client):
    """Test db-stats endpoint returns statistics."""
    response = client.get('/api/db-stats')
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


def test_fusion_no_input():
    """Test fusion with no input returns error."""
    from utils.fusion import fuse_risk_scores

    result = fuse_risk_scores()
    assert 'error' in result