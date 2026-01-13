# Monitor Research Run

Tail logs for a specific research run to see real-time progress.

## Arguments

- `$ARGUMENTS` - Run ID to monitor (e.g., "healthcare_discovery_20250113")

## What This Does

1. Find the execution ID for the specified run from manifest
2. Locate the corresponding log file
3. Display recent log entries
4. Offer to tail logs in real-time

## Execution

### Step 1: Parse Arguments

```
Run ID: $ARGUMENTS
```

If no run ID provided, list available runs and ask user to specify.

### Step 2: Find Execution ID

```bash
cat runs/manifest.json | python -c "
import json, sys
manifest = json.load(sys.stdin)
run_id = '$ARGUMENTS'
run = next((r for r in manifest['runs'] if r['run_id'] == run_id), None)
if run:
    print(run['execution_id'])
else:
    print('ERROR: Run not found')
    sys.exit(1)
"
```

### Step 3: Locate Log File

```bash
# Find log file by execution ID
ls ../src/logs/execution_*{execution_id}*.log
```

### Step 4: Display Recent Entries

```bash
# Show last 50 lines
tail -50 {log_file}
```

### Step 5: Offer Tail Option

Ask user:
```
Monitor logs in real-time? [Y/n]

If yes:
  tail -f {log_file} | grep -E "(INFO|Complete|Progress|ERROR)"
```

## Progress Indicators

Parse log for key events:
- "Agent {name} starting" → Agent started
- "Turn {N} tokens: in={X}, out={Y}" → Agent progress
- "Agent {name} completed" → Agent finished
- "Layer {N} complete" → Layer finished
- "Review gate" → Waiting for user input
- "ERROR" → Something failed

Display summary:
```
## Progress Summary for {run_id}

Layer 1: ████████░░ 80% (4/5 agents complete)
  ✅ buyer_journey (2.5 hours, $3.20)
  ✅ channels_competitive (3.1 hours, $4.50)
  ✅ customer_expansion (2.8 hours, $3.80)
  ✅ messaging_positioning (1.9 hours, $2.10)
  🔄 gtm_synthesis (in progress, 0.5 hours, $1.20 so far)

Layer 2: ░░░░░░░░░░ 0% (not started)
Layer 3: ░░░░░░░░░░ 0% (not started)

Total Cost: $14.80 / $24-26 estimated
Time Elapsed: 11.8 hours
```

## Example

```
/research-monitor healthcare_discovery_20250113
```
