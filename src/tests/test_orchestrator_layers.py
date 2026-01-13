# tests/test_orchestrator_layers.py
"""
Unit tests for Layer 2 and Layer 3 orchestrator methods.

Tests vertical and title agent execution logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from research_orchestrator.orchestrator import ResearchOrchestrator, BudgetExceededError


class TestLayer2VerticalAgentExecution:
    """Test Layer 2 vertical agent execution."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with necessary dependencies."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_config, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            # Setup config
            mock_config.return_value = {
                'execution': {'id': 'test_exec'},
                'verticals': ['healthcare'],
                'title_clusters': [],
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
                    'layers': {'layer_2': 'claude-haiku-4-20250514'},
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
    async def test_vertical_agent_checks_layer_1_dependencies(self, mock_orchestrator):
        """Test that vertical agent verifies Layer 1 is complete."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=False)
        
        await mock_orchestrator._execute_vertical_agent('healthcare')
        
        mock_orchestrator.state.can_execute_layer_2.assert_called_once_with('healthcare')
        mock_orchestrator.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_vertical_agent_extracts_layer_1_context(self, mock_orchestrator):
        """Test that vertical agent extracts Layer 1 context."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_get_context, \
             patch('research_orchestrator.prompts.build_vertical_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_get_context.return_value = {'buyer_journey': {}}
            mock_build_prompt.return_value = "Test prompt"
            
            # Setup mock session
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
            
            await mock_orchestrator._execute_vertical_agent('healthcare')
            
            mock_get_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vertical_agent_builds_prompt_correctly(self, mock_orchestrator):
        """Test that vertical prompt is built with correct parameters."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_get_context, \
             patch('research_orchestrator.prompts.build_vertical_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            layer_1_ctx = {'buyer_journey': {'content': 'test'}}
            mock_get_context.return_value = layer_1_ctx
            mock_build_prompt.return_value = "Test prompt"
            
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
            
            await mock_orchestrator._execute_vertical_agent('healthcare')
            
            mock_build_prompt.assert_called_once_with('healthcare', layer_1_ctx)
    
    @pytest.mark.asyncio
    async def test_vertical_agent_saves_output(self, mock_orchestrator):
        """Test that vertical agent saves output correctly."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_get_context, \
             patch('research_orchestrator.prompts.build_vertical_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_get_context.return_value = {}
            mock_build_prompt.return_value = "Test prompt"
            
            result_data = {
                'deliverables': 'Test output',
                'searches_performed': 10,
                'total_turns': 5,
                'execution_time_seconds': 60.0,
                'completion_status': 'complete',
                'estimated_cost_usd': 1.0
            }
            
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(return_value=result_data)
            mock_session.return_value = mock_session_instance
            
            await mock_orchestrator._execute_vertical_agent('healthcare')
            
            mock_orchestrator._save_agent_output.assert_called_once()
            call_args = mock_orchestrator._save_agent_output.call_args
            assert call_args[0][0] == 'vertical_healthcare'
            assert call_args[0][1] == 'layer_2'
    
    @pytest.mark.asyncio
    async def test_vertical_agent_marks_state_complete(self, mock_orchestrator):
        """Test that vertical agent marks state as complete."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        
        with patch('research_orchestrator.prompts.get_layer_1_context'), \
             patch('research_orchestrator.prompts.build_vertical_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_build_prompt.return_value = "Test prompt"
            
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
            
            await mock_orchestrator._execute_vertical_agent('healthcare')
            
            mock_orchestrator.state.mark_complete.assert_called_once()
            call_args = mock_orchestrator.state.mark_complete.call_args
            assert call_args[1]['layer'] == 'layer_2'
    
    @pytest.mark.asyncio
    async def test_vertical_agent_handles_failure(self, mock_orchestrator):
        """Test that vertical agent handles failures gracefully."""
        mock_orchestrator.state.can_execute_layer_2 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_failed = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context'), \
             patch('research_orchestrator.prompts.build_vertical_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_build_prompt.return_value = "Test prompt"
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(side_effect=Exception("Test error"))
            mock_session.return_value = mock_session_instance
            
            with pytest.raises(Exception, match="Test error"):
                await mock_orchestrator._execute_vertical_agent('healthcare')
            
            mock_orchestrator.state.mark_failed.assert_called_once()
            call_args = mock_orchestrator.state.mark_failed.call_args
            assert call_args[0][0] == 'vertical_healthcare'
            assert 'Test error' in call_args[0][1]
            assert call_args[1]['layer'] == 'layer_2'


class TestLayer3TitleAgentExecution:
    """Test Layer 3 title agent execution."""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator with necessary dependencies."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_config, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
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
                    'layers': {'layer_3': 'claude-haiku-4-20250514'},
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
    async def test_title_agent_checks_dependencies(self, mock_orchestrator):
        """Test that title agent verifies Layer 1 and 2 are complete."""
        mock_orchestrator.state.can_execute_layer_3 = Mock(return_value=False)
        
        await mock_orchestrator._execute_title_agent('cfo_cluster')
        
        mock_orchestrator.state.can_execute_layer_3.assert_called_once_with('cfo_cluster')
        mock_orchestrator.logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_title_agent_extracts_both_layer_contexts(self, mock_orchestrator):
        """Test that title agent extracts Layer 1 and Layer 2 context."""
        mock_orchestrator.state.can_execute_layer_3 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_get_l1, \
             patch('research_orchestrator.prompts.get_layer_2_context') as mock_get_l2, \
             patch('research_orchestrator.prompts.build_title_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_get_l1.return_value = {'buyer_journey': {}}
            mock_get_l2.return_value = {'healthcare': {}}
            mock_build_prompt.return_value = "Test prompt"
            
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
            
            await mock_orchestrator._execute_title_agent('cfo_cluster')
            
            mock_get_l1.assert_called_once()
            mock_get_l2.assert_called_once_with(mock_orchestrator.state, mock_orchestrator.config['verticals'])
    
    @pytest.mark.asyncio
    async def test_title_agent_builds_prompt_with_dual_context(self, mock_orchestrator):
        """Test that title prompt is built with Layer 1 and 2 context."""
        mock_orchestrator.state.can_execute_layer_3 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context') as mock_get_l1, \
             patch('research_orchestrator.prompts.get_layer_2_context') as mock_get_l2, \
             patch('research_orchestrator.prompts.build_title_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            layer_1_ctx = {'buyer_journey': {'content': 'l1'}}
            layer_2_ctx = {'healthcare': {'content': 'l2'}}
            mock_get_l1.return_value = layer_1_ctx
            mock_get_l2.return_value = layer_2_ctx
            mock_build_prompt.return_value = "Test prompt"
            
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
            
            await mock_orchestrator._execute_title_agent('cfo_cluster')
            
            mock_build_prompt.assert_called_once_with('cfo_cluster', layer_1_ctx, layer_2_ctx)
    
    @pytest.mark.asyncio
    async def test_title_agent_marks_state_complete(self, mock_orchestrator):
        """Test that title agent marks state as complete."""
        mock_orchestrator.state.can_execute_layer_3 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_complete = Mock()
        mock_orchestrator._save_agent_output = Mock(return_value=Path('output.md'))
        
        with patch('research_orchestrator.prompts.get_layer_1_context'), \
             patch('research_orchestrator.prompts.get_layer_2_context'), \
             patch('research_orchestrator.prompts.build_title_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_build_prompt.return_value = "Test prompt"
            
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
            
            await mock_orchestrator._execute_title_agent('cfo_cluster')
            
            mock_orchestrator.state.mark_complete.assert_called_once()
            call_args = mock_orchestrator.state.mark_complete.call_args
            assert call_args[1]['layer'] == 'layer_3'
    
    @pytest.mark.asyncio
    async def test_title_agent_handles_failure(self, mock_orchestrator):
        """Test that title agent handles failures gracefully."""
        mock_orchestrator.state.can_execute_layer_3 = Mock(return_value=True)
        mock_orchestrator.state.mark_in_progress = Mock()
        mock_orchestrator.state.mark_failed = Mock()
        
        with patch('research_orchestrator.prompts.get_layer_1_context'), \
             patch('research_orchestrator.prompts.get_layer_2_context'), \
             patch('research_orchestrator.prompts.build_title_prompt') as mock_build_prompt, \
             patch('research_orchestrator.orchestrator.ResearchSession') as mock_session:
            
            mock_build_prompt.return_value = "Test prompt"
            mock_session_instance = Mock()
            mock_session_instance.execute_research = AsyncMock(side_effect=Exception("Test error"))
            mock_session.return_value = mock_session_instance
            
            with pytest.raises(Exception, match="Test error"):
                await mock_orchestrator._execute_title_agent('cfo_cluster')
            
            mock_orchestrator.state.mark_failed.assert_called_once()
            call_args = mock_orchestrator.state.mark_failed.call_args
            assert call_args[0][0] == 'title_cfo_cluster'
            assert 'Test error' in call_args[0][1]
            assert call_args[1]['layer'] == 'layer_3'
