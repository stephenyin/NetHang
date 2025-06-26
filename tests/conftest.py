"""
Pytest configuration and common fixtures for NetHang tests.

This file contains shared fixtures and configuration that can be used
across all test modules.

Author: Hang Yin
Date: 2025-06-11
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open


@pytest.fixture(scope="session")
def temp_test_dir():
    """Create a temporary directory for testing that persists for the test session."""
    temp_dir = tempfile.mkdtemp(prefix="nethang_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_flask_app():
    """Mock Flask app for testing."""
    mock_app = MagicMock()
    mock_app.logger = MagicMock()
    return mock_app


@pytest.fixture
def mock_config_paths():
    """Mock configuration paths for testing."""
    with patch('nethang.config_manager.CONFIG_PATH', '/tmp/test_config'):
        with patch('nethang.config_manager.MODELS_FILE', '/tmp/test_config/models.yaml'):
            with patch('nethang.config_manager.CONFIG_FILE', '/tmp/test_config/config.yaml'):
                with patch('nethang.config_manager.PATHS_FILE', '/tmp/test_config/paths.yaml'):
                    yield


@pytest.fixture
def mock_app_logger():
    """Mock Flask app logger for testing."""
    with patch('nethang.config_manager.app') as mock_app:
        mock_app.logger = MagicMock()
        yield mock_app


@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration for testing."""
    return {
        'version': '0.1.0',
        'components': {
            'delay_components': {
                'delay_lan': {'delay': 2},
                'delay_intercity': {'delay': 15}
            },
            'jitter_components': {
                'jitter_moderate_wireless': {'slot': [100, 100]}
            },
            'loss_components': {
                'loss_slight': {'loss': 1}
            },
            'rate_components': {
                'rate_1000M': {'rate_limit': 1000000, 'qdepth': 1000}
            }
        },
        'models': {
            'test_model': {
                'description': 'Test network model',
                'global': {
                    'uplink': {'delay': 10},
                    'downlink': {'delay': 10}
                },
                'timeline': []
            }
        }
    }


@pytest.fixture
def invalid_yaml_content():
    """Invalid YAML content for testing error handling."""
    return "invalid: yaml: content: ["


@pytest.fixture
def mock_github_response_success(sample_yaml_config):
    """Mock successful GitHub API response."""
    import yaml
    mock_response = MagicMock()
    mock_response.text = yaml.dump(sample_yaml_config)
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_github_response_error():
    """Mock failed GitHub API response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")
    return mock_response


@pytest.fixture
def mock_requests_get_success(mock_github_response_success):
    """Mock successful requests.get call."""
    with patch('requests.get', return_value=mock_github_response_success) as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_get_error():
    """Mock failed requests.get call."""
    with patch('requests.get', side_effect=Exception("Network error")) as mock_get:
        yield mock_get


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with patch('builtins.open', mock_open()) as mock_file:
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.path.exists') as mock_exists:
                yield {
                    'file': mock_file,
                    'makedirs': mock_makedirs,
                    'exists': mock_exists
                }


@pytest.fixture
def mock_shutil_operations():
    """Mock shutil operations for testing."""
    with patch('shutil.copy2') as mock_copy:
        yield mock_copy


@pytest.fixture
def mock_time_operations():
    """Mock time operations for testing."""
    with patch('time.time') as mock_time:
        with patch('os.path.getmtime') as mock_getmtime:
            yield {
                'time': mock_time,
                'getmtime': mock_getmtime
            }