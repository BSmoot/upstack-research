"""
Layer 0: Service Category Research Agent Prompts

Prompt templates for service category intelligence agents.
These discover buyer behavior, evaluation criteria, and market dynamics
for specific infrastructure service categories.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context_injector import ResearchContextInjector

logger = logging.getLogger('research_orchestrator')


SERVICE_CATEGORY_PROMPT_TEMPLATE = """
You are the {category_name} Category Intelligence Agent.

SERVICE CATEGORY CONTEXT (from config):
- Category: {category_name}
- Subcategories: {subcategories}
- Key Suppliers to Research: {key_suppliers}

YOUR RESEARCH MISSION:
DISCOVER (not pre-defined):
- Buyer triggers for {category_name}
- Evaluation criteria buyers use
- Market pressures driving demand
- How suppliers position against each other
- Where buyers research {category_name} solutions

YOUR RESEARCH QUESTIONS:

1. CATEGORY BUYER DISCOVERY
- How do buyers discover they need {category_name} solutions?
- What search terms do buyers use? (buyer-problem-centric, not advisory)
- Where do buyers research? (G2, TrustRadius, LinkedIn, YouTube, vendor webinars)
- What pain points trigger {category_name} evaluations?
- What business events or incidents create urgency?

2. EVALUATION CRITERIA
- What criteria do buyers use to evaluate {category_name} vendors?
- How do they compare the key suppliers: {key_suppliers}?
- What peer reviews and analyst reports influence decisions?
- What feature comparisons matter most?
- What pricing models and contract terms are standard?
- What proof points do buyers require (case studies, references, trials)?

3. SUPPLIER POSITIONING
- How do the key suppliers position against each other?
- What are their primary value propositions?
- What competitive claims do they make?
- What are their strengths and weaknesses according to buyers?
- How do they differentiate in the market?
- What gaps exist in current supplier offerings?

4. MARKET DYNAMICS
- What macro trends drive {category_name} demand?
- What recent incidents or events elevated this category?
- How is AI/automation affecting this category?
- What regulatory or compliance pressures exist?
- What technology shifts are reshaping {category_name}?
- What analyst predictions influence buying timelines?

5. BUYER JOURNEY
- What is the typical buying journey for {category_name}?
- What content do buyers consume at each stage (awareness, consideration, decision)?
- What triggers the final decision?
- Who are the typical stakeholders involved?
- What objections or concerns delay decisions?
- What post-purchase implementation challenges exist?

6. CATEGORY MARKET PRESSURES
- What analyst predictions influence buying timelines?
- What competitive pressures force evaluation?
- What security incidents or breaches drive urgency?
- What compliance deadlines create buying windows?
- What budget cycles affect procurement timing?
- What vendor consolidation or M&A affects the market?

DELIVERABLES (Markdown format):
- Executive Summary (7-10 key findings about {category_name} buyer behavior)
- Buyer Discovery Patterns (how buyers find and research {category_name})
- Evaluation Criteria Framework (ranked by importance to buyers)
- Supplier Competitive Landscape (positioning of {key_suppliers})
- Market Dynamics Analysis (trends, pressures, shifts)
- Buyer Journey Map for {category_name} (stage-by-stage)
- Search Term Vocabulary (buyer-centric terms, not advisory jargon)
- Information Source Analysis (where buyers research)
- Sources Consulted (full bibliography with dates)
- Research Gaps & Confidence Assessment

METHODOLOGY:
- Use 30-50 web_search operations
- Prioritize: G2, TrustRadius, peer reviews, analyst reports (Gartner, Forrester), vendor comparison sites
- Search using buyer-problem terms, not advisory terms
- Look for actual buyer quotes, reviews, and case studies
- Every major claim needs source citations
- Flag low-confidence areas explicitly
- Compare supplier positioning across multiple sources

Begin research now.
"""


def build_service_category_prompt(
    category_key: str,
    context_injector: 'ResearchContextInjector'
) -> str:
    """
    Build complete service category prompt with dynamic context injection.

    Args:
        category_key: Service category identifier (e.g., 'security', 'customer_experience')
        context_injector: ResearchContextInjector instance for loading category data

    Returns:
        Formatted prompt string ready for ResearchSession

    Raises:
        ValueError: If category_key not found in baseline.yaml
    """
    # Load category config from baseline.yaml
    category_config = context_injector.get_service_category(category_key)

    if not category_config:
        available_categories = list(context_injector.load_service_categories().keys())
        raise ValueError(
            f"Unknown service category: {category_key}. "
            f"Valid options: {', '.join(available_categories)}"
        )

    # Format subcategories as comma-separated list
    subcategories_str = ", ".join(category_config['subcategories']) if category_config['subcategories'] else "None specified"

    # Format key suppliers as comma-separated list (strip YAML comments)
    suppliers = [s.split('#')[0].strip() for s in category_config['key_suppliers']]
    key_suppliers_str = ", ".join(suppliers) if suppliers else "None specified"

    # Build complete prompt
    prompt = SERVICE_CATEGORY_PROMPT_TEMPLATE.format(
        category_name=category_config['name'],
        subcategories=subcategories_str,
        key_suppliers=key_suppliers_str
    )

    logger.info(
        'Built service category prompt for %s (%s)',
        category_key,
        category_config['name']
    )

    return prompt
