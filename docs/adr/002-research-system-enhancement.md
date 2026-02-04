# ADR-002: Research System Enhancement

**Status**: Proposed
**Date**: 2026-02-04
**Authors**: apex-architect, apex-guardian

---

## Context

A system audit identified six critical gaps in the upstack-research system:

1. **Search Term Breadth**: Prompts use advisory-centric terms rather than buyer-problem-centric terms
2. **Information Source Discovery**: Missing LinkedIn, YouTube, G2/TrustRadius, vendor webinars, industry events
3. **Suppliers as Competition**: Researching other advisors instead of direct vendor sales (the actual primary competition)
4. **Context File Injection**: Project configs reference context files but prompts don't inject them
5. **Service Category Dimension**: Research treats all services as monolithic; playbooks lack service specificity
6. **Missing Validation Step**: No quality gate before outputs are production-ready

---

## Decision

Implement a multi-faceted enhancement addressing all six gaps:

### 1. Layer 0: Service Category Research

Add a new research layer that runs BEFORE Layer 1, researching how buyers discover and evaluate specific service categories (Security, CX, Network, etc.).

**Execution Flow**:
```
Layer 0 (Service Categories) → Layer 1 (Horizontal) → Layer 2 (Vertical) → Layer 3 (Title) → Playbooks → Validation → Brand Alignment
```

### 2. Enhanced Search Terms & Information Sources

Update all prompts with:
- Buyer-centric search vocabulary ("best CCaaS for healthcare", "SD-WAN comparison")
- Required information source categories (G2, TrustRadius, LinkedIn, YouTube, etc.)

### 3. Supplier Competition Research

Update `CHANNELS_COMPETITIVE_PROMPT` to research how suppliers (AT&T, Verizon, AWS, Five9, Palo Alto, etc.) position and sell directly to buyers.

### 4. Context Injection Mechanism

Create `ResearchContextInjector` that loads `baseline.yaml` and `writing-standards.yaml` and injects content into all prompts automatically.

### 5. 3-Dimensional Playbooks

Extend playbook generation from `Vertical × Title` to `Vertical × Title × Service Category`.

### 6. Validation Agent

Add quality gate after playbook generation that assesses completeness, accuracy, and actionability before outputs are considered production-ready.

---

## Critical Requirement: Dynamic Configuration

### All service categories, subcategories, and suppliers MUST be user-defined in configuration files.

**NO HARDCODING** of:
- Service category names
- Service subcategories
- Supplier/vendor names
- Vertical names
- Title cluster names

### Configuration Source: `research-manager/context/baseline.yaml`

```yaml
company:
  services:
    security:
      name: "Network Security"
      subcategories:
        - "EDR (endpoint detection and response)"
        - "MDR (managed detection and response)"
        - "IAM (identity and access management)"
        - "SASE (secure access service edge)"
        - "ZTNA (zero trust network access)"
      key_suppliers:           # ← REQUIRED: Factual vendor names (seed data for research)
        - "Palo Alto Networks"
        - "CrowdStrike"
        - "Zscaler"
        - "Okta"
        - "Microsoft Defender"
      # NOTE: buyer_triggers, evaluation_criteria, etc. are DISCOVERED by research
      # Do NOT pre-define them here - the research system investigates these

    customer_experience:
      name: "Customer Experience (CX)"
      subcategories:
        - "CCaaS (cloud contact center)"
        - "Conversational AI / IVA"
        - "Workforce optimization"
        - "Omnichannel engagement"
      key_suppliers:           # ← REQUIRED: Factual vendor names
        - "Five9"
        - "Genesys"
        - "NICE"
        - "Talkdesk"
        - "Amazon Connect"

    network:
      name: "Network & Connectivity"
      subcategories:
        - "SD-WAN (software-defined WAN)"
        - "Dedicated Internet Access (DIA)"
        - "MPLS and Ethernet services"
        - "Cloud direct connects"
      key_suppliers:           # ← REQUIRED: Factual vendor names
        - "AT&T"
        - "Verizon"
        - "Lumen"
        - "Cradlepoint"
        - "Fortinet"

    # ... additional categories (data_center, communications, cloud)
```

### Loading Pattern

