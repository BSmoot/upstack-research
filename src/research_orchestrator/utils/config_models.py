# research_orchestrator/utils/config_models.py
"""
Model selection and configuration resolution utilities.
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import yaml

from .constants import Models


def load_config_with_inheritance(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration with inheritance support.
    
    Supports 'extends' keyword to inherit from parent configs.
    Project configs can override parent settings.
    
    Args:
        config_path: Path to project configuration file
        
    Returns:
        Merged configuration dictionary
        
    Example:
        # parent.yaml
        model_strategy:
          default: "claude-haiku-4"
        
        # project.yaml
        extends: "../parent.yaml"
        verticals: ["Healthcare"]
        
        # Result: project inherits model_strategy from parent
    """
    config_path = Path(config_path)
    
    # Load project config
    with open(config_path, 'r') as f:
        project_config = yaml.safe_load(f)
    
    # Check for inheritance
    if 'extends' in project_config:
        parent_path = config_path.parent / project_config['extends']

        # Recursive load to support multi-level inheritance
        parent_config = load_config_with_inheritance(parent_path)

        # Merge configs (project overrides parent)
        merged = deep_merge(parent_config, project_config)

        # Remove 'extends' from final config
        merged.pop('extends', None)

        config = merged
    else:
        config = project_config

    # Validate with Pydantic schema and apply defaults
    from .config_schema import validate_research_config
    return validate_research_config(config)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries. Override takes precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Override takes precedence
            result[key] = value
    
    return result


def get_model_for_agent(
    config: Dict[str, Any], 
    layer: str, 
    agent_name: str
) -> str:
    """
    Resolve which model to use for a specific agent.
    
    Resolution order (first match wins):
    1. model_strategy.layers.{layer}.agents.{agent_name}
    2. model_strategy.layers.{layer}.default
    3. model_strategy.layers.{layer} (if string)
    4. model_strategy.default
    5. Hardcoded fallback (claude-haiku-4-20250514)
    
    Args:
        config: Configuration dictionary
        layer: Layer name (e.g., 'layer_1', 'layer_2', 'playbooks')
        agent_name: Agent name (e.g., 'buyer_journey')
        
    Returns:
        Model identifier string
        
    Examples:
        >>> config = {
        ...     'model_strategy': {
        ...         'default': 'claude-haiku-4-20250514',
        ...         'layers': {
        ...             'layer_1': {
        ...                 'default': 'claude-haiku-4-20250514',
        ...                 'agents': {
        ...                     'gtm_synthesis': 'claude-sonnet-4-20250514'
        ...                 }
        ...             }
        ...         }
        ...     }
        ... }
        >>> get_model_for_agent(config, 'layer_1', 'gtm_synthesis')
        'claude-sonnet-4-20250514'
        >>> get_model_for_agent(config, 'layer_1', 'buyer_journey')
        'claude-haiku-4-20250514'
    """
    strategy = config.get('model_strategy', {})
    
    # 1. Check agent-specific override
    layer_config = strategy.get('layers', {}).get(layer, {})
    if isinstance(layer_config, dict):
        agent_model = layer_config.get('agents', {}).get(agent_name)
        if agent_model:
            return agent_model
        
        # 2. Check layer default
        if 'default' in layer_config:
            return layer_config['default']
    
    # 3. Check if layer config is a simple string
    elif isinstance(layer_config, str):
        return layer_config
    
    # 4. Check global default
    if 'default' in strategy:
        return strategy['default']
    
    # 5. Hardcoded fallback
    return Models.DEFAULT


def get_model_config(
    config: Dict[str, Any],
    model: str
) -> Dict[str, Any]:
    """
    Get model-specific configuration (max_tokens, temperature, etc).
    
    Args:
        config: Configuration dictionary
        model: Model identifier
        
    Returns:
        Dictionary with model-specific settings
        
    Example:
        >>> config = {
        ...     'model_strategy': {
        ...         'model_configs': {
        ...             'claude-haiku-4-20250514': {
        ...                 'max_tokens': 8000,
        ...                 'temperature': 1.0
        ...             }
        ...         }
        ...     }
        ... }
        >>> get_model_config(config, 'claude-haiku-4-20250514')
        {'max_tokens': 8000, 'temperature': 1.0}
    """
    model_configs = config.get('model_strategy', {}).get('model_configs', {})
    
    # Return model-specific config or defaults
    return model_configs.get(model, {
        'max_tokens': 8000,
        'temperature': 1.0,
        'timeout_seconds': 300
    })


