# research_orchestrator/prompts/types.py
"""
Type definitions for the prompt system.

Provides type safety for vertical configurations, title cluster configurations,
and context summaries used throughout the research orchestration system.
"""

from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict


class VerticalConfig(TypedDict):
    """Configuration for a vertical industry research agent."""
    name: str
    description: str
    key_regulations: str
    key_challenges: str


class TitleClusterConfig(TypedDict):
    """Configuration for a title cluster research agent."""
    name: str
    titles: List[str]
    decision_authority: str
    key_focus: str


class ContextSummary(TypedDict):
    """Summary of agent output for cross-layer context."""
    agent_name: str
    summary: str
    key_findings: str
    output_path: str


class AgentOutput(TypedDict, total=False):
    """Complete agent output structure."""
    status: str
    completed_at: Optional[str]
    started_at: Optional[str]
    output_path: Optional[str]
    searches_performed: Optional[int]
    total_turns: Optional[int]
    execution_time_seconds: Optional[float]
    completion_status: Optional[str]
    estimated_cost_usd: Optional[float]
    content: Optional[str]
    error: Optional[str]
