# Claude Code Implementation Prompt: Brand Enrichment System

## Objective

Upgrade the brand alignment system in upstack-research from a "rewrite" model to a surgical "enrich" model. Add a target company alignment agent that mirrors the brand enrichment architecture. Both changes must integrate cleanly with the existing orchestrator, config, and context-loading patterns.

---

## System Context (READ BEFORE STARTING)

### Architecture you must follow

- **Orchestrator**: `src/research_orchestrator/orchestrator.py` — manages execution flow, layer sequencing, agent dispatch
- **Research sessions**: `src/research_orchestrator/research_session.py` — wraps Anthropic API calls with multi-turn accumulation
- **Prompts directory**: `src/research_orchestrator/prompts/` — one module per agent type. Each exports a builder function (`build_*_prompt()`) that accepts content + context and returns a formatted prompt string
- **Context loaders**: `src/research_orchestrator/utils/brand_context.py` and `src/research_orchestrator/prompts/context_injector.py` — load YAML context files and format them for prompt injection
- **Config files**: `build/config/projects/*.yaml` — per-run config. Inherit from `build/config/defaults.yaml` via `extends`
- **Brand context files**: `research-manager/context/*.yaml` — baseline.yaml, glossary.yaml, audience-personas.yaml, writing-standards.yaml
- **Output flow**: Layer 0 → Layer 1 → Layer 2 → Layer 3 → Playbooks → Validation → Brand Alignment (last step)

### Patterns you must match

- Context loaders: follow `BrandContextLoader` pattern (init with config_dir + file paths, `load_all()`, `format_for_prompt()`, YAML caching)
- Prompt builders: follow `build_brand_alignment_prompt(content, context)` pattern — pure functions that return formatted strings
- Config: YAML with relative paths from config file location. Brand alignment section already exists, extend it
- State tracking: use `self.state.initialize_*()`, `mark_in_progress()`, `mark_complete()`, `mark_failed()` with layer names
- Agent execution: `ResearchSession` with `execute_research()`, results saved via `_save_agent_output()`

---

## Task 1: Brand Assets Context File

### Create `research-manager/context/brand-assets.yaml`

This file provides concrete, insertable UPSTACK material. The brand alignment agent will reference this to enrich outputs with specific UPSTACK content.

Schema:

```yaml
# Brand Assets — Concrete insertable material for brand enrichment
# Unlike baseline.yaml (structural facts), this file contains
# ready-to-use proof points, methodology descriptions, and positioning lines

methodology:
  name: ""  # e.g., "UPSTACK Advisory Framework"
  tagline: ""  # One-line description
  steps: []  # Ordered list of named phases
  description: ""  # 2-3 sentence overview

proof_points:
  general: []  # Company-wide proof points (strings)
  by_service_category:
    security: []  # Each item: {point: "...", use_when: "..."}
    customer_experience: []
    network: []
    data_center: []
    communications: []
    cloud: []
  by_vertical:
    healthcare: []
    financial_services: []

case_studies:
  # Anonymized or approved case studies
  # Each item: {id, headline, vertical, service_category, situation, approach, outcome, metrics}
  - id: ""
    headline: ""
    vertical: ""
    service_categories: []
    situation: ""
    approach: ""
    outcome: ""
    metrics: []  # e.g., ["30% cost reduction", "8-week evaluation vs. 6-month average"]

positioning_lines:
  # Pre-written sentences the enrichment agent should use or adapt
  # Keyed by usage context
  vendor_neutral_intro: ""
  trust_model_explanation: ""
  advisory_vs_broker: ""
  advisory_vs_consultant: ""
  engagement_model: ""

credentials:
  certifications: []  # Team certifications relevant to advisory credibility
  partnerships: []  # Vendor/supplier partnerships
  by_vertical:
    healthcare: []  # e.g., "HIPAA compliance expertise", "Epic integration experience"
    financial_services: []

metadata:
  updated: ""
  version: "1.0"
  notes: "Populated by brand enrichment data agent. Review before use."
```

