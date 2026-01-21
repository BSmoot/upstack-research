# tests/test_budget_errors.py
"""
Unit tests for budget enforcement and BudgetExceededError handling.

Tests budget limit checks for searches and costs across different scenarios.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from research_orchestrator.orchestrator import ResearchOrchestrator, BudgetExceededError


class TestBudgetErrors:
    """Test budget limit enforcement and error handling."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with budget tracking."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_config, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):

            mock_config.return_value = {
                'execution': {'id': 'test_budget'},
                'verticals': ['healthcare'],
                'title_clusters': ['cfo_cluster'],
                'execution_settings': {
                    'logging': {'directory': 'logs', 'level': 'INFO', 'console_output': True},
                    'api': {'model': 'claude-haiku-4-20250514', 'max_tokens': 8000},
                    'checkpointing': {'directory': 'checkpoints'},
                    'outputs': {'directory': 'outputs'},
                    'budget': {'max_searches': 20, 'max_cost_usd': 10.0},
                    'review_gates': {'after_layer_1': False, 'after_layer_2': False}
                },
                'model_strategy': {
                    'default': 'claude-haiku-4-20250514',
                    'layers': {'layer_1': 'claude-haiku-4-20250514'},
                    'model_configs': {
                        'claude-haiku-4-20250514': {'max_tokens': 8000}
                    },
                    'budgets': {
                        'claude-haiku-4-20250514': {'max_searches_per_agent': 15}
                    }
                }
            }

            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()

            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            orchestrator.logger = Mock()

            yield orchestrator

    @pytest.mark.asyncio
    async def test_budget_exceeded_on_search_limit(self, mock_orchestrator):
        """Test that BudgetExceededError is raised when search limit is exceeded."""
        mock_orchestrator.state.is_agent_complete = Mock(return_value=False)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator.state.mark_failed = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

        # Set budget to be at limit
        mock_orchestrator.budget['current_searches'] = 19
        mock_orchestrator.budget['max_total_searches'] = 20

        with patch('research_orchestrator.orchestrator.get_model_for_agent') as mock_get_model, \
             patch('research_orchestrator.orchestrator.get_model_config') as mock_get_config, \
             patch('research_orchestrator.orchestrator.get_search_budget_for_model') as mock_get_budget, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session, \
             patch('research_orchestrator.orchestrator.get_context_section') as mock_get_context:

            mock_get_model.return_value = 'claude-haiku-4-20250514'
            mock_get_config.return_value = {'max_tokens': 8000}
            mock_get_budget.return_value = 15
            mock_get_context.return_value = ""

            # Mock session to return result that exceeds budget
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 5,  # This will push total to 24 > 20
                'total_turns': 3,
                'execution_time_seconds': 30.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            # Execute agent should raise BudgetExceededError
            with pytest.raises(BudgetExceededError, match="Search"):
                await mock_orchestrator._execute_agent('buyer_journey', layer='layer_1')

    @pytest.mark.asyncio
    async def test_budget_exceeded_on_cost_limit(self, mock_orchestrator):
        """Test that BudgetExceededError is raised when cost limit is exceeded."""
        mock_orchestrator.state.is_agent_complete = Mock(return_value=False)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator.state.mark_failed = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

        # Set budget to be at cost limit
        mock_orchestrator.budget['current_cost_usd'] = 9.0
        mock_orchestrator.budget['max_total_cost_usd'] = 10.0

        with patch('research_orchestrator.orchestrator.get_model_for_agent') as mock_get_model, \
             patch('research_orchestrator.orchestrator.get_model_config') as mock_get_config, \
             patch('research_orchestrator.orchestrator.get_search_budget_for_model') as mock_get_budget, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session, \
             patch('research_orchestrator.orchestrator.get_context_section') as mock_get_context:

            mock_get_model.return_value = 'claude-haiku-4-20250514'
            mock_get_config.return_value = {'max_tokens': 8000}
            mock_get_budget.return_value = 15
            mock_get_context.return_value = ""

            # Mock session to return result that exceeds cost budget
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 5,
                'total_turns': 3,
                'execution_time_seconds': 30.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 2.5  # This will push total to $11.50 > $10.00
            })
            mock_session.return_value = mock_session_instance

            # Execute agent should raise BudgetExceededError
            with pytest.raises(BudgetExceededError, match="Cost"):
                await mock_orchestrator._execute_agent('buyer_journey', layer='layer_1')

    @pytest.mark.asyncio
    async def test_budget_tracking_updates_correctly(self, mock_orchestrator):
        """Test that budget tracking updates correctly after agent execution."""
        mock_orchestrator.state.is_agent_complete = Mock(return_value=False)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")

        initial_searches = mock_orchestrator.budget['current_searches']
        initial_cost = mock_orchestrator.budget['current_cost_usd']

        with patch('research_orchestrator.orchestrator.get_model_for_agent') as mock_get_model, \
             patch('research_orchestrator.orchestrator.get_model_config') as mock_get_config, \
             patch('research_orchestrator.orchestrator.get_search_budget_for_model') as mock_get_budget, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session, \
             patch('research_orchestrator.orchestrator.get_context_section') as mock_get_context:

            mock_get_model.return_value = 'claude-haiku-4-20250514'
            mock_get_config.return_value = {'max_tokens': 8000}
            mock_get_budget.return_value = 15
            mock_get_context.return_value = ""

            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 5,
                'total_turns': 3,
                'execution_time_seconds': 30.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.5
            })
            mock_session.return_value = mock_session_instance

            await mock_orchestrator._execute_agent('buyer_journey', layer='layer_1')

            # Budget should be updated
            assert mock_orchestrator.budget['current_searches'] == initial_searches + 5
            assert mock_orchestrator.budget['current_cost_usd'] == initial_cost + 1.5

    @pytest.mark.asyncio
    async def test_budget_allows_execution_within_limits(self, mock_orchestrator):
        """Test that agent executes successfully when within budget limits."""
        mock_orchestrator.state.is_agent_complete = Mock(return_value=False)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")

        # Set budget well below limits
        mock_orchestrator.budget['current_searches'] = 5
        mock_orchestrator.budget['max_total_searches'] = 20
        mock_orchestrator.budget['current_cost_usd'] = 2.0
        mock_orchestrator.budget['max_total_cost_usd'] = 10.0

        with patch('research_orchestrator.orchestrator.get_model_for_agent') as mock_get_model, \
             patch('research_orchestrator.orchestrator.get_model_config') as mock_get_config, \
             patch('research_orchestrator.orchestrator.get_search_budget_for_model') as mock_get_budget, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session, \
             patch('research_orchestrator.orchestrator.get_context_section') as mock_get_context:

            mock_get_model.return_value = 'claude-haiku-4-20250514'
            mock_get_config.return_value = {'max_tokens': 8000}
            mock_get_budget.return_value = 15
            mock_get_context.return_value = ""

            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 3,
                'total_turns': 3,
                'execution_time_seconds': 30.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            # Should not raise exception
            await mock_orchestrator._execute_agent('buyer_journey', layer='layer_1')

            # Should mark complete
            mock_orchestrator.state.mark_complete.assert_called_once()

    def test_budget_initialization_from_config(self, mock_orchestrator):
        """Test that budget is initialized correctly from config."""
        assert mock_orchestrator.budget['max_total_searches'] == 20
        assert mock_orchestrator.budget['max_total_cost_usd'] == 10.0
        assert mock_orchestrator.budget['current_searches'] == 0
        assert mock_orchestrator.budget['current_cost_usd'] == 0.0
