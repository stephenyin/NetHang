import os
import yaml
import pytest
from nethang import app

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Create a test session
        with client.session_transaction() as session:
            session['logged_in'] = True
        yield client

@pytest.fixture
def mock_models_yaml(tmp_path):
    """Create a temporary models.yaml file for testing."""
    models_dir = tmp_path / ".nethang"
    models_dir.mkdir()
    models_file = models_dir / "models.yaml"

    # Create test models.yaml content
    models_content = {
        'version': '1.0.0',
        'models': [
            {'name': 'test_model', 'description': 'Test model'}
        ]
    }

    with open(models_file, 'w') as f:
        yaml.dump(models_content, f)

    # Store original HOME and set it to tmp_path
    original_home = os.environ.get('HOME')
    os.environ['HOME'] = str(tmp_path)

    yield models_file

    # Restore original HOME
    if original_home:
        os.environ['HOME'] = original_home
    else:
        del os.environ['HOME']

def test_about_page_requires_login(client):
    """Test that about page requires login."""
    # Clear session
    with client.session_transaction() as session:
        session.clear()

    response = client.get('/about')
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.location

def test_about_page_loads(client):
    """Test that about page loads successfully."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About NetHang' in response.data
    assert b'0.1.3' in response.data  # Current version from pyproject.toml

def test_about_page_contains_links(client):
    """Test that about page contains all required links."""
    response = client.get('/about')
    assert b'github.com/stephenyin/NetHang' in response.data
    assert b'linkedin.com/in/hang-yin-stephen' in response.data
    assert b'mailto:stephen.yin.h@gmail.com' in response.data