# tests/test_integration.py
"""
Integration tests for the complete research orchestration system.

Tests the full flow from Layer 1 → Layer 2 → Layer 3 → Integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import json


class TestFullSystemIntegration:
    """Integration tests for complete system flow."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create subdirectories
            (tmpdir_path / 'checkpoints').mkdir()
            (tmpdir_path / 'outputs' / 'layer_1').mkdir(parents=True)
            (tmpdir_path / 'outputs' / 'layer_2').mkdir(parents=True)
            (tmpdir_path / 'outputs' / 'layer_3').mkdir(parents=True)
            (tmpdir_path / 'outputs' / 'playbooks').mkdir(parents=True)
            (tmpdir_path / 'logs').mkdir()
            
            yield tmpdir_path
    
    @pytest.fixture
    def mock_config(self, temp_dirs):
        """Create mock configuration."""
        return {
            'execution': {'id': 'integration_test'},
            'verticals': ['healthcare'],
            'title_clusters': ['cfo_cluster'],
            'priority_combinations': [
                {'vertical': 'healthcare', 'title': 'cfo_cluster', 'priority': 1}
            ],
            'execution_settings': {
                'logging': {
                    'directory': str(temp_dirs / 'logs'),
                    'level': 'INFO',
                    'console_output': False
                },
                'api': {
                    'model': 'claude-haiku-4-20250514',
                    'max_tokens': 8000
                },
                'checkpointing': {
                    'directory': str(temp_dirs / 'checkpoints')
                },
                'outputs': {
                    'directory': str(temp_dirs / 'outputs')
                },
                'budget': {
                    'max_searches': 200,
                    'max_cost_usd': 100.0
                },
                'review_gates': {
                    'after_layer_1': False,
                    'after_layer_2': False,
                    'after_layer_3': False
                }
            },
            'model_strategy': {
                'default': 'claude-haiku-4-20250514',
                'layers': {
                    'layer_1': 'claude-haiku-4-20250514',
                    'layer_2': 'claude-haiku-4-20250514',
                    'layer_3': 'claude-haiku-4-20250514',
                    'integrations': 'claude-haiku-4-20250514'
                },
                'model_configs': {
                    'claude-haiku-4-20250514': {'max_tokens': 8000}
                },
                'budgets': {
                    'claude-haiku-4-20250514': {'max_searches_per_agent': 10}
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_full_research_flow(self, temp_dirs, mock_config):
        """Test complete research flow through all layers."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('research_orchestrator.orchestrator.get_priority_combinations') as mock_combinations, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            
            # Setup mocks
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_combinations.return_value = [('healthcare', 'cfo_cluster')]
            
            # Mock Anthropic client
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Create orchestrator
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Mock ResearchSession to return fake results
            with patch('research_orchestrator.orchestrator.ResearchSession') as mock_session_class:
                
                def create_mock_session(agent_name, *args, **kwargs):
                    """Create a mock session that returns agent-specific results."""
                    session = Mock()
                    session.execute_research = AsyncMock(return_value={
                        'deliverables': f'# {agent_name} Research\n\n## Executive Summary\n\nTest findings for {agent_name}',
                        'searches_performed': 5,
                        'total_turns': 3,
                        'execution_time_seconds': 30.0,
                        'completion_status': 'complete',
                        'estimated_cost_usd': 0.5
                    })
                    return session
                
                mock_session_class.side_effect = create_mock_session
                
                # Execute Layer 1
                await orchestrator.execute_layer_1_parallel()
                
                # Verify Layer 1 completion
                assert orchestrator.state.is_layer_complete('layer_1')
                
                # Verify Layer 1 outputs exist
                layer_1_agents = ['buyer_journey', 'channels_competitive', 'customer_expansion',
                                  'messaging_positioning', 'gtm_synthesis']
                for agent in layer_1_agents:
                    output_file = temp_dirs / 'outputs' / 'layer_1' / f'{agent}.md'
                    assert output_file.exists(), f"Layer 1 output missing: {agent}"
                
                # Execute Layer 2
                await orchestrator.execute_layer_2_parallel()
                
                # Verify Layer 2 completion
                assert orchestrator.state.is_layer_complete('layer_2')
                
                # Verify Layer 2 outputs exist
                output_file = temp_dirs / 'outputs' / 'layer_2' / 'vertical_healthcare.md'
                assert output_file.exists()
                
                # Execute Layer 3
                await orchestrator.execute_layer_3_parallel()
                
                # Verify Layer 3 completion
                assert orchestrator.state.is_layer_complete('layer_3')
                
                # Verify Layer 3 outputs exist
                output_file = temp_dirs / 'outputs' / 'layer_3' / 'title_cfo_cluster.md'
                assert output_file.exists()
                
                # Execute Integration
                await orchestrator.generate_playbooks_parallel()
                
                # Verify playbook outputs exist
                output_file = temp_dirs / 'outputs' / 'playbooks' / 'playbook_healthcare_cfo_cluster.md'
                assert output_file.exists(), f"Playbook output missing"
                
                # Verify playbook completion in state
                assert orchestrator.state.is_agent_complete('playbook_healthcare_cfo_cluster'), \
                    "Playbook agent not marked complete"
                
                # Verify integrations layer completion
                assert orchestrator.state.is_layer_complete('integrations'), \
                    "Integrations layer not complete"
    
    @pytest.mark.asyncio
    async def test_context_flow_between_layers(self, temp_dirs, mock_config):
        """Test that context flows correctly between layers."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            from research_orchestrator.prompts import (
                get_layer_1_context,
                get_layer_2_context,
                get_layer_3_context
            )
            
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Manually mark Layer 1 complete with mock data
            for agent in ['buyer_journey', 'channels_competitive', 'customer_expansion',
                          'messaging_positioning', 'gtm_synthesis']:
                orchestrator.state.mark_complete(agent, {
                    'output_path': str(temp_dirs / 'outputs' / 'layer_1' / f'{agent}.md'),
                    'content': f'## Executive Summary\n\nTest content for {agent}'
                }, 'layer_1')
            
            # Test Layer 1 context extraction
            layer_1_ctx = get_layer_1_context(orchestrator.state)
            assert len(layer_1_ctx) == 5
            assert 'buyer_journey' in layer_1_ctx
            
            # Mark Layer 2 complete
            orchestrator.state.mark_complete('vertical_healthcare', {
                'output_path': str(temp_dirs / 'outputs' / 'layer_2' / 'vertical_healthcare.md'),
                'content': '## Executive Summary\n\nHealthcare vertical findings'
            }, 'layer_2')
            
            # Test Layer 2 context extraction
            layer_2_ctx = get_layer_2_context(orchestrator.state, ['healthcare'])
            assert 'healthcare' in layer_2_ctx
            
            # Mark Layer 3 complete
            orchestrator.state.mark_complete('title_cfo_cluster', {
                'output_path': str(temp_dirs / 'outputs' / 'layer_3' / 'title_cfo_cluster.md'),
                'content': '## Executive Summary\n\nCFO cluster findings'
            }, 'layer_3')
            
            # Test Layer 3 context extraction
            layer_3_ctx = get_layer_3_context(orchestrator.state, ['cfo_cluster'])
            assert 'cfo_cluster' in layer_3_ctx
    
    @pytest.mark.asyncio
    async def test_checkpoint_and_resume(self, temp_dirs, mock_config):
        """Test checkpoint creation and resume functionality."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            # Create orchestrator and complete some work
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            execution_id = orchestrator.state.execution_id
            
            # Mark some agents as complete
            orchestrator.state.mark_complete('buyer_journey', {
                'output_path': str(temp_dirs / 'outputs' / 'layer_1' / 'buyer_journey.md'),
                'searches_performed': 10
            }, 'layer_1')
            
            orchestrator.state.mark_complete('channels_competitive', {
                'output_path': str(temp_dirs / 'outputs' / 'layer_1' / 'channels_competitive.md'),
                'searches_performed': 10
            }, 'layer_1')
            
            # Verify checkpoint file exists
            checkpoint_file = temp_dirs / 'checkpoints' / f'{execution_id}.json'
            assert checkpoint_file.exists()
            
            # Load checkpoint and verify content
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            assert checkpoint_data['execution_id'] == execution_id
            assert checkpoint_data['layer_1']['buyer_journey']['status'] == 'complete'
            assert checkpoint_data['layer_1']['channels_competitive']['status'] == 'complete'
            
            # Create new orchestrator with same execution_id (simulating resume)
            orchestrator2 = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Verify state was loaded
            assert orchestrator2.state.is_agent_complete('buyer_journey')
            assert orchestrator2.state.is_agent_complete('channels_competitive')
            assert not orchestrator2.state.is_agent_complete('customer_expansion')
    
    @pytest.mark.asyncio
    async def test_budget_enforcement(self, temp_dirs, mock_config):
        """Test that budget limits are enforced across all layers."""
        # Set very low budget
        mock_config['execution_settings']['budget']['max_searches'] = 5
        mock_config['execution_settings']['budget']['max_cost_usd'] = 2.0
        
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator, BudgetExceededError
            
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Mock ResearchSession to exceed budget
            with patch('research_orchestrator.orchestrator.ResearchSession') as mock_session_class:
                session = Mock()
                session.execute_research = AsyncMock(return_value={
                    'deliverables': 'Test output',
                    'searches_performed': 10,  # Exceeds budget
                    'total_turns': 5,
                    'execution_time_seconds': 60.0,
                    'completion_status': 'complete',
                    'estimated_cost_usd': 5.0  # Exceeds budget
                })
                mock_session_class.return_value = session
                
                # Should raise BudgetExceededError
                with pytest.raises(BudgetExceededError):
                    await orchestrator._execute_agent('buyer_journey', 'layer_1')
    
    @pytest.mark.asyncio
    async def test_dependency_enforcement(self, temp_dirs, mock_config):
        """Test that layer dependencies are enforced."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'):
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Try to execute Layer 2 without Layer 1 complete
            await orchestrator.execute_layer_2_parallel()
            
            # Should not execute (Layer 1 not complete)
            assert not orchestrator.state.is_agent_complete('vertical_healthcare')
            
            # Complete Layer 1
            for agent in ['buyer_journey', 'channels_competitive', 'customer_expansion',
                          'messaging_positioning', 'gtm_synthesis']:
                orchestrator.state.mark_complete(agent, {
                    'output_path': str(temp_dirs / 'outputs' / 'layer_1' / f'{agent}.md')
                }, 'layer_1')
            
            # Try to execute Layer 3 without Layer 2 complete
            await orchestrator.execute_layer_3_parallel()
            
            # Should not execute (Layer 2 not complete)
            assert not orchestrator.state.is_agent_complete('title_cfo_cluster')
            
            # Complete Layer 2
            orchestrator.state.mark_complete('vertical_healthcare', {
                'output_path': str(temp_dirs / 'outputs' / 'layer_2' / 'vertical_healthcare.md')
            }, 'layer_2')
            
            # Now Layer 3 should be able to execute (with mocking)
            with patch('research_orchestrator.orchestrator.ResearchSession') as mock_session_class:
                session = Mock()
                session.execute_research = AsyncMock(return_value={
                    'deliverables': 'Test output',
                    'searches_performed': 5,
                    'total_turns': 3,
                    'execution_time_seconds': 30.0,
                    'completion_status': 'complete',
                    'estimated_cost_usd': 1.0
                })
                mock_session_class.return_value = session
                
                await orchestrator.execute_layer_3_parallel()
                
                # Should now be complete
                assert orchestrator.state.is_agent_complete('title_cfo_cluster')


class TestErrorRecovery:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self):
        """Test that agent failures are properly handled and logged."""
        with patch('research_orchestrator.orchestrator.load_config') as mock_load, \
             patch('research_orchestrator.orchestrator.setup_logging') as mock_logging, \
             patch('research_orchestrator.orchestrator.AsyncAnthropic') as mock_client, \
             patch('os.getenv', return_value='fake-api-key'), \
             tempfile.TemporaryDirectory() as tmpdir:
            
            from research_orchestrator.orchestrator import ResearchOrchestrator
            
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / 'checkpoints').mkdir()
            (tmpdir_path / 'outputs').mkdir()
            (tmpdir_path / 'logs').mkdir()
            
            mock_config = {
                'execution': {'id': 'error_test'},
                'verticals': [],
                'title_clusters': [],
                'execution_settings': {
                    'logging': {'directory': str(tmpdir_path / 'logs'), 'level': 'INFO', 'console_output': False},
                    'api': {'model': 'claude-haiku-4-20250514', 'max_tokens': 8000},
                    'checkpointing': {'directory': str(tmpdir_path / 'checkpoints')},
                    'outputs': {'directory': str(tmpdir_path / 'outputs')},
                    'budget': {'max_searches': 100, 'max_cost_usd': 50.0},
                    'review_gates': {}
                },
                'model_strategy': {
                    'default': 'claude-haiku-4-20250514',
                    'layers': {},
                    'model_configs': {'claude-haiku-4-20250514': {'max_tokens': 8000}},
                    'budgets': {'claude-haiku-4-20250514': {'max_searches_per_agent': 10}}
                }
            }
            
            mock_load.return_value = mock_config
            mock_logging.return_value = Mock()
            mock_client.return_value = AsyncMock()
            
            orchestrator = ResearchOrchestrator(Path('test_config.yaml'))
            
            # Mock ResearchSession to raise an error
            with patch('research_orchestrator.orchestrator.ResearchSession') as mock_session_class:
                session = Mock()
                session.execute_research = AsyncMock(side_effect=Exception("Test error"))
                mock_session_class.return_value = session
                
                # Should raise exception
                with pytest.raises(Exception, match="Test error"):
                    await orchestrator._execute_agent('buyer_journey', 'layer_1')
                
                # Verify agent marked as failed in state
                agent_state = orchestrator.state.get_agent_output('buyer_journey', 'layer_1')
                assert agent_state is not None
                assert agent_state['status'] == 'failed'
                assert 'Test error' in agent_state['error']
