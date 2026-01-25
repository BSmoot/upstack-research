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
        thinking_budget: int = 10000,
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
            thinking_budget: Maximum tokens for extended thinking (default: 10000)
            logger: Optional logger instance
        """
        self.agent_name = agent_name
        self.client = anthropic_client
        self.model = model
        self.max_tokens = max_tokens
        self.max_searches = max_searches
        self.thinking_budget = thinking_budget
        self.logger = logger or logging.getLogger(__name__)

        # Conversation tracking
        self.conversation_history: List[Dict[str, Any]] = []
        self.searches_performed = 0
        self.total_turns = 0
        self.tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_thinking_tokens = 0
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
            accumulated_text: List[str] = []  # Collect text across all turns
            
            for turn in range(max_turns):
                self.total_turns = turn + 1
                self.logger.info(f"[{self.agent_name}] Turn {self.total_turns}/{max_turns}")
                
                # Check search budget
                if self.searches_performed >= self.max_searches:
                    self.logger.warning(
                        f"[{self.agent_name}] Search budget exceeded ({self.max_searches} searches)"
                    )
                    completion_status = 'budget_exceeded'
                    final_response = self._join_accumulated_text(accumulated_text) if accumulated_text else self._extract_final_content(messages)
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
                        turn_thinking = getattr(response.usage, 'thinking_tokens', 0)

                        self.total_input_tokens += turn_input
                        self.total_output_tokens += turn_output
                        self.total_thinking_tokens += turn_thinking
                        self.tokens_used = self.total_input_tokens + self.total_output_tokens + self.total_thinking_tokens
                        self.estimated_cost_usd = self._calculate_cost()

                        # Log turn-level token usage for visibility
                        if turn_thinking > 0:
                            self.logger.info(
                                f"[{self.agent_name}] Turn {self.total_turns} tokens: "
                                f"in={turn_input:,}, out={turn_output:,}, thinking={turn_thinking:,}, "
                                f"cumulative={self.tokens_used:,} (${self.estimated_cost_usd:.4f})"
                            )
                        else:
                            self.logger.info(
                                f"[{self.agent_name}] Turn {self.total_turns} tokens: "
                                f"in={turn_input:,}, out={turn_output:,}, "
                                f"cumulative={self.tokens_used:,} (${self.estimated_cost_usd:.4f})"
                            )
                    
                    # Track tool usage from response (server-side execution)
                    self._track_tool_usage(response.content)

                    # Accumulate text content from every turn
                    turn_text = self._extract_text_content(response.content)
                    if turn_text:
                        accumulated_text.append(turn_text)

                    # Add assistant response to conversation (filter empty text blocks)
                    filtered_content = [
                        block for block in response.content
                        if not (hasattr(block, 'type') and block.type == "text"
                                and hasattr(block, 'text') and not block.text.strip())
                    ]
                    messages.append({"role": "assistant", "content": filtered_content})

                    # Check stop reason
                    if response.stop_reason == "end_turn":
                        # Use all accumulated text as the final deliverable
                        final_response = self._join_accumulated_text(accumulated_text)
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
                        final_response = self._join_accumulated_text(accumulated_text) if accumulated_text else ""
                        completion_status = 'complete'
                        break
                
                except anthropic.APIError as e:
                    # Unrecoverable API error after retries
                    self.logger.error(
                        f"[{self.agent_name}] Unrecoverable API error on turn {self.total_turns}: {e}"
                    )
                    # Save partial results from accumulated text
                    final_response = self._join_accumulated_text(accumulated_text) if accumulated_text else self._extract_final_content(messages)
                    completion_status = 'error'
                    break
            
            # End of conversation loop
            self.end_time = datetime.utcnow()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            if completion_status == 'max_turns':
                self.logger.warning(
                    f"[{self.agent_name}] Reached max_turns ({max_turns}) without completion"
                )
                # Use accumulated text, fall back to extracting from messages
                if accumulated_text:
                    final_response = self._join_accumulated_text(accumulated_text)
                elif messages:
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
                # Prepare API call parameters
                api_params = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": messages,
                    "tools": [{
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": self.max_searches
                    }]
                }

                # Add extended thinking if budget is configured
                if self.thinking_budget > 0:
                    api_params["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_budget
                    }

                # Use streaming to handle long-running requests (required for Opus)
                async with self.client.messages.stream(**api_params) as stream:
                    response = await stream.get_final_message()
                return response

            except ValueError as e:
                # Handle streaming requirement error (fallback shouldn't be needed now)
                if "streaming is required" in str(e).lower():
                    self.logger.warning(f"[{self.agent_name}] Streaming required - this should not happen")
                raise

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
            
            except TypeError as e:
                # SDK doesn't support thinking parameter - fall back without it
                if "thinking" in str(e) and self.thinking_budget > 0:
                    self.logger.warning(
                        f"[{self.agent_name}] SDK does not support extended thinking, retrying without it"
                    )
                    self.thinking_budget = 0  # Disable for future calls
                    continue
                raise

            except anthropic.APIError as e:
                # For API-level thinking errors, fall back without thinking
                if "thinking" in str(e).lower() and self.thinking_budget > 0:
                    self.logger.warning(
                        f"[{self.agent_name}] Extended thinking not supported by API, retrying without it"
                    )
                    self.thinking_budget = 0  # Disable for future calls
                    continue

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
        """
        Extract deliverable content from API response blocks.

        Strategy:
        1. Concatenate ALL text blocks (order preserved)
        2. Find document boundary (first # header or horizontal rule)
        3. Remove everything before boundary (reasoning preamble)
        4. Clean empty list items and excess whitespace
        5. If no boundary found, return all text (fallback for well-formed responses)

        Args:
            content: List of response blocks from Claude API

        Returns:
            Cleaned deliverable text, or empty string if no text found
        """
        import re

        # Step 1: Collect text blocks (skip thinking blocks)
        text_blocks = []
        has_thinking_blocks = False

        for block in content:
            if hasattr(block, 'type'):
                if block.type == "thinking":
                    has_thinking_blocks = True
                    # Skip thinking blocks - they're for internal reasoning only
                    continue
                elif block.type == "text":
                    if hasattr(block, 'text'):
                        text_blocks.append(block.text)

        if not text_blocks:
            return ""

        # Step 2: Concatenate into single document
        full_text = "\n".join(text_blocks)

        # Step 3: If we have thinking blocks, text should already be clean
        if has_thinking_blocks:
            # With extended thinking, only apply minimal cleanup
            cleaned_text = re.sub(r'^[-*]\s*$', '', full_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^\d+\.\s*$', '', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            cleaned_text = '\n'.join(line.rstrip() for line in cleaned_text.split('\n'))
            cleaned_text = cleaned_text.strip()

            self.logger.debug(
                f"[{self.agent_name}] Extracted text content with extended thinking"
            )
            return cleaned_text

        # Step 4: Legacy fallback - find document boundary for responses without thinking
        # Pattern 1: Markdown header (# Header)
        header_match = re.search(r'^#{1,6}\s+\w', full_text, re.MULTILINE)

        # Pattern 2: Horizontal rule at line start (---)
        hr_match = re.search(r'^---+\s*$', full_text, re.MULTILINE)

        # Determine boundary position (use earliest match)
        boundary_pos = None

        if header_match and hr_match:
            # Both found - use whichever comes first
            boundary_pos = min(header_match.start(), hr_match.start())
        elif header_match:
            boundary_pos = header_match.start()
        elif hr_match:
            boundary_pos = hr_match.start()

        # Step 5: Slice from boundary (or return all if no boundary)
        if boundary_pos is not None:
            # Found boundary - remove everything before it
            cleaned_text = full_text[boundary_pos:]

            # Log amount of content removed (detect significant preamble)
            removed_length = boundary_pos
            if removed_length > 200:
                self.logger.info(
                    f"[{self.agent_name}] Removed {removed_length} chars of reasoning preamble"
                )
        else:
            # No boundary found - assume entire response is deliverable
            cleaned_text = full_text
            self.logger.debug(
                f"[{self.agent_name}] No document boundary found, using all text"
            )

        # Step 6: Post-process cleanup
        # Remove empty bullet points (- \n or * \n)
        cleaned_text = re.sub(r'^[-*]\s*$', '', cleaned_text, flags=re.MULTILINE)

        # Remove empty numbered items (1. \n or 2. \n)
        cleaned_text = re.sub(r'^\d+\.\s*$', '', cleaned_text, flags=re.MULTILINE)

        # Collapse excessive newlines (3+ -> 2)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # Remove trailing whitespace from each line
        cleaned_text = '\n'.join(line.rstrip() for line in cleaned_text.split('\n'))

        # Remove leading/trailing whitespace from entire document
        cleaned_text = cleaned_text.strip()

        return cleaned_text

    def _join_accumulated_text(self, accumulated_text: List[str]) -> str:
        """
        Intelligently join multi-turn text fragments.

        Strategy:
        - If previous fragment ends incomplete (no period/punctuation)
          AND next fragment starts lowercase or continues mid-sentence,
          join with single space (continuation)
        - Otherwise, join with double newline (separate sections)

        Args:
            accumulated_text: List of text fragments from multiple turns

        Returns:
            Joined text with appropriate separators
        """
        if not accumulated_text:
            return ""

        if len(accumulated_text) == 1:
            return accumulated_text[0]

        # Join fragments intelligently
        result = []

        for i, fragment in enumerate(accumulated_text):
            if i == 0:
                result.append(fragment)
                continue

            prev_fragment = result[-1]

            # Check if previous fragment ends incomplete
            prev_ends_incomplete = (
                prev_fragment
                and prev_fragment[-1] not in '.!?\n'
                and not prev_fragment.endswith('**')  # Bold markers
            )

            # Check if current fragment starts as continuation
            current_starts_continuation = (
                fragment
                and (
                    fragment[0].islower()  # Lowercase start
                    or fragment[0] == ','  # Starts with comma
                    or fragment[:2] == '**'  # Starts with bold
                )
            )

            # Decide separator
            if prev_ends_incomplete and current_starts_continuation:
                # Continuation - join with space
                result.append(' ' + fragment)
                self.logger.debug(
                    f"[{self.agent_name}] Joined fragments {i-1} and {i} as continuation"
                )
            else:
                # Separate section - join with double newline
                result.append('\n\n' + fragment)

        return ''.join(result)

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

        Note: Thinking tokens are billed at output token rates.
        """
        input_price, output_price = Models.get_pricing(self.model)
        input_cost = (self.total_input_tokens / 1_000_000) * input_price

        # Thinking tokens are billed at output rates
        output_and_thinking_tokens = self.total_output_tokens + self.total_thinking_tokens
        output_cost = (output_and_thinking_tokens / 1_000_000) * output_price

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
