# Package Research Results

Package completed research into stakeholder-ready deliverables.

## Arguments

- `$ARGUMENTS` - Run ID to package (e.g., "healthcare_discovery_20250113")

## What This Does

1. Verify research is actually complete
2. Understand stakeholder needs (executive, tactical, strategic)
3. Create organized deliverable package
4. Generate summary documents
5. Provide shareable format (ZIP, links)

## Execution

### Step 1: Parse Arguments and Verify Completion

```
Run ID: $ARGUMENTS
```

Check if run is complete:
```bash
cat runs/manifest.json | python -c "
import json, sys
manifest = json.load(sys.stdin)
run_id = '$ARGUMENTS'
run = next((r for r in manifest['runs'] if r['run_id'] == run_id), None)
if run and run['status'] == 'completed':
    print('COMPLETE')
    print(run['execution_id'])
    print(run['outputs_path'])
else:
    print('ERROR: Run not complete or not found')
    sys.exit(1)
"
```

### Step 2: Gather Available Outputs

```bash
# List all outputs
find {outputs_path} -name "*.md" -type f
```

Categorize outputs:
- Layer 1: buyer_journey.md, channels_competitive.md, etc.
- Layer 2: vertical_{name}.md files
- Layer 3: title_{name}.md files
- Playbooks: playbook_{vertical}_{title}.md files

### Step 3: Understand Stakeholder Needs

Ask user:
```markdown
## Research Results Ready: {run_id}

**Outputs Available**:
✅ Layer 1: Horizontal research (5 reports)
✅ Layer 2: Vertical research ({count} reports)
✅ Layer 3: Title research ({count} reports)
✅ Playbooks: {count} vertical × title combinations

**Which stakeholder package do you need?**

1. **Executive Package** (C-suite)
   - One-page executive summary
   - Top 5 insights with business impact
   - Recommended actions
   - Cost/timeline

2. **Tactical Package** (Marketing/Sales)
   - All playbooks organized by vertical
   - Messaging frameworks
   - Objection handlers
   - Channel recommendations

3. **Strategic Package** (Product/Strategy)
   - Complete research outputs
   - Competitive landscape analysis
   - Market trends and dynamics
   - Gap analysis

4. **Custom Package**
   - Tell me what to include

Select (1-4): ___
```

### Step 4: Create Package

Based on selection, create package in:
```
runs/{run_id}/deliverables/{package_type}/
```

#### Executive Package Structure:
```
deliverables/executive/
├── README.md (navigation guide)
├── executive_summary.md (1-pager)
├── top_insights.md (5 key findings)
├── recommended_actions.md (next steps)
└── appendix/
    └── gtm_synthesis.md (from Layer 1)
```

#### Tactical Package Structure:
```
deliverables/tactical/
├── README.md
├── overview.md (how to use playbooks)
├── playbooks/
│   ├── {vertical}_{title}.md (each combination)
│   └── ...
├── messaging/
│   ├── frameworks.md (from Layer 1)
│   └── positioning.md
└── channels/
    └── recommendations.md (from Layer 1)
```

#### Strategic Package Structure:
```
deliverables/strategic/
├── README.md
├── executive_summary.md
├── layer_1/ (all horizontal research)
├── layer_2/ (all vertical research)
├── layer_3/ (all title research)
├── playbooks/ (all combinations)
├── competitive_analysis.md (extracted)
├── market_trends.md (extracted)
└── gap_analysis.md (synthesized)
```

### Step 5: Generate Summary Documents

Create package-specific summaries:

**Executive Summary Template**:
```markdown
# Executive Summary: {run_name}

## Research Objective
{from config}

## Key Findings

### 1. [Insight Category]
**Finding**: [What we learned]
**Business Impact**: [Why it matters]
**Recommended Action**: [What to do]

[Repeat for top 5 insights]

## Market Landscape
[High-level overview from competitive analysis]

## Recommended Next Steps
1. [Action 1 with timeline]
2. [Action 2 with timeline]
3. [Action 3 with timeline]

## Investment Summary
- Research completed: {date}
- Investment: ${cost}
- Deliverables: {count} playbooks, {reports} reports
```

### Step 6: Create Shareable Format

```bash
cd runs/{run_id}/deliverables/{package_type}
zip -r ../../{run_id}_{package_type}_results.zip .
```

Provide download link or path.

### Step 7: Next Steps Guidance

Suggest:
```markdown
## Next Steps

**Share Results**:
- ZIP file: `runs/{run_id}/{run_id}_{package_type}_results.zip`
- Individual reports: `runs/{run_id}/deliverables/{package_type}/`

**Iterate Research**:
- Run deeper vertical studies
- Test specific messaging variations
- Expand to new buyer personas
- Competitive deep-dive

**Implementation**:
- Update messaging based on findings
- Train sales team on playbooks
- Adjust channel strategy
- Refine ICP based on insights

**Validation**:
- Test messaging with prospects
- A/B test channel approaches
- Measure conversion changes

Would you like me to:
1. Create another package type
2. Set up a follow-on research run
3. Help you present these findings
```

## Example

```
/research-results healthcare_discovery_20250113
```
