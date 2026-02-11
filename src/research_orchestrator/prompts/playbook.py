# research_orchestrator/prompts/playbook.py
"""
Integration: Playbook Generation Prompts

Synthesizes research layers into actionable ABM playbooks.

Supports both 2D (V × T) and 3D (V × T × SC) playbook generation:
- 2D: Vertical × Title combinations (original format)
- 3D: Vertical × Title × Service Category combinations (enhanced format)
"""

from typing import Any

from .vertical import VERTICALS
from .title import TITLE_CLUSTERS
from .context_helpers import extract_summary
from .types import ServiceCategoryConfig


PLAYBOOK_GENERATION_PROMPT = """
You are the Playbook Integration Agent.

MISSION: Synthesize research from all three layers into an actionable ABM playbook for {vertical_name} {title_name}.

{context_section}

{company_context_section}

YOUR INTEGRATION TASK:

CRITICAL METHODOLOGY:
- Ground all value propositions in the company's actual business model
- Use only verified proof points — do not invent statistics
- If the advisory is vendor-reimbursed at zero cost to the buyer, do not invent pricing tiers or fees
- Recommendations should extend the existing engagement model, not replace it

Create a complete go-to-market playbook that combines:
- Horizontal insights (buyer journey, competitive landscape, messaging patterns)
- Vertical specifics ({vertical_name} industry context, regulations, buying patterns)
- Title context ({title_name} pain points, decision authority, communication preferences)

CRITICAL INTEGRATION QUESTIONS:

1. PAIN POINTS (Vertical x Title Specific)
- How do {title_name} pain points manifest differently in {vertical_name}?
- What are the top 3-5 pain points for {title_name} in {vertical_name} specifically?
- Which infrastructure advisory services address these pain points?

2. VALUE PROPOSITION (Adapted)
- What is the primary value proposition for {vertical_name} {title_name}?
- How does this differ from generic messaging?
- What vertical-specific language should be used?

3. PROOF POINTS (Relevant Evidence)
- What proof points resonate with {title_name} in {vertical_name}?
- What case studies or metrics are most relevant?
- What credentials or certifications matter?

4. OUTBOUND SEQUENCE (Multi-Touch Campaign)
- What is the optimal outreach sequence?
- What channels does {title_name} in {vertical_name} prefer?
- What content offers drive engagement at each stage?

DELIVERABLES (Markdown format):

## Executive Summary
- What makes {vertical_name} x {title_name} unique
- Top 3 pain points and how advisory services address them
- Key success factors for this combination

## Target Profile
### Vertical Context
- {vertical_name} industry dynamics
- Regulatory environment
- Technology priorities

### Title Context  
- {title_name} responsibilities and pressures
- Decision authority in {vertical_name}
- Success metrics

### Combined Profile
- Decision authority specific to this combination
- Budget thresholds
- Primary pain points (ranked)

## Messaging Framework
### Value Proposition (Vertical x Title Specific)
- Primary: [One sentence adapted for this combination]
- Supporting points: [3-5 bullets]

### Key Messages (Ranked by Resonance)
1. [Message using vertical terminology and title priorities]
2. [Message]
3. [Message]

### Proof Points (Vertical x Title Relevant)
1. [Case study or metric from similar companies/roles]
2. [Proof point]
3. [Proof point]

## Outbound Sequence
### Touch 1: Email
**Subject:** [Vertical x Title Specific]
**Body:** [Email copy that speaks to their specific context]

### Touch 2: LinkedIn
**Format:** [Connection request / InMail]
**Content:** [Vertical-relevant content]

### Touch 3: Phone
**Opening:** [Context-setting intro]
**Discovery Questions:** 
- [Question specific to vertical pain point]
- [Question specific to title responsibility]

### Touch 4-5: [Additional touches]

## Objection Handling
### Objection 1: [Vertical x Title Specific]
**Objection:** "[Likely objection in their words]"
**Response:** [Proof points and reframe]

### Objection 2-3: [Additional objections]

## Timing & Triggers
### Best Timing
- **Time of year:** [Based on vertical buying cycles]
- **Time of quarter:** [Based on title authority/budget]

### Trigger Events
- [Event that indicates buying window]
- [Event that signals opportunity]

## Implementation Checklist
### Content Assets Needed
- [ ] {vertical_name} case studies featuring {title_name}
- [ ] ROI calculator with {vertical_name} metrics
- [ ] {title_name} role-specific one-pager

### Sales Enablement
- [ ] {vertical_name} x {title_name} battle card
- [ ] Discovery question bank
- [ ] Objection handling guide

## Research Integration Notes
### From Layer 1 (Horizontal)
- [Key insights from buyer journey, competitive analysis, messaging]

### From Layer 2 (Vertical)
- [Key {vertical_name}-specific insights]

### From Layer 3 (Title)
- [Key {title_name} insights in {vertical_name} context]

METHODOLOGY:
- Synthesize insights from all prior layers
- Create cohesive narrative specific to this combination
- Make concrete and immediately actionable
- Ground all recommendations in research
- Be specific, not generic

Begin playbook generation now.
"""


