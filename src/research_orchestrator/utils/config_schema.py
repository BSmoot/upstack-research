"""Pydantic schemas for configuration validation."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ApiConfig(BaseModel):
    """API configuration for Anthropic Claude."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = Field(default=16000, ge=1000, le=200000)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)


class BudgetConfig(BaseModel):
    """Budget limits for research execution."""
    max_searches: int = Field(default=500, ge=1)
    max_cost_usd: float = Field(default=200.0, ge=0.0)


class CheckpointingConfig(BaseModel):
    """Checkpointing configuration."""
    enabled: bool = True
    frequency: Literal['per_agent', 'per_layer'] = 'per_agent'
    directory: str = 'checkpoints'


class ReviewGatesConfig(BaseModel):
    """Review gates configuration."""
    after_layer_0: bool = False
    after_layer_1: bool = True
    after_layer_2: bool = True
    after_layer_3: bool = False
    after_playbooks: bool = False
    after_validation: bool = False


class OutputsConfig(BaseModel):
    """Output configuration."""
    directory: str = 'outputs'
    format: Literal['markdown', 'json'] = 'markdown'
    include_conversation_history: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'
    directory: str = 'logs'
    console_output: bool = True


class BrandAlignmentOutputConfig(BaseModel):
    """Brand alignment output settings."""
    suffix: str = ".aligned"
    replace_original: bool = False


class BrandAlignmentConfig(BaseModel):
    """Brand alignment configuration."""
    enabled: bool = False
    context_files: Dict[str, str] = Field(default_factory=dict)
    align_targets: List[str] = Field(default_factory=lambda: ["playbooks"])
    model: str = "claude-haiku-4-5-20251001"
    output: BrandAlignmentOutputConfig = Field(default_factory=BrandAlignmentOutputConfig)


class ExecutionSettings(BaseModel):
    """Execution settings for research orchestration."""
    max_concurrent_agents: int = Field(default=5, ge=1, le=50)
    api: ApiConfig = Field(default_factory=ApiConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    research_depth: Literal['minimal', 'standard', 'comprehensive'] = 'comprehensive'
    checkpointing: CheckpointingConfig = Field(default_factory=CheckpointingConfig)
    review_gates: ReviewGatesConfig = Field(default_factory=ReviewGatesConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ExecutionConfig(BaseModel):
    """Execution metadata."""
    id: str = Field(min_length=1)
    description: Optional[str] = None


class ResearchConfig(BaseModel):
    """Top-level research configuration schema."""
    execution: ExecutionConfig
    verticals: List[str] = Field(default_factory=list)
    title_clusters: List[str] = Field(default_factory=list)
    service_categories: List[str] = Field(default_factory=list)
    priority_service_categories: List[str] = Field(default_factory=list)
    execution_settings: ExecutionSettings = Field(default_factory=ExecutionSettings)
    model_strategy: Optional[Dict[str, Any]] = None
    priority_combinations: Optional[List[Dict[str, Any]]] = None
    company_context: Optional[Dict[str, Any]] = None
    brand_alignment: Optional[BrandAlignmentConfig] = None

    model_config = {"extra": "allow"}

    @field_validator('verticals', 'title_clusters', 'service_categories', 'priority_service_categories')
    @classmethod
    def validate_non_empty_strings(cls, v: List[str]) -> List[str]:
        """Ensure list items (if any) are non-empty strings."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"List items must be non-empty strings, got: {item}")
        return v


def validate_research_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize research configuration."""
    validated_model = ResearchConfig(**config_dict)
    return validated_model.model_dump()
