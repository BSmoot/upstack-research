# tests/test_config_inheritance.py
"""
Unit tests for configuration inheritance and validation.

Tests the 'extends' keyword functionality and configuration loading.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from research_orchestrator.utils.config import load_config


class TestConfigInheritance:
    """Test configuration inheritance via 'extends' keyword."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_simple_config_load_without_extends(self, temp_config_dir):
        """Test loading a simple config without inheritance."""
        config_path = temp_config_dir / "simple.yaml"

        config_data = {
            'execution': {'id': 'test_simple'},
            'verticals': ['healthcare'],
            'title_clusters': ['cfo_cluster'],
            'execution_settings': {
                'api': {'model': 'claude-haiku-4-20250514', 'max_tokens': 8000}
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        loaded_config = load_config(config_path)

        assert loaded_config['execution']['id'] == 'test_simple'
        assert 'healthcare' in loaded_config['verticals']
        assert 'cfo_cluster' in loaded_config['title_clusters']

    def test_config_extends_base_config(self, temp_config_dir):
        """Test that child config extends base config correctly."""
        # Create base config
        base_path = temp_config_dir / "base.yaml"
        base_data = {
            'execution': {'id': 'base_execution'},
            'verticals': ['healthcare', 'financial_services'],
            'title_clusters': ['cfo_cluster'],
            'execution_settings': {
                'api': {'model': 'claude-haiku-4-20250514', 'max_tokens': 8000},
                'budget': {'max_searches': 100, 'max_cost_usd': 50.0}
            }
        }

        with open(base_path, 'w') as f:
            yaml.dump(base_data, f)

        # Create child config that extends base
        child_path = temp_config_dir / "child.yaml"
        child_data = {
            'extends': str(base_path),
            'execution': {'id': 'child_execution'},
            'verticals': ['manufacturing']  # Override verticals
        }

        with open(child_path, 'w') as f:
            yaml.dump(child_data, f)

        loaded_config = load_config(child_path)

        # Child should override execution.id
        assert loaded_config['execution']['id'] == 'child_execution'

        # Child should override verticals
        assert loaded_config['verticals'] == ['manufacturing']

        # Child should inherit title_clusters from base
        assert loaded_config['title_clusters'] == ['cfo_cluster']

        # Child should inherit execution_settings from base
        assert loaded_config['execution_settings']['budget']['max_searches'] == 100

    def test_config_extends_merges_nested_dicts(self, temp_config_dir):
        """Test that nested dictionaries are merged correctly."""
        base_path = temp_config_dir / "base.yaml"
        base_data = {
            'execution': {'id': 'base'},
            'verticals': ['healthcare'],
            'title_clusters': ['cfo_cluster'],
            'execution_settings': {
                'api': {
                    'model': 'claude-haiku-4-20250514',
                    'max_tokens': 8000,
                    'temperature': 1.0
                },
                'budget': {
                    'max_searches': 100,
                    'max_cost_usd': 50.0
                }
            }
        }

        with open(base_path, 'w') as f:
            yaml.dump(base_data, f)

        child_path = temp_config_dir / "child.yaml"
        child_data = {
            'extends': str(base_path),
            'execution': {'id': 'child'},
            'execution_settings': {
                'api': {
                    'max_tokens': 16000  # Override only max_tokens
                }
            }
        }

        with open(child_path, 'w') as f:
            yaml.dump(child_data, f)

        loaded_config = load_config(child_path)

        # max_tokens should be overridden
        assert loaded_config['execution_settings']['api']['max_tokens'] == 16000

        # model and temperature should be inherited
        assert loaded_config['execution_settings']['api']['model'] == 'claude-haiku-4-20250514'
        assert loaded_config['execution_settings']['api']['temperature'] == 1.0

        # budget should be inherited entirely
        assert loaded_config['execution_settings']['budget']['max_searches'] == 100

    def test_config_validation_adds_defaults(self, temp_config_dir):
        """Test that config validation adds default execution settings."""
        config_path = temp_config_dir / "minimal.yaml"
        config_data = {
            'execution': {'id': 'test'},
            'verticals': ['healthcare'],
            'title_clusters': ['cfo_cluster']
            # No execution_settings
        }

        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        loaded_config = load_config(config_path)

        # Should have defaults added
        assert 'execution_settings' in loaded_config
        assert 'api' in loaded_config['execution_settings']
        assert 'budget' in loaded_config['execution_settings']
        assert 'logging' in loaded_config['execution_settings']
        assert 'checkpointing' in loaded_config['execution_settings']

    def test_config_validation_preserves_custom_settings(self, temp_config_dir):
        """Test that custom settings are preserved when defaults are added."""
        config_path = temp_config_dir / "custom.yaml"
        config_data = {
            'execution': {'id': 'test'},
            'verticals': ['healthcare'],
            'title_clusters': ['cfo_cluster'],
            'execution_settings': {
                'api': {
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': 32000
                }
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        loaded_config = load_config(config_path)

        # Custom settings should be preserved
        assert loaded_config['execution_settings']['api']['model'] == 'claude-sonnet-4-20250514'
        assert loaded_config['execution_settings']['api']['max_tokens'] == 32000

        # Defaults should be added for missing fields
        assert 'budget' in loaded_config['execution_settings']
