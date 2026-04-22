import pytest
import sqlite3
import os
import sys

# Add parent dir to sys.path to easily import ACEest_Fitness
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ACEest_Fitness import app, init_db, DB_NAME

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Init DB schema and default 'admin'
    init_db()
    
    with app.test_client() as client:
        yield client

def test_login_page_renders(client):
    """Test the login page loads."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Username" in response.data

def test_health_check(client):
    """Test the health check endpoint for Kubernetes."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_protected_dashboard_redirects(client):
    """Test that accessing dashboard without login redirects."""
    response = client.get('/dashboard')
    # Should redirect to /login
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_successful_login(client):
    """Test login as admin and accessing dashboard."""
    response = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert response.status_code == 200
    # The dashboard should greet the admin
    assert b"User: admin" in response.data
    assert b"Clients" in response.data
