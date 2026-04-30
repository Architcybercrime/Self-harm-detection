import pytest
import sys
import os

# Mock Supabase before imports
class MockSupabase:
    def table(self, name):
        return self
    def select(self, *args):
        return self
    def eq(self, *args):
        return self
    def execute(self):
        class Result:
            data = []
        return Result()
    def insert(self, *args):
        return self

sys.modules['supabase'] = type('MockModule', (), {'create_client': lambda *args: MockSupabase()})()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import app
from app import app
from utils.auth import _mock_users

@pytest.fixture
def client():
    """Create test client and reset mock users before each test."""
    # Clear mock users before each test
    _mock_users.clear()
    
    # Configure Flask for testing
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client
    
    # Cleanup after test
    _mock_users.clear()


@pytest.fixture
def auth_headers(client):
    """Register a test user and return auth headers."""
    # Clear any existing users
    _mock_users.clear()
    
    # Register test user
    register_response = client.post('/api/register',
        json={"username": "testuser", "password": "TestPassword123"})
    
    if register_response.status_code != 201:
        # User already exists, try login
        pass
    
    # Login and get token
    login_response = client.post('/api/login',
        json={"username": "testuser", "password": "TestPassword123"})
    
    if login_response.status_code == 200:
        data = login_response.get_json()
        token = data.get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    # Fallback
    return {"Authorization": f"Bearer invalid_token"}