### Create the loader

**File**: `src/research_orchestrator/utils/brand_assets.py`

Follow the `BrandContextLoader` pattern exactly:
- Class `BrandAssetsLoader` with `__init__(self, config_dir, file_path, logger)`
- `load() -> dict` — loads and caches the YAML
- `format_for_prompt(context, vertical=None, service_category=None, title_cluster=None) -> str` — formats relevant assets for prompt injection. This method must FILTER assets by the playbook's vertical/service_category/title so the agent only sees relevant material
- `get_case_studies(vertical=None, service_category=None) -> list` — returns matching case studies
- `get_proof_points(service_category=None, vertical=None) -> list` — returns matching proof points

Key requirement: the `format_for_prompt()` method must produce a focused, filtered subset. Do NOT dump the entire assets file into the prompt. If the playbook is healthcare + security, only include healthcare proof points, security proof points, healthcare case studies, and healthcare credentials.

---

## Task 2: Rewrite Brand Alignment Prompt

### Replace `src/research_orchestrator/prompts/brand_alignment.py`

The current prompt asks the model to "rewrite" the entire document. Replace it with a surgical enrichment prompt.

**New prompt strategy:**

```
You are the UPSTACK Brand Enrichment Agent.

Your task is to ENRICH the following research playbook with specific UPSTACK
context. You are NOT rewriting — you are making targeted insertions and
replacements.

# UPSTACK Brand Assets
{brand_assets}

# Brand Voice & Standards
{brand_context}

# Original Playbook Content
{original_content}

# Enrichment Instructions

Make ONLY these specific changes to the original content:

## 1. UPSTACK Advisory Perspective Insertions
After each major pain point or challenge section, add a brief (2-3 sentence)
"UPSTACK Advisory Perspective" callout that connects the pain point to
UPSTACK's specific capability. Use proof points and case studies from the
Brand Assets above.

## 2. Methodology References
Where the playbook discusses evaluation frameworks or advisory processes,
reference UPSTACK's specific methodology by name and describe the relevant
steps.

## 3. Case Study Integration
Where the playbook discusses outcomes, ROI, or proof points, insert relevant
case studies from the Brand Assets. Match by vertical and service category.
Format as: "**Client Example:** [headline] — [1-2 sentence outcome with metrics]"

## 4. Terminology Alignment
Replace generic advisory language with UPSTACK-specific terms:
- "advisory firm" → "UPSTACK" (where contextually appropriate)
- "vendor-neutral advisor" → use UPSTACK's positioning language
- Generic trust model descriptions → UPSTACK's specific trust model

## 5. Credentials & Credibility
In sections discussing qualifications or credibility, add relevant UPSTACK
credentials and partnerships from the Brand Assets.

# Rules

- PRESERVE all research findings, data points, and citations unchanged
- PRESERVE the original document structure and headers
- DO NOT remove or paraphrase existing content
- DO NOT add generic filler — every addition must reference specific Brand Assets
- If no relevant Brand Asset exists for a section, leave that section unchanged
- Additions should feel organic, not bolted on
- Use the brand voice standards for any new text you write

Return the complete enriched document in markdown.
```

**Update the builder function:**

```python
def build_brand_alignment_prompt(
    original_content: str,
    brand_context: str,
    brand_assets: str
) -> str:
```

Note: this changes the function signature. Update the call site in `orchestrator.py` (`_execute_alignment_agent`, ~line 940).

---

## Task 3: Update Orchestrator Integration

### In `orchestrator.py.__init__()` (~line 141):

When brand alignment is enabled, also initialize a `BrandAssetsLoader` alongside the existing `BrandContextLoader`:

