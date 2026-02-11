# tests/test_layer_1.py
"""
Unit tests for Layer 1 orchestrator execution.

Tests the 3-phase parallel execution pattern:
- Phase 1: buyer_journey, channels_competitive, customer_expansion (parallel)
- Phase 2: messaging_positioning (depends on Phase 1)
- Phase 3: gtm_synthesis (depends on all prior)

Also tests company context injection via format_layer_1_prompt.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from research_orchestrator.orchestrator import ResearchOrchestrator, BudgetExceededError
from research_orchestrator.prompts.horizontal import (
    GTM_SYNTHESIS_PROMPT,
    BUYER_JOURNEY_PROMPT,
    format_layer_1_prompt,
)


class TestLayer1Execution:
    """Test Layer 1 parallel execution with dependency management."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with necessary dependencies."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_config, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):

            # Setup config
            mock_config.return_value = {
                'execution': {'id': 'test_layer_1'},
                'verticals': ['healthcare'],
                'title_clusters': ['cfo_cluster'],
                'execution_settings': {
                    'logging': {'directory': 'logs', 'level': 'INFO', 'console_output': True},
                    'api': {'model': 'claude-haiku-4-20250514', 'max_tokens': 8000},
                    'checkpointing': {'directory': 'checkpoints'},
                    'outputs': {'directory': 'outputs'},
                    'budget': {'max_searches': 100, 'max_cost_usd': 50.0},
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

            # Setup logging
            mock_logging.return_value = Mock()

            # Setup client
            mock_client.return_value = AsyncMock()

            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            orchestrator.logger = Mock()

            yield orchestrator

    @pytest.mark.asyncio
    async def test_phase_1_agents_execute_in_parallel(self, mock_orchestrator):
        """Test that Phase 1 agents execute in parallel."""
        mock_orchestrator.state.is_agent_complete = Mock(return_value=False)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

        with patch('research_orchestrator.orchestrator.get_model_for_agent') as mock_get_model, \
             patch('research_orchestrator.orchestrator.get_model_config') as mock_get_config, \
             patch('research_orchestrator.orchestrator.get_search_budget_for_model') as mock_get_budget, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session, \
             patch('research_orchestrator.orchestrator.get_context_section') as mock_get_context:

            mock_get_model.return_value = 'claude-haiku-4-20250514'
            mock_get_config.return_value = {'max_tokens': 8000}
            mock_get_budget.return_value = 15
            mock_get_context.return_value = ""

            # Mock session results
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 5,
                'total_turns': 3,
                'execution_time_seconds': 30.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            await mock_orchestrator.execute_layer_1_parallel()

            # Verify Phase 1 agents were executed
            phase_1_agents = ['buyer_journey', 'channels_competitive', 'customer_expansion']
            for agent in phase_1_agents:
                assert any(
                    call.kwargs.get('agent_name') == agent or (call.args and call.args[0] == agent)
                    for call in mock_orchestrator.state.mark_complete.call_args_list
                )

    @pytest.mark.asyncio
    async def test_phase_2_waits_for_phase_1(self, mock_orchestrator):
        """Test that messaging_positioning waits for Phase 1 to complete."""
        # Phase 1 incomplete
        def is_complete_mock(agent_name):
            phase_1 = ['buyer_journey', 'channels_competitive', 'customer_expansion']
            return agent_name not in phase_1

        mock_orchestrator.state.is_agent_complete = Mock(side_effect=is_complete_mock)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

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
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            await mock_orchestrator.execute_layer_1_parallel()

            # messaging_positioning should NOT be executed
            messaging_calls = [
                call for call in mock_orchestrator.state.mark_complete.call_args_list
                if call.kwargs.get('agent_name') == 'messaging_positioning' or (call.args and call.args[0] == 'messaging_positioning')
            ]
            assert len(messaging_calls) == 0

    @pytest.mark.asyncio
    async def test_layer_1_complete_execution(self, mock_orchestrator):
        """Test complete Layer 1 execution when all agents run successfully."""
        # Track which agents have been completed
        completed = set()

        def is_complete_side_effect(agent_name):
            return agent_name in completed

        def mark_complete_side_effect(agent_name, outputs, layer):
            completed.add(agent_name)

        mock_orchestrator.state.is_agent_complete = Mock(side_effect=is_complete_side_effect)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock(side_effect=mark_complete_side_effect)
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

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
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            await mock_orchestrator.execute_layer_1_parallel()

            # Verify all 5 agents were marked complete
            expected_agents = [
                'buyer_journey',
                'channels_competitive',
                'customer_expansion',
                'messaging_positioning',
                'gtm_synthesis'
            ]

            for agent in expected_agents:
                assert agent in completed, f"Agent {agent} should be completed"

    @pytest.mark.asyncio
    async def test_layer_1_skips_already_complete_agents(self, mock_orchestrator):
        """Test that Layer 1 skips agents that are already complete."""
        # Buyer journey already complete
        def is_complete_mock(agent_name):
            return agent_name == 'buyer_journey'

        mock_orchestrator.state.is_agent_complete = Mock(side_effect=is_complete_mock)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        mock_orchestrator._get_agent_prompt = Mock(return_value="Test prompt")
        mock_orchestrator._print_layer_status = Mock()

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
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance

            await mock_orchestrator.execute_layer_1_parallel()

            # buyer_journey should NOT be in mark_complete calls
            buyer_calls = [
                call for call in mock_orchestrator.state.mark_complete.call_args_list
                if call.kwargs.get('agent_name') == 'buyer_journey' or (call.args and call.args[0] == 'buyer_journey')
            ]
            assert len(buyer_calls) == 0


class TestLayer1CompanyContextInjection:
    """Test that company context is injected correctly into Layer 1 prompts."""

    def test_gtm_synthesis_includes_company_context(self):
        """GTM synthesis prompt should include company context when provided."""
        company_ctx = "**Company**: TestCorp\n**Model**: Vendor-reimbursed"

        result = format_layer_1_prompt(
            prompt_template=GTM_SYNTHESIS_PROMPT,
            company_context=company_ctx,
        )

        assert "COMPANY MODEL CONTEXT" in result
        assert "TestCorp" in result
        assert "Vendor-reimbursed" in result

    def test_other_agents_get_empty_company_context(self):
        """Non-GTM agents should not get company context (empty by default)."""
        result = format_layer_1_prompt(
            prompt_template=BUYER_JOURNEY_PROMPT,
        )

        assert "COMPANY MODEL CONTEXT" not in result

    def test_gtm_includes_model_constraints(self):
        """GTM prompt should include constraints about pricing and team building."""
        result = format_layer_1_prompt(
            prompt_template=GTM_SYNTHESIS_PROMPT,
            company_context="Some context",
        )

        assert "Do NOT recommend pricing tiers" in result
        assert "Do NOT recommend building a sales team" in result

    def test_backward_compatible_without_company_context(self):
        """All prompts should work without company_context (default empty)."""
        result = format_layer_1_prompt(
            prompt_template=GTM_SYNTHESIS_PROMPT,
        )

        assert isinstance(result, str)
        assert "GTM Planning & Synthesis Agent" in result
        # Should NOT have company context section when empty
        assert "COMPANY MODEL CONTEXT" not in result