def build_playbook_prompt(
    vertical_key: str,
    title_key: str,
    layer_1_context: dict[str, Any],
    layer_2_context: dict[str, Any],
    layer_3_context: dict[str, Any],
    company_context: str = ""
) -> str:
    """
    Build integration prompt with full context from all layers.

    Args:
        vertical_key: Vertical identifier (e.g., 'healthcare')
        title_key: Title cluster identifier (e.g., 'cfo_cluster')
        layer_1_context: Dictionary of Layer 1 agent outputs
        layer_2_context: Dictionary of Layer 2 vertical agent outputs
        layer_3_context: Dictionary of Layer 3 title agent outputs
        company_context: Optional pre-formatted company context string

    Returns:
        Formatted prompt string ready for ResearchSession

    Raises:
        ValueError: If vertical_key or title_key not found
    """
    if vertical_key not in VERTICALS:
        raise ValueError(
            f"Unknown vertical: {vertical_key}. "
            f"Valid options: {', '.join(VERTICALS.keys())}"
        )
    
    if title_key not in TITLE_CLUSTERS:
        raise ValueError(
            f"Unknown title cluster: {title_key}. "
            f"Valid options: {', '.join(TITLE_CLUSTERS.keys())}"
        )
    
    vertical = VERTICALS[vertical_key]
    title = TITLE_CLUSTERS[title_key]
    
    # Build comprehensive context summary
    context_summary = _format_integration_context(
        vertical_key, title_key, vertical, title,
        layer_1_context, layer_2_context, layer_3_context
    )

    # Format company context section
    if company_context:
        company_section = f"=== COMPANY CONTEXT ===\n\n{company_context}\n\n---"
    else:
        company_section = ""

    return PLAYBOOK_GENERATION_PROMPT.format(
        vertical_name=vertical['name'],
        title_name=title['name'],
        context_section=context_summary,
        company_context_section=company_section
    )


def _format_integration_context(
    vertical_key: str,
    title_key: str,
    vertical: dict[str, str],
    title: dict[str, Any],
    layer_1_context: dict[str, Any],
    layer_2_context: dict[str, Any],
    layer_3_context: dict[str, Any]
) -> str:
    """Format complete context from all three layers for playbook generation."""
    
    # Layer 1 context
    layer_1_text = "=== LAYER 1: HORIZONTAL RESEARCH ===\n\n"
    
    agent_sections = [
        ('buyer_journey', 'BUYER JOURNEY INSIGHTS'),
        ('channels_competitive', 'COMPETITIVE INTELLIGENCE'),
        ('customer_expansion', 'CUSTOMER EXPANSION PATTERNS'),
        ('messaging_positioning', 'MESSAGING RESEARCH'),
        ('gtm_synthesis', 'GTM STRATEGY')
    ]
    
    for agent_key, section_title in agent_sections:
        if agent_key in layer_1_context:
            summary = extract_summary(layer_1_context[agent_key], max_length=300)
            layer_1_text += f"**{section_title}:**\n{summary}\n\n"
    
    # Layer 2 context
    layer_2_text = f"=== LAYER 2: VERTICAL RESEARCH ({vertical['name']}) ===\n\n"
    
    if vertical_key in layer_2_context:
        summary = extract_summary(layer_2_context[vertical_key], max_length=400)
        layer_2_text += f"**VERTICAL SUMMARY:**\n{summary}\n\n"
    
    layer_2_text += f"**Key Regulations:** {vertical['key_regulations']}\n"
    layer_2_text += f"**Key Challenges:** {vertical['key_challenges']}\n\n"
    
    # Layer 3 context
    layer_3_text = f"=== LAYER 3: TITLE RESEARCH ({title['name']}) ===\n\n"
    
    if title_key in layer_3_context:
        summary = extract_summary(layer_3_context[title_key], max_length=400)
        layer_3_text += f"**TITLE SUMMARY:**\n{summary}\n\n"
    
    layer_3_text += f"**Decision Authority:** {title['decision_authority']}\n"
    layer_3_text += f"**Key Focus:** {title['key_focus']}\n\n"
    
    # Integration mission
    mission_text = f"""=== YOUR INTEGRATION MISSION ===

Combine these three layers into ONE cohesive playbook for:
TARGET: {vertical['name']} {title['name']}

Make it specific, actionable, and grounded in the research above.
---
"""
    
    return layer_1_text + layer_2_text + layer_3_text + mission_text


