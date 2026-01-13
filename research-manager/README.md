# Research Manager

**Conversational interface for managing UPSTACK research projects through Claude Code.**

Navigate to this directory and run `claude` to access the research elicitation agent that helps you set up, execute, monitor, and package market research.

## Quick Start

```bash
cd research-manager
claude
```

Then use slash commands:
- `/research-new` - Start new research project (guided setup)
- `/research-status` - Check status of all runs
- `/research-monitor {run_id}` - Monitor specific run progress
- `/research-results {run_id}` - Package completed research

## What This Does

The research manager provides a conversational interface to:

1. **Define Research** - Ask questions to understand what you want to research
2. **Manage Context** - Guide appropriate context inclusion (baseline vs detailed)
3. **Isolate Runs** - Create separate runs that don't contaminate each other
4. **Track Progress** - Monitor research execution and costs
5. **Package Results** - Create stakeholder-ready deliverables

## Directory Structure

```
research-manager/
├── .claude/
│   ├── agents/
│   │   └── research-elicitation.md    # Main agent
│   ├── commands/
│   │   ├── research-new.md            # /research-new
│   │   ├── research-status.md         # /research-status
│   │   ├── research-monitor.md        # /research-monitor
│   │   └── research-results.md        # /research-results
│   └── settings.json                  # Claude Code settings
│
├── context/
│   ├── baseline.yaml                  # Shared company context
│   └── README.md                      # Context documentation
│
├── runs/
│   ├── manifest.json                  # Tracks all runs
│   ├── {run_id}/                     # Each run directory
│   │   ├── config.yaml               # Run configuration
│   │   ├── context/                  # Run-specific context
│   │   ├── deliverables/             # Packaged results
│   │   └── monitor.sh                # Monitoring script
│   └── README.md                      # Runs documentation
│
├── templates/
│   ├── config_discovery.yaml          # Discovery template
│   ├── config_validation.yaml         # Validation template
│   └── config_competitive.yaml        # Competitive template
│
└── README.md                          # This file
```

## Research Types

### 1. Pure Discovery
**When**: Exploring new market without bias
**Context**: Baseline only (no detailed materials)
**Output**: Unbiased market intelligence
**Example**: "How do healthcare CFOs actually buy infrastructure advisory?"

### 2. Validation
**When**: Testing existing messaging/approach against market
**Context**: Baseline + detailed materials (services, messaging, case studies)
**Output**: Gap analysis between market reality and your current approach
**Example**: "Does our financial services messaging resonate with CIOs?"

### 3. Competitive
**When**: Benchmarking against competitors
**Context**: Baseline + competitive materials
**Output**: Competitive positioning analysis
**Example**: "How does our approach compare to [Competitor X] in manufacturing?"

## Context Isolation Strategy

### Baseline Context (Shared)
Located in `context/baseline.yaml`

**What it contains**:
- Company name and description
- Service categories (high-level)
- Geographic focus
- General target segments

**Used by**: ALL research runs

### Run-Specific Context (Isolated)
Located in `runs/{run_id}/context/`

**What it contains**:
- Detailed service descriptions
- Current messaging/positioning
- Case studies
- Competitive intelligence
- Pricing materials

**Used by**: ONLY that specific run

### Why Isolation Matters

```
WITHOUT ISOLATION:
Discovery run sees detailed messaging
  ↓
Agents validate existing beliefs
  ↓
You get back what you put in
  ↓
Miss opportunities for discovery

WITH ISOLATION:
Discovery run: baseline only → unbiased market truth
Validation run: baseline + detailed → gap analysis
  ↓
You learn what you don't know
```

## Typical Workflows

### Workflow A: New Market Discovery

```bash
cd research-manager
claude
```

```
> /research-new healthcare market discovery

AGENT: Great! Let me help you set up healthcare market discovery.

      What's your research objective?
      A) Pure discovery - understand buyer behavior
      B) Validation - test our messaging
      C) Competitive - benchmark competitors

> A

AGENT: Perfect. Pure discovery = unbiased market research.

      Which healthcare segments?
      1. Healthcare Providers
      2. Health Insurance
      3. Medical Devices

> 1, 2

[... agent guides through setup ...]

AGENT: ✅ Run created: healthcare_discovery_20250113

      Launch command:
      cd ../src && python run_research.py --config ...

      Estimated cost: $24-26
      Estimated time: 2-3 days

      Start now? [Y/n]
```

### Workflow B: Check Progress

```bash
> /research-status
```

```
AGENT: Current Research Runs:

      🔄 RUNNING: healthcare_discovery_20250113
         Progress: Layer 2 (2/3 verticals complete)
         Time: 18 hours elapsed
         Cost: $18.50 / $24-26 estimated
         ETA: 6-8 hours

      ✅ COMPLETED: financial_validation_20250112
         Completed: 2025-01-12
         Cost: $26.10
         Action: Run /research-results to package
```

### Workflow C: Package Results

```bash
> /research-results healthcare_discovery_20250113
```

```
AGENT: Research completed: healthcare_discovery_20250113

      Outputs available:
      ✅ Layer 1: 5 horizontal reports
      ✅ Layer 2: 2 vertical reports
      ✅ Layer 3: 3 title reports
      ✅ Playbooks: 6 combinations

      Which package for stakeholders?
      1. Executive (1-pager + key insights)
      2. Tactical (playbooks + frameworks)
      3. Strategic (complete research)

> 1

AGENT: Creating executive package...

      ✅ Package created:
      runs/healthcare_discovery_20250113/deliverables/executive/

      Download:
      runs/healthcare_discovery_20250113/healthcare_discovery_executive.zip
```

## Run Naming Convention

Format: `{vertical}_{type}_{date}`

Examples:
- `healthcare_discovery_20250113`
- `financial_validation_20250114`
- `manufacturing_competitive_20250115`

## Cost Management

### Model Strategy (from defaults.yaml)

**Layer 1** (Horizontal research):
- Haiku for most agents ($1-2 each)
- Sonnet for synthesis ($4-6)
- Total: $6-8

**Layer 2** (Vertical research):
- Haiku for all verticals
- ~$1-2 per vertical
- Total: $3-6 (depends on vertical count)

**Layer 3** (Title research):
- Haiku for all titles
- ~$1-2 per title
- Total: $3-6 (depends on title count)

**Playbooks** (Integration):
- Sonnet for quality playbooks
- ~$2 per playbook
- Total: Depends on combinations

**Typical Run**: $24-40 for comprehensive research

## Monitoring

### Real-time Monitoring

```bash
cd runs/{run_id}
bash monitor.sh
```

Shows:
- Current layer/agent
- Token usage and costs
- Progress through research
- Errors (if any)

### Log Files

Located at: `../src/logs/execution_{timestamp}.log`

Contains:
- Agent start/complete events
- Turn-by-turn token usage
- Search counts
- Error details

### Checkpoint Files

Located at: `../src/checkpoints/{execution_id}.json`

Contains:
- Completed agents
- Layer status
- Dependency tracking
- Resume state

## Best Practices

### 1. Start with Discovery
Before validation, run pure discovery to establish baseline truth.

### 2. Isolate Context
Never mix detailed context into discovery runs.

### 3. Track Everything
Use manifest.json to track all runs - makes iteration easier.

### 4. Package Early
Create stakeholder packages while research is fresh.

### 5. Iterate
Use discoveries to inform next research questions.

## Troubleshooting

### Run fails to start
**Check**:
- Config file syntax (valid YAML)
- Context files exist (if referenced)
- API key set in `../src/.env`

### Research stops mid-execution
**Check**:
- Logs for error message
- Budget limits in config
- Network connectivity

**Recovery**:
```bash
cd ../src
python run_research.py --resume {execution_id}
```

### Cost exceeds estimate
**Causes**:
- Extended thinking (Sonnet 4)
- More searches than expected
- Longer conversations

**Solutions**:
- Switch to Haiku in config
- Reduce search budgets
- Use narrower research scope

### Results incomplete
**Check**:
- All layers actually completed (check status)
- Review gates approved
- Outputs exist at expected paths

## Integration with Main Research System

This research-manager directory is a **front-end** to the main research orchestrator at `../src/`.

**Flow**:
```
research-manager/  (you interact here)
   ↓
   Creates config in runs/{run_id}/config.yaml
   ↓
   Launches: ../src/run_research.py --config runs/{run_id}/config.yaml
   ↓
   Research executes in ../src/
   ↓
   Outputs: ../src/outputs/
   ↓
   Package results back to runs/{run_id}/deliverables/
```

## Getting Help

From within research-manager Claude Code session:

```
> Can you explain {topic}?
```

Topics:
- "How do I create a discovery run?"
- "What's the difference between discovery and validation?"
- "How do I monitor progress?"
- "How do I package results for executives?"
- "What context should I include?"

The research-elicitation agent will guide you.

## Updates and Maintenance

### Update Baseline Context
```bash
edit context/baseline.yaml
```
Changes apply to all NEW runs.

### Archive Old Runs
```bash
mkdir -p runs/archive
mv runs/{old_run_id} runs/archive/
# Update manifest.json to remove entry
```

### Clean Logs
```bash
cd ../src/logs
# Archive or delete old logs
```

### Check Disk Usage
```bash
du -sh runs/*/deliverables/
# Large deliverable packages can accumulate
```

---

**Ready to start?**

```bash
cd research-manager
claude
/research-new
```

The agent will guide you from there.
