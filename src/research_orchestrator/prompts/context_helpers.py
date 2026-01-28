# research_orchestrator/prompts/context_helpers.py
"""
Helper functions for extracting and formatting context between research layers.

These utilities enable downstream agents to access and use outputs from
prior layers, maintaining continuity and building upon previous research.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger('research_orchestrator')


def get_layer_1_context(state_tracker) -> Dict[str, Any]:
    """
    Extract all Layer 1 outputs for downstream agents.
    
    Args:
        state_tracker: StateTracker instance with checkpoint data
        
    Returns:
        Dictionary mapping agent names to their outputs:
        {
            'buyer_journey': {...},
            'channels_competitive': {...},
            'customer_expansion': {...},
            'messaging_positioning': {...},
            'gtm_synthesis': {...}
        }
    """
    layer_1_agents = [
        'buyer_journey',
        'channels_competitive',
        'customer_expansion',
        'messaging_positioning',
        'gtm_synthesis'
    ]
    
    context = {}
    for agent_name in layer_1_agents:
        output = state_tracker.get_agent_output(agent_name, 'layer_1')
        if output:
            context[agent_name] = output
    
    return context


def get_layer_2_context(state_tracker, verticals: List[str]) -> Dict[str, Any]:
    """
    Extract Layer 2 outputs for Layer 3 agents.
    
    Args:
        state_tracker: StateTracker instance
        verticals: List of vertical names to retrieve
        
    Returns:
        Dictionary mapping vertical names to their outputs:
        {
            'healthcare': {...},
            'financial_services': {...},
            ...
        }
    """
    context = {}
    for vertical in verticals:
        agent_name = f'vertical_{vertical}'
        output = state_tracker.get_agent_output(agent_name, 'layer_2')
        if output:
            context[vertical] = output
    
    return context


def get_layer_3_context(state_tracker, title_clusters: List[str]) -> Dict[str, Any]:
    """
    Extract Layer 3 outputs for integration/playbook agents.
    
    Args:
        state_tracker: StateTracker instance
        title_clusters: List of title cluster names to retrieve
        
    Returns:
        Dictionary mapping title cluster names to their outputs:
        {
            'cfo_cluster': {...},
            'cio_cto_cluster': {...},
            ...
        }
    """
    context = {}
    for title in title_clusters:
        agent_name = f'title_{title}'
        output = state_tracker.get_agent_output(agent_name, 'layer_3')
        if output:
            context[title] = output
    
    return context


def _validate_output_path(path: Path, base_dir: Optional[Path] = None) -> bool:
    """
    Validate that path is within allowed directory (prevents path traversal).

    Args:
        path: The path to validate
        base_dir: The base directory to check against (defaults to ./outputs)

    Returns:
        True if path is within an outputs directory, False otherwise
    """
    try:
        resolved = path.resolve()

        # If explicit base_dir provided, check against it
        if base_dir is not None:
            base_resolved = base_dir.resolve()
            return resolved.is_relative_to(base_resolved)

        # Default: check against cwd/outputs
        cwd_outputs = (Path.cwd() / "outputs").resolve()
        if resolved.is_relative_to(cwd_outputs):
            return True

        # Also allow paths within any "outputs" ancestor directory
        # This supports temp directories used in testing
        for parent in resolved.parents:
            if parent.name == "outputs":
                return resolved.is_relative_to(parent)

        return False
    except (ValueError, RuntimeError):
        return False


def extract_summary(agent_output: Dict[str, Any], max_length: int = 500) -> str:
    """
    Extract concise summary from agent output for context injection.
    
    Attempts to find the Executive Summary section from markdown output.
    Falls back to truncated content if section not found.
    
    Args:
        agent_output: Complete agent output dictionary
        max_length: Maximum character length for summary (default 500)
        
    Returns:
        Summary string suitable for inclusion in prompts
    """
    if not agent_output:
        return "Summary not available"
    
    # Try to get content from output
    content = None
    
    # Check if there's an output_path we can read
    if 'output_path' in agent_output:
        try:
            output_path = Path(agent_output['output_path'])
            if not _validate_output_path(output_path):
                logger.warning(f"Path traversal attempt blocked: {output_path}")
                return "Summary not available"
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
        except Exception:
            pass
    
    # Fallback to content field if available
    if not content and 'content' in agent_output:
        content = agent_output['content']
    
    if not content:
        return "Summary not available"

    # Try to extract Executive Summary section (case-insensitive)
    import re
    summary_match = re.search(r'^##\s+EXECUTIVE\s+SUMMARY\s*$', content, re.IGNORECASE | re.MULTILINE)

    if summary_match:
        try:
            # Find content after the Executive Summary header
            summary_start = summary_match.end()
            content_after_summary = content[summary_start:]

            # Find next level-2 header (## but not ###)
            # Use regex to match \n## followed by space (not another #)
            next_section = re.search(r'\n##\s+[^#]', content_after_summary)
            if next_section:
                summary_section = content_after_summary[:next_section.start()]
            else:
                summary_section = content_after_summary

            summary_text = summary_section.strip()

            # Return truncated if needed
            if len(summary_text) > max_length:
                return summary_text[:max_length] + "..."
            return summary_text
        except Exception:
            # If parsing fails, fall through to truncation
            pass

    # Fallback: find first markdown header and start from there (skip reasoning preamble)
    first_header = re.search(r'^#\s+.+$', content, re.MULTILINE)
    if first_header:
        content_from_header = content[first_header.start():]
        truncated = content_from_header[:max_length].strip()
        if len(content_from_header) > max_length:
            truncated += "..."
        return truncated

    # Final fallback: return first max_length characters
    truncated = content[:max_length].strip()
    if len(content) > max_length:
        truncated += "..."

    return truncated


def format_layer_1_context_for_vertical(layer_1_context: Dict[str, Any]) -> str:
    """
    Format Layer 1 outputs for inclusion in vertical agent prompts.
    
    Args:
        layer_1_context: Dictionary of Layer 1 agent outputs
        
    Returns:
        Formatted markdown string with key findings from each agent
    """
    if not layer_1_context:
        return "No Layer 1 research available."
    
    sections = []
    
    # Order matters for readability
    agent_order = [
        ('buyer_journey', 'BUYER JOURNEY RESEARCH'),
        ('channels_competitive', 'COMPETITIVE & CHANNEL ANALYSIS'),
        ('customer_expansion', 'CUSTOMER EXPANSION RESEARCH'),
        ('messaging_positioning', 'MESSAGING & POSITIONING RESEARCH'),
        ('gtm_synthesis', 'GTM STRATEGY SYNTHESIS')
    ]
    
    for agent_key, section_title in agent_order:
        if agent_key in layer_1_context:
            output = layer_1_context[agent_key]
            summary = extract_summary(output, max_length=400)
            
            sections.append(f"""
### {section_title}

{summary}

---
""")
    
    if not sections:
        return "No Layer 1 research available."
    
    return "\n".join(sections)


def format_layer_2_context_for_title(layer_2_context: Dict[str, Any]) -> str:
    """
    Format Layer 2 vertical research for inclusion in title agent prompts.
    
    Args:
        layer_2_context: Dictionary of Layer 2 vertical agent outputs
        
    Returns:
        Formatted markdown string with vertical-specific insights
    """
    if not layer_2_context:
        return "No vertical research available yet."
    
    sections = []
    
    for vertical_name, output in layer_2_context.items():
        summary = extract_summary(output, max_length=300)
        
        sections.append(f"""
### {vertical_name.upper().replace('_', ' ')} VERTICAL

{summary}

---
""")
    
    if not sections:
        return "No vertical research available yet."
    
    return "\n".join(sections)
