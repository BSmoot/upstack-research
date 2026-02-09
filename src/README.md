# Research Orchestrator

AI-powered market research system that executes multi-layer research through intelligent parallel execution using Claude's web search capabilities.

## Overview

The Research Orchestrator compresses weeks of sequential market research into days through:

- **Layer 0**: Service category research (buyer journey per category, vendor landscape, search terms) ✅ **NEW**
- **Layer 1**: Horizontal research (buyer journey, competitive landscape, customer expansion, messaging, GTM synthesis) ✅ **COMPLETE**
- **Layer 2**: Vertical-specific research (industry adaptations) ✅ **COMPLETE**
- **Layer 3**: Title-specific research (buyer persona insights) ✅ **COMPLETE**
- **Integration**: 3D Playbook generation (Vertical × Title × Service Category) ✅ **NEW**
- **Validation**: Quality gate assessment before production use ✅ **NEW**
- **Brand Alignment**: Align outputs with brand voice and standards ✅ **COMPLETE**

## Features

- ✅ **Parallel Execution**: Multiple research agents run simultaneously across all layers
- ✅ **Checkpoint/Resume**: Never lose progress if interrupted
- ✅ **Dependency Management**: Automatic sequencing based on research dependencies
- ✅ **Human Review Gates**: Pause between layers for quality review
- ✅ **Structured Output**: Markdown reports with proper citations
- ✅ **Direct API Control**: No framework overhead - just Python + Anthropic SDK
- ✅ **Multi-Layer Research**: Full 4-layer research capability (L0 → L1 → L2 → L3)
- ✅ **Context Flow**: Automatic context extraction and injection between layers
- ✅ **3D Playbooks**: Service-category-specific playbooks (V × T × SC)
- ✅ **Validation Agent**: Quality gate scoring (Completeness, Specificity, Actionability, Research Grounding)
- ✅ **Force Re-run**: Selectively re-run completed agents with `--force`

## Installation

### 1. Prerequisites

