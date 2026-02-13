# research_orchestrator/prompts/title.py
"""
Layer 3: Title Cluster Research Agent Prompts

Prompt templates for title-specific buyer persona research agents.
These create role-specific messaging for decision-maker personas.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List
from .types import TitleClusterConfig
from .context_helpers import (
    format_layer_1_context_for_vertical,
    format_layer_2_context_for_title
)

logger = logging.getLogger('research_orchestrator')


# Hardcoded title cluster configurations (fallback)
_HARDCODED_TITLE_CLUSTERS: Dict[str, TitleClusterConfig] = {
    'cfo_cluster': {
        'name': 'C-Suite (CFO, CEO, COO)',
        'titles': ['CFO', 'CEO', 'COO', 'President', 'General Manager'],
        'decision_authority': 'Final approval for strategic/large investments',
        'key_focus': 'Business outcomes, financial performance, strategic risk'
    },
    'cio_cto_cluster': {
        'name': 'Technology Leadership (CIO, CTO, CISO)',
        'titles': ['CIO', 'CTO', 'CISO', 'VP IT', 'VP Engineering'],
        'decision_authority': 'Primary authority for most infrastructure decisions',
        'key_focus': 'Technology debt, innovation vs stability, talent shortage'
    },
    'vp_it_operations': {
        'name': 'IT Operations (VP IT, Director IT, Manager)',
        'titles': ['VP IT Operations', 'Director IT', 'IT Manager', 'Network Manager'],
        'decision_authority': 'Tactical decisions, influence strategic',
        'key_focus': 'Vendor management burden, resource constraints, firefighting'
    },
    'procurement': {
        'name': 'Procurement & Sourcing',
        'titles': ['VP Procurement', 'Director Sourcing', 'Strategic Sourcing Manager'],
        'decision_authority': 'Vendor selection process, contract negotiation',
        'key_focus': 'Cost optimization, supplier management, contract compliance'
    },
    'business_unit': {
        'name': 'Business Unit Leaders',
        'titles': ['VP Sales', 'VP Customer Success', 'VP Operations', 'Regional GM'],
        'decision_authority': 'Department-level technology decisions',
        'key_focus': 'Business outcomes, speed, minimal IT dependency'
    },
    'security_leadership': {
        'name': 'Security Leadership (CISO, VP Security)',
        'titles': ['CISO', 'VP Security', 'Director Information Security', 'Security Architect', 'Head of Cybersecurity'],
        'decision_authority': 'Security tool selection, risk decisions, compliance sign-off',
        'key_focus': 'Threat landscape, compliance requirements, incident response, vendor security assessment'
    }
}


def _load_title_clusters() -> Dict[str, TitleClusterConfig]:
    """Load title clusters from YAML with fallback to hardcoded values."""
    yaml_path = Path(__file__).parent.parent.parent.parent / "build" / "config" / "title_clusters.yaml"

    if yaml_path.exists():
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)
                logger.info(f"Loaded title clusters from {yaml_path}")
                return loaded_data
        except Exception as e:
            logger.warning(f"Failed to load title_clusters.yaml: {e}. Using hardcoded defaults.")
    else:
        logger.warning(f"title_clusters.yaml not found at {yaml_path}. Using hardcoded defaults.")

    return _HARDCODED_TITLE_CLUSTERS


TITLE_CLUSTERS: Dict[str, TitleClusterConfig] = _load_title_clusters()


TITLE_AGENT_PROMPT_TEMPLATE = """
You are the {title_name} Intelligence Agent.

MISSION: Research the day-to-day reality, pain points, and decision-making context of {title_name}. Create precision messaging that resonates with their specific pressures.

PRIOR RESEARCH CONTEXT:

## Layer 1: Horizontal Research Summary

{layer_1_context}

## Layer 2: Vertical Research Summary

{layer_2_context}

{company_context_section}

TITLE CLUSTER CONTEXT:
- Roles: {titles}
- Decision Authority: {decision_authority}
- Key Focus Areas: {key_focus}

YOUR RESEARCH QUESTIONS:

1. ROLE DEFINITION & RESPONSIBILITIES
- What are day-to-day responsibilities of {title_name}?
- What are typical KPIs and success metrics?
- What is typical career path to/from this role?
- How has this role evolved in recent years?