```python
if brand_config.get('enabled', False):
    # Existing brand context loader
    context_files = brand_config.get('context_files', {})
    config_dir = Path(config_path).parent
    self.brand_context_loader = BrandContextLoader(...)

    # New brand assets loader
    assets_file = brand_config.get('assets_file', '../../../research-manager/context/brand-assets.yaml')
    self.brand_assets_loader = BrandAssetsLoader(
        config_dir=config_dir,
        file_path=assets_file,
        logger=self.logger
    )
```

### In `_execute_alignment_agent()` (~line 904):

Update to:
1. Determine the vertical, service_category, and title_cluster from the original agent name (parse from `playbook_{vertical}_{title_cluster}` or 3D `playbook_{vertical}_{title}_{service_category}`)
2. Load filtered brand assets via `self.brand_assets_loader.format_for_prompt(context, vertical=..., service_category=...)`
3. Pass both `brand_context_formatted` AND `brand_assets_formatted` to the updated `build_brand_alignment_prompt()`

### Upgrade default model:

In `_execute_alignment_agent()` (~line 944), change the default model from `claude-haiku-4-5-20251001` to `claude-sonnet-4-5-20250929`:

```python
model = brand_config.get('model', 'claude-sonnet-4-5-20250929')
```

---

## Task 4: Target Company Alignment Agent

### Create `research-manager/context/targets/` directory

Each target company gets a YAML file:

```yaml
# research-manager/context/targets/{company_slug}.yaml

company:
  name: ""
  slug: ""  # filename-safe identifier
  industry: ""
  sub_industry: ""
  size: ""  # employee count or range
  revenue: ""  # if public
  headquarters: ""

known_stack:
  # Known technology in use (from job postings, press releases, public data)
  ehr: ""  # if healthcare
  crm: ""
  cloud: []  # e.g., ["AWS", "Azure"]
  network: ""
  security: []
  communications: ""

pain_signals:
  # Observable indicators of need
  - signal: ""
    source: ""  # "job posting", "earnings call", "press release", "news"
    date: ""
    relevance: ""  # How this connects to UPSTACK services

compliance:
  # Known regulatory requirements
  - ""

recent_events:
  # M&A, leadership changes, incidents, expansions
  - event: ""
    date: ""
    relevance: ""

engagement_history:
  # Prior UPSTACK interactions (if any)
  - ""

notes: ""

metadata:
  updated: ""
  source: ""  # "manual", "data_agent", "enrichment"
```

### Create `src/research_orchestrator/utils/target_context.py`

Follow the same loader pattern:
- Class `TargetContextLoader`
- `load(target_slug: str) -> dict`
- `format_for_prompt(context: dict) -> str`

### Create `src/research_orchestrator/prompts/target_alignment.py`

Prompt strategy — this runs AFTER brand enrichment:

```
You are the Target Company Personalization Agent.

Your task is to tailor this UPSTACK-enriched playbook for a specific
prospect. You are making the content feel like it was written FOR this
company, not AT this company.

# Target Company Profile
{target_context}

# Enriched Playbook Content
{enriched_content}

# Personalization Instructions

## 1. Stack-Aware Recommendations
Where the playbook discusses technology categories, reference the target's
known stack. Frame recommendations as improvements or complements to what
they already have.

Example: If they use Epic for EHR and the playbook discusses healthcare IT,
reference Epic-specific integration considerations.

## 2. Pain Signal Mapping
Connect the playbook's pain points to the target's observable pain signals.
Add brief "This applies to [Company]" callouts where pain signals match.

## 3. Compliance Contextualization
Where the playbook discusses regulatory requirements, emphasize the specific
regulations that apply to this company.

## 4. Event-Driven Urgency
If the target has recent events (M&A, leadership changes, incidents),
connect these to the playbook's trigger events analysis.

## 5. Language Calibration
Adjust formality, technical depth, and example relevance based on the
target's industry and size.

# Rules

- PRESERVE all UPSTACK brand enrichments from the prior step
- PRESERVE all research data and citations
- DO NOT fabricate information about the target company
- Only reference target details that appear in the Target Company Profile
- If a section has no relevant target-specific angle, leave it unchanged
- Personalization should feel insightful, not stalker-ish

Return the complete personalized document in markdown.
```

