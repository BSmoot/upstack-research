# tests/test_context_helpers.py
"""
Unit tests for context helper functions.

Tests the extraction and formatting of context between research layers.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from research_orchestrator.prompts.context_helpers import (
    get_layer_1_context,
    get_layer_2_context,
    extract_summary,
    format_layer_1_context_for_vertical,
    format_layer_2_context_for_title
)


class TestGetLayer1Context:
    """Test get_layer_1_context function."""
    
    def test_returns_all_layer_1_agents(self):
        """Test that all Layer 1 agents are retrieved."""
        # Setup mock state tracker
        mock_tracker = Mock()
        mock_tracker.get_agent_output = Mock(side_effect=lambda name, layer: {
            'status': 'complete',
            'output_path': f'/path/to/{name}.md'
        })
        
        # Execute
        result = get_layer_1_context(mock_tracker)
        
        # Verify
        assert len(result) == 5
        assert 'buyer_journey' in result
        assert 'channels_competitive' in result
        assert 'customer_expansion' in result
        assert 'messaging_positioning' in result
        assert 'gtm_synthesis' in result
    
    def test_handles_missing_agents(self):
        """Test that missing agents are excluded from context."""
        # Setup mock state tracker that returns None for some agents
        mock_tracker = Mock()
        def mock_get_output(name, layer):
            if name in ['buyer_journey', 'channels_competitive']:
                return {'status': 'complete', 'output_path': f'/path/to/{name}.md'}
            return None
        
        mock_tracker.get_agent_output = Mock(side_effect=mock_get_output)
        
        # Execute
        result = get_layer_1_context(mock_tracker)
        
        # Verify
        assert len(result) == 2
        assert 'buyer_journey' in result
        assert 'channels_competitive' in result
        assert 'customer_expansion' not in result
    
    def test_calls_get_agent_output_with_correct_layer(self):
        """Test that layer_1 is passed to get_agent_output."""
        mock_tracker = Mock()
        mock_tracker.get_agent_output = Mock(return_value={'status': 'complete'})
        
        get_layer_1_context(mock_tracker)
        
        # Verify all calls used 'layer_1'
        for call in mock_tracker.get_agent_output.call_args_list:
            assert call[0][1] == 'layer_1'


class TestGetLayer2Context:
    """Test get_layer_2_context function."""
    
    def test_returns_specified_verticals(self):
        """Test that only specified verticals are retrieved."""
        mock_tracker = Mock()
        mock_tracker.get_agent_output = Mock(side_effect=lambda name, layer: {
            'status': 'complete',
            'output_path': f'/path/to/{name}.md'
        })
        
        verticals = ['healthcare', 'financial_services']
        result = get_layer_2_context(mock_tracker, verticals)
        
        assert len(result) == 2
        assert 'healthcare' in result
        assert 'financial_services' in result
    
    def test_handles_missing_verticals(self):
        """Test that missing verticals are excluded."""
        mock_tracker = Mock()
        def mock_get_output(name, layer):
            if name == 'vertical_healthcare':
                return {'status': 'complete'}
            return None
        
        mock_tracker.get_agent_output = Mock(side_effect=mock_get_output)
        
        verticals = ['healthcare', 'financial_services']
        result = get_layer_2_context(mock_tracker, verticals)
        
        assert len(result) == 1
        assert 'healthcare' in result
        assert 'financial_services' not in result
    
    def test_uses_vertical_prefix_in_agent_name(self):
        """Test that 'vertical_' prefix is added to agent names."""
        mock_tracker = Mock()
        mock_tracker.get_agent_output = Mock(return_value={'status': 'complete'})
        
        verticals = ['healthcare']
        get_layer_2_context(mock_tracker, verticals)
        
        mock_tracker.get_agent_output.assert_called_once_with('vertical_healthcare', 'layer_2')


class TestExtractSummary:
    """Test extract_summary function."""
    
    def test_extracts_executive_summary_section(self):
        """Test extraction of Executive Summary section from markdown."""
        agent_output = {
            'content': """# Research Report

## Executive Summary

This is the key summary content.
It spans multiple lines.

## Detailed Analysis

This is detailed content that should not be included.
"""
        }
        
        result = extract_summary(agent_output, max_length=500)
        
        assert 'key summary content' in result
        assert 'detailed content' not in result
    
    def test_truncates_to_max_length(self):
        """Test that summary is truncated to max_length."""
        long_content = "A" * 1000
        agent_output = {
            'content': f"""## Executive Summary