2. DECISION-MAKING AUTHORITY
- What infrastructure decisions does {title_name} have authority to make?
- Where do they have influence but not final authority?
- What decisions are outside their scope?
- Who do they need to convince/collaborate with?

3. PAIN POINTS & PRESSURES
- What are top 5 challenges facing {title_name} today?
- What external pressures affect them? (market, competition, regulation)
- What internal pressures affect them? (budget, resources, politics)
- What keeps them up at night?
- How do pain points differ across industries?

4. COMMUNICATION & CONTENT PREFERENCES
- How does {title_name} prefer to consume information?
- What professional communities/platforms do they use?
- Where do they spend time professionally?
- When are they most receptive to outreach?
- What content formats work best?

5. BUYING BEHAVIOR & VENDOR SELECTION
- How does {title_name} typically engage with vendors?
- What criteria do they use to evaluate vendors?
- How do they validate vendor claims?
- What triggers them to look for outside help?
- What's their procurement process involvement?

6. OBJECTIONS & CONCERNS
- What objections does {title_name} typically raise about advisors?
- What concerns do they have about changing vendors?
- What past experiences shape their skepticism?
- What would cause them to walk away?

7. VALUE PROPOSITION & PROOF POINTS
- What business outcomes matter most to {title_name}?
- What value propositions resonate?
- What proof points validate value to {title_name}?
- What ROI metrics do they care about?
- How do priorities differ from other decision-makers?

8. MESSAGING PRECISION
- What language does {title_name} use to describe their work?
- What terminology resonates vs. turns them off?
- What tone works best?
- How technical should messaging be?
- What makes them pay attention?

DELIVERABLES (Markdown format):
- Executive Summary (5-7 key insights about {title_name})
- Title Role Profile & Evolution
- Decision-Making Authority Map
- Pain Point Analysis (ranked top 5)
- Communication & Content Preferences
- Buying Behavior Analysis
- Objection Handling Framework
- Value Proposition & Proof Points
- Messaging Guidelines for {title_name}
- Outbound Sequence Design Recommendations
- Cross-Vertical Insights (how this role varies by industry)
- Sources Consulted (full bibliography with dates)
- Research Gaps & Confidence Assessment

METHODOLOGY:
- Use 30-40 web_search operations
- Prioritize: LinkedIn discussions, professional surveys, role descriptions, interview transcripts
- Focus on LIVED EXPERIENCE not theoretical role definitions
- Look for day-in-the-life content
- Find what actual people in these roles say about their challenges
- Compare across industries where data available
- Every major claim needs source citations
- Flag low-confidence areas explicitly

Begin research now.
"""


def build_title_prompt(
    title_key: str,
    layer_1_context: Dict[str, Any],
    layer_2_context: Dict[str, Any],
    company_context: str = ""
) -> str:
    """
    Build complete title-specific prompt with Layer 1 & 2 context.

    Args:
        title_key: Title cluster identifier (e.g., 'cfo_cluster', 'cio_cto_cluster')
        layer_1_context: Dictionary of Layer 1 agent outputs
        layer_2_context: Dictionary of Layer 2 vertical agent outputs
        company_context: Optional company context string

    Returns:
        Formatted prompt string ready for ResearchSession

    Raises:
        ValueError: If title_key not found in TITLE_CLUSTERS
    """
    if title_key not in TITLE_CLUSTERS:
        raise ValueError(
            f"Unknown title cluster: {title_key}. "
            f"Valid options: {', '.join(TITLE_CLUSTERS.keys())}"
        )

    title = TITLE_CLUSTERS[title_key]

    # Format Layer 1 context
    layer_1_text = format_layer_1_context_for_vertical(layer_1_context)

    # Format Layer 2 context
    layer_2_text = format_layer_2_context_for_title(layer_2_context)

    # Wrap company context if provided
    if company_context:
        company_section = f"=== COMPANY CONTEXT ===\n\n{company_context}\n\n---"
    else:
        company_section = ""

    # Build complete prompt
    return TITLE_AGENT_PROMPT_TEMPLATE.format(
        title_name=title['name'],
        titles=', '.join(title['titles']),
        decision_authority=title['decision_authority'],
        key_focus=title['key_focus'],
        layer_1_context=layer_1_text,
        layer_2_context=layer_2_text,
        company_context_section=company_section
    )
