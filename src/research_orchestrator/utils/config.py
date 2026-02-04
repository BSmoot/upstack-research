# research_orchestrator/utils/config.py
"""
Configuration loading and validation.
"""

import yaml
from pathlib import Path
from typing import Any

from .config_models import load_config_with_inheritance
from .constants import Models


def load_config(config_path: Path) -> dict[str, Any]:
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


def _validate_config(config: dict[str, Any]):
    """Validate configuration structure."""

    # Check execution section
    if 'execution' not in config:
        config['execution'] = {'id': 'research_default'}

    # Note: verticals and title_clusters can be empty for partial runs (e.g., Layer 1 only)
    # Layer-specific validation happens at runtime in the orchestrator
    
    # Set defaults for execution settings
    if 'execution_settings' not in config:
        config['execution_settings'] = {}
    
    defaults = {
        'max_concurrent_agents': 5,
        'api': {
            'model': Models.HIGH_QUALITY,
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


def get_priority_combinations(config: dict[str, Any]) -> list:
    """
    Extract priority vertical x title combinations from config.

    Returns:
        List of (vertical, title) tuples for 2D playbooks
    """
    combinations = []

    priority_combos = config.get('priority_combinations')
    if priority_combos:
        for combo in priority_combos:
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


def get_priority_combinations_3d(config: dict[str, Any]) -> list:
    """
    Extract priority vertical x title x service_category combinations from config.

    For 3D playbooks (V × T × SC), combines:
    - priority_combinations (or all verticals x titles)
    - priority_service_categories

    Returns:
        List of (vertical, title, service_category) tuples for 3D playbooks.
        Empty list if priority_service_categories is not configured.
    """
    # Get priority service categories
    priority_service_categories = config.get('priority_service_categories', [])
    if not priority_service_categories:
        return []

    # Get 2D combinations (V × T)
    vt_combinations = get_priority_combinations(config)
    if not vt_combinations:
        return []

    # Generate 3D combinations (V × T × SC)
    combinations_3d = []
    for vertical, title in vt_combinations:
        for service_category in priority_service_categories:
            combinations_3d.append((vertical, title, service_category))

    return combinations_3d