def get_search_budget_for_model(
    config: Dict[str, Any],
    model: str
) -> int:
    """
    Get search budget for a specific model.
    
    Args:
        config: Configuration dictionary
        model: Model identifier
        
    Returns:
        Maximum searches allowed for this model
    """
    budgets = config.get('model_strategy', {}).get('budgets', {})
    model_budget = budgets.get(model, {})
    
    return model_budget.get('max_searches_per_agent', 15)


def estimate_agent_cost(
    config: Dict[str, Any],
    layer: str,
    agent_name: str
) -> float:
    """
    Estimate cost for a single agent based on its assigned model.
    
    Args:
        config: Configuration dictionary
        layer: Layer name
        agent_name: Agent name
        
    Returns:
        Estimated cost in USD
    """
    model = get_model_for_agent(config, layer, agent_name)
    budgets = config.get('model_strategy', {}).get('budgets', {})
    model_budget = budgets.get(model, {})
    
    return model_budget.get('estimated_cost_per_agent', 5.0)


def estimate_research_cost(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate total cost before execution.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with cost breakdown by layer and model
        
    Example return:
        {
            'layer_1': {
                'agents': [
                    {'name': 'buyer_journey', 'model': 'haiku', 'cost': 1.0},
                    ...
                ],
                'total_cost': 8.0
            },
            'layer_2': {...},
            'layer_3': {...},
            'playbooks': {...},
            'total_estimated_cost': 45.0,
            'breakdown_by_model': {
                'claude-haiku-4-20250514': 37.0,
                'claude-sonnet-4-20250514': 8.0
            }
        }
    """
    # Layer 1 agents (hardcoded list)
    layer_1_agents = [
        'buyer_journey',
        'channels_competitive',
        'customer_expansion',
        'messaging_positioning',
        'gtm_synthesis'
    ]
    
    # Estimate Layer 1
    layer_1_estimate = {
        'agents': [],
        'total_cost': 0.0
    }
    for agent in layer_1_agents:
        model = get_model_for_agent(config, 'layer_1', agent)
        cost = estimate_agent_cost(config, 'layer_1', agent)
        layer_1_estimate['agents'].append({
            'name': agent,
            'model': model,
            'cost': cost
        })
        layer_1_estimate['total_cost'] += cost
    
    # Estimate Layer 2 (verticals)
    verticals = config.get('verticals', [])
    layer_2_estimate = {
        'agents': [],
        'total_cost': 0.0
    }
    for vertical in verticals:
        agent_name = f"vertical_{vertical}"
        model = get_model_for_agent(config, 'layer_2', agent_name)
        cost = estimate_agent_cost(config, 'layer_2', agent_name)
        layer_2_estimate['agents'].append({
            'name': agent_name,
            'model': model,
            'cost': cost
        })
        layer_2_estimate['total_cost'] += cost
    
    # Estimate Layer 3 (titles)
    titles = config.get('title_clusters', [])
    layer_3_estimate = {
        'agents': [],
        'total_cost': 0.0
    }
    for title in titles:
        agent_name = f"title_{title}"
        model = get_model_for_agent(config, 'layer_3', agent_name)
        cost = estimate_agent_cost(config, 'layer_3', agent_name)
        layer_3_estimate['agents'].append({
            'name': agent_name,
            'model': model,
            'cost': cost
        })
        layer_3_estimate['total_cost'] += cost
    
    # Estimate Playbooks
    from .config import get_priority_combinations
    combinations = get_priority_combinations(config)
    playbooks_estimate = {
        'count': len(combinations),
        'agents': [],
        'total_cost': 0.0
    }
    for vertical, title in combinations:
        agent_name = f"playbook_{vertical}_{title}"
        model = get_model_for_agent(config, 'playbooks', agent_name)
        cost = estimate_agent_cost(config, 'playbooks', agent_name)
        playbooks_estimate['agents'].append({
            'name': agent_name,
            'model': model,
            'cost': cost
        })
        playbooks_estimate['total_cost'] += cost
    
    # Calculate totals
    total_cost = (
        layer_1_estimate['total_cost'] +
        layer_2_estimate['total_cost'] +
        layer_3_estimate['total_cost'] +
        playbooks_estimate['total_cost']
    )
    
    # Breakdown by model
    model_costs: Dict[str, float] = {}
    for layer_est in [layer_1_estimate, layer_2_estimate, layer_3_estimate, playbooks_estimate]:
        for agent in layer_est.get('agents', []):
            model = agent['model']
            cost = agent['cost']
            model_costs[model] = model_costs.get(model, 0.0) + cost
    
    return {
        'layer_1': layer_1_estimate,
        'layer_2': layer_2_estimate,
        'layer_3': layer_3_estimate,
        'playbooks': playbooks_estimate,
        'total_estimated_cost': total_cost,
        'breakdown_by_model': model_costs
    }
