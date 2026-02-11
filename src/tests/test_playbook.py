# tests/test_playbook.py
"""
Unit tests for playbook generation functionality.

Tests the integration of all three layers into actionable playbooks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from research_orchestrator.prompts.playbook import (
    build_playbook_prompt,
    _format_integration_context
)
from research_orchestrator.prompts.vertical import VERTICALS
from research_orchestrator.prompts.title import TITLE_CLUSTERS


class TestBuildPlaybookPrompt:
    """Test build_playbook_prompt function."""
    
    def test_builds_prompt_with_all_contexts(self):
        """Test that prompt includes all three layer contexts."""
        layer_1_ctx = {'buyer_journey': {'content': 'L1 content'}}
        layer_2_ctx = {'healthcare': {'content': 'L2 content'}}
        layer_3_ctx = {'cfo_cluster': {'content': 'L3 content'}}
        
        result = build_playbook_prompt(
            'healthcare', 'cfo_cluster',
            layer_1_ctx, layer_2_ctx, layer_3_ctx
        )
        
        assert 'LAYER 1: HORIZONTAL RESEARCH' in result
        assert 'LAYER 2: VERTICAL RESEARCH' in result
        assert 'LAYER 3: TITLE RESEARCH' in result
    
    def test_includes_vertical_and_title_names(self):
        """Test that vertical and title names are in the prompt."""
        layer_1_ctx = {}
        layer_2_ctx = {}
        layer_3_ctx = {}
        
        result = build_playbook_prompt(
            'healthcare', 'cfo_cluster',
            layer_1_ctx, layer_2_ctx, layer_3_ctx
        )
        
        assert 'Healthcare' in result
        assert 'C-Suite' in result
    
    def test_raises_error_for_invalid_vertical(self):
        """Test error handling for invalid vertical key."""
        with pytest.raises(ValueError, match="Unknown vertical"):
            build_playbook_prompt(
                'invalid_vertical', 'cfo_cluster',
                {}, {}, {}
            )
    
    def test_raises_error_for_invalid_title(self):
        """Test error handling for invalid title key."""
        with pytest.raises(ValueError, match="Unknown title cluster"):
            build_playbook_prompt(
                'healthcare', 'invalid_title',
                {}, {}, {}
            )


class TestBuildPlaybookPromptCompanyContext:
    """Test build_playbook_prompt with company context injection."""

    def test_includes_company_context_when_provided(self):
        """Test that company context is included in the prompt."""
        company_ctx = "## Company Context\n\n**Company**: TestCorp\n**Business Model**: Vendor-reimbursed"

        result = build_playbook_prompt(
            'healthcare', 'cfo_cluster',
            {}, {}, {},
            company_context=company_ctx
        )

        assert 'COMPANY CONTEXT' in result
        assert 'TestCorp' in result
        assert 'Vendor-reimbursed' in result

    def test_backward_compatible_without_company_context(self):
        """Test that prompt works without company_context (default empty string)."""
        result = build_playbook_prompt(
            'healthcare', 'cfo_cluster',
            {}, {}, {}
        )

        # Should NOT contain the company context section header
        assert 'COMPANY CONTEXT' not in result
        # Should still contain the standard prompt elements
        assert 'Playbook Integration Agent' in result
        assert 'LAYER 1: HORIZONTAL RESEARCH' in result

    def test_includes_methodology_bullets_with_company_context(self):
        """Test that methodology constraints appear when company context provided."""
        result = build_playbook_prompt(
            'healthcare', 'cfo_cluster',
            {}, {}, {},
            company_context="Some company context"
        )

        assert 'do not invent statistics' in result
        assert 'vendor-reimbursed' in result.lower()


class TestFormatIntegrationContext:
    """Test _format_integration_context function."""
    
    def test_formats_layer_1_context(self):
        """Test Layer 1 context formatting."""
        vertical = VERTICALS['healthcare']
        title = TITLE_CLUSTERS['cfo_cluster']
        
        layer_1_ctx = {
            'buyer_journey': {'content': '## Executive Summary\n\nBuyer insights'},
            'channels_competitive': {'content': '## Executive Summary\n\nCompetitive insights'}
        }
        
        result = _format_integration_context(
            'healthcare', 'cfo_cluster', vertical, title,
            layer_1_ctx, {}, {}
        )
        
        assert 'BUYER JOURNEY INSIGHTS' in result
        assert 'COMPETITIVE INTELLIGENCE' in result
        assert 'Buyer insights' in result
    
    def test_formats_layer_2_context(self):
        """Test Layer 2 context formatting."""
        vertical = VERTICALS['healthcare']
        title = TITLE_CLUSTERS['cfo_cluster']
        
        layer_2_ctx = {
            'healthcare': {'content': '## Executive Summary\n\nHealthcare vertical insights'}
        }
        
        result = _format_integration_context(
            'healthcare', 'cfo_cluster', vertical, title,
            {}, layer_2_ctx, {}
        )
        
        assert 'LAYER 2: VERTICAL RESEARCH (Healthcare)' in result
        assert 'Healthcare vertical insights' in result
        assert 'HIPAA' in result  # Key regulation
    
    def test_formats_layer_3_context(self):
        """Test Layer 3 context formatting."""
        vertical = VERTICALS['healthcare']
        title = TITLE_CLUSTERS['cfo_cluster']
        
        layer_3_ctx = {
            'cfo_cluster': {'content': '## Executive Summary\n\nCFO title insights'}
        }
        
        result = _format_integration_context(
            'healthcare', 'cfo_cluster', vertical, title,
            {}, {}, layer_3_ctx
        )
        
        assert 'LAYER 3: TITLE RESEARCH (C-Suite' in result
        assert 'CFO title insights' in result
        assert 'Final approval' in result  # Decision authority
    
    def test_includes_integration_mission(self):
        """Test that integration mission is included."""
        vertical = VERTICALS['healthcare']
        title = TITLE_CLUSTERS['cfo_cluster']
        
        result = _format_integration_context(
            'healthcare', 'cfo_cluster', vertical, title,
            {}, {}, {}
        )
        
        assert 'YOUR INTEGRATION MISSION' in result
        assert 'Healthcare C-Suite' in result


class TestPlaybookOrchestratorIntegration:
    """Test playbook execution in orchestrator."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator for testing."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_config, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            
            mock_config.return_value = {
                'execution': {'id': 'test_exec'},
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
                    'layers': {'integrations': 'claude-haiku-4-20250514'},
                    'model_configs': {
                        'claude-haiku-4-20250514': {'max_tokens': 8000}
                    },
                    'budgets': {
                        'claude-haiku-4-20250514': {'max_searches_per_agent': 20}
                    }
                }
            }
            
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            orchestrator.logger = Mock()
            
            yield orchestrator
    
    @pytest.mark.asyncio
    async def test_playbook_checks_all_layer_dependencies(self, mock_orchestrator):
        """Test that playbook verifies all layers are complete."""
        mock_orchestrator.state.is_layer_complete = Mock(return_value=False)
        
        await mock_orchestrator._execute_playbook('healthcare', 'cfo_cluster')
        
        # Should check layer dependencies (stops at first incomplete layer)
        assert mock_orchestrator.state.is_layer_complete.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_playbook_extracts_all_layer_contexts(self, mock_orchestrator):
        """Test that playbook extracts context from all three layers."""
        mock_orchestrator.state.is_layer_complete = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_l1, \
             patch('research_orchestrator.prompts.get_layer_2_context') as mock_l2, \
             patch('research_orchestrator.prompts.get_layer_3_context') as mock_l3, \
             patch('research_orchestrator.prompts.build_playbook_prompt') as mock_build, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_l1.return_value = {}
            mock_l2.return_value = {}
            mock_l3.return_value = {}
            mock_build.return_value = "Test prompt"
            
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 10,
                'total_turns': 5,
                'execution_time_seconds': 60.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance
            
            await mock_orchestrator._execute_playbook('healthcare', 'cfo_cluster')
            
            mock_l1.assert_called_once()
            mock_l2.assert_called_once()
            mock_l3.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_playbook_builds_prompt_correctly(self, mock_orchestrator):
        """Test that playbook prompt is built with all contexts."""
        mock_orchestrator.state.is_layer_complete = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_l1, \
             patch('research_orchestrator.prompts.get_layer_2_context') as mock_l2, \
             patch('research_orchestrator.prompts.get_layer_3_context') as mock_l3, \
             patch('research_orchestrator.prompts.build_playbook_prompt') as mock_build, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            l1_ctx = {'buyer_journey': {}}
            l2_ctx = {'healthcare': {}}
            l3_ctx = {'cfo_cluster': {}}
            
            mock_l1.return_value = l1_ctx
            mock_l2.return_value = l2_ctx
            mock_l3.return_value = l3_ctx
            mock_build.return_value = "Test prompt"
            
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 10,
                'total_turns': 5,
                'execution_time_seconds': 60.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance
            
            await mock_orchestrator._execute_playbook('healthcare', 'cfo_cluster')
            
            mock_build.assert_called_once_with(
                'healthcare', 'cfo_cluster',
                l1_ctx, l2_ctx, l3_ctx,
                company_context=""
            )
    
    @pytest.mark.asyncio
    async def test_playbook_saves_to_integrations_layer(self, mock_orchestrator):
        """Test that playbook is saved to integrations layer."""
        mock_orchestrator.state.is_layer_complete = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        
        with patch('research_orchestrator.prompts.get_layer_1_context'), \
             patch('research_orchestrator.prompts.get_layer_2_context'), \
             patch('research_orchestrator.prompts.get_layer_3_context'), \
             patch('research_orchestrator.prompts.build_playbook_prompt') as mock_build, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_build.return_value = "Test prompt"
            
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value={
                'deliverables': 'Test output',
                'searches_performed': 10,
                'total_turns': 5,
                'execution_time_seconds': 60.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            })
            mock_session.return_value = mock_session_instance
            
            await mock_orchestrator._execute_playbook('healthcare', 'cfo_cluster')
            
            # Verify saved to integrations layer
            mock_orchestrator._save_agent_output.assert_called_once()
            call_args = mock_orchestrator._save_agent_output.call_args
            assert call_args[0][1] == 'integrations'
            
            # Verify state marked complete in integrations layer
            mock_orchestrator.state.mark_complete.assert_called_once()
            call_args = mock_orchestrator.state.mark_complete.call_args
            assert call_args[1]['layer'] == 'integrations'