```python
# In ResearchContextInjector or service_category.py
def load_service_categories(baseline_path: Path) -> Dict[str, ServiceCategoryConfig]:
    """Load service categories from baseline.yaml - NO HARDCODING."""
    with open(baseline_path) as f:
        baseline = yaml.safe_load(f)

    return baseline.get('company', {}).get('services', {})

# Usage in prompts
categories = load_service_categories(baseline_path)
security = categories['security']
vendors = security['key_suppliers']  # Dynamic from config
```

### Prompt Template Pattern

```python
SERVICE_CATEGORY_PROMPT_TEMPLATE = """
You are the {category_name} Category Intelligence Agent.

SERVICE CATEGORY CONTEXT (from config):
- Category: {category_name}
- Subcategories: {subcategories}
- Key Suppliers to Research: {key_suppliers}  ← Factual seed data from config

YOUR RESEARCH MISSION:
DISCOVER (not pre-defined):
- Buyer triggers for {category_name}
- Evaluation criteria buyers use
- Market pressures driving demand
- How suppliers position against each other
- Where buyers research {category_name} solutions

YOUR RESEARCH QUESTIONS:
...
"""
```

---

## Layer Handoffs: Context Flow Between Layers

### What Each Layer Receives and Produces

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 0: Service Category Research                                          │
│ ─────────────────────────────────────                                        │
│ RECEIVES: key_suppliers from baseline.yaml (factual seed data)              │
│ DISCOVERS: buyer triggers, evaluation criteria, discovery patterns,         │
│            vendor positioning, market dynamics                               │
│ PRODUCES: Category-specific buyer journey, vendor landscape, search terms   │
│ PASSES TO: Layer 1 (informs horizontal research scope)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Horizontal Research                                                 │
│ ─────────────────────────────────────                                        │
│ RECEIVES: Layer 0 category insights (buyer patterns, vendor positioning)    │
│ DISCOVERS: Cross-category buyer journey, competitive landscape,              │
│            messaging patterns, customer expansion paths                      │
│ PRODUCES: Horizontal insights applicable across verticals                   │
│ PASSES TO: Layer 2 (via format_layer_1_context_for_vertical)                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: Vertical Research                                                   │
│ ─────────────────────────────────────                                        │
│ RECEIVES: Layer 1 horizontal insights                                        │
│ DISCOVERS: Industry-specific buying patterns, regulations, market pressures,│
│            vertical-specific triggers, competitive dynamics                  │
│ PRODUCES: Vertical playbooks with industry context                          │
│ PASSES TO: Layer 3 (via format_layer_2_context_for_title)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: Title Research                                                      │
│ ─────────────────────────────────────                                        │
│ RECEIVES: Layer 1 + Layer 2 context                                          │
│ DISCOVERS: Role-specific pain points, decision authority, messaging         │
│ PRODUCES: Persona playbooks                                                  │
│ PASSES TO: Playbooks (all layer context)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PLAYBOOKS: Integration (V × T × SC)                                          │
│ ─────────────────────────────────────                                        │
│ RECEIVES: Layer 0 + Layer 1 + Layer 2 + Layer 3 context                     │
│ PRODUCES: Actionable playbooks with service-specific messaging              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Context Helper Functions Required

```python
# In context_helpers.py

def get_layer_0_context(state_tracker, service_categories: List[str]) -> Dict[str, Any]:
    """Extract Layer 0 outputs for downstream agents."""
    context = {}
    for category in service_categories:
        agent_name = f'service_category_{category}'
        output = state_tracker.get_agent_output(agent_name, 'layer_0')
        if output:
            context[category] = output
    return context


def format_layer_0_context_for_layer_1(layer_0_context: Dict[str, Any]) -> str:
    """Format Layer 0 service category research for Layer 1 agents.

    Includes:
    - Category-specific buyer discovery patterns
    - Vendor positioning insights
    - Search term vocabulary for buyer-centric research
    - Key evaluation criteria discovered
    """
    sections = []
    for category_name, output in layer_0_context.items():
        summary = extract_summary(output, max_length=400)
        sections.append(f"""
### {category_name.upper()} CATEGORY INSIGHTS

{summary}

---
""")
    return "\n".join(sections)
```

---

## Research Scope: Provided vs. Discovered

### Provided Upfront (Configuration)

