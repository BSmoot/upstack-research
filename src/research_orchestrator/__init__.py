# research_orchestrator/__init__.py
"""
Research Orchestrator - AI-powered market research system.

Executes three-layer research framework through intelligent parallel execution.
"""

__version__ = "1.0.0"

from .research_session import ResearchSession
from .orchestrator import ResearchOrchestrator
from .state.tracker import StateTracker

__all__ = ['ResearchSession', 'ResearchOrchestrator', 'StateTracker']
