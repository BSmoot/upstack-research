# research_orchestrator/prompts/__init__.py
"""Research agent prompt templates."""

from .horizontal import (
    BUYER_JOURNEY_PROMPT,
    CHANNELS_COMPETITIVE_PROMPT,
    CUSTOMER_EXPANSION_PROMPT,
    MESSAGING_POSITIONING_PROMPT,
    GTM_SYNTHESIS_PROMPT,
    get_context_section
)

from .vertical import (
    VERTICALS,
    build_vertical_prompt
)

from .title import (
    TITLE_CLUSTERS,
    build_title_prompt
)

from .context_helpers import (
    get_layer_1_context,
    get_layer_2_context,
    get_layer_3_context,
    extract_summary,
    format_layer_1_context_for_vertical,
    format_layer_2_context_for_title
)

from .playbook import (
    build_playbook_prompt
)

__all__ = [
    'BUYER_JOURNEY_PROMPT',
    'CHANNELS_COMPETITIVE_PROMPT',
    'CUSTOMER_EXPANSION_PROMPT',
    'MESSAGING_POSITIONING_PROMPT',
    'GTM_SYNTHESIS_PROMPT',
    'get_context_section',
    'VERTICALS',
    'build_vertical_prompt',
    'TITLE_CLUSTERS',
    'build_title_prompt',
    'get_layer_1_context',
    'get_layer_2_context',
    'get_layer_3_context',
    'extract_summary',
    'format_layer_1_context_for_vertical',
    'format_layer_2_context_for_title',
    'build_playbook_prompt'
]
