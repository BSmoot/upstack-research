#!/usr/bin/env python3
"""
Test script for model selection system.
Run this to verify the composable model selection implementation.
"""

from pathlib import Path
from research_orchestrator.utils.config import load_config
from research_orchestrator.utils.config_models import (
    load_config_with_inheritance,
    get_model_for_agent,
    get_model_config,
    estimate_research_cost
)

def test_config_inheritance():
    """Test that config inheritance works."""
    print("=" * 60)
    print("TEST 1: Config Inheritance")
    print("=" * 60)
    
    config_path = Path('../build/config/projects/healthcare_2025.yaml')
    config = load_config_with_inheritance(config_path)
    
    # Check that model_strategy was inherited
    assert 'model_strategy' in config, "model_strategy not found in config"
    assert 'default' in config['model_strategy'], "model_strategy.default not found"
    
    print("✓ Config inheritance works")
    print(f"  Default model: {config['model_strategy']['default']}")
    print()

def test_model_resolution():
    """Test that model resolution works correctly."""
    print("=" * 60)
    print("TEST 2: Model Resolution")
    print("=" * 60)
    
    config_path = Path('../build/config/projects/healthcare_2025.yaml')
    config = load_config_with_inheritance(config_path)
    
    # Test Layer 1 agents
    buyer_journey_model = get_model_for_agent(config, 'layer_1', 'buyer_journey')
    gtm_synthesis_model = get_model_for_agent(config, 'layer_1', 'gtm_synthesis')
    
    print(f"✓ buyer_journey uses: {buyer_journey_model}")
    print(f"✓ gtm_synthesis uses: {gtm_synthesis_model}")
    
    # Verify expected models
    assert buyer_journey_model == 'claude-haiku-4-20250514', \
        f"Expected Haiku for buyer_journey, got {buyer_journey_model}"
    assert gtm_synthesis_model == 'claude-sonnet-4-20250514', \
        f"Expected Sonnet for gtm_synthesis, got {gtm_synthesis_model}"
    
    # Test playbooks
    playbook_model = get_model_for_agent(config, 'playbooks', 'any_playbook')
    print(f"✓ playbooks use: {playbook_model}")
    assert playbook_model == 'claude-sonnet-4-20250514', \
        f"Expected Sonnet for playbooks, got {playbook_model}"
    
    print()

def test_model_config():
    """Test that model-specific config is retrieved correctly."""
    print("=" * 60)
    print("TEST 3: Model Configuration")
    print("=" * 60)
    
    config_path = Path('../build/config/projects/healthcare_2025.yaml')
    config = load_config_with_inheritance(config_path)
    
    # Test Haiku config
    haiku_config = get_model_config(config, 'claude-haiku-4-20250514')
    print(f"✓ Haiku config: {haiku_config}")
    assert haiku_config['max_tokens'] == 8000, \
        f"Expected 8000 tokens for Haiku, got {haiku_config['max_tokens']}"
    
    # Test Sonnet config
    sonnet_config = get_model_config(config, 'claude-sonnet-4-20250514')
    print(f"✓ Sonnet config: {sonnet_config}")
    assert sonnet_config['max_tokens'] == 16000, \
        f"Expected 16000 tokens for Sonnet, got {sonnet_config['max_tokens']}"
    
    print()

def test_cost_estimation():
    """Test cost estimation function."""
    print("=" * 60)
    print("TEST 4: Cost Estimation")
    print("=" * 60)
    
    config_path = Path('../build/config/projects/healthcare_2025.yaml')
    config = load_config(config_path)
    
    estimate = estimate_research_cost(config)
    
    print(f"✓ Total estimated cost: ${estimate['total_estimated_cost']:.2f}")
    print()
    print("Breakdown by layer:")
    print(f"  Layer 1: ${estimate['layer_1']['total_cost']:.2f} ({len(estimate['layer_1']['agents'])} agents)")
    print(f"  Layer 2: ${estimate['layer_2']['total_cost']:.2f} ({len(estimate['layer_2']['agents'])} agents)")
    print(f"  Layer 3: ${estimate['layer_3']['total_cost']:.2f} ({len(estimate['layer_3']['agents'])} agents)")
    print(f"  Playbooks: ${estimate['playbooks']['total_cost']:.2f} ({estimate['playbooks']['count']} playbooks)")
    print()
    print("Breakdown by model:")
    for model, cost in estimate['breakdown_by_model'].items():
        model_name = model.split('-')[1].capitalize()  # Extract 'haiku' or 'sonnet'
        print(f"  {model_name}: ${cost:.2f}")
    print()
    
    # Verify estimates are reasonable
    assert estimate['total_estimated_cost'] > 0, "Total cost should be > 0"
    assert estimate['total_estimated_cost'] < 100, "Total cost should be < $100 for hybrid strategy"

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Model Selection System Tests" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_config_inheritance()
        test_model_resolution()
        test_model_config()
        test_cost_estimation()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("The composable model selection system is working correctly!")
        print()
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        return 1
    
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST ERROR")
        print("=" * 60)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