# =============================================================================
# 3D PLAYBOOK GENERATION (V × T × SC)
# =============================================================================

PLAYBOOK_GENERATION_PROMPT_3D = """
You are the Playbook Integration Agent.

MISSION: Create an actionable playbook for:
- VERTICAL: {vertical_name}
- TITLE: {title_name}
- SERVICE CATEGORY: {service_category_name}

{context_section}

{company_context_section}

YOUR INTEGRATION TASK:

CRITICAL METHODOLOGY:
- Ground all value propositions in the company's actual business model
- Use only verified proof points — do not invent statistics
- If the advisory is vendor-reimbursed at zero cost to the buyer, do not invent pricing tiers or fees
- Recommendations should extend the existing engagement model, not replace it

Create a service-category-specific go-to-market playbook that combines:
- Service Category Intelligence ({service_category_name} buyer journey, vendor landscape, search terms)
- Horizontal insights (buyer journey, competitive landscape, messaging patterns)
- Vertical specifics ({vertical_name} industry context, regulations, buying patterns)
- Title context ({title_name} pain points, decision authority, communication preferences)

CRITICAL INTEGRATION REQUIREMENTS:

1. USE {service_category_name}-SPECIFIC BUYER TRIGGERS from Layer 0
   - What triggers {vertical_name} {title_name} to evaluate {service_category_name}?
   - What {service_category_name} evaluation criteria matter to {title_name}?

2. REFERENCE {service_category_name} VENDORS when discussing competition
   - How do {service_category_name} vendors sell directly to {vertical_name}?
   - What vendor positioning should we counter?

3. APPLY {service_category_name} EVALUATION CRITERIA to value proposition
   - What {service_category_name} criteria does {title_name} prioritize?
   - How does advisory expertise differentiate vs. vendor sales?

4. USE {service_category_name} SEARCH TERMS in content recommendations
   - What terms do {title_name} use when researching {service_category_name}?
   - What content should we create to capture this search behavior?

5. ADDRESS {service_category_name} MARKET PRESSURES in messaging urgency
   - What macro trends create urgency for {service_category_name} in {vertical_name}?
   - How do we frame timing and urgency?

DELIVERABLES (Markdown format):

## Executive Summary
- Unique value proposition for {vertical_name} {title_name} evaluating {service_category_name}
- Top 3 service-category-specific pain points
- Key success factors for this V × T × SC combination

## Target Profile
### Service Category Context
- {service_category_name} market dynamics
- Key vendors: {key_suppliers}
- Buyer evaluation criteria for {service_category_name}
- Current market pressures

### Vertical Context
- {vertical_name} industry dynamics for {service_category_name}
- Regulatory requirements affecting {service_category_name}
- Technology priorities

### Title Context
- {title_name} responsibilities for {service_category_name} decisions
- Decision authority in {vertical_name}
- Success metrics

### Combined Profile (V × T × SC)
- Decision authority for {service_category_name} in {vertical_name}
- Budget thresholds for {service_category_name}
- Primary pain points (ranked, service-category-specific)

## Messaging Framework
### Value Proposition ({service_category_name} Specific)
- Primary: [One sentence adapted for this V × T × SC combination]
- Supporting points: [3-5 bullets using {service_category_name} terminology]

### Key Messages (Service-Category Specific)
1. [Message using {service_category_name} terminology and {title_name} priorities]
2. [Message addressing vendor vs. advisory comparison]
3. [Message addressing {service_category_name} market pressure]

### Proof Points ({service_category_name} Relevant)
1. [{service_category_name} case study or metric from similar companies/roles]
2. [Vendor comparison proof point]
3. [ROI or risk reduction proof point]

### Vendor Comparison Positioning
- How we differentiate from {key_suppliers} direct sales
- Objections {key_suppliers} sales teams raise about advisors
- Counter-positioning language

## Outbound Sequence
### Touch 1: Email
**Subject:** [{service_category_name} specific for {vertical_name}]
**Body:** [Email copy referencing {service_category_name} triggers]

### Touch 2: LinkedIn
**Format:** [Connection request / InMail]
**Content:** [{service_category_name} content or insight]

### Touch 3: Phone
**Opening:** [{service_category_name} context-setting intro]
**Discovery Questions:**
- [Question about {service_category_name} evaluation criteria]
- [Question about vendor experience with {key_suppliers}]

### Touch 4-5: [Additional touches]

## Objection Handling
### Objection 1: "We're already talking to [vendor] directly"
**Response:** [Advisory value vs. vendor sales]

### Objection 2: "{service_category_name}-specific objection"
**Response:** [Proof points and reframe]

### Objection 3: [Vertical x Title Specific]
**Response:** [Proof points and reframe]

## Timing & Triggers
### Best Timing
- **{service_category_name} Timing:** [Contract renewal cycles, budget cycles]
- **Vertical Timing:** [Based on {vertical_name} buying cycles]
- **Title Timing:** [Based on {title_name} authority/budget]

### Trigger Events
- [{service_category_name} event: contract expiration, vendor EOL, security incident]
- [{vertical_name} event: regulation change, M&A, leadership change]

## Implementation Checklist
### Content Assets Needed
- [ ] {service_category_name} comparison guide for {vertical_name}
- [ ] {vertical_name} x {service_category_name} case studies featuring {title_name}
- [ ] ROI calculator for {service_category_name} in {vertical_name}
- [ ] {title_name} role-specific {service_category_name} one-pager

### Sales Enablement
- [ ] {vertical_name} x {title_name} x {service_category_name} battle card
- [ ] {service_category_name} discovery question bank
- [ ] Vendor comparison objection handling guide

## Research Integration Notes
### From Layer 0 (Service Category: {service_category_name})
- [Key {service_category_name} buyer journey insights]
- [Vendor positioning insights]
- [Evaluation criteria]

### From Layer 1 (Horizontal)
- [Key insights from buyer journey, competitive analysis, messaging]

### From Layer 2 (Vertical: {vertical_name})
- [Key {vertical_name}-specific insights for {service_category_name}]

### From Layer 3 (Title: {title_name})
- [Key {title_name} insights for {service_category_name} decisions]

METHODOLOGY:
- Synthesize insights from all four layers (L0 + L1 + L2 + L3)
- Prioritize {service_category_name}-specific insights
- Create cohesive narrative specific to this V × T × SC combination
- Make concrete and immediately actionable
- Ground all recommendations in research
- Be specific, not generic
- Use actual {service_category_name} vendor names and terminology

Begin playbook generation now.
"""


