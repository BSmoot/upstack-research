# Model Selection System - Complete Guide

**Status:** ✅ Implemented  
**Date:** October 10, 2025  
**Version:** 1.0

## Overview

The research orchestrator now supports **composable model selection** - configure your model strategy once in a global defaults file, then create project-specific configs that automatically inherit these settings.

## Key Benefits

✅ **DRY (Don't Repeat Yourself)** - Define model strategy once  
✅ **Flexible Overrides** - Override at project or agent level when needed  
✅ **Cost Control** - Use cheaper models by default, expensive models selectively  
✅ **Easy Maintenance** - Update model strategy in one place

---

## Quick Start

### 1. Use the Hybrid Strategy (Recommended)

```bash
cd src
python run_research.py --config ../build/config/projects/healthcare_2025.yaml
```

**Expected cost:** $24-26 for full run  
**Strategy:** Haiku for research, Sonnet for synthesis

### 2. Test with Ultra Budget

Create a quick test config:
```yaml
# test.yaml
extends: "../config/defaults.yaml"

# Override to use only Haiku
model_strategy_override:
  default: "claude-haiku-4-20250514"
  layers:
    playbooks: "claude-haiku-4-20250514"  # Even playbooks use Haiku

execution:
  id: "quick_test"

verticals: ["Technology"]
title_clusters: ["CTO"]
priority_combinations: []
```

**Expected cost:** $5-8 for Layer 1 only

---

## Architecture

### File Structure

```
build/
├── config/
│   ├── defaults.yaml              # Global model strategy (ONE FILE)
│   └── projects/
│       ├── healthcare_2025.yaml   # Project: Healthcare
│       ├── fintech_q1.yaml        # Project: Financial services
│       └── enterprise_saas.yaml   # Project: Enterprise SaaS
```

### Configuration Hierarchy

```
1. Project-specific overrides (highest priority)
   ↓
2. Global defaults (defaults.yaml)
   ↓
3. Hardcoded fallbacks (lowest priority)
```

---

## Global Defaults (`build/config/defaults.yaml`)

This file defines your standard model selection strategy:

```yaml
model_strategy:
  # Default for all agents
  default: "claude-haiku-4-20250514"
  
  # Per-layer configuration
  layers:
    layer_1:
      default: "claude-haiku-4-20250514"
      agents:
        gtm_synthesis: "claude-sonnet-4-20250514"  # Sonnet for synthesis
    
    layer_2: "claude-haiku-4-20250514"
    layer_3: "claude-haiku-4-20250514"
    playbooks: "claude-sonnet-4-20250514"  # Sonnet for playbooks
  
  # Model-specific settings
  model_configs:
    "claude-haiku-4-20250514":
      max_tokens: 8000
      temperature: 1.0
    
    "claude-sonnet-4-20250514":
      max_tokens: 16000
      temperature: 1.0
  
  # Budget per model
  budgets:
    "claude-haiku-4-20250514":
      max_searches_per_agent: 15
      estimated_cost_per_agent: 1.0
    
    "claude-sonnet-4-20250514":
      max_searches_per_agent: 20
      estimated_cost_per_agent: 8.0
```

**This is the only file you need to edit to change model strategy globally.**

---

## Project Configs

Project configs inherit from defaults.yaml and add project-specific details:

```yaml
# healthcare_2025.yaml
extends: "../defaults.yaml"  # ← Inherit model strategy

execution:
  id: "healthcare_research_2025"

verticals:
  - "Healthcare Providers"
  - "Health Insurance"

title_clusters:
  - "CFO/Finance Leadership"
  - "CIO/Technology Leadership"

# Project uses model strategy from defaults.yaml
# Expected cost: $24-26
```

---

## Model Resolution Logic

When an agent needs a model, the system resolves in this order:

### 1. Check Agent-Specific Override

```yaml
model_strategy:
  layers:
    layer_1:
      agents:
        buyer_journey: "claude-sonnet-4-20250514"  # ← This agent uses Sonnet
```

Result: `buyer_journey` uses Sonnet 4

### 2. Check Layer Default

```yaml
model_strategy:
  layers:
    layer_1:
      default: "claude-haiku-4-20250514"  # ← Layer default
```

Result: Other Layer 1 agents use Haiku 4

### 3. Check Global Default

```yaml
model_strategy:
  default: "claude-haiku-4-20250514"  # ← Global default
```

Result: Any agent without layer/agent override uses Haiku 4

### 4. Hardcoded Fallback

If nothing specified: `claude-haiku-4-20250514`

---

## Cost Estimation

Before running research, estimate costs:

```python
from research_orchestrator.utils.config_models import estimate_research_cost
from research_orchestrator.utils.config import load_config

config = load_config("path/to/config.yaml")
estimate = estimate_research_cost(config)

print(f"Total estimated cost: ${estimate['total_estimated_cost']:.2f}")
print(f"\nBy model:")
for model, cost in estimate['breakdown_by_model'].items():
    print(f"  {model}: ${cost:.2f}")
```

**Example output:**
```
Total estimated cost: $26.00

By model:
  claude-haiku-4-20250514: $14.00
  claude-sonnet-4-20250514: $12.00
```

---

## Pre-Configured Strategies

### Strategy 1: Hybrid (Default - RECOMMENDED)

**File:** `build/config/defaults.yaml` (already configured)

**Strategy:**
- Haiku for all research agents
- Sonnet for gtm_synthesis and playbooks

**Cost:** $35-50 per full run  
**Quality:** 90-95% of full Sonnet

**Use when:**
- Standard production runs
- Good balance of cost and quality
- Most use cases

### Strategy 2: Ultra Budget

**To use:** Override in project config:
```yaml
extends: "../defaults.yaml"

model_strategy_override:
  default: "claude-haiku-4-20250514"
  layers:
    layer_1: "claude-haiku-4-20250514"
    layer_2: "claude-haiku-4-20250514"
    layer_3: "claude-haiku-4-20250514"
    playbooks: "claude-haiku-4-20250514"
```

**Cost:** $20-30 per full run  
**Quality:** 85-90% of full Sonnet

**Use when:**
- Testing and iteration
- Budget constraints
- Quick exploratory research

### Strategy 3: High Quality

**To use:** Override in project config:
```yaml
extends: "../defaults.yaml"

model_strategy_override:
  default: "claude-sonnet-4-20250514"
```

**Cost:** $150-230 per full run  
**Quality:** 100%, highest quality

**Use when:**
- Critical strategic decisions
- Final production runs
- Quality > cost

---

## Override Examples

### Example 1: Single Agent Override

Use Sonnet for one specific agent:

```yaml
extends: "../defaults.yaml"

model_strategy_override:
  layers:
    layer_1:
      agents:
        buyer_journey: "claude-sonnet-4-20250514"

# All other agents use defaults.yaml settings
# Only buyer_journey uses Sonnet
```

### Example 2: Layer Override

Use Sonnet for entire Layer 1:

```yaml
extends: "../defaults.yaml"

model_strategy_override:
  layers:
    layer_1: "claude-sonnet-4-20250514"

# Layer 1: All Sonnet
# Layers 2-3: Use defaults (Haiku)
# Playbooks: Use defaults (Sonnet)
```

### Example 3: Selective Quality

High quality for critical agents only:

```yaml
extends: "../defaults.yaml"

model_strategy_override:
  layers:
    layer_1:
      default: "claude-haiku-4-20250514"
      agents:
        messaging_positioning: "claude-sonnet-4-20250514"
        gtm_synthesis: "claude-sonnet-4-20250514"
    
    playbooks: "claude-sonnet-4-20250514"

# Most research: Haiku (cheap)
# Critical synthesis: Sonnet (quality)
# Playbooks: Sonnet (quality)
```

---

## Migration Guide

### From Old System to New System

**Old way (no inheritance):**
```yaml
# Every config file had full settings
execution_settings:
  api:
    model: "claude-sonnet-4-20250514"
    max_tokens: 16000
    # ... all settings duplicated

verticals: [...]
```

**New way (with inheritance):**
```yaml
# defaults.yaml has model strategy
model_strategy:
  default: "claude-haiku-4-20250514"
  # ... defined once

# Project configs just reference it
extends: "../defaults.yaml"
verticals: [...]
```

### Migration Steps

1. **Create `build/config/defaults.yaml`** (already done)
2. **Move existing config to `build/config/projects/`**
3. **Add `extends: "../defaults.yaml"`** at top
4. **Remove duplicate settings** (api, execution_settings, etc.)
5. **Keep only project-specific** (verticals, titles, priorities)
6. **Test** with one project config

---

## Troubleshooting

### Issue: "extends path not found"

**Problem:** Relative path to defaults.yaml is wrong

**Solution:** Check your directory structure:
```
build/config/projects/your_project.yaml
build/config/defaults.yaml
```

Path should be: `extends: "../defaults.yaml"`

### Issue: "Model not found"

**Problem:** Typo in model name

**Solution:** Use exact model names:
- `claude-haiku-4-20250514` ✓
- `claude-sonnet-4-20250514` ✓
- `claude-haiku-4` ✗ (wrong)

### Issue: "Costs higher than expected"

**Problem:** May be using Sonnet when expecting Haiku

**Solution:** Check logs for model selection:
```
[agent_name] Model: claude-sonnet-4-20250514, Max tokens: 16000
```

Verify your model_strategy settings.

### Issue: "Agent using wrong model"

**Problem:** Override hierarchy not working as expected

**Solution:** Remember priority order:
1. Agent-specific override (highest)
2. Layer default
3. Global default
4. Hardcoded fallback (lowest)

---

## Best Practices

1. **Edit defaults.yaml once** - Don't duplicate model settings
2. **Use inheritance** - Always use `extends:` in project configs
3. **Override sparingly** - Only override when project needs different strategy
4. **Test with Haiku first** - Verify quality before using Sonnet
5. **Monitor actual costs** - Compare estimates vs actual at console.anthropic.com
6. **Document overrides** - Add comments explaining why you override

---

## API Reference

### `load_config_with_inheritance(config_path)`

Load config with inheritance support.

```python
from research_orchestrator.utils.config_models import load_config_with_inheritance

config = load_config_with_inheritance(Path("config.yaml"))
```

### `get_model_for_agent(config, layer, agent_name)`

Resolve which model to use for an agent.

```python
from research_orchestrator.utils.config_models import get_model_for_agent

model = get_model_for_agent(config, "layer_1", "buyer_journey")
# Returns: "claude-haiku-4-20250514"
```

### `get_model_config(config, model)`

Get model-specific settings.

```python
from research_orchestrator.utils.config_models import get_model_config

settings = get_model_config(config, "claude-haiku-4-20250514")
# Returns: {'max_tokens': 8000, 'temperature': 1.0, ...}
```

### `estimate_research_cost(config)`

Estimate total cost before execution.

```python
from research_orchestrator.utils.config_models import estimate_research_cost

estimate = estimate_research_cost(config)
print(f"Total: ${estimate['total_estimated_cost']:.2f}")
```

---

## Summary

**Model selection is now:**
- ✅ Composable (define once, reuse everywhere)
- ✅ Flexible (override at any level)
- ✅ Cost-effective (use cheap models by default)
- ✅ Maintainable (one place to update)

**To get started:**
1. Use `build/config/projects/healthcare_2025.yaml` as template
2. Change verticals/titles for your research
3. Run: `python run_research.py --config ../build/config/projects/your_project.yaml`
4. Monitor costs and adjust strategy as needed

**For questions:**
- Model selection: This guide
- Cost analysis: `src/COST_ANALYSIS.md`
- Bug fixes: `src/FIX_SUMMARY_20251010.md`
- General system: `src/HANDOFF.md`
