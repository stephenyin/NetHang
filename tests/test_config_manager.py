"""
Tests for nethang/config_manager.py

This module contains comprehensive tests for the ConfigManager class.

Author: Hang Yin
Date: 2025-06-25
"""

import pytest
import os
import yaml
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from nethang.config_manager import ConfigManager

class TestConfigManager:
    """Test cases for ConfigManager class"""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigManager instance for testing"""
        return ConfigManager()

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_models_file(self, temp_config_dir):
        """Create a mock models.yaml file"""
        models_file = os.path.join(temp_config_dir, 'models.yaml')
        test_models = {
            'version': '0.1.0',
            'components': {
                'delay_components': {
                    'delay_lan': {'delay': 2}
                }
            },
            'models': {
                'test_model': {
                    'description': 'Test model',
                    'global': {
                        'uplink': {'delay': 10},
                        'downlink': {'delay': 10}
                    }
                }
            }
        }

        os.makedirs(temp_config_dir, exist_ok=True)
        with open(models_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_models, f)

        return models_file

    def test_init(self, config_manager):
        """Test ConfigManager initialization"""
        assert config_manager.github_config_url == "https://raw.githubusercontent.com/stephenyin/nethang/main/config_files/models.yaml"
        assert config_manager.fallback_models is not None
        assert "version: 0.1.0" in config_manager.fallback_models
        assert "components:" in config_manager.fallback_models
        assert "models:" in config_manager.fallback_models

    def test_fallback_models_structure(self, config_manager):
        """Test that fallback models have correct YAML structure"""
        # Parse fallback models to ensure they're valid YAML
        parsed_models = yaml.safe_load(config_manager.fallback_models)

        assert 'version' in parsed_models
        assert 'components' in parsed_models
        assert 'models' in parsed_models

        # Check components structure
        components = parsed_models['components']
        assert 'delay_components' in components
        assert 'jitter_components' in components
        assert 'loss_components' in components
        assert 'rate_components' in components

        # Check that models exist
        models = parsed_models['models']
        assert len(models) > 0

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    def test_ensure_models_file_exists(self, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test ensure_models when models file already exists"""
        # Mock that file exists
        with patch('os.path.exists', return_value=True):
            config_manager.ensure_models()
            # Should not call create_config_from_github when file exists
            # (we can't easily test this without more complex mocking)

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    def test_ensure_models_file_not_exists(self, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test ensure_models when models file doesn't exist"""
        # Mock that file doesn't exist
        with patch('os.path.exists', return_value=False):
            with patch.object(config_manager, 'create_config_from_github') as mock_create:
                config_manager.ensure_models()
                mock_create.assert_called_once()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    @patch('requests.get')
    def test_create_config_from_github_success(self, mock_get, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test successful config download from GitHub"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = yaml.dump({
            'version': '0.1.0',
            'components': {'test': 'data'},
            'models': {'test_model': {}}
        })
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs') as mock_makedirs:
                config_manager.create_config_from_github()

                mock_makedirs.assert_called_once_with(mock_config_path, exist_ok=True)
                mock_get.assert_called_once_with(config_manager.github_config_url, timeout=10)
                mock_file.assert_called_once_with(mock_models_file, 'w', encoding='utf-8')

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    @patch('requests.get')
    def test_create_config_from_github_invalid_yaml(self, mock_get, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test config download with invalid YAML"""
        # Mock response with invalid YAML
        mock_response = MagicMock()
        mock_response.text = "invalid: yaml: content: ["
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.object(config_manager, 'create_fallback_config') as mock_fallback:
            with patch('os.makedirs'):
                config_manager.create_config_from_github()
                mock_fallback.assert_called_once()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    @patch('requests.get')
    def test_create_config_from_github_request_error(self, mock_get, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test config download with request error"""
        # Mock request error
        mock_get.side_effect = Exception("Network error")

        with patch.object(config_manager, 'create_fallback_config') as mock_fallback:
            with patch('os.makedirs'):
                config_manager.create_config_from_github()
                mock_fallback.assert_called_once()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    def test_create_fallback_config_success(self, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test successful fallback config creation"""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.makedirs') as mock_makedirs:
                config_manager.create_fallback_config()

                mock_makedirs.assert_called_once_with(mock_config_path, exist_ok=True)
                mock_file.assert_called_once_with(mock_models_file, 'w', encoding='utf-8')

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    def test_create_fallback_config_error(self, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test fallback config creation with error"""
        with patch('builtins.open', side_effect=Exception("Write error")):
            with patch('os.makedirs'):
                config_manager.create_fallback_config()
                # Should log warning but not raise exception

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_check_config_update_force(self, mock_app, mock_models_file, config_manager):
        """Test config update check with force update"""
        with patch.object(config_manager, 'update_config_from_github') as mock_update:
            config_manager.check_config_update(force_update=True)
            mock_update.assert_called_once()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_check_config_update_old_file(self, mock_app, mock_models_file, config_manager):
        """Test config update check with old file"""
        # Mock old file (8 days old)
        with patch('os.path.getmtime', return_value=0):
            with patch('time.time', return_value=8 * 24 * 3600):
                with patch.object(config_manager, 'update_config_from_github') as mock_update:
                    config_manager.check_config_update()
                    mock_update.assert_called_once()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_check_config_update_recent_file(self, mock_app, mock_models_file, config_manager):
        """Test config update check with recent file"""
        # Mock recent file (1 day old)
        with patch('os.path.getmtime', return_value=0):
            with patch('time.time', return_value=1 * 24 * 3600):
                with patch.object(config_manager, 'update_config_from_github') as mock_update:
                    config_manager.check_config_update()
                    mock_update.assert_not_called()

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    @patch('requests.get')
    def test_update_config_from_github_success(self, mock_get, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test successful config update from GitHub"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = yaml.dump({
            'version': '0.2.0',
            'components': {'updated': 'data'},
            'models': {'new_model': {}}
        })
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.exists', return_value=True):
                with patch('shutil.copy2') as mock_copy:
                    config_manager.update_config_from_github()

                    mock_get.assert_called_once_with(config_manager.github_config_url, timeout=10)
                    mock_copy.assert_called_once()  # Backup existing file
                    mock_file.assert_called_once_with(mock_models_file, 'w', encoding='utf-8')

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.CONFIG_PATH')
    @patch('nethang.config_manager.app')
    @patch('requests.get')
    def test_update_config_from_github_error_with_backup(self, mock_get, mock_app, mock_config_path, mock_models_file, config_manager):
        """Test config update error with backup restoration"""
        # Mock request error
        mock_get.side_effect = Exception("Network error")

        backup_file = os.path.join(mock_config_path, 'models.yaml.backup')

        with patch('os.path.exists', side_effect=lambda path: path == backup_file):
            with patch('shutil.copy2') as mock_copy:
                config_manager.update_config_from_github()
                # Should restore from backup
                mock_copy.assert_called_with(backup_file, mock_models_file)

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_load_models_success(self, mock_app, mock_models_file, config_manager):
        """Test successful models loading"""
        with patch('builtins.open', mock_open(read_data=yaml.dump({
            'version': '0.1.0',
            'components': {'test': 'data'},
            'models': {'test_model': {}}
        }))):
            result = config_manager.load_models()

            assert result is not None
            assert 'version' in result
            assert 'components' in result
            assert 'models' in result
            assert result['version'] == '0.1.0'

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_load_models_file_not_found(self, mock_app, mock_models_file, config_manager):
        """Test models loading when file doesn't exist"""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = config_manager.load_models()

            # Should return fallback models as string
            assert result == config_manager.fallback_models

    @patch('nethang.config_manager.MODELS_FILE')
    @patch('nethang.config_manager.app')
    def test_load_models_yaml_error(self, mock_app, mock_models_file, config_manager):
        """Test models loading with YAML parsing error"""
        with patch('builtins.open', mock_open(read_data="invalid: yaml: [")):
            result = config_manager.load_models()

            # Should return fallback models as string
            assert result == config_manager.fallback_models

    def test_fallback_models_contains_required_models(self, config_manager):
        """Test that fallback models contain all required network models"""
        parsed_models = yaml.safe_load(config_manager.fallback_models)
        models = parsed_models['models']

        # Check for some key models
        expected_models = [
            '(Scenario) Elevator',
            '(Scenario) High_speed_Driving',
            '(Scenario) Underground_parking_lot',
            'EDGE_with_handover',
            '3G_with_handover',
            'LTE_with_handover',
            'Starlink',
            '(NLC) Very_bad_network',
            '(NLC) Wi-Fi',
            '(NLC) LTE',
            '(NLC) EDGE',
            '(NLC) DSL'
        ]

        for model_name in expected_models:
            assert model_name in models, f"Expected model '{model_name}' not found in fallback models"

    def test_fallback_models_components_structure(self, config_manager):
        """Test that fallback models have proper component structure"""
        parsed_models = yaml.safe_load(config_manager.fallback_models)
        components = parsed_models['components']

        # Check delay components
        delay_components = components['delay_components']
        expected_delays = [
            'delay_lan', 'delay_intercity', 'delay_intercontinental',
            'delay_DSL', 'delay_cellular_LTE_uplink', 'delay_cellular_LTE_downlink',
            'delay_cellular_3G', 'delay_cellular_EDGE_uplink', 'delay_cellular_EDGE_downlink',
            'delay_very_bad_network', 'delay_starlink_low_latency',
            'delay_starlink_moderate_latency', 'delay_starlink_high_latency'
        ]

        for delay_name in expected_delays:
            assert delay_name in delay_components, f"Expected delay component '{delay_name}' not found"
            assert 'delay' in delay_components[delay_name], f"Delay component '{delay_name}' missing 'delay' field"

        # Check jitter components
        jitter_components = components['jitter_components']
        expected_jitters = [
            'jitter_moderate_wireless', 'jitter_bad_wireless',
            'jitter_moderate_congestion', 'jitter_severe_congestion',
            'jitter_starlink_handover', 'jitter_wireless_handover',
            'jitter_wireless_low_snr'
        ]

        for jitter_name in expected_jitters:
            assert jitter_name in jitter_components, f"Expected jitter component '{jitter_name}' not found"
            assert 'jitter' in jitter_components[jitter_name], f"Jitter component '{jitter_name}' missing 'jitter' field"

        # Check loss components
        loss_components = components['loss_components']
        expected_losses = [
            'loss_slight', 'loss_low', 'loss_moderate', 'loss_high',
            'loss_severe', 'loss_wireless_low_snr', 'loss_very_bad_network'
        ]

        for loss_name in expected_losses:
            assert loss_name in loss_components, f"Expected loss component '{loss_name}' not found"
            assert 'loss' in loss_components[loss_name], f"Loss component '{loss_name}' missing 'loss' field"

        # Check rate components
        rate_components = components['rate_components']
        expected_rates = [
            'rate_1000M', 'rate_1M_qdepth_1', 'rate_1M_nlc', 'rate_1M_qdepth_150',
            'rate_2M_qdepth_150', 'rate_100M_qdepth_1000', 'rate_DSL_uplink',
            'rate_DSL_downlink', 'rate_cellular_EDGE_uplink', 'rate_cellular_EDGE_downlink',
            'rate_cellular_LTE_uplink', 'rate_cellular_LTE_downlink',
            'rate_cellular_3G_uplink', 'rate_cellular_3G_downlink', 'rate_cellular_3G',
            'rate_wifi_uplink', 'rate_wifi_downlink', 'rate_starlink_uplink',
            'rate_starlink_downlink'
        ]

        for rate_name in expected_rates:
            assert rate_name in rate_components, f"Expected rate component '{rate_name}' not found"
            assert 'rate_limit' in rate_components[rate_name], f"Rate component '{rate_name}' missing 'rate_limit' field"
            assert 'qdepth' in rate_components[rate_name], f"Rate component '{rate_name}' missing 'qdepth' field"


if __name__ == '__main__':
    pytest.main([__file__])