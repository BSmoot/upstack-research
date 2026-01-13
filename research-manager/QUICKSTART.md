# Quick Start Guide

Get started with research-manager in 5 minutes.

## Step 1: Navigate to research-manager

```bash
cd upstack-research/research-manager
```

## Step 2: Start Claude Code

```bash
claude
```

## Step 3: Start New Research

Type one of these commands:

```
/research-new
```

OR provide context in your command:

```
/research-new healthcare market discovery
/research-new validate our financial services messaging
/research-new competitive analysis for manufacturing
```

## Step 4: Answer Questions

The research-elicitation agent will guide you through:

1. **Research Objective** - What do you want to learn?
2. **Target Audience** - Which verticals and buyer personas?
3. **Context Strategy** - Pure discovery or validation?
4. **Cost Approval** - Review estimated costs and timeline

## Step 5: Launch Research

Agent will provide launch command:

```bash
cd ../src
python run_research.py --config ../research-manager/runs/{run_id}/config.yaml
```

Run it and research begins!

## Step 6: Monitor Progress

Check status anytime:

```
/research-status
```

Monitor specific run:

```
/research-monitor {run_id}
```

## Step 7: Package Results

When research completes:

```
/research-results {run_id}
```

Agent will help you create stakeholder-ready packages.

---

## Example Session

```bash
$ cd upstack-research/research-manager
$ claude
```

```
Welcome to Claude Code!

> /research-new healthcare discovery

Research Elicitation Agent: Great! Let me help you set up a healthcare
market discovery project.

What's your research objective?

A) Pure discovery - understand how healthcare buyers actually behave
B) Validation - test our current messaging against market reality
C) Competitive - benchmark against competitors

Select (A-C): A

Perfect! Pure discovery means unbiased market research.

Which healthcare segments?
1. Healthcare Providers
2. Health Insurance
3. Medical Devices
4. Pharmaceutical

(Select multiple, comma-separated): 1, 2

Healthcare Providers and Health Insurance - got it.

Which buyer personas?
1. CFO/Finance Leadership
2. CIO/Technology Leadership
3. VP Operations
4. Procurement Leaders

(Select multiple): 1, 2, 3

Excellent! Setting up:
- Verticals: Healthcare Providers, Health Insurance
- Personas: CFO, CIO, VP Operations
- Type: Pure discovery (no bias)
- Playbooks: 6 (2 verticals × 3 personas)

Estimated cost: $24-26
Estimated time: 2-3 days

Creating run: healthcare_discovery_20250113

✅ Run created!

To launch research:
```bash
cd ../src
python run_research.py --config ../research-manager/runs/healthcare_discovery_20250113/config.yaml
```

Start now? (Y/n): Y

Launching research...

Monitor with: /research-monitor healthcare_discovery_20250113
```

---

## That's It!

You now have:
- ✅ Research run configured
- ✅ Execution started
- ✅ Monitoring commands available
- ✅ Results packaging ready when complete

## Next Steps

1. **Wait for completion** (2-3 days for typical run)
2. **Check status periodically**: `/research-status`
3. **Package results**: `/research-results {run_id}`
4. **Share with stakeholders**

## Need Help?

Ask the agent:
- "How do I monitor progress?"
- "What's the difference between discovery and validation?"
- "How do I create a custom research type?"
- "Can I pause and resume research?"

The research-elicitation agent will guide you.

---

**Common Commands**:
- `/research-new` - Start new project
- `/research-status` - Check all runs
- `/research-monitor {run_id}` - Tail logs
- `/research-results {run_id}` - Package deliverables

**File Locations**:
- Configs: `runs/{run_id}/config.yaml`
- Context: `runs/{run_id}/context/`
- Outputs: `../src/outputs/`
- Deliverables: `runs/{run_id}/deliverables/`