def build_playbook_prompt_3d(
    vertical_key: str,
    title_key: str,
    service_category: ServiceCategoryConfig,
    service_category_key: str,
    layer_0_context: dict[str, Any],
    layer_1_context: dict[str, Any],
    layer_2_context: dict[str, Any],
    layer_3_context: dict[str, Any],
    company_context: str = ""
) -> str:
    """
    Build 3D integration prompt with full context from all four layers.

    Args:
        vertical_key: Vertical identifier (e.g., 'healthcare')
        title_key: Title cluster identifier (e.g., 'cfo_cluster')
        service_category: ServiceCategoryConfig from baseline.yaml
        service_category_key: Service category key (e.g., 'security')
        layer_0_context: Dictionary of Layer 0 service category agent outputs
        layer_1_context: Dictionary of Layer 1 agent outputs
        layer_2_context: Dictionary of Layer 2 vertical agent outputs
        layer_3_context: Dictionary of Layer 3 title agent outputs
        company_context: Optional pre-formatted company context string

    Returns:
        Formatted prompt string ready for ResearchSession

    Raises:
        ValueError: If vertical_key or title_key not found
    """
    if vertical_key not in VERTICALS:
        raise ValueError(
            f"Unknown vertical: {vertical_key}. "
            f"Valid options: {', '.join(VERTICALS.keys())}"
        )

    if title_key not in TITLE_CLUSTERS:
        raise ValueError(
            f"Unknown title cluster: {title_key}. "
            f"Valid options: {', '.join(TITLE_CLUSTERS.keys())}"
        )

    vertical = VERTICALS[vertical_key]
    title = TITLE_CLUSTERS[title_key]

    # Format key suppliers (strip YAML comments)
    key_suppliers = [s.split('#')[0].strip() for s in service_category.get('key_suppliers', [])]
    key_suppliers_str = ", ".join(key_suppliers) if key_suppliers else "various vendors"

    # Build comprehensive context summary
    context_summary = _format_integration_context_3d(
        vertical_key=vertical_key,
        title_key=title_key,
        service_category_key=service_category_key,
        vertical=vertical,
        title=title,
        service_category=service_category,
        layer_0_context=layer_0_context,
        layer_1_context=layer_1_context,
        layer_2_context=layer_2_context,
        layer_3_context=layer_3_context
    )

    # Format company context section
    if company_context:
        company_section = f"=== COMPANY CONTEXT ===\n\n{company_context}\n\n---"
    else:
        company_section = ""

    return PLAYBOOK_GENERATION_PROMPT_3D.format(
        vertical_name=vertical['name'],
        title_name=title['name'],
        service_category_name=service_category['name'],
        key_suppliers=key_suppliers_str,
        context_section=context_summary,
        company_context_section=company_section
    )


