# research_orchestrator/utils/config.py
"""
Configuration loading and validation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .config_models import load_config_with_inheritance


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate research configuration from YAML file.
    
    Supports inheritance via 'extends' keyword.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load config with inheritance support
    config = load_config_with_inheritance(config_path)
    
    # Validate required fields
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]):
    """Validate configuration structure."""
    
    # Check execution section
    if 'execution' not in config:
        config['execution'] = {'id': 'research_default'}
    
    # Check verticals
    if 'verticals' not in config or not config['verticals']:
        raise ValueError("Configuration must specify at least one vertical")
    
    # Check title clusters
    if 'title_clusters' not in config or not config['title_clusters']:
        raise ValueError("Configuration must specify at least one title cluster")
    
    # Set defaults for execution settings
    if 'execution_settings' not in config:
        config['execution_settings'] = {}
    
    defaults = {
        'max_concurrent_agents': 5,
        'api': {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 16000,
            'temperature': 1.0,
            'timeout_seconds': 300
        },
        'research_depth': 'comprehensive',
        'checkpointing': {
            'enabled': True,
            'frequency': 'per_agent',
            'directory': 'checkpoints'
        },
        'review_gates': {
            'after_layer_1': True,
            'after_layer_2': True,
            'after_layer_3': False
        },
        'outputs': {
            'directory': 'outputs',
            'format': 'markdown',
            'include_conversation_history': False
        },
        'logging': {
            'level': 'INFO',
            'directory': 'logs',
            'console_output': True
        }
    }
    
    # Merge defaults
    for key, value in defaults.items():
        if key not in config['execution_settings']:
            config['execution_settings'][key] = value
        elif isinstance(value, dict):
            for subkey, subvalue in value.items():
                if subkey not in config['execution_settings'][key]:
                    config['execution_settings'][key][subkey] = subvalue


def get_priority_combinations(config: Dict[str, Any]) -> list:
    """
    Extract priority vertical x title combinations from config.
    
    Returns:
        List of (vertical, title) tuples
    """
    combinations = []
    
    if 'priority_combinations' in config:
        for combo in config['priority_combinations']:
            vertical = combo.get('vertical')
            titles = combo.get('titles', [])
            for title in titles:
                combinations.append((vertical, title))
    else:
        # Generate all combinations if no priorities specified
        verticals = config.get('verticals', [])
        titles = config.get('title_clusters', [])
        for vertical in verticals:
            for title in titles:
                combinations.append((vertical, title))
    
    return combinations
