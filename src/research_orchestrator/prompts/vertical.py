# research_orchestrator/prompts/vertical.py
"""
Layer 2: Vertical Research Agent Prompts

Prompt templates for vertical-specific industry research agents.
These adapt horizontal findings to specific industry verticals.
"""

from typing import Dict, Any
from .types import VerticalConfig
from .context_helpers import format_layer_1_context_for_vertical


# Vertical industry configurations
VERTICALS: Dict[str, VerticalConfig] = {
    'healthcare': {
        'name': 'Healthcare',
        'description': 'Hospitals, health systems, payers, pharma, medtech',
        'key_regulations': 'HIPAA, HITECH, state privacy laws',
        'key_challenges': 'Digital transformation + compliance + cost pressure'
    },
    'financial_services': {
        'name': 'Financial Services',
        'description': 'Banks, credit unions, insurance, wealth management, fintech',
        'key_regulations': 'SOX, PCI-DSS, GLBA, FFIEC',
        'key_challenges': 'Innovation vs risk management balance'
    },
    'manufacturing': {
        'name': 'Manufacturing',
        'description': 'Discrete manufacturing, process manufacturing, distribution',
        'key_regulations': 'Varies by sub-sector (FDA, EPA, etc.)',
        'key_challenges': 'Industry 4.0 transformation + supply chain resilience'
    },
    'retail': {
        'name': 'Retail',
        'description': 'Traditional retail, e-commerce, omnichannel, grocery',
        'key_regulations': 'PCI-DSS, state privacy laws',
        'key_challenges': 'E-commerce competition + margin pressure'
    },
    'technology': {
        'name': 'Technology/Software',
        'description': 'SaaS, software vendors, technology services',
        'key_regulations': 'SOC 2, ISO 27001, GDPR, CCPA',
        'key_challenges': 'Rapid scaling + efficiency at scale'
    }
}


VERTICAL_AGENT_PROMPT_TEMPLATE = """
You are the {vertical_name} Vertical Intelligence Agent.

MISSION: Adapt horizontal research findings to the {vertical_name} industry. Identify what's different, more acute, or unique about infrastructure advisory in {vertical_name}.

PRIOR RESEARCH CONTEXT:

{context_section}

VERTICAL CONTEXT:
- Industry: {description}
- Key Regulations: {key_regulations}
- Key Challenges: {key_challenges}

YOUR RESEARCH QUESTIONS:

1. VERTICAL INFRASTRUCTURE LANDSCAPE
- What infrastructure services are most critical in {vertical_name}?
- What are typical technology budgets and spending patterns?
- What technology decisions are strategic vs tactical in this vertical?
- How does infrastructure spending compare to other industries?

2. VERTICAL REGULATORY & COMPLIANCE
- What regulations affect infrastructure procurement in {vertical_name}?
- How do compliance requirements affect vendor selection?
- What are consequences of non-compliance?
- What compliance-related infrastructure needs exist?

3. VERTICAL BUYING PATTERNS
- Who typically drives infrastructure decisions in {vertical_name}?
- What is the typical procurement process?
- What triggers infrastructure procurement in this vertical?
- How long are typical sales cycles?

4. VERTICAL PAIN POINTS
- What are top 5 infrastructure challenges in {vertical_name}?
- How do these differ from general B2B challenges?
- What business outcomes are most valued?
- What keeps {vertical_name} IT leaders up at night?

5. VERTICAL COMPETITIVE LANDSCAPE
- Who are dominant infrastructure suppliers in {vertical_name}?
- Are there vertical-specific advisory firms?
- What are common vendor selection criteria?
- How do {vertical_name} companies typically engage advisors?

6. VERTICAL VALUE PROPOSITION
- How should an advisory firm's value proposition adapt for {vertical_name}?
- What vertical-specific proof points are needed?
- What objections are unique to {vertical_name}?
- What ROI metrics matter most in this vertical?

7. VERTICAL PARTNERSHIPS & ECOSYSTEM
- What technology vendors dominate in {vertical_name}?
- What industry associations and communities exist?
- What referral networks are effective?

8. VERTICAL GTM RECOMMENDATIONS
- What channels work best for reaching {vertical_name} prospects?
- What content types resonate?
- What events and communities matter?
- How should messaging adapt for this vertical?

DELIVERABLES (Markdown format):
- Executive Summary (5-7 key findings specific to {vertical_name})
- Vertical Infrastructure Landscape
- Vertical Regulatory & Compliance Analysis
- Vertical Buying Process Analysis
- Vertical Pain Point Analysis (ranked top 5)
- Vertical Competitive Intelligence
- Vertical Value Proposition Framework
- Vertical Partnership Ecosystem Map
- Vertical GTM Recommendations
- Sources Consulted (full bibliography with dates)
- Research Gaps & Confidence Assessment

METHODOLOGY:
- Use 40-60 web_search operations
- Prioritize: Industry analyst reports, trade publications, regulatory docs, {vertical_name}-specific case studies
- Look for {vertical_name}-specific data and statistics
- Compare to general B2B patterns from Layer 1 research
- Every major claim needs source citations
- Flag low-confidence areas explicitly

Begin research now.
"""


def build_vertical_prompt(vertical_key: str, layer_1_context: Dict[str, Any]) -> str:
    """
    Build complete vertical-specific prompt with Layer 1 context.
    
    Args:
        vertical_key: Vertical identifier (e.g., 'healthcare', 'financial_services')
        layer_1_context: Dictionary of Layer 1 agent outputs
        
    Returns:
        Formatted prompt string ready for ResearchSession
        
    Raises:
        ValueError: If vertical_key not found in VERTICALS
    """
    if vertical_key not in VERTICALS:
        raise ValueError(
            f"Unknown vertical: {vertical_key}. "
            f"Valid options: {', '.join(VERTICALS.keys())}"
        )
    
    vertical = VERTICALS[vertical_key]
    
    # Format Layer 1 context for inclusion
    context_text = format_layer_1_context_for_vertical(layer_1_context)
    
    # Build complete prompt
    return VERTICAL_AGENT_PROMPT_TEMPLATE.format(
        vertical_name=vertical['name'],
        description=vertical['description'],
        key_regulations=vertical['key_regulations'],
        key_challenges=vertical['key_challenges'],
        context_section=context_text
    )