### Add to orchestrator

In `orchestrator.py.run()` (~line 360), add target alignment as an optional step AFTER brand alignment:

```python
# Target Company Alignment (if configured)
target_config = self.config.get('target_alignment', {})
if target_config.get('enabled', False):
    await self.execute_target_alignment()
```

Create `execute_target_alignment()` following the same pattern as `execute_brand_alignment()`:
- Find completed brand-aligned outputs (or playbooks if brand alignment disabled)
- Load target context from configured YAML
- Execute alignment agent per playbook
- Save to `outputs/<run>/target_aligned/` directory

### Config extension

Add to project YAML configs:

```yaml
target_alignment:
  enabled: false
  target_file: "../../../research-manager/context/targets/acme_health.yaml"
  model: "claude-sonnet-4-5-20250929"
  align_targets:
    - "brand_alignment"  # Runs on brand-aligned output, or "playbooks" if no brand step
```

---

## Task 5: Update Config and Tests

### Update `build/config/projects/e2e_minimal_test.yaml`:

Add `assets_file` to brand_alignment section:

```yaml
brand_alignment:
  enabled: true
  assets_file: "../../../research-manager/context/brand-assets.yaml"
  context_files:
    baseline: "../../../research-manager/context/baseline.yaml"
    writing_standards: "../../../research-manager/context/writing-standards.yaml"
    audience_personas: "../../../research-manager/context/audience-personas.yaml"
    glossary: "../../../research-manager/context/glossary.yaml"
  align_targets:
    - "playbooks"
  model: "claude-sonnet-4-5-20250929"  # Upgraded from Haiku
```

### Add unit tests

**File**: `src/tests/test_brand_assets.py`

Test the `BrandAssetsLoader`:
- `test_load_assets` — loads valid YAML
- `test_format_for_prompt_filters_by_vertical` — only healthcare assets when vertical="healthcare"
- `test_format_for_prompt_filters_by_service_category` — only security proof points when service_category="security"
- `test_get_case_studies_filtering` — returns matching case studies
- `test_missing_file_handling` — graceful handling when file doesn't exist

**File**: `src/tests/test_target_context.py`

Test the `TargetContextLoader`:
- `test_load_target` — loads valid YAML
- `test_format_for_prompt` — produces formatted markdown
- `test_missing_target_file` — graceful handling

### Update existing test for new prompt signature

In `src/tests/`, if there are tests that call `build_brand_alignment_prompt()`, update them to pass the new `brand_assets` parameter.

---

## Execution Order

1. Create `research-manager/context/brand-assets.yaml` with schema (placeholder values — will be populated by data agent)
2. Create `src/research_orchestrator/utils/brand_assets.py`
3. Rewrite `src/research_orchestrator/prompts/brand_alignment.py`
4. Update `orchestrator.py` — init, `_execute_alignment_agent()`, model default
5. Create `research-manager/context/targets/` directory with example schema
6. Create `src/research_orchestrator/utils/target_context.py`
7. Create `src/research_orchestrator/prompts/target_alignment.py`
8. Add `execute_target_alignment()` to orchestrator
9. Update config files
10. Write and run tests

---

## Constraints

- Do NOT modify `research_session.py` (the join fix is already in place)
- Do NOT change the Layer 0-3 or playbook generation flow
- Do NOT change the validation agent
- Keep `brand-assets.yaml` populated with placeholder/example values — the data agent prompt (separate deliverable) will generate real content
- Maintain backward compatibility: if `assets_file` is not in config, brand alignment should still work with just the existing context files (degrade gracefully)
- Maintain backward compatibility: if `target_alignment` is not in config, skip it entirely
- Follow all rules in CLAUDE.md (no `as any`, no `Math.random()`, explicit return types, etc.)
