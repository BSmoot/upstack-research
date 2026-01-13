# research_orchestrator/prompts/playbook.py
"""
Integration: Playbook Generation Prompts

Synthesizes all three research layers into actionable ABM playbooks
for specific vertical × title combinations.
"""

from typing import Dict, Any
from .vertical import VERTICALS
from .title import TITLE_CLUSTERS
from .context_helpers import extract_summary


PLAYBOOK_GENERATION_PROMPT = """
You are the Playbook Integration Agent.

MISSION: Synthesize research from all three layers into an actionable ABM playbook for {vertical_name} {title_name}.

{context_section}

YOUR INTEGRATION TASK:

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
    layer_1_context: Dict[str, Any],
    layer_2_context: Dict[str, Any],
    layer_3_context: Dict[str, Any]
) -> str:
    """
    Build integration prompt with full context from all layers.
    
    Args:
        vertical_key: Vertical identifier (e.g., 'healthcare')
        title_key: Title cluster identifier (e.g., 'cfo_cluster')
        layer_1_context: Dictionary of Layer 1 agent outputs
        layer_2_context: Dictionary of Layer 2 vertical agent outputs
        layer_3_context: Dictionary of Layer 3 title agent outputs
        
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
    
    return PLAYBOOK_GENERATION_PROMPT.format(
        vertical_name=vertical['name'],
        title_name=title['name'],
        context_section=context_summary
    )


def _format_integration_context(
    vertical_key: str,
    title_key: str,
    vertical: Dict[str, str],
    title: Dict[str, Any],
    layer_1_context: Dict[str, Any],
    layer_2_context: Dict[str, Any],
    layer_3_context: Dict[str, Any]
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
