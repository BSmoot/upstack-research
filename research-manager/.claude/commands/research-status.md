# Check Research Status

Display status of all research runs: completed, running, paused, or failed.

## What This Does

1. Read `runs/manifest.json` to get all runs
2. Check checkpoint files in `../src/checkpoints/` for current status
3. Calculate progress, costs, and time elapsed
4. Display in organized format with action items

## Execution

### Step 1: Load Manifest

```bash
cat runs/manifest.json
```

If file doesn't exist, inform user no runs have been created yet.

### Step 2: Check Each Run Status

For each run in manifest:

```bash
# Check if checkpoint exists
cat ../src/checkpoints/{execution_id}.json

# Get latest log entries
tail -20 ../src/logs/execution_{timestamp}.log
```

### Step 3: Display Status

Format:
```
## Current Research Runs

### ✅ COMPLETED: {run_id}
- Completed: {date}
- Cost: ${actual_cost}
- Outputs: {output_path}
- Action: Run `/research-results {run_id}` to package

### 🔄 RUNNING: {run_id}
- Progress: Layer {X} ({Y}/{Z} agents complete)
- Time: {hours} elapsed
- Cost: ${current_cost} (${estimated} estimated)
- ETA: {remaining_hours} remaining

### ⏸️ PAUSED: {run_id}
- Status: {reason} (review gate / error / user pause)
- Action: {what_user_needs_to_do}

### ❌ FAILED: {run_id}
- Error: {error_message}
- Failed at: Layer {X}, agent {agent_name}
- Action: Check logs at {log_path}
```

### Step 4: Provide Actions

List available commands:
- `/research-monitor {run_id}` - Tail logs for specific run
- `/research-results {run_id}` - Package completed run results
- `/research-new` - Start new research project

## Example

```
/research-status
```
