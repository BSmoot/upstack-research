# research_orchestrator/prompts/types.py
"""
Type definitions for the prompt system.

Provides type safety for vertical configurations, title cluster configurations,
service category configurations, and context summaries used throughout the
research orchestration system.
"""

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
    titles: list[str]
    decision_authority: str
    key_focus: str


class ServiceCategoryConfig(TypedDict):
    """Configuration for a service category from baseline.yaml."""
    name: str
    subcategories: list[str]
    key_suppliers: list[str]
    market_notes: list[str] | None


class ContextSummary(TypedDict):
    """Summary of agent output for cross-layer context."""
    agent_name: str
    summary: str
    key_findings: str
    output_path: str


class AgentOutput(TypedDict, total=False):
    """Complete agent output structure."""
    status: str
    completed_at: str | None
    started_at: str | None
    output_path: str | None
    searches_performed: int | None
    total_turns: int | None
    execution_time_seconds: float | None
    completion_status: str | None
    estimated_cost_usd: float | None
    content: str | None
    error: str | None


# Type alias for the services dictionary from baseline.yaml
ServiceCategoriesDict = dict[str, ServiceCategoryConfig]