| Data Type | Source | Purpose |
|-----------|--------|---------|
| Supplier/vendor names | `baseline.yaml` key_suppliers | Seed data for competitive research |
| Service categories | `baseline.yaml` services | Define research scope |
| Subcategories | `baseline.yaml` subcategories | Specificity in research |
| Verticals | `verticals.yaml` | Industry focus |
| Title clusters | `title_clusters.yaml` | Persona focus |

### Discovered Through Research

| Data Type | Layer | Research Method |
|-----------|-------|-----------------|
| Buyer triggers | L0, L1, L2 | Web search for buying signals |
| Evaluation criteria | L0, L1, L2 | Peer reviews, analyst reports |
| Market pressures | L0, L2 | Current news, analyst commentary |
| Vendor positioning | L0, L1 | Vendor websites, messaging analysis |
| Pain points | L2, L3 | Forums, interviews, case studies |
| Decision authority | L3 | Role research, org studies |
| Messaging language | L1, L3 | Buyer quotes, forum discussions |

**Note**: `buyer_triggers` in baseline.yaml is OPTIONAL suggestive data. Research validates/extends/overrides.

---

## Market Pressures in Vertical Research

### Current Gap

The vertical prompt asks about triggers but doesn't specifically research **current market pressures**.

### Required Enhancement to `VERTICAL_AGENT_PROMPT_TEMPLATE`

Add new research vector:

```python
# In vertical.py - ADD after VERTICAL PAIN POINTS section

5. CURRENT MARKET PRESSURES (NEW)
- What macro trends are forcing {vertical_name} to re-evaluate infrastructure?
- What recent disruptions (AI, economic, regulatory) are driving urgency?
- What competitor moves are creating pressure to act?
- What analyst predictions are influencing buying timelines?
- What budget pressures or expansions are affecting procurement?
- How has the buying environment changed in the past 12 months?
```

### Required Enhancement to `SERVICE_CATEGORY_PROMPT_TEMPLATE`

Add market pressure research:

```python
# In service_category.py

6. CATEGORY MARKET PRESSURES
- What macro trends are driving demand for {category_name}?
- What recent incidents or events have elevated this category's priority?
- How is AI/automation affecting this category?
- What analyst predictions are influencing buying timelines?
- What competitive pressures are forcing evaluation of {category_name}?
```

---

## Service Category Information Flow to Outputs

### How Service Category Context Appears in Playbooks

The 3D playbook prompt MUST integrate service category research:

```python
PLAYBOOK_GENERATION_PROMPT_3D = """
You are the Playbook Integration Agent.

MISSION: Create actionable playbook for:
- VERTICAL: {vertical_name}
- TITLE: {title_name}
- SERVICE CATEGORY: {service_category_name}

LAYER 0 CONTEXT ({service_category_name}):
{layer_0_context}   ← Service category buyer journey, vendor landscape, search terms

...

INTEGRATION REQUIREMENTS:
1. Use {service_category_name}-specific buyer triggers from Layer 0
2. Reference {service_category_name} vendors when discussing competition
3. Apply {service_category_name} evaluation criteria to value proposition
4. Use {service_category_name} search terms in content recommendations
5. Address {service_category_name} market pressures in messaging urgency
"""
```

### Playbook Output MUST Include

- Service-category-specific pain points (not generic)
- Vendor comparison positioning (vs. the specific suppliers)
- Category-specific buyer triggers
- Category-specific evaluation criteria
- Market pressure urgency messaging

---

## Contracts (from Guardian Analysis)

### StateTracker Updates
- Add `layer_0` key to state dict
- Add `initialize_layer_0(service_categories: List[str])` method
- Update `can_execute_layer_2()` to require layer_0 complete

### Config Schema Updates
- Add `service_categories: List[str]` to ResearchConfig
- Add `priority_service_categories: List[str]` for 3D playbooks
- Add `after_layer_0: bool` and `after_validation: bool` to ReviewGatesConfig

### New Files
- `src/research_orchestrator/prompts/service_category.py`
- `src/research_orchestrator/prompts/validation.py`
- `src/research_orchestrator/prompts/context_injector.py`

### Modified Files
- `src/research_orchestrator/orchestrator.py` - Layer 0 execution, context injection, output directories
- `src/research_orchestrator/state/tracker.py` - Layer 0 state management
- `src/research_orchestrator/prompts/horizontal.py` - Enhanced search terms, supplier competition
- `src/research_orchestrator/prompts/playbook.py` - 3D playbook support
- `research-manager/context/baseline.yaml` - Add key_suppliers to each service category ✅ DONE