def _format_integration_context_3d(
    vertical_key: str,
    title_key: str,
    service_category_key: str,
    vertical: dict[str, str],
    title: dict[str, Any],
    service_category: ServiceCategoryConfig,
    layer_0_context: dict[str, Any],
    layer_1_context: dict[str, Any],
    layer_2_context: dict[str, Any],
    layer_3_context: dict[str, Any]
) -> str:
    """Format complete context from all four layers for 3D playbook generation."""

    # Layer 0 context (Service Category)
    layer_0_text = f"=== LAYER 0: SERVICE CATEGORY RESEARCH ({service_category['name']}) ===\n\n"

    if service_category_key in layer_0_context:
        summary = extract_summary(layer_0_context[service_category_key], max_length=500)
        layer_0_text += f"**SERVICE CATEGORY INTELLIGENCE:**\n{summary}\n\n"

    # Add service category metadata
    subcategories = service_category.get('subcategories', [])
    if subcategories:
        layer_0_text += f"**Subcategories:** {', '.join(subcategories)}\n"

    key_suppliers = [s.split('#')[0].strip() for s in service_category.get('key_suppliers', [])]
    if key_suppliers:
        layer_0_text += f"**Key Vendors:** {', '.join(key_suppliers)}\n"

    layer_0_text += "\n"

    # Layer 1 context
    layer_1_text = "=== LAYER 1: HORIZONTAL RESEARCH ===\n\n"

    agent_sections = [
        ('buyer_journey', 'BUYER JOURNEY INSIGHTS'),
        ('channels_competitive', 'COMPETITIVE INTELLIGENCE'),
        ('customer_expansion', 'CUSTOMER EXPANSION PATTERNS'),
        ('messaging_positioning', 'MESSAGING RESEARCH'),
        ('gtm_synthesis', 'GTM STRATEGY')
    ]

    for agent_key, section_title in agent_sections:
        if agent_key in layer_1_context:
            summary = extract_summary(layer_1_context[agent_key], max_length=250)
            layer_1_text += f"**{section_title}:**\n{summary}\n\n"

    # Layer 2 context
    layer_2_text = f"=== LAYER 2: VERTICAL RESEARCH ({vertical['name']}) ===\n\n"

    if vertical_key in layer_2_context:
        summary = extract_summary(layer_2_context[vertical_key], max_length=350)
        layer_2_text += f"**VERTICAL SUMMARY:**\n{summary}\n\n"

    layer_2_text += f"**Key Regulations:** {vertical['key_regulations']}\n"
    layer_2_text += f"**Key Challenges:** {vertical['key_challenges']}\n\n"

    # Layer 3 context
    layer_3_text = f"=== LAYER 3: TITLE RESEARCH ({title['name']}) ===\n\n"

    if title_key in layer_3_context:
        summary = extract_summary(layer_3_context[title_key], max_length=350)
        layer_3_text += f"**TITLE SUMMARY:**\n{summary}\n\n"

    layer_3_text += f"**Decision Authority:** {title['decision_authority']}\n"
    layer_3_text += f"**Key Focus:** {title['key_focus']}\n\n"

    # Integration mission
    mission_text = f"""=== YOUR INTEGRATION MISSION ===

Combine these FOUR layers into ONE cohesive playbook for:
TARGET: {vertical['name']} {title['name']} evaluating {service_category['name']}

CRITICAL: This is a 3D playbook. The service category dimension is PRIMARY.
- Use {service_category['name']}-specific buyer triggers
- Reference {service_category['name']} vendors in competitive positioning
- Apply {service_category['name']} evaluation criteria

Make it specific, actionable, and grounded in the research above.
---
"""

    return layer_0_text + layer_1_text + layer_2_text + layer_3_text + mission_text
