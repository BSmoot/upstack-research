# E2E Test Plan: Research Orchestrator

End-to-end test scenarios for the complete research pipeline.

## Prerequisites

- Python 3.11+
- `ANTHROPIC_API_KEY` environment variable set (for API-dependent scenarios)
- All pip dependencies installed: `pip install -r requirements.txt`
- Working directory: project root (`upstack-research/`)

## Cost Estimates

| Scenario | Approximate Cost | Requires API Key |
|----------|-----------------|------------------|
| S1: Full Pipeline | ~$49 | Yes |
| S2: Layer 0 Only | ~$2 | Yes |
| S3: Selective Vertical | ~$2 | Yes |
| S4: Selective Title | ~$2 | Yes |
| S5: Selective Service Category | ~$2 | Yes |
| S6: Force Re-run | ~$2 | Yes |
| S7: Resume After Interrupt | ~$2 | Yes |
| S8: Dry Run | $0 | No |
| S9: Invalid Config | $0 | No |
| S10: Budget Exceeded | <$0.01 | Yes |

**Total (all scenarios): ~$61**

## Scenarios

### S1: Full Pipeline

Runs the complete research flow: L0 → L1 → L2 → L3 → Playbooks → Validation → Brand Alignment.

**Command:**
```bash
python src/run_research.py --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Stdout contains: "RESEARCH EXECUTION COMPLETE"
- Output files created:
  - `outputs/e2e_minimal_test/layer_0/service_category_security.md`
  - `outputs/e2e_minimal_test/layer_1/buyer_journey.md`
  - `outputs/e2e_minimal_test/layer_1/channels_competitive.md`
  - `outputs/e2e_minimal_test/layer_1/customer_expansion.md`
  - `outputs/e2e_minimal_test/layer_1/messaging_positioning.md`
  - `outputs/e2e_minimal_test/layer_1/gtm_synthesis.md`
  - `outputs/e2e_minimal_test/layer_2/vertical_healthcare.md`
  - `outputs/e2e_minimal_test/layer_3/title_cio_cto_cluster.md`
  - `outputs/e2e_minimal_test/playbooks/playbook_healthcare_cio_cto_cluster.md`
  - `outputs/e2e_minimal_test/validation/validate_playbook_healthcare_cio_cto_cluster.md`
  - `outputs/e2e_minimal_test/brand_alignment/align_playbook_healthcare_cio_cto_cluster.md`
- Checkpoint: `checkpoints/e2e_minimal_test.json` with all agents `complete`

---

### S2: Layer 0 Only

Runs only Layer 0 (service category research).

**Command:**
```bash
python src/run_research.py --layer 0 --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Stdout contains: "RESEARCH EXECUTION COMPLETE"
- Output files created:
  - `outputs/e2e_minimal_test/layer_0/service_category_security.md`
- No Layer 1/2/3 files created

---

### S3: Selective Vertical

Runs only the healthcare vertical in Layer 2.

**Command:**
```bash
python src/run_research.py --layer 2 --verticals healthcare --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Output files created:
  - `outputs/e2e_minimal_test/layer_2/vertical_healthcare.md`
- Only healthcare vertical runs (no other verticals)

---

### S4: Selective Title

Runs only the CIO/CTO title cluster in Layer 3.

**Command:**
```bash
python src/run_research.py --layer 3 --titles cio_cto_cluster --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Output files created:
  - `outputs/e2e_minimal_test/layer_3/title_cio_cto_cluster.md`

---

### S5: Selective Service Category

Runs only the security service category in Layer 0.

**Command:**
```bash
python src/run_research.py --layer 0 --service-categories security --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Output files created:
  - `outputs/e2e_minimal_test/layer_0/service_category_security.md`

---

### S6: Force Re-run

Forces re-run of a previously completed vertical agent.

**Prerequisites:** Run S3 first to generate a checkpoint.

**Command:**
```bash
python src/run_research.py --resume e2e_minimal_test --layer 2 --verticals healthcare --force --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Prior output preserved with timestamp suffix
- New output generated at original path
- Checkpoint updated with new completion timestamp

---

### S7: Resume After Interrupt

Resumes execution from a checkpoint after interruption.

**Prerequisites:** Run S2 first (Layer 0 only), then resume to continue.

**Command:**
```bash
python src/run_research.py --resume e2e_minimal_test --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Stdout contains: "Resuming execution: e2e_minimal_test"
- Layer 0 agents not re-run (already complete)
- Remaining layers execute

---

### S8: Dry Run

Validates configuration without executing any research.

**Command:**
```bash
python src/run_research.py --dry-run --config build/config/projects/e2e_minimal_test.yaml
```

**Expected:**
- Exit code: 0
- Stdout contains: "Configuration valid!"
- Stdout contains: "Verticals: healthcare"
- Stdout contains: "Title Clusters: cio_cto_cluster"
- No API calls made
- No output files created

---

### S9: Invalid Config

Tests error handling for nonexistent config file.

**Command:**
```bash
python src/run_research.py --config nonexistent.yaml
```

**Expected:**
- Exit code: 1
- Stdout contains: "Error: Configuration file not found"

---

### S10: Budget Exceeded

Tests budget enforcement with extremely low limits.

**Command:**
```bash
python src/run_research.py --config build/config/projects/e2e_budget_fail.yaml
```

**Expected:**
- Exit code: 1
- Stderr/stdout contains error related to budget
- Checkpoint preserved for potential resume

---

## Running Tests

### Using PowerShell Script

```powershell
# Run all scenarios
.\src\tests\e2e\run_e2e.ps1

# Run a specific scenario
.\src\tests\e2e\run_e2e.ps1 -Scenario dry-run

# Preview commands without executing
.\src\tests\e2e\run_e2e.ps1 -DryRun
```

### Manual Execution

Run any scenario command from the project root directory.

## Output Directory Structure

```
outputs/{execution_id}/
  layer_0/
    service_category_{key}.md
  layer_1/
    buyer_journey.md
    channels_competitive.md
    customer_expansion.md
    messaging_positioning.md
    gtm_synthesis.md
  layer_2/
    vertical_{key}.md
  layer_3/
    title_{key}.md
  playbooks/
    playbook_{vertical}_{title}.md
    playbook_{vertical}_{title}_{service_category}.md
  validation/
    validate_playbook_{vertical}_{title}.md
  brand_alignment/
    align_playbook_{vertical}_{title}.md
```

## Checkpoint Format

JSON file at `checkpoints/{execution_id}.json`:

```json
{
  "execution_id": "e2e_minimal_test",
  "started_at": "2026-02-08T10:00:00",
  "last_updated": "2026-02-08T10:30:00",
  "layer_0": {
    "service_category_security": {
      "status": "complete",
      "output_path": "outputs/e2e_minimal_test/layer_0/service_category_security.md"
    }
  },
  "layer_1": { "...": "..." },
  "layer_2": { "...": "..." },
  "layer_3": { "...": "..." }
}
```

## Verification Checklist

After running scenarios, verify:
- [ ] All expected output files exist and are non-empty
- [ ] Checkpoint JSON contains correct agent statuses
- [ ] No API errors in logs
- [ ] Validation scores meet minimum threshold (70+)
- [ ] Force re-run preserves prior outputs
- [ ] Resume skips completed agents
- [ ] Dry run makes no API calls
- [ ] Invalid config exits cleanly with error message
- [ ] Budget exceeded preserves checkpoint