- Python 3.11 or higher
- Anthropic API key ([get one here](https://console.anthropic.com))

### 2. Install Dependencies

```bash
cd src
pip install -r requirements.txt
```

### 3. Configure API Key

Copy the `.env.example` file to `.env` and add your Anthropic API key:

```bash
cp .env.example .env
# Edit .env and add your API key
```

The `.env` file should contain:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Recent Updates (February 2026)

### ✅ ADR-003: CLI Selective Updates, Unit Tests & E2E Infrastructure (2026-02-08)

Exposed selective update CLI flags, added dedicated unit tests, and prepared E2E test infrastructure:

**CLI Flags for Selective Execution**
- `--layer 0` — Run Layer 0 (service category research) independently
- `--verticals healthcare,legal` — Run specific verticals in Layer 2
- `--titles cfo_cluster,cio_cto_cluster` — Run specific title clusters in Layer 3
- `--service-categories security,cx` — Run specific service categories in Layer 0
- `--force` — Force re-run of completed agents (even if already in checkpoint)

**Dedicated Unit Tests**
- `test_validation.py` — 21 tests covering `build_validation_prompt()` and `build_batch_validation_prompt()`
- `test_service_category.py` — 28 tests covering `ResearchContextInjector` and `build_service_category_prompt()`

**E2E Test Infrastructure**
- 10 end-to-end test scenarios documented in `tests/e2e/README.md`
- PowerShell test runner (`tests/e2e/run_e2e.ps1`) with colored output
- Budget failure test config (`build/config/projects/e2e_budget_fail.yaml`)

### ✅ ADR-002: Research System Enhancement

Implemented comprehensive enhancements addressing six critical gaps:

**Layer 0: Service Category Research**
- New research layer runs BEFORE horizontal research
- Researches how buyers discover and evaluate specific service categories
- Provides category-specific buyer journey, vendor landscape, search terms
- Configure via `service_categories` in config YAML

**3D Playbooks (V × T × SC)**
- Extended playbook generation from `Vertical × Title` to `Vertical × Title × Service Category`
- Service-category-specific messaging, vendor positioning, and buyer triggers
- Configure via `priority_service_categories` in config YAML

**Validation Agent**
- Quality gate assessment after playbook generation
- Scores on 4 dimensions: Completeness, Specificity, Actionability, Research Grounding
- Produces validation reports with specific improvement recommendations
- Auto-runs after playbooks (configurable)

**Force Re-run Capability**
- Selectively re-run completed agents with `force_agents` parameter
- Preserves prior output files (renamed with timestamp)
- Preserves checkpoint history for audit trail

**Enhanced Prompts**
- Buyer-centric search terms (not advisory jargon)
- Supplier competition research (direct vendor sales as primary competition)
- Dynamic context injection from baseline.yaml

See `docs/adr/002-research-system-enhancement.md` for full details.

---

## Previous Updates (October 2025)

### ✅ Composable Model Selection System
- Define model strategy once in `build/config/defaults.yaml`
- Create project configs that inherit settings
- Per-agent model selection (use Haiku for research, Sonnet for synthesis)
- Cost estimation before execution
- **Result: 80-90% cost reduction** compared to using Sonnet 4 everywhere

### ✅ Critical Bug Fixes
- Fixed `pause_turn` handling for Claude's extended thinking
- Enhanced logging with per-turn token usage and costs
- Research now completes properly with full outputs

### ✅ Documentation
- **`MODEL_SELECTION_GUIDE.md`** - Complete model selection guide
- **`COST_ANALYSIS.md`** - Detailed cost breakdown and optimization
- **`FIX_SUMMARY_20251010.md`** - Recent bug fix summary

### Test the System

Run the test script to verify everything works:
```bash
cd src
python test_model_selection.py
```

Expected output:
```
✅ ALL TESTS PASSED
The composable model selection system is working correctly!
```

## Configuration

### Quick Start: Use Pre-Configured Settings

Use the optimized config with hybrid model strategy (recommended):
```bash
python run_research.py --config ../build/config/projects/healthcare_2025.yaml
```

**Expected cost:** $24-26 for healthcare project (vs $150-230 with all-Sonnet)

### Custom Configuration

Edit the research configuration file to customize your research targets. The default config is at:
```
../build/design/251002_initial_design/research_config.yaml
```

Or create a new project config that inherits from defaults:
```yaml
# build/config/projects/my_project.yaml
extends: "../defaults.yaml"  # Inherit model strategy

execution:
  id: "my_research_2026"

# NEW: Layer 0 Service Categories (optional)
service_categories:
  - security
  - customer_experience
  - network

# NEW: 3D Playbooks - which service categories to combine with V × T
priority_service_categories:
  - security
  - customer_experience

verticals:
  - "Your Industry 1"
  - "Your Industry 2"

title_clusters:
  - "C-Suite"
  - "VP/Director"
```

Key configuration options:

```yaml
# Which verticals to research
verticals:
  - healthcare
  - financial_services
  - manufacturing

# Which title clusters to research
title_clusters:
  - cfo_cluster
  - cio_cto_cluster
  - vp_it_operations

# Execution settings
execution_settings:
  max_concurrent_agents: 5  # How many agents run in parallel
  research_depth: "comprehensive"  # quick, standard, or comprehensive
```

## Usage

### Validate Configuration

Test your configuration without executing:

```bash
python run_research.py --config ../build/design/251002_initial_design/research_config.yaml --dry-run
```

### Run Single Agent (Recommended First Test)

Test with a single agent before running the full system:

```bash
python run_research.py --agents buyer_journey --config ../build/design/251002_initial_design/research_config.yaml
```

**Expected behavior:**
- Executes 40-60 web searches
- Takes 2-3 hours to complete
- Generates structured markdown report
- Saves to `outputs/layer_1/buyer_journey.md`

### Run Layer 0 (Service Category Research)

Execute service category research agents:

```bash
python run_research.py --layer 0 --config ../build/config/projects/healthcare_2025.yaml
```

Run specific service categories only:

```bash
python run_research.py --layer 0 --service-categories security,customer_experience --config path/to/config.yaml
```

### Run Full Layer 1

Execute all 5 horizontal research agents:

```bash
python run_research.py --layer 1 --config ../build/design/251002_initial_design/research_config.yaml
```

**Timeline:** 2-3 days (mostly unattended)

### Run Selective Verticals or Titles

Run specific verticals in Layer 2:

```bash
python run_research.py --layer 2 --verticals healthcare,financial_services --config path/to/config.yaml
```

Run specific title clusters in Layer 3:

```bash
python run_research.py --layer 3 --titles cfo_cluster,cio_cto_cluster --config path/to/config.yaml
```

### Force Re-run Completed Agents

Re-run agents even if already complete in the checkpoint:

```bash
# Re-run a specific service category
python run_research.py --layer 0 --service-categories security --force --config path/to/config.yaml

# Re-run a specific vertical
python run_research.py --layer 2 --verticals healthcare --force --config path/to/config.yaml

# Re-run all of Layer 1
python run_research.py --layer 1 --force --config path/to/config.yaml
```

### Run Full Research Program

Execute complete three-layer research with human review gates:

```bash
python run_research.py --config ../build/design/251002_initial_design/research_config.yaml
```

**Timeline:** 
- Layer 1: 2-3 days
- Review Gate (manual)
- Layer 2: 2-3 days
- Review Gate (manual)
- Layer 3: 1-2 days
- Integration: 1 day
- **Total: 6-10 days** (execution time) + review time

### Resume Interrupted Research

If execution is interrupted, resume from checkpoint:

```bash
python run_research.py --resume research_20251002_143000 --config path/to/config.yaml
```

You can combine `--resume` with `--layer` to run a specific layer using an existing checkpoint:

```bash
# Resume and run only Layer 2
python run_research.py --resume research_20251002_143000 --layer 2 --config path/to/config.yaml
```

## Output Structure

```
outputs/{execution_id}/
├── layer_0/                              # Service Category Research (NEW)
│   ├── service_category_security.md
│   ├── service_category_customer_experience.md
│   ├── service_category_network.md
│   └── ...
│
├── layer_1/
│   ├── buyer_journey.md
│   ├── channels_competitive.md
│   ├── customer_expansion.md
│   ├── messaging_positioning.md
│   └── gtm_synthesis.md
│
├── layer_2/
│   ├── vertical_healthcare.md
│   ├── vertical_financial_services.md
│   └── vertical_manufacturing.md
│
├── layer_3/
│   ├── title_cfo_cluster.md
│   ├── title_cio_cto_cluster.md
│   └── title_vp_it_operations.md
│
├── playbooks/
│   ├── playbook_healthcare_cfo_cluster.md          # 2D: V × T
│   ├── playbook_healthcare_cfo_cluster_security.md # 3D: V × T × SC (NEW)
│   └── ...
│
├── validation/                           # Quality Gate Reports (NEW)
│   ├── validate_playbook_healthcare_cfo_cluster.md
│   └── ...
│
└── brand_alignment/
    └── ...
```

## Output Format

Each research report includes:

- **Executive Summary**: Key findings
- **Detailed Sections**: Organized by research question
- **Source Citations**: Every major claim backed by sources
- **Confidence Assessment**: High/medium/low confidence areas
- **Research Gaps**: Areas needing more investigation
- **Methodology**: Search queries and source types

## Monitoring Execution

### Console Output

The system logs progress to console:
```
2025-10-02 17:30:00 | INFO | Starting Layer 1: Horizontal Research
2025-10-02 17:30:01 | INFO | Phase 1: Launching 3 independent agents in parallel
2025-10-02 17:30:05 | INFO | [buyer_journey] Turn 1/50
2025-10-02 17:30:15 | INFO | [buyer_journey] Search 1: "infrastructure advisory buying triggers"
```

### Log Files

Detailed logs are saved to `logs/execution_YYYYMMDD_HHMMSS.log`

### Checkpoints

State is saved after each agent completes to `checkpoints/research_YYYYMMDD_HHMMSS.json`

## Architecture

### Core Components

1. **ResearchSession** (`research_session.py`)
   - Manages individual Claude API conversations
   - Handles web_search tool use loops automatically
   - Produces structured markdown output

2. **StateTracker** (`state/tracker.py`)
   - Checkpoint/resume capability
   - Dependency tracking between layers
   - Agent completion status

3. **ResearchOrchestrator** (`orchestrator.py`)
   - Main coordination logic
   - Parallel execution within layers
   - Human review gates between layers

4. **Prompts** (`prompts/horizontal.py`)
   - Comprehensive research questions
   - Output format specifications
   - Quality standards

### Execution Flow

```
Layer 0: [service_category_security, service_category_cx, ...] → Parallel (optional)
              ↓
         Review Gate (optional)
              ↓
Layer 1 Phase 1: [buyer_journey, channels_competitive, customer_expansion] → Parallel
              ↓
Layer 1 Phase 2: messaging_positioning (depends on Phase 1)
              ↓
Layer 1 Phase 3: gtm_synthesis (depends on all prior)
              ↓
         Review Gate
              ↓
Layer 2: [vertical_1, vertical_2, ...] → Parallel
              ↓
         Review Gate
              ↓
Layer 3: [title_1, title_2, ...] → Parallel
              ↓
         Review Gate (optional)
              ↓
Integration: Generate 2D Playbooks (V × T) → Parallel
              ↓
Integration: Generate 3D Playbooks (V × T × SC) → Parallel (optional)
              ↓
Validation: Quality Gate Assessment → Parallel
              ↓
         Review Gate (optional)
              ↓
Brand Alignment: Align outputs with brand standards → Parallel (optional)
```

## Troubleshooting

### API Rate Limits

If you hit API rate limits:
```yaml
# In config file, reduce concurrent agents:
execution_settings:
  max_concurrent_agents: 3  # Down from 5
```

### Agent Fails Mid-Research

The system automatically saves checkpoints. Just re-run the same command - it will skip completed agents and continue from where it left off.

### Output Quality Issues

If research quality is poor:
1. Review the output markdown file
2. Identify specific gaps
3. Adjust prompts in `research_orchestrator/prompts/horizontal.py`
4. Re-run the specific agent

### Memory/Performance Issues

For limited resources:
```yaml
# Reduce research depth:
execution_settings:
  research_depth: "standard"  # Down from "comprehensive"
```

## Cost Estimates

API costs for full research program:

- **Layer 1**: ~$50-75 (200-300 searches)
- **Layer 2**: ~$75-100 per vertical
- **Layer 3**: ~$50-75 per title cluster
- **Total**: $200-400 for complete 3-layer research

Compare to:
- Traditional consultants: $50K-100K
- Timeline: 16-20 weeks

**ROI: 100-250X cost efficiency**

## Development

### Project Structure

```
src/
├── research_orchestrator/
│   ├── __init__.py
│   ├── research_session.py       # Claude API session manager
│   ├── orchestrator.py            # Main coordinator
│   ├── state/
│   │   └── tracker.py             # State & checkpoints
│   ├── prompts/
│   │   ├── horizontal.py          # Layer 1 prompts
│   │   ├── vertical.py            # Layer 2 prompts
│   │   ├── title.py               # Layer 3 prompts
│   │   ├── playbook.py            # Playbook generation (2D & 3D)
│   │   ├── service_category.py    # Layer 0 service category prompts
│   │   ├── validation.py          # Validation agent prompts
│   │   ├── brand_alignment.py     # Brand alignment prompts
│   │   └── context_injector.py    # Dynamic context injection from baseline.yaml
│   └── utils/
│       ├── logging_setup.py       # Logging config
│       ├── config.py              # Config loader
│       └── config_schema.py       # Pydantic config models
├── tests/
│   ├── test_api_connection.py     # Standalone API connection tests
│   ├── test_research_session.py   # ResearchSession unit & integration tests
│   ├── test_validation.py         # Validation prompt unit tests (21 tests)
│   ├── test_service_category.py   # Service category & context injector tests (28 tests)
│   ├── e2e/
│   │   ├── README.md              # 10 E2E test scenarios
│   │   └── run_e2e.ps1            # PowerShell E2E test runner
│   └── README.md                  # Testing guide
├── run_research.py                # CLI interface
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

### Adding New Agents

To add a new research agent:

1. Create prompt in `prompts/` directory
2. Add agent name to StateTracker initialization
3. Add execution logic to Orchestrator
4. Update configuration schema

## Best Practices

### 1. Test Single Agent First

Always test with one agent before running full system:
```bash
python run_research.py --agents buyer_journey --config path/to/config.yaml
```

### 2. Start Small

Begin with 1-2 verticals and 1-2 title clusters. Scale up after validating quality.

### 3. Review Between Layers

Use review gates to ensure quality before proceeding to next layer.

### 4. Test Messaging Early

Don't wait for perfect research. Test messaging with 20 prospects after Layer 1.

### 5. Iterate Based on Market Feedback

Use real prospect responses to refine prompts and re-run research.

### 6. DETAILED SETUP:

Research Customization & Business Context Integration
How Research Gets Customized
1. Configuration-Driven Research (research_config.yaml)
What you control:
yaml# Direct control over scope
verticals: [healthcare, finserv]  # System researches ONLY these
title_clusters: [cfo_cluster]     # System researches ONLY these

# Business context injection
company_context:
  name: "UPSTACK"
  services:
    - "Network connectivity advisory"
    - "Data center consulting"
  current_customers:
    primary_verticals: ["healthcare"]
    typical_deal_size: "$50K-$250K"
  competitors:
    direct: ["Competitor A", "Competitor B"]
How it's used:
When agents research, this context becomes part of their prompt:
python# In vertical agent prompt:
f"""
You are researching {vertical_name} for a company that:
- Offers these services: {config['services']}
- Currently serves: {config['current_customers']['primary_verticals']}
- Competes with: {config['competitors']}

CRITICAL: Adapt your research to THIS specific business context.
Research how {vertical_name} companies would evaluate THESE specific services.
"""
Example impact:

Generic research: "What do healthcare companies need for infrastructure?"
Your research: "How do healthcare companies evaluate network connectivity advisory services vs. going direct to AT&T/Verizon?"

2. Prompt-Driven Research Focus
Three customization points:
A. Research Questions (What gets searched)
Currently in prompts_layer_1_horizontal.py:
pythonBUYER_JOURNEY_PROMPT = """
YOUR RESEARCH QUESTIONS:

1. TRIGGER EVENTS & AWARENESS
- What events trigger companies to seek infrastructure advisory help?
...
"""
To customize:

Edit the prompt file directly
Add UPSTACK-specific questions:

pythonBUYER_JOURNEY_PROMPT = """
YOUR RESEARCH QUESTIONS:

1. TRIGGER EVENTS & AWARENESS
- What events trigger companies to seek infrastructure advisory help?
- Specifically: When do companies consider advisory vs. going direct to suppliers?
- UPSTACK context: How do companies discover vendor-reimbursed advisory models?

2. UPSTACK-SPECIFIC DECISION FACTORS
- What concerns do buyers have about "free" advisory services?
- How do buyers validate advisor independence when vendor-reimbursed?
- What proof points overcome skepticism about advisor conflicts of interest?
...
"""
B. Source Priorities (What sources to use)
Currently:
pythonMETHODOLOGY:
- Use 40-60 web_search operations
- Prioritize: surveys, B2B buyer studies, case studies, forums
To customize:
pythonMETHODOLOGY:
- Use 40-60 web_search operations
- Prioritize sources in this order:
  1. Gartner/Forrester advisory services research
  2. Healthcare IT publications (for healthcare vertical)
  3. CIO Magazine buyer journey studies
  4. Reddit r/sysadmin discussions about advisors
  5. LinkedIn posts from target titles discussing procurement
  
- AVOID generic marketing content
- AVOID supplier-published "research" (biased)
C. Search Keywords (What terms to use)
Currently implied, but you can make explicit:
pythonSEARCH_STRATEGY:
Start with these seed queries:
- "infrastructure advisory services evaluation"
- "network connectivity advisor vs direct supplier"
- "technology procurement consultant selection"
- "vendor-reimbursed advisory model"

Expand based on findings:
- If research shows concern about conflicts: search "advisor independence validation"
- If research shows price sensitivity: search "technology advisory pricing models"
3. Context File Injection
Add detailed business context:
yaml# In research_config.yaml
company_context:
  context_files:
    services_doc: "context/upstack_services.md"
    case_studies: "context/case_studies.md"
    pricing: "context/pricing_guide.md"
Create these files:
markdown# context/upstack_services.md

## UPSTACK Service Portfolio

### Network Connectivity Advisory
- Carriers: AT&T, Verizon, Lumen, Windstream, etc.
- Services: Dedicated Internet, MPLS, SD-WAN, 5G
- Deal sizes: $50K-$500K annually
- Typical buyer: VP IT, CIO
- Pain points we solve: 
  - Carrier confusion (200+ options)
  - Price opacity
  - Contract complexity

### Data Center & Colocation Advisory
- Providers: Equinix, Digital Realty, CyrusOne, etc.
...

## Our Differentiation
- 80M data points on supplier pricing/performance
- Vendor-reimbursed model (free to buyers)
- Full-service (not just brokerage)
...
System injects this into prompts:
python# When agent researches
prompt = f"""
{base_prompt}

UPSTACK CONTEXT:
{load_file('context/upstack_services.md')}

Research how buyers in {vertical} would evaluate THESE specific services.
Use UPSTACK's differentiation points as lens for competitive research.
"""
4. Dynamic Research Adaptation
System learns during execution:
When buyer_journey agent completes, its findings inform later agents:
python# messaging_positioning agent receives:
context = {
    'buyer_journey_findings': {
        'key_pain_point': 'Buyers skeptical of "free" advisory',
        'objection_pattern': '60% question advisor independence',
        'trust_signal': 'Third-party case studies critical'
    }
}

# Messaging agent adapts research:
prompt = f"""
Based on buyer journey research showing skepticism about free advisory:

FOCUS YOUR MESSAGING RESEARCH ON:
1. How do vendor-reimbursed services (recruiting, real estate) build trust?
2. What independence proof points work in analogous industries?
3. How do buyers validate advisor neutrality?

{standard_messaging_questions}
"""
Current vs. Desired State
What System Does NOW (Out of Box)
✅ Vertical filtering: Only researches configured verticals
✅ Title filtering: Only researches configured titles
✅ Basic context: Company name and services in prompts
❌ Deep context: Doesn't use detailed service descriptions
❌ Competitor focus: Doesn't specifically research your competitors
❌ Custom questions: Uses generic research questions
❌ Source steering: Doesn't prioritize specific publications
What You SHOULD Customize
Priority 1 (Before first run):

Add detailed context files:

context/upstack_services.md (what you actually offer)
context/upstack_differentiation.md (why you're different)
context/target_customers.md (who you want to reach)


Update research questions in prompts:

Add UPSTACK-specific questions
Focus on vendor-reimbursed model validation
Include competitor-specific research



Priority 2 (After first run):

Refine based on output quality:

If research too generic → add more specific context
If missing key insights → add focused research questions
If wrong sources → specify preferred publications



Priority 3 (Ongoing):

Iterate based on market feedback:

Prospect objections → research why objection exists
Messaging that fails → research alternative approaches
Successful tactics → research how to scale



Practical Customization Workflow
Before First Run
1. Create context files (30 minutes):
bashmkdir context
context/upstack_business.md:
markdown# UPSTACK Business Model

## What We Do
Infrastructure technology advisory - help companies select and negotiate:
- Network connectivity (carriers, SD-WAN)
- Data center & colocation
- Cloud connectivity
- Communication services (CCaaS, UCaaS)
- Security services

## How We're Paid
Vendor-reimbursed model:
- Free to buyers
- Suppliers pay us (standard practice in industry)
- Maintains independence through multi-supplier model

## Key Differentiation
1. 80M data points on supplier pricing/performance
2. Full-service (not just brokerage)
3. Technical + commercial expertise
4. 500+ supplier relationships

## Current Challenges
- Buyers skeptical of "free" model
- Confused with technology resellers/brokers
- Small agencies competing on boutique positioning
- Suppliers increasingly going direct with better tools

## Target Customer
- Mid-market to enterprise (500-5000+ employees)
- Multi-location (3+ sites)
- Technology refresh cycles or growth-driven needs
- Decision-makers: CIO, CFO, VP IT, VP Procurement
2. Update config (5 minutes):
yamlcompany_context:
  context_files:
    business_model: "context/upstack_business.md"
3. Customize buyer journey prompt (15 minutes):
python# Edit prompts_layer_1_horizontal.py

BUYER_JOURNEY_PROMPT = """
You are the Buyer Journey Intelligence Agent.

MISSION: Research how companies evaluate infrastructure advisory services.

{context_section}

UPSTACK-SPECIFIC CONTEXT:
{upstack_context}  # ← Injected from context file

YOUR RESEARCH QUESTIONS:

1. TRIGGER EVENTS & AWARENESS
- What events trigger companies to seek infrastructure advisory help?
- When do companies consider advisors vs. going direct to suppliers?
- What role do vendor-reimbursed advisory models play? ← ADDED

2. SKEPTICISM & TRUST
- What concerns do buyers have about "free" advisory services? ← ADDED
- How do buyers validate advisor independence? ← ADDED
- What proof points overcome skepticism? ← ADDED

3. COMPETITIVE DYNAMICS
- How do buyers differentiate between advisors and brokers? ← ADDED
- What makes buyers choose boutique agencies vs. full-service? ← ADDED
...
"""
After First Run (Iteration)
Review outputs → Identify gaps → Refine prompts
Example gap: "Buyer journey research doesn't address our specific business model concerns"
Fix:
python# Add to buyer_journey prompt
CRITICAL RESEARCH FOCUS:
UPSTACK uses a vendor-reimbursed "free to buyer" model.
You MUST research:
- How do buyers perceive vendor-reimbursed services? (recruiting, real estate analogs)
- What validates independence in these models?
- What are common objections and how are they overcome?

Search queries to include:
- "vendor paid advisory services buyer trust"
- "commission-free advisor independence"
- "technology advisor conflicts of interest"
Based on Market Feedback (Ongoing)
Prospect says: "We tried an advisor before, they just pushed one supplier"
Research update:
python# Add to competitive intelligence prompt
RESEARCH PRIORITY:
Multiple prospects report bad experiences with advisors favoring specific suppliers.

INVESTIGATE:
1. How common is supplier favoritism among technology advisors?
2. What structural factors cause this? (e.g., single-supplier relationships)
3. How do buyers identify truly independent advisors?
4. What proof points demonstrate multi-supplier neutrality?

This is CRITICAL for competitive positioning.
Bottom Line
Current system:

Uses your vertical/title choices ✅
Uses basic company context ✅
Uses generic research questions ❌
Uses generic source priorities ❌

After customization:

Uses your vertical/title choices ✅
Uses detailed business context ✅
Uses UPSTACK-specific questions ✅
Uses prioritized source steering ✅

Effort required:

Initial: 1-2 hours to create context and customize prompts
Ongoing: 30 min per iteration to refine based on learnings

Impact:

Generic → Specific research (addresses YOUR business challenges)
Broad → Focused insights (answers YOUR strategic questions)
Theory → Practice (validated against YOUR market reality)

The system is a framework, not a black box. You tune the research drivers, it executes at scale.

## Support

For issues or questions:

1. Check the logs in `logs/` directory
2. Review the checkpoint file in `checkpoints/`
3. Verify API key is set correctly
4. Ensure Python 3.11+ is installed

## License

MIT License - See LICENSE file for details

## Version

- **1.2.0** - CLI selective updates, dedicated unit tests, E2E test infrastructure (ADR-003)
- **1.1.0** - Research system enhancement: Layer 0, 3D playbooks, validation, context injection (ADR-002)
- **1.0.0** - Initial release
