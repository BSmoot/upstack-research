# Context Management

This directory contains **baseline context** shared across all research runs.

## Files

- `baseline.yaml` - Core company information shared across all runs
- `glossary.yaml` - Industry terminology and acronyms reference (200+ terms)
- `audience-personas.yaml` - Enterprise IT decision-maker profiles and communication preferences
- `writing-standards.yaml` - Voice and tone guidelines for all research output

## What Goes Here

**INCLUDE** (shared facts):
- Company name and description
- Service categories (high-level)
- Geographic focus
- General target market segments

**DO NOT INCLUDE** (run-specific):
- Detailed service descriptions → `runs/{run_id}/context/`
- Current messaging/positioning → `runs/{run_id}/context/`
- Case studies → `runs/{run_id}/context/`
- Competitive materials → `runs/{run_id}/context/`
- Pricing details → `runs/{run_id}/context/`

## Context Isolation Strategy

```
context/baseline.yaml
  ↓
  Used by ALL runs

runs/healthcare_discovery_20250113/context/
  ↓
  Used ONLY by this specific run
  NO detailed materials (pure discovery)

runs/healthcare_validation_20250114/context/
  ↓
  Used ONLY by this specific run
  INCLUDES detailed materials (validation)
```

## Updating Baseline Context

When company facts change:
1. Edit `baseline.yaml`
2. Version bump (update `version` field)
3. Update `updated` date
4. Changes apply to all NEW runs
5. Existing runs keep their configuration unchanged

## Run-Specific Context

Created by elicitation agent in:
`runs/{run_id}/context/`

See individual run directories for their context files.
