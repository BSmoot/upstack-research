# research_orchestrator/research_session.py
"""
ResearchSession - Manages individual Claude API research conversations.

Handles server-side web_search tool automatically and produces structured markdown outputs.
"""

import anthropic
from anthropic import AsyncAnthropic
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .utils.constants import Models


class ResearchSession:
    """
    Handles a single research conversation with Claude.
    Manages server-side web_search tool automatically.
    Produces structured markdown output.
    """
    
    def __init__(
        self, 
        agent_name: str, 
        anthropic_client: AsyncAnthropic,
        model: str = Models.HIGH_QUALITY,
        max_tokens: int = 16000,
        max_searches: int = 60,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize research session.
        
        Args:
            agent_name: Identifier for this research agent
            anthropic_client: Initialized Anthropic async client
            model: Claude model to use
            max_tokens: Maximum tokens per response
            max_searches: Maximum web searches allowed
            logger: Optional logger instance
        """
        self.agent_name = agent_name
        self.client = anthropic_client
        self.model = model
        self.max_tokens = max_tokens
        self.max_searches = max_searches
        self.logger = logger or logging.getLogger(__name__)
        
        # Conversation tracking
        self.conversation_history: List[Dict[str, Any]] = []
        self.searches_performed = 0
        self.total_turns = 0
        self.tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.estimated_cost_usd = 0.0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    async def execute_research(
        self, 
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_turns: int = 50
    ) -> Dict[str, Any]:
        """
        Execute research conversation until completion or max turns.
        
        Args:
            prompt: Initial research prompt for the agent
            context: Optional context from prior agents
            max_turns: Maximum conversation turns before stopping
            
        Returns:
            {
                'deliverables': str,  # Structured markdown output
                'conversation': [...],  # Full conversation history
                'searches_performed': int,
                'total_turns': int,
                'tokens_used': int,
                'estimated_cost_usd': float,
                'execution_time_seconds': float,
                'completion_status': 'complete'|'max_turns'|'error'|'budget_exceeded'
            }
        """
        self.logger.info(f"Starting research session for agent: {self.agent_name}")
        self.start_time = datetime.utcnow()
        
        try:
            # Initialize conversation with user prompt
            messages = [{"role": "user", "content": prompt}]
            
            # Execute conversation loop with server-side tool use
            completion_status = 'max_turns'
            final_response = None
            
            for turn in range(max_turns):
                self.total_turns = turn + 1
                self.logger.info(f"[{self.agent_name}] Turn {self.total_turns}/{max_turns}")
                
                # Check search budget
                if self.searches_performed >= self.max_searches:
                    self.logger.warning(
                        f"[{self.agent_name}] Search budget exceeded ({self.max_searches} searches)"
                    )
                    completion_status = 'budget_exceeded'
                    final_response = self._extract_final_content(messages)
                    break
                
                # Make API call with retry logic
                try:
                    response = await self._api_call_with_retry(messages)
                    
                    # Track conversation
                    self.conversation_history.append({
                        "turn": self.total_turns,
                        "response": response.model_dump() if hasattr(response, 'model_dump') else str(response)
                    })
                    
                    # Track usage and costs with actual input/output tokens
                    if hasattr(response, 'usage'):
                        turn_input = response.usage.input_tokens
                        turn_output = response.usage.output_tokens
                        self.total_input_tokens += turn_input
                        self.total_output_tokens += turn_output
                        self.tokens_used = self.total_input_tokens + self.total_output_tokens
                        self.estimated_cost_usd = self._calculate_cost()
                        
                        # Log turn-level token usage for visibility
                        self.logger.info(
                            f"[{self.agent_name}] Turn {self.total_turns} tokens: "
                            f"in={turn_input:,}, out={turn_output:,}, "
                            f"cumulative={self.tokens_used:,} (${self.estimated_cost_usd:.4f})"
                        )
                    
                    # Track tool usage from response (server-side execution)
                    self._track_tool_usage(response.content)
                    
                    # Add assistant response to conversation
                    messages.append({"role": "assistant", "content": response.content})
                    
                    # Check stop reason
                    if response.stop_reason == "end_turn":
                        # Extract final response
                        final_response = self._extract_text_content(response.content)
                        completion_status = 'complete'
                        self.logger.info(
                            f"[{self.agent_name}] Research complete after {self.total_turns} turns"
                        )
                        break
                    
                    # Handle pause_turn (extended thinking)
                    elif response.stop_reason == "pause_turn":
                        self.logger.info(
                            f"[{self.agent_name}] Extended thinking pause - continuing conversation..."
                        )
                        # Add continuation prompt to resume the conversation
                        messages.append({
                            "role": "user", 
                            "content": "Please continue with your research and provide the complete analysis."
                        })
                        continue
                    
                    # Handle max_tokens (response truncated)
                    elif response.stop_reason == "max_tokens":
                        self.logger.warning(f"[{self.agent_name}] Response truncated at max_tokens")
                        messages.append({"role": "user", "content": "Please continue your response."})
                        continue
                    
                    else:
                        # Unexpected stop reason
                        self.logger.warning(
                            f"[{self.agent_name}] Unexpected stop_reason: {response.stop_reason}"
                        )
                        final_response = self._extract_text_content(response.content)
                        completion_status = 'complete'
                        break
                
                except anthropic.APIError as e:
                    # Unrecoverable API error after retries
                    self.logger.error(
                        f"[{self.agent_name}] Unrecoverable API error on turn {self.total_turns}: {e}"
                    )
                    # Save partial results
                    final_response = self._extract_final_content(messages)
                    completion_status = 'error'
                    break
            
            # End of conversation loop
            self.end_time = datetime.utcnow()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            if completion_status == 'max_turns':
                self.logger.warning(
                    f"[{self.agent_name}] Reached max_turns ({max_turns}) without completion"
                )
                # Extract whatever we have as final response
                if messages:
                    final_response = self._extract_final_content(messages)
            
            # Return results
            return {
                'deliverables': final_response or "Research incomplete",
                'conversation': self.conversation_history,
                'searches_performed': self.searches_performed,
                'total_turns': self.total_turns,
                'tokens_used': self.tokens_used,
                'estimated_cost_usd': self.estimated_cost_usd,
                'execution_time_seconds': execution_time,
                'completion_status': completion_status
            }
            
        except Exception as e:
            self.logger.error(f"[{self.agent_name}] Research session failed: {e}", exc_info=True)
            self.end_time = datetime.utcnow()
            
            return {
                'deliverables': None,
                'conversation': self.conversation_history,
                'searches_performed': self.searches_performed,
                'total_turns': self.total_turns,
                'tokens_used': self.tokens_used,
                'estimated_cost_usd': self.estimated_cost_usd,
                'execution_time_seconds': (
                    (self.end_time - self.start_time).total_seconds() 
                    if self.start_time and self.end_time else 0
                ),
                'completion_status': 'error',
                'error': str(e)
            }
    
    async def _api_call_with_retry(
        self, 
        messages: List[Dict[str, Any]], 
        max_retries: int = 3
    ) -> Any:
        """
        Make API call with exponential backoff retry logic.
        
        Args:
            messages: Conversation messages
            max_retries: Maximum number of retries
            
        Returns:
            API response
            
        Raises:
            anthropic.APIError: If all retries exhausted
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages,
                    tools=[{
                        "type": "web_search_20250305",  # Correct server-side tool
                        "name": "web_search",
                        "max_uses": self.max_searches
                    }]
                )
                return response
                
            except anthropic.RateLimitError as e:
                if attempt < max_retries - 1:
                    # Get retry-after header or use exponential backoff
                    retry_after = int(e.response.headers.get('retry-after', 2 ** attempt * 5))
                    self.logger.warning(
                        f"[{self.agent_name}] Rate limited. Retrying after {retry_after}s"
                    )
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    raise
            
            except anthropic.APIConnectionError as e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt * 5  # Exponential backoff: 5s, 10s, 20s
                    self.logger.warning(
                        f"[{self.agent_name}] Connection error. Retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            
            except anthropic.APIError as e:
                # Other API errors - don't retry
                self.logger.error(f"[{self.agent_name}] API error: {e}")
                raise
    
    def _track_tool_usage(self, content: List[Any]):
        """
        Track tool usage from server-side execution.
        
        With server-side tools, Claude's response includes:
        - server_tool_use blocks (queries)
        - web_search_tool_result blocks (results)
        
        We just count the searches, we don't inject results.
        """
        for block in content:
            if hasattr(block, 'type') and block.type == "server_tool_use":
                if hasattr(block, 'name') and block.name == "web_search":
                    self.searches_performed += 1
                    query = block.input.get('query', 'N/A') if hasattr(block, 'input') else 'N/A'
                    self.logger.info(
                        f"[{self.agent_name}] Search {self.searches_performed}: {query}"
                    )
    
    def _extract_text_content(self, content: List[Any]) -> str:
        """Extract text content from response blocks."""
        text_parts = []
        for block in content:
            if hasattr(block, 'type') and block.type == "text":
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
        return "\n\n".join(text_parts)
    
    def _extract_final_content(self, messages: List[Dict[str, Any]]) -> str:
        """Extract final content from conversation messages."""
        # Look for last assistant message with text content
        for message in reversed(messages):
            if message["role"] == "assistant":
                content = message.get("content", [])
                if isinstance(content, list):
                    text = self._extract_text_content(content)
                    if text:
                        return text
                elif isinstance(content, str):
                    return content
        return ""
    
    def _calculate_cost(self) -> float:
        """
        Calculate actual cost based on tracked token counts and model-specific pricing.

        Uses Models.get_pricing() to retrieve current pricing for the model being used.
        Returns exact cost based on actual input/output token usage.
        """
        input_price, output_price = Models.get_pricing(self.model)
        input_cost = (self.total_input_tokens / 1_000_000) * input_price
        output_cost = (self.total_output_tokens / 1_000_000) * output_price

        return input_cost + output_cost
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session execution summary."""
        return {
            'agent_name': self.agent_name,
            'searches_performed': self.searches_performed,
            'total_turns': self.total_turns,
            'tokens_used': self.tokens_used,
            'estimated_cost_usd': self.estimated_cost_usd,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time_seconds': (
                (self.end_time - self.start_time).total_seconds() 
                if self.start_time and self.end_time else None
            )
        }