{long_content}

## Next Section
"""
        }
        
        result = extract_summary(agent_output, max_length=100)
        
        assert len(result) <= 104  # 100 + "..."
        assert result.endswith('...')
    
    def test_reads_from_output_path_if_available(self, tmp_path):
        """Test that content is read from file if output_path exists."""
        # Create temp file
        test_file = tmp_path / "test_output.md"
        test_file.write_text("## Executive Summary\n\nFile content")
        
        agent_output = {
            'output_path': str(test_file)
        }
        
        result = extract_summary(agent_output)
        
        assert 'File content' in result
    
    def test_falls_back_to_content_field(self):
        """Test fallback to content field when output_path doesn't exist."""
        agent_output = {
            'output_path': '/nonexistent/path.md',
            'content': '## Executive Summary\n\nContent field data'
        }
        
        result = extract_summary(agent_output)
        
        assert 'Content field data' in result
    
    def test_handles_missing_executive_summary(self):
        """Test fallback when Executive Summary section not found."""
        agent_output = {
            'content': 'Just some plain content without sections.'
        }
        
        result = extract_summary(agent_output, max_length=20)
        
        assert len(result) <= 23  # 20 + "..."
        assert 'Just some' in result
    
    def test_returns_not_available_for_empty_output(self):
        """Test handling of None or empty agent output."""
        assert extract_summary(None) == "Summary not available"
        assert extract_summary({}) == "Summary not available"


class TestFormatLayer1ContextForVertical:
    """Test format_layer_1_context_for_vertical function."""
    
    def test_formats_all_layer_1_agents(self):
        """Test that all Layer 1 agents are formatted."""
        layer_1_context = {
            'buyer_journey': {'content': '## Executive Summary\n\nBuyer journey insights'},
            'channels_competitive': {'content': '## Executive Summary\n\nCompetitive insights'},
            'customer_expansion': {'content': '## Executive Summary\n\nExpansion insights'},
            'messaging_positioning': {'content': '## Executive Summary\n\nMessaging insights'},
            'gtm_synthesis': {'content': '## Executive Summary\n\nGTM insights'}
        }
        
        result = format_layer_1_context_for_vertical(layer_1_context)
        
        assert 'BUYER JOURNEY RESEARCH' in result
        assert 'COMPETITIVE & CHANNEL ANALYSIS' in result
        assert 'CUSTOMER EXPANSION RESEARCH' in result
        assert 'MESSAGING & POSITIONING RESEARCH' in result
        assert 'GTM STRATEGY SYNTHESIS' in result
    
    def test_preserves_agent_order(self):
        """Test that agents are formatted in correct order."""
        layer_1_context = {
            'gtm_synthesis': {'content': 'GTM content'},
            'buyer_journey': {'content': 'Buyer content'},
        }
        
        result = format_layer_1_context_for_vertical(layer_1_context)
        
        # Buyer should appear before GTM
        buyer_pos = result.find('BUYER JOURNEY')
        gtm_pos = result.find('GTM STRATEGY')
        assert buyer_pos < gtm_pos
    
    def test_returns_default_message_for_empty_context(self):
        """Test handling of empty context."""
        assert format_layer_1_context_for_vertical({}) == "No Layer 1 research available."
        assert format_layer_1_context_for_vertical(None) == "No Layer 1 research available."


class TestFormatLayer2ContextForTitle:
    """Test format_layer_2_context_for_title function."""
    
    def test_formats_all_verticals(self):
        """Test that all verticals are formatted."""
        layer_2_context = {
            'healthcare': {'content': '## Executive Summary\n\nHealthcare insights'},
            'financial_services': {'content': '## Executive Summary\n\nFinance insights'}
        }
        
        result = format_layer_2_context_for_title(layer_2_context)
        
        assert 'HEALTHCARE VERTICAL' in result
        assert 'FINANCIAL SERVICES VERTICAL' in result
    
    def test_replaces_underscores_in_vertical_names(self):
        """Test that underscores are replaced with spaces."""
        layer_2_context = {
            'financial_services': {'content': 'Finance content'}
        }
        
        result = format_layer_2_context_for_title(layer_2_context)
        
        assert 'FINANCIAL SERVICES' in result
        assert 'financial_services' not in result
    
    def test_returns_default_message_for_empty_context(self):
        """Test handling of empty context."""
        result = format_layer_2_context_for_title({})
        assert "No vertical research available" in result
        
        result = format_layer_2_context_for_title(None)
        assert "No vertical research available" in result