### Output Directory Structure (Updated)

```
outputs/{execution_id}/
├── layer_0/                    # ← NEW: Service category research
│   ├── service_category_security.md
│   ├── service_category_customer_experience.md
│   ├── service_category_network.md
│   ├── service_category_data_center.md
│   ├── service_category_communications.md
│   └── service_category_cloud.md
├── layer_1/
│   ├── buyer_journey.md
│   ├── channels_competitive.md
│   ├── customer_expansion.md
│   ├── messaging_positioning.md
│   └── gtm_synthesis.md
├── layer_2/
│   ├── vertical_healthcare.md
│   └── vertical_financial_services.md
├── layer_3/
│   ├── title_cfo_cluster.md
│   ├── title_cio_cto_cluster.md
│   └── ...
├── playbooks/
│   ├── playbook_healthcare_cfo_security.md      # ← 3D: V × T × SC
│   ├── playbook_healthcare_cfo_customer_experience.md
│   └── ...
├── validation/                 # ← NEW: Validation reports
│   └── validation_report.md
└── brand_alignment/
    └── ...
```

### Orchestrator Output Directory Update

```python
# In orchestrator.py __init__, update line 125:
for layer in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'playbooks', 'validation', 'brand_alignment']:
    (self.output_dir / layer).mkdir(parents=True, exist_ok=True)
```

---

## Selective Update Capability

### Current Support

| Capability | Status | Command |
|------------|--------|---------|
| Run specific layer | ✅ Exists | `--layer 1\|2\|3` |
| Run specific agents | ✅ Exists | `--agents buyer_journey,vertical_healthcare` |
| Resume from checkpoint | ✅ Exists | `--resume execution_id` |
| Skip completed agents | ✅ Exists | Automatic via `is_agent_complete()` |

### Required Additions

| Capability | Status | Command |
|------------|--------|---------|
| Run Layer 0 | ❌ Add | `--layer 0` |
| Force re-run completed agent | ❌ Add | `--force` or `--refresh` flag |
| Selective vertical refresh | ❌ Add | `--verticals healthcare,legal` |
| Selective title refresh | ❌ Add | `--titles cfo_cluster,security_leadership` |
| Selective service category | ❌ Add | `--service-categories security,cx` |

### Update Workflow Example

```bash
# Initial full run
python run_research.py --config gtm_phase1_2026.yaml

# 6 months later: Market shifted for Security category
python run_research.py --resume gtm_phase1_2026 \
  --layer 0 --service-categories security \
  --force \
  --config gtm_phase1_2026.yaml

# Then update downstream layers that depend on Security
python run_research.py --resume gtm_phase1_2026 \
  --layer 2 --verticals healthcare \
  --force \
  --config gtm_phase2_2026.yaml
```

### Output Preservation

When `--force` re-runs an agent:
- Prior output renamed to `{agent}_prior_{timestamp}.md`
- New output saved to `{agent}.md`
- Checkpoint updated with new metadata
- Prior checkpoint version preserved in `checkpoints/history/`

---

## Backward Compatibility

1. **Layer 0 is optional**: If `service_categories` config is empty, skip Layer 0
2. **3D playbooks are opt-in**: Only generate if `priority_service_categories` is non-empty
3. **Existing checkpoints**: Handle missing `layer_0` key gracefully
4. **Config migration**: New fields have default empty values

---

## Cost Impact

| Component | Additional Cost |
|-----------|-----------------|
| Layer 0 (6 service categories) | +$6-12/run |
| 3D Playbooks (depends on scope) | +$10-20/run |
| Validation Agent | +$1-2/run |
| **Total** | +$17-34/run |

---

## Implementation Phases

1. **Phase 1**: Update `baseline.yaml` with key_suppliers (prerequisite)
2. **Phase 2**: Context injection mechanism
3. **Phase 3**: Enhanced prompts (search terms, sources, supplier competition)
4. **Phase 4**: Layer 0 service category research
5. **Phase 5**: 3D playbooks
6. **Phase 6**: Validation agent

---

## Verification

Before implementation begins:
- [ ] `baseline.yaml` updated with `key_suppliers` for all service categories
- [ ] No hardcoded vendor/supplier names in any Python files
- [ ] All service category data loaded dynamically from config
