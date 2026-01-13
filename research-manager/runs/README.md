# Research Runs

This directory contains all research runs, each with isolated configuration and context.

## Structure

```
runs/
├── manifest.json                          # Tracks all runs
├── manifest-schema.json                   # Schema for manifest
├── {run_id}/                             # Each run gets own directory
│   ├── config.yaml                       # Run configuration
│   ├── context/                          # Run-specific context files
│   │   ├── services_detailed.md          # (validation/competitive only)
│   │   ├── messaging_current.md          # (validation/competitive only)
│   │   ├── case_studies.md               # (optional)
│   │   └── competitive_intel.md          # (competitive only)
│   ├── deliverables/                     # Packaged results
│   │   ├── executive/                    # Executive package
│   │   ├── tactical/                     # Tactical package
│   │   └── strategic/                    # Strategic package
│   └── monitor.sh                        # Monitoring script
```

## Run Naming Convention

Format: `{vertical}_{research_type}_{date}`

Examples:
- `healthcare_discovery_20250113` - Pure discovery for healthcare
- `financial_validation_20250114` - Validation study for financial services
- `manufacturing_competitive_20250115` - Competitive analysis for manufacturing

## Run Lifecycle

### 1. Created
- Run directory created
- Configuration generated from template
- Context prepared (if needed)
- Added to manifest with status: `pending`

### 2. Running
- Research execution started
- Status updated to: `running`
- Checkpoint file created in `../src/checkpoints/`
- Logs written to `../src/logs/`

### 3. Review Required (optional)
- Human review gate reached
- Status updated to: `review_required`
- User must review outputs and approve before continuing

### 4. Completed
- All layers finished
- Status updated to: `completed`
- Outputs available in `../src/outputs/`
- Ready for packaging

### 5. Failed (if error)
- Error occurred during execution
- Status updated to: `failed`
- Error details captured in manifest
- Can attempt resume from checkpoint

## Run Status Values

| Status | Meaning | Actions Available |
|--------|---------|------------------|
| `pending` | Created but not started | Launch research |
| `running` | Currently executing | Monitor progress |
| `paused` | User-initiated pause | Resume execution |
| `review_required` | Waiting at review gate | Review outputs, approve/reject |
| `completed` | Successfully finished | Package results |
| `failed` | Error occurred | Check logs, attempt resume |
| `cancelled` | User cancelled | Archive or delete |

## Context Isolation

Each run maintains its own context directory to prevent contamination:

**Discovery Run** (baseline only):
```
runs/healthcare_discovery_20250113/
└── context/
    └── (empty - uses ../context/baseline.yaml only)
```

**Validation Run** (baseline + detailed):
```
runs/healthcare_validation_20250114/
└── context/
    ├── services_detailed.md
    ├── messaging_current.md
    └── case_studies.md
```

**Competitive Run** (baseline + competitive):
```
runs/manufacturing_competitive_20250115/
└── context/
    ├── services_detailed.md
    ├── messaging_current.md
    └── competitive_intel.md
```

## Manifest Management

The `manifest.json` file tracks all runs. Updated by:
- `/research-new` command (adds new run)
- `/research-status` command (reads status)
- Research orchestrator (updates status during execution)
- `/research-results` command (adds deliverables)

### Adding Run to Manifest

```json
{
  "run_id": "healthcare_discovery_20250113",
  "created": "2025-01-13T17:30:00Z",
  "research_type": "pure_discovery",
  "verticals": ["Healthcare Providers", "Health Insurance"],
  "title_clusters": ["CFO/Finance Leadership", "CIO/Technology Leadership"],
  "status": "pending",
  "execution_id": "healthcare_research_2025",
  "estimated_cost": "$24-26",
  "actual_cost": null,
  "context_used": "baseline_only",
  "started": null,
  "completed": null,
  "outputs_path": "../src/outputs/",
  "config_path": "runs/healthcare_discovery_20250113/config.yaml",
  "checkpoint_path": null,
  "error": null,
  "deliverables": [],
  "notes": "Initial healthcare market discovery"
}
```

### Updating Run Status

When research starts:
```json
{
  "status": "running",
  "started": "2025-01-13T18:00:00Z",
  "checkpoint_path": "../src/checkpoints/healthcare_research_2025.json"
}
```

When research completes:
```json
{
  "status": "completed",
  "completed": "2025-01-15T22:30:00Z",
  "actual_cost": 25.30
}
```

When deliverables created:
```json
{
  "deliverables": [
    {
      "package_type": "executive",
      "created": "2025-01-16T10:00:00Z",
      "path": "runs/healthcare_discovery_20250113/deliverables/executive/"
    }
  ]
}
```

## Best Practices

1. **One directory per run** - Never reuse run directories
2. **Descriptive run IDs** - Include vertical, type, and date
3. **Isolate context** - Each run has own context files (if needed)
4. **Track in manifest** - Always update manifest when creating/modifying runs
5. **Preserve outputs** - Keep run directories even after packaging results
6. **Document decisions** - Use `notes` field for important context

## Cleanup

Old runs can be:
- **Archived**: Move to `runs/archive/` directory
- **Deleted**: Remove directory (ensure deliverables extracted first)

Before deleting:
1. Extract any valuable deliverables
2. Note any insights in notes
3. Remove from manifest.json
4. Delete directory

## Querying Runs

### Active runs:
```bash
cat manifest.json | python -c "
import json, sys
manifest = json.load(sys.stdin)
active = [r for r in manifest['runs'] if r['status'] in ['running', 'review_required']]
for run in active:
    print(f\"{run['run_id']}: {run['status']}\")
"
```

### Completed runs:
```bash
cat manifest.json | python -c "
import json, sys
manifest = json.load(sys.stdin)
completed = [r for r in manifest['runs'] if r['status'] == 'completed']
for run in completed:
    print(f\"{run['run_id']}: \${run['actual_cost']}\")
"
```

### Failed runs:
```bash
cat manifest.json | python -c "
import json, sys
manifest = json.load(sys.stdin)
failed = [r for r in manifest['runs'] if r['status'] == 'failed']
for run in failed:
    print(f\"{run['run_id']}: {run['error']['message'] if run['error'] else 'Unknown error'}\")
"
```
