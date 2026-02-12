# Strategic Messaging Architecture Population Prompt

## Your Task

You have access to UPSTACK's marketing materials, strategic documents, and the work product from the outreach audit, cross-team comparison, IRIS/Lumopath gap analysis, ad campaign analysis, buyer trends integration, and the established messaging architecture.

Your job is to populate the `strategic-messaging.yaml` file with the specific strategic content that our research agents need to produce UPSTACK-aligned output. The scaffold file has placeholder sections — you need to fill each one with real content drawn from the established strategic work.

## Context: Why This Matters

We have an automated research pipeline that produces market intelligence, vertical analysis, buyer journey research, and sales playbooks. The problem: the research agents are producing **generic advisory firm** output because they lack the strategic framing that you've already established. They don't know about the category creation thesis, the maturity model, the three pillars, the intelligence staging framework, or the champion enablement requirements. As a result, they position UPSTACK as "a vendor-neutral advisory firm" competing within the existing advisory market instead of defining a new category.

The `strategic-messaging.yaml` file you're populating will be injected into every research agent's prompt context, giving them the strategic rails they need.

## What You Need to Populate

For each section below, provide the actual content from the established messaging architecture. Do not invent new strategy — extract and codify what already exists.

### 1. Category Creation Framework (`category_creation`)

From the category creation thesis work, provide:

- **`category_thesis`**: The full argument for why Technology Vendor Lifecycle Management is an unmanaged discipline. This should be 3-5 paragraphs covering the problem, why it matters, why now, and the market creation opportunity.
- **`framing_rules`**: Review the 3 example rules in the scaffold. Add any additional framing rules from the established architecture. Each rule needs a `rule`, `example_bad`, and `example_good`.

### 2. Three Pillars (`three_pillars`)

From the established pillar framework, provide for each pillar:

- **`name`**: The pillar name as established
- **`description`**: One-sentence description
- **`replaces`**: What this pillar replaces (the old/broken way enterprises handle this)
- **`proof_point_refs`**: Reference IDs or descriptions that map to verified proof points in `brand-assets.yaml`
- **`agent_guidance`**: How research agents should invoke this pillar in their outputs

### 3. Maturity Model (`maturity_model`)

From the vendor lifecycle management maturity model, provide:

- **`name`**: The official maturity model name
- **`purpose`**: How it's used in messaging (2-3 sentences)
- **`levels`**: 4-5 maturity levels, each with:
  - `level_number` (1-5)
  - `name` (e.g., "Reactive", "Managed", etc.)
  - `description` (what the enterprise looks like at this level)
  - `symptoms` (observable indicators a prospect is at this level)
  - `upstack_value` (what UPSTACK provides to move them to the next level)
- **`agent_guidance`**: Instructions for how research agents use the maturity model in playbooks

### 4. Six Service Components (`service_components`)

From the established service component framework, provide for each component:

- **`name`**: Component name
- **`description`**: One-sentence description
- **`methodology_mapping`**: Which UPSTACK Advisory Process step(s) it maps to (Discovery, Strategy, Sourcing, Implementation, Lifecycle)
- **`without_it`**: What goes wrong when enterprises lack this component
- **`agent_guidance`**: How to reference in playbooks

### 5. Intelligence Staging Framework (`intelligence_staging`)

From the established intelligence staging work, provide:

- **`purpose`**: Why staging matters (2-3 sentences)
- **`levels`**: Each staging level with:
  - `level` (1, 2, 3)
  - `name` (e.g., "Transactional Intelligence")
  - `description` (what can be communicated at this level)
  - `safe_language` (list of phrases that are approved for this level)
  - `unsafe_language` (list of phrases that must NOT be used at this level)
  - `use_when` (what contexts this level applies to)
- **`agent_guidance`**: Default level for research outputs and escalation rules

### 6. Champion Enablement (`champion_enablement`)

From the buying committee analysis and champion enablement work, provide:

- **`context`**: The buying committee problem statement (reference the 25-person committee, 17% vendor time, 80% regret stats from `brand-assets.yaml`)
- **`requirements`**: 4-6 specific content requirements for champion-friendly outputs
- **`forwardable_criteria`**: What makes content forwardable (`good` list) vs. not (`bad` list)
- **`agent_guidance`**: Structural requirements for playbook sections (word limits, self-contained sections, etc.)

### 7. Operational Proof Narratives (`operational_proof`)

From the IRIS/Lumopath gap analysis and operational records, provide:

- **`purpose`**: Why these narratives matter (2-3 sentences)
- **`narratives`**: 3-5 real operational proof stories, each with:
  - `title` (short headline)
  - `problem` (what happened)
  - `intervention` (what UPSTACK did)
  - `counterfactual` (what would have happened without UPSTACK)
  - `service_component` (which of the six components this demonstrates)
  - `source` (where this was documented — IRIS, Lumopath, case study, etc.)

Include the examples referenced in the assessment:
  - Catching Verizon billing fraud
  - Diagnosing carrier problems carriers missed
  - Getting executive intervention at Colt
  - Any other strong operational proof stories

### 8. Outreach Audit Findings (`outreach_audit`)

From the outreach audit and cross-team comparison, provide:

- **`anti_patterns`**: 5-8 patterns found in actual UPSTACK outreach that must not be repeated, each with:
  - `pattern` (what was wrong)
  - `why_it_matters` (the damage it causes)
  - `instead` (what to do instead)
- **`kill_items`**: List of specific things that must NEVER appear in research outputs (e.g., "performance-based" claim, "not commission-based" claim — some are already in `brand-assets.yaml` language_standards, but include any additional ones)

### 9. Vertical Messaging Adaptations (`vertical_adaptations`)

For financial services and healthcare, provide:

- **`category_thesis_adaptation`**: How the vendor lifecycle management problem manifests specifically in this vertical (2-3 paragraphs)
- **`maturity_model_emphasis`**: Which maturity levels are most common in this vertical and what the typical progression looks like
- **`primary_proof_narratives`**: Which operational proof narratives are most relevant
- **`champion_profile`**: Who the internal champion typically is and what they need to sell internally

## Format Requirements

- Output as valid YAML
- Keep the same structure and key names as the scaffold file
- Change all `status` fields from "SCAFFOLD" to "POPULATED"
- Use `|` for multi-line text blocks
- Keep individual text blocks under 500 words
- Be specific and concrete — research agents will use this literally, not interpret it
- Reference `brand-assets.yaml` proof points by description when applicable (the research agents have access to both files)

## Quality Checklist

Before submitting, verify:

- [ ] Every PLACEHOLDER is replaced with real content from the established architecture
- [ ] No content is invented — everything traces back to existing strategic work
- [ ] Language standards from `brand-assets.yaml` are respected (no prohibited terms)
- [ ] Framing rules are actionable (each has bad/good examples)
- [ ] Maturity model levels are distinct and progressive
- [ ] Intelligence staging levels have clear safe/unsafe language boundaries
- [ ] Champion enablement requirements are structural, not just aspirational
- [ ] Operational proof narratives include the counterfactual ("without UPSTACK...")
- [ ] Kill items don't duplicate what's already in `brand-assets.yaml` `language_standards.prohibited_terms`
- [ ] Vertical adaptations are genuinely different from each other, not copy-paste with word swaps
