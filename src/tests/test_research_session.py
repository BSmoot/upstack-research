"""
Pytest Test Suite for ResearchSession

Tests the ResearchSession class integration with Anthropic API.
Run with: pytest test_research_session.py -v
"""

import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from anthropic import AsyncAnthropic
from research_orchestrator.research_session import ResearchSession


@pytest.fixture
def anthropic_client():
    """Create a real Anthropic client for integration tests."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return AsyncAnthropic(api_key=api_key)


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for unit tests."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


class TestResearchSessionInitialization:
    """Test ResearchSession initialization."""
    
    def test_initialization_with_defaults(self, mock_anthropic_client, mock_logger):
        """Test initialization with default parameters."""
        session = ResearchSession(
            agent_name="test_agent",
            anthropic_client=mock_anthropic_client,
            logger=mock_logger
        )
        
        assert session.agent_name == "test_agent"
        assert session.client == mock_anthropic_client
        assert session.model == "claude-sonnet-4-20250514"
        assert session.max_tokens == 16000
        assert session.max_searches == 60
        assert session.searches_performed == 0
        assert session.total_turns == 0
        assert session.tokens_used == 0
        assert session.estimated_cost_usd == 0.0
    
    def test_initialization_with_custom_params(self, mock_anthropic_client, mock_logger):
        """Test initialization with custom parameters."""
        session = ResearchSession(
            agent_name="custom_agent",
            anthropic_client=mock_anthropic_client,
            model="claude-opus-4-20250514",
            max_tokens=8000,
            max_searches=30,
            logger=mock_logger
        )
        
        assert session.agent_name == "custom_agent"
        assert session.model == "claude-opus-4-20250514"
        assert session.max_tokens == 8000
        assert session.max_searches == 30


class TestResearchSessionTokenTracking:
    """Test token usage tracking and cost estimation."""
    
    def test_estimate_cost(self, mock_anthropic_client, mock_logger):
        """Test cost calculation with tracked tokens."""
        session = ResearchSession(
            agent_name="test_agent",
            anthropic_client=mock_anthropic_client,
            logger=mock_logger
        )

        # Set tracked tokens (400 input, 600 output)
        session.total_input_tokens = 400
        session.total_output_tokens = 600
        cost = session._calculate_cost()

        # Expected: (400/1M * $3) + (600/1M * $15) = $0.0012 + $0.009 = $0.0102
        expected_cost = 0.0102
        assert abs(cost - expected_cost) < 0.0001
    
    def test_estimate_cost_large_numbers(self, mock_anthropic_client, mock_logger):
        """Test cost calculation with large token counts."""
        session = ResearchSession(
            agent_name="test_agent",
            anthropic_client=mock_anthropic_client,
            logger=mock_logger
        )

        # Set tracked tokens (40k input, 60k output)
        session.total_input_tokens = 40000
        session.total_output_tokens = 60000
        cost = session._calculate_cost()

        # Expected: (40k/1M * $3) + (60k/1M * $15) = $0.12 + $0.90 = $1.02
        expected_cost = 1.02
        assert abs(cost - expected_cost) < 0.01


class TestResearchSessionContentExtraction:
    """Test content extraction from responses."""
    
    def test_extract_text_content(self, mock_anthropic_client, mock_logger):
        """Test extracting text from response blocks."""
        session = ResearchSession(
            agent_name="test_agent",
            anthropic_client=mock_anthropic_client,
            logger=mock_logger
        )
        
        # Create mock content blocks
        class MockTextBlock:
            def __init__(self, text):
                self.type = "text"
                self.text = text
        
        content = [
            MockTextBlock("First paragraph."),
            MockTextBlock("Second paragraph.")
        ]
        
        result = session._extract_text_content(content)
        assert result == "First paragraph.\n\nSecond paragraph."
    
    def test_extract_text_content_mixed_blocks(self, mock_anthropic_client, mock_logger):
        """Test extracting text when mixed with other block types."""
        session = ResearchSession(
            agent_name="test_agent",
            anthropic_client=mock_anthropic_client,
            logger=mock_logger
        )
        
        class MockTextBlock:
            def __init__(self, text):
                self.type = "text"
                self.text = text
        
        class MockToolBlock:
            def __init__(self):
                self.type = "tool_use"
        
        content = [
            MockTextBlock("Text before tool."),
            MockToolBlock(),
            MockTextBlock("Text after tool.")
        ]
        
        result = session._extract_text_content(content)
        assert result == "Text before tool.\n\nText after tool."


@pytest.mark.asyncio
@pytest.mark.integration
class TestResearchSessionIntegration:
    """Integration tests that make real API calls."""
    
    async def test_simple_research_execution(self, anthropic_client):
        """Test executing a simple research prompt."""
        session = ResearchSession(
            agent_name="integration_test",
            anthropic_client=anthropic_client,
            max_tokens=500,
            max_searches=5
        )
        
        prompt = "Provide a brief (2-3 sentence) explanation of what API testing is."
        
        result = await session.execute_research(
            prompt=prompt,
            max_turns=3
        )
        
        # Verify result structure
        assert 'deliverables' in result
        assert 'conversation' in result
        assert 'searches_performed' in result
        assert 'total_turns' in result
        assert 'tokens_used' in result
        assert 'estimated_cost_usd' in result
        assert 'execution_time_seconds' in result
        assert 'completion_status' in result
        
        # Verify we got actual content
        assert result['deliverables'] is not None
        assert len(result['deliverables']) > 0
        
        # Verify reasonable token usage
        assert result['tokens_used'] > 0
        assert result['tokens_used'] < 3000  # Should be small for simple request
        
        # Verify cost is calculated
        assert result['estimated_cost_usd'] > 0
        assert result['estimated_cost_usd'] < 1.0  # Should be very cheap
        
        # Verify turns
        assert result['total_turns'] >= 1
        assert result['total_turns'] <= 3
        
        print(f"\nIntegration test results:")
        print(f"  Deliverables length: {len(result['deliverables'])} chars")
        print(f"  Tokens used: {result['tokens_used']}")
        print(f"  Cost: ${result['estimated_cost_usd']:.6f}")
        print(f"  Turns: {result['total_turns']}")
        print(f"  Searches: {result['searches_performed']}")
        print(f"  Execution time: {result['execution_time_seconds']:.2f}s")
    
    async def test_research_with_web_search(self, anthropic_client):
        """Test research that likely triggers web search."""
        session = ResearchSession(
            agent_name="search_test",
            anthropic_client=anthropic_client,
            max_tokens=1000,
            max_searches=10
        )
        
        # Prompt that should trigger search
        prompt = """Find the current (2025) stock price of Apple Inc. (AAPL).
        Provide just the price and date, nothing more."""
        
        result = await session.execute_research(
            prompt=prompt,
            max_turns=5
        )
        
        # Verify search was used
        assert result['searches_performed'] > 0
        
        print(f"\nSearch test results:")
        print(f"  Searches performed: {result['searches_performed']}")
        print(f"  Response preview: {result['deliverables'][:200]}...")
    
    async def test_max_turns_limit(self, anthropic_client):
        """Test that max_turns is respected."""
        session = ResearchSession(
            agent_name="max_turns_test",
            anthropic_client=anthropic_client,
            max_tokens=200,
            max_searches=5
        )
        
        # Simple prompt with very low max_turns
        prompt = "Count from 1 to 100."
        
        result = await session.execute_research(
            prompt=prompt,
            max_turns=1  # Artificially low
        )
        
        # Should hit max turns or complete
        assert result['total_turns'] <= 1
        assert result['completion_status'] in ['complete', 'max_turns']
    
    async def test_get_summary(self, anthropic_client):
        """Test session summary generation."""
        session = ResearchSession(
            agent_name="summary_test",
            anthropic_client=anthropic_client,
            max_tokens=300
        )
        
        # Execute a simple research
        await session.execute_research(
            prompt="What is 2+2?",
            max_turns=2
        )
        
        # Get summary
        summary = session.get_summary()
        
        # Verify summary structure
        assert 'agent_name' in summary
        assert summary['agent_name'] == "summary_test"
        assert 'searches_performed' in summary
        assert 'total_turns' in summary
        assert 'tokens_used' in summary
        assert 'estimated_cost_usd' in summary
        assert 'start_time' in summary
        assert 'end_time' in summary
        assert 'execution_time_seconds' in summary
        
        # Verify reasonable values
        assert summary['total_turns'] > 0
        assert summary['tokens_used'] > 0
        assert summary['execution_time_seconds'] > 0


@pytest.mark.asyncio
class TestResearchSessionRetryLogic:
    """Test retry logic for API errors."""

    async def test_retry_on_rate_limit(self, mock_logger):
        """Test retry behavior on rate limit errors."""
        from anthropic import RateLimitError
        from anthropic.types import Message, Usage

        # Create mock client that fails twice then succeeds
        mock_client = AsyncMock()

        # Create mock response for successful call
        mock_response = Mock()
        mock_response.content = []
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Usage(input_tokens=10, output_tokens=20)

        # Track call count for the stream mock
        call_count = 0

        async def mock_stream_generator():
            """Async context manager that simulates stream behavior."""
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First two calls raise RateLimitError
                raise RateLimitError(
                    "Rate limited",
                    response=Mock(headers={'retry-after': '0'}),
                    body={}
                )

            # Third call succeeds - return mock stream
            mock_stream = AsyncMock()
            mock_stream.get_final_message = AsyncMock(return_value=mock_response)
            return mock_stream

        # Create async context manager mock for messages.stream()
        class MockStreamContextManager:
            async def __aenter__(self):
                return await mock_stream_generator()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        mock_client.messages.stream = Mock(return_value=MockStreamContextManager())

        session = ResearchSession(
            agent_name="retry_test",
            anthropic_client=mock_client,
            logger=mock_logger
        )

        # Execute research - should succeed after retries
        result = await session.execute_research(
            prompt="Test",
            max_turns=1
        )

        # Should have completed successfully
        assert result['completion_status'] == 'complete'

        # Should have been called 3 times (2 failures + 1 success)
        assert call_count == 3


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
