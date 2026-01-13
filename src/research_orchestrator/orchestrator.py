# research_orchestrator/orchestrator.py
"""
ResearchOrchestrator - Main coordination logic for multi-layer research execution.

Manages parallel execution within layers and handles human review gates between layers.
"""

import anthropic
from anthropic import AsyncAnthropic
import asyncio
import os
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .research_session import ResearchSession
from .state.tracker import StateTracker
from .utils.logging_setup import setup_logging
from .utils.config import load_config, get_priority_combinations
from .utils.config_models import (
    get_model_for_agent,
    get_model_config,
    get_search_budget_for_model,
    estimate_research_cost
)
from .prompts.horizontal import (
    BUYER_JOURNEY_PROMPT,
    CHANNELS_COMPETITIVE_PROMPT,
    CUSTOMER_EXPANSION_PROMPT,
    MESSAGING_POSITIONING_PROMPT,
    GTM_SYNTHESIS_PROMPT,
    get_context_section
)


class BudgetExceededError(Exception):
    """Raised when cost or search budget is exceeded."""
    pass


class ResearchOrchestrator:
    """
    Coordinates multi-layer research execution.
    Manages parallel execution within layers.
    Handles human review gates between layers.
    """
    
    def __init__(
        self, 
        config_path: Path,
        execution_id: Optional[str] = None
    ):
        """
        Initialize research orchestrator.
        
        Args:
            config_path: Path to configuration YAML file
            execution_id: Optional execution ID for resume
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Set up logging
        log_config = self.config['execution_settings']['logging']
        self.logger = setup_logging(
            log_dir=Path(log_config['directory']),
            level=log_config['level'],
            console_output=log_config['console_output']
        )
        
        self.logger.info("=" * 80)
        self.logger.info("Research Orchestrator Initialized")
        self.logger.info("=" * 80)
        
        # Initialize Anthropic async client (CRITICAL: must be async for parallel execution)
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Generate unique execution correlation ID for structured logging
        self.execution_correlation_id = str(uuid.uuid4())
        
        # Budget tracking
        budget_config = self.config['execution_settings'].get('budget', {})
        self.budget = {
            'max_total_searches': budget_config.get('max_searches', 500),
            'max_total_cost_usd': budget_config.get('max_cost_usd', 200.0),
            'current_searches': 0,
            'current_cost_usd': 0.0
        }
        
        # API settings
        api_config = self.config['execution_settings']['api']
        self.model = api_config['model']
        self.max_tokens = api_config['max_tokens']
        
        # Initialize state tracker
        checkpoint_config = self.config['execution_settings']['checkpointing']
        self.state = StateTracker(
            checkpoint_dir=Path(checkpoint_config['directory']),
            execution_id=execution_id or self.config['execution']['id'],
            logger=self.logger
        )
        
        # Initialize layers in state
        self.state.initialize_layer_2(self.config['verticals'])
        self.state.initialize_layer_3(self.config['title_clusters'])
        
        # Priority combinations for integration
        combinations = get_priority_combinations(self.config)
        self.state.initialize_integrations(combinations)
        
        # Output directory
        self.output_dir = Path(self.config['execution_settings']['outputs']['directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create layer output directories
        for layer in ['layer_1', 'layer_2', 'layer_3', 'playbooks']:
            (self.output_dir / layer).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Configuration loaded: {config_path}")
        self.logger.info(f"Execution ID: {self.state.execution_id}")
        self.logger.info(f"Checkpoint file: {self.state.checkpoint_file}")
    
    async def execute_full_research(self):
        """
        Execute complete three-layer research program.
        Includes human review gates between layers.
        """
        try:
            self.logger.info("Starting full research program")
            
            # Layer 1: Horizontal Research
            self.logger.info("\n" + "=" * 80)
            self.logger.info("LAYER 1: Horizontal Research")
            self.logger.info("=" * 80)
            await self.execute_layer_1_parallel()
            
            # Human review gate
            if self.config['execution_settings']['review_gates']['after_layer_1']:
                if not self._prompt_for_review("Layer 1"):
                    self.logger.info("Research halted by user after Layer 1")
                    return
            
            # Layer 2: Vertical Research
            self.logger.info("\n" + "=" * 80)
            self.logger.info("LAYER 2: Vertical Research")
            self.logger.info("=" * 80)
            await self.execute_layer_2_parallel()
            
            # Human review gate
            if self.config['execution_settings']['review_gates']['after_layer_2']:
                if not self._prompt_for_review("Layer 2"):
                    self.logger.info("Research halted by user after Layer 2")
                    return
            
            # Layer 3: Title Research
            self.logger.info("\n" + "=" * 80)
            self.logger.info("LAYER 3: Title Research")
            self.logger.info("=" * 80)
            await self.execute_layer_3_parallel()
            
            # Human review gate (optional)
            if self.config['execution_settings']['review_gates'].get('after_layer_3', False):
                if not self._prompt_for_review("Layer 3"):
                    self.logger.info("Research halted by user after Layer 3")
                    return
            
            # Integration: Generate Playbooks
            self.logger.info("\n" + "=" * 80)
            self.logger.info("INTEGRATION: Generating Playbooks")
            self.logger.info("=" * 80)
            await self.generate_playbooks_parallel()
            
            # Final summary
            self.logger.info("\n" + "=" * 80)
            self.logger.info("RESEARCH PROGRAM COMPLETE")
            self.logger.info("=" * 80)
            self._print_execution_summary()
            
        except Exception as e:
            self.logger.error(f"Research program failed: {e}", exc_info=True)
            raise
    
    async def execute_layer_1_parallel(self):
        """
        Execute 5 horizontal agents with proper dependency management.
        
        Phase 1: buyer_journey, channels_competitive, customer_expansion (parallel)
        Phase 2: messaging_positioning (depends on Phase 1)
        Phase 3: gtm_synthesis (depends on all prior)
        """
        self.logger.info("Executing Layer 1: Horizontal Research")
        
        # Phase 1: Independent agents (parallel)
        phase_1_agents = ['buyer_journey', 'channels_competitive', 'customer_expansion']
        
        self.logger.info(f"Phase 1: Launching {len(phase_1_agents)} independent agents in parallel")
        
        tasks = []
        for agent_name in phase_1_agents:
            if not self.state.is_agent_complete(agent_name):
                tasks.append(self._execute_agent(agent_name, layer='layer_1'))
            else:
                self.logger.info(f"Skipping {agent_name} (already complete)")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Phase 2: Messaging agent (depends on phase 1)
        self.logger.info("Phase 2: Executing messaging_positioning agent")
        
        if not self.state.is_agent_complete('messaging_positioning'):
            # Verify dependencies
            for dep in phase_1_agents:
                if not self.state.is_agent_complete(dep):
                    self.logger.error(f"Cannot execute messaging_positioning: {dep} not complete")
                    return
            
            await self._execute_agent('messaging_positioning', layer='layer_1')
        else:
            self.logger.info("Skipping messaging_positioning (already complete)")
        
        # Phase 3: GTM synthesis (depends on all prior)
        self.logger.info("Phase 3: Executing gtm_synthesis agent")
        
        if not self.state.is_agent_complete('gtm_synthesis'):
            # Verify dependencies
            all_deps = phase_1_agents + ['messaging_positioning']
            for dep in all_deps:
                if not self.state.is_agent_complete(dep):
                    self.logger.error(f"Cannot execute gtm_synthesis: {dep} not complete")
                    return
            
            await self._execute_agent('gtm_synthesis', layer='layer_1')
        else:
            self.logger.info("Skipping gtm_synthesis (already complete)")
        
        self.logger.info("Layer 1 complete!")
        self._print_layer_status('layer_1')
    
    async def execute_layer_2_parallel(self):
        """Execute all configured verticals in parallel."""
        self.logger.info("Executing Layer 2: Vertical Research")
        
        # Check if Layer 1 is complete
        if not self.state.is_layer_complete('layer_1'):
            self.logger.error("Cannot execute Layer 2: Layer 1 not complete")
            return
        
        verticals = self.config['verticals']
        self.logger.info(f"Launching {len(verticals)} vertical agents in parallel")
        
        tasks = []
        for vertical in verticals:
            agent_name = f"vertical_{vertical}"
            if not self.state.is_agent_complete(agent_name):
                tasks.append(self._execute_vertical_agent(vertical))
            else:
                self.logger.info(f"Skipping {vertical} (already complete)")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Layer 2 complete!")
        self._print_layer_status('layer_2')
    
    async def execute_layer_3_parallel(self):
        """Execute all configured title clusters in parallel."""
        self.logger.info("Executing Layer 3: Title Research")
        
        # Check if Layer 1 and 2 are complete
        if not self.state.is_layer_complete('layer_1'):
            self.logger.error("Cannot execute Layer 3: Layer 1 not complete")
            return
        
        if not self.state.is_layer_complete('layer_2'):
            self.logger.error("Cannot execute Layer 3: Layer 2 not complete")
            return
        
        title_clusters = self.config['title_clusters']
        self.logger.info(f"Launching {len(title_clusters)} title agents in parallel")
        
        tasks = []
        for title_cluster in title_clusters:
            agent_name = f"title_{title_cluster}"
            if not self.state.is_agent_complete(agent_name):
                tasks.append(self._execute_title_agent(title_cluster))
            else:
                self.logger.info(f"Skipping {title_cluster} (already complete)")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Layer 3 complete!")
        self._print_layer_status('layer_3')
    
    async def generate_playbooks_parallel(self):
        """Generate playbooks for priority vertical x title combinations."""
        self.logger.info("Generating integration playbooks")
        
        combinations = get_priority_combinations(self.config)
        self.logger.info(f"Generating {len(combinations)} playbooks in parallel")
        
        tasks = []
        for vertical, title in combinations:
            agent_name = f"playbook_{vertical}_{title}"
            if not self.state.is_agent_complete(agent_name):
                tasks.append(self._execute_playbook(vertical, title))
            else:
                self.logger.info(f"Skipping {vertical}_{title} playbook (already complete)")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Integration complete!")
        self._print_layer_status('integrations')
    
    async def _execute_agent(self, agent_name: str, layer: str = 'layer_1'):
        """
        Execute a single research agent with per-agent model selection.
        
        Args:
            agent_name: Name of the agent to execute
            layer: Layer identifier
        """
        try:
            self.logger.info(f"Starting agent: {agent_name}")
            self.state.mark_in_progress(agent_name, layer)
            
            # Resolve model for this specific agent
            model = get_model_for_agent(self.config, layer, agent_name)
            model_config = get_model_config(self.config, model)
            max_searches = get_search_budget_for_model(self.config, model)
            
            self.logger.info(
                f"[{agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}, "
                f"Max searches: {max_searches}"
            )
            
            # Get prompt for this agent
            prompt = self._get_agent_prompt(agent_name)
            
            # Get context from prior agents
            context = self.state.get_context_for_agent(agent_name)
            
            # Format prompt with context
            if context:
                context_text = get_context_section(context)
                prompt = prompt.format(context_section=context_text)
            else:
                prompt = prompt.format(context_section="")
            
            # Execute research session with resolved model settings
            session = ResearchSession(
                agent_name=agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )
            
            result = await session.execute_research(
                prompt=prompt,
                context=context,
                max_turns=50
            )
            
            # Save output
            output_path = self._save_agent_output(agent_name, layer, result)
            
            # Mark complete in state
            self.state.mark_complete(
                agent_name=agent_name,
                outputs={
                    'output_path': str(output_path),
                    'searches_performed': result['searches_performed'],
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer=layer
            )
            
            # Update budget tracking
            self.budget['current_searches'] += result['searches_performed']
            self.budget['current_cost_usd'] += result.get('estimated_cost_usd', 0.0)
            
            self.logger.info(f"Completed agent: {agent_name}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")
            
            # Check budget limits
            if self.budget['current_searches'] >= self.budget['max_total_searches']:
                self.logger.error("SEARCH BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Search budget exceeded: {self.budget['current_searches']}/{self.budget['max_total_searches']}"
                )
            
            if self.budget['current_cost_usd'] >= self.budget['max_total_cost_usd']:
                self.logger.error("COST BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Cost budget exceeded: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}"
                )
            
        except BudgetExceededError:
            # Re-raise budget errors without marking as failed
            raise
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer=layer)
            raise
    
    async def _execute_vertical_agent(self, vertical: str):
        """
        Execute a vertical research agent (Layer 2).
        
        Args:
            vertical: Vertical industry identifier (e.g., 'healthcare', 'financial_services')
        """
        from .prompts import build_vertical_prompt, get_layer_1_context
        
        agent_name = f"vertical_{vertical}"
        
        try:
            self.logger.info(f"Starting vertical agent: {vertical}")
            self.state.mark_in_progress(agent_name, 'layer_2')
            
            # Verify Layer 1 dependencies
            if not self.state.can_execute_layer_2(vertical):
                self.logger.error(f"Cannot execute {vertical}: Layer 1 not complete")
                return
            
            # Extract Layer 1 context
            layer_1_context = get_layer_1_context(self.state)
            
            # Build vertical-specific prompt
            prompt = build_vertical_prompt(vertical, layer_1_context)
            
            # Resolve model for this vertical agent
            model = get_model_for_agent(self.config, 'layer_2', agent_name)
            model_config = get_model_config(self.config, model)
            max_searches = get_search_budget_for_model(self.config, model)
            
            self.logger.info(
                f"[{agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}, "
                f"Max searches: {max_searches}"
            )
            
            # Execute research session
            session = ResearchSession(
                agent_name=agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )
            
            result = await session.execute_research(
                prompt=prompt,
                context=layer_1_context,
                max_turns=50
            )
            
            # Save output
            output_path = self._save_agent_output(agent_name, 'layer_2', result)
            
            # Mark complete in state
            self.state.mark_complete(
                agent_name=agent_name,
                outputs={
                    'output_path': str(output_path),
                    'searches_performed': result['searches_performed'],
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='layer_2'
            )
            
            # Update budget tracking
            self.budget['current_searches'] += result['searches_performed']
            self.budget['current_cost_usd'] += result.get('estimated_cost_usd', 0.0)
            
            self.logger.info(f"Completed vertical agent: {vertical}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            
            # Check budget limits
            if self.budget['current_searches'] >= self.budget['max_total_searches']:
                self.logger.error("SEARCH BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Search budget exceeded: {self.budget['current_searches']}/{self.budget['max_total_searches']}"
                )
            
            if self.budget['current_cost_usd'] >= self.budget['max_total_cost_usd']:
                self.logger.error("COST BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Cost budget exceeded: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}"
                )
            
        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Vertical agent {vertical} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='layer_2')
            raise
    
    async def _execute_title_agent(self, title_cluster: str):
        """
        Execute a title research agent (Layer 3).
        
        Args:
            title_cluster: Title cluster identifier (e.g., 'cfo_cluster', 'cio_cto_cluster')
        """
        from .prompts import build_title_prompt, get_layer_1_context, get_layer_2_context
        
        agent_name = f"title_{title_cluster}"
        
        try:
            self.logger.info(f"Starting title agent: {title_cluster}")
            self.state.mark_in_progress(agent_name, 'layer_3')
            
            # Verify Layer 1 and 2 dependencies
            if not self.state.can_execute_layer_3(title_cluster):
                self.logger.error(f"Cannot execute {title_cluster}: Layer 1 or 2 not complete")
                return
            
            # Extract Layer 1 and Layer 2 context
            layer_1_context = get_layer_1_context(self.state)
            layer_2_context = get_layer_2_context(self.state, self.config['verticals'])
            
            # Build title-specific prompt
            prompt = build_title_prompt(title_cluster, layer_1_context, layer_2_context)
            
            # Resolve model for this title agent
            model = get_model_for_agent(self.config, 'layer_3', agent_name)
            model_config = get_model_config(self.config, model)
            max_searches = get_search_budget_for_model(self.config, model)
            
            self.logger.info(
                f"[{agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}, "
                f"Max searches: {max_searches}"
            )
            
            # Execute research session
            session = ResearchSession(
                agent_name=agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )
            
            result = await session.execute_research(
                prompt=prompt,
                context={'layer_1': layer_1_context, 'layer_2': layer_2_context},
                max_turns=50
            )
            
            # Save output
            output_path = self._save_agent_output(agent_name, 'layer_3', result)
            
            # Mark complete in state
            self.state.mark_complete(
                agent_name=agent_name,
                outputs={
                    'output_path': str(output_path),
                    'searches_performed': result['searches_performed'],
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='layer_3'
            )
            
            # Update budget tracking
            self.budget['current_searches'] += result['searches_performed']
            self.budget['current_cost_usd'] += result.get('estimated_cost_usd', 0.0)
            
            self.logger.info(f"Completed title agent: {title_cluster}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            
            # Check budget limits
            if self.budget['current_searches'] >= self.budget['max_total_searches']:
                self.logger.error("SEARCH BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Search budget exceeded: {self.budget['current_searches']}/{self.budget['max_total_searches']}"
                )
            
            if self.budget['current_cost_usd'] >= self.budget['max_total_cost_usd']:
                self.logger.error("COST BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Cost budget exceeded: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}"
                )
            
        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Title agent {title_cluster} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='layer_3')
            raise
    
    async def _execute_playbook(self, vertical: str, title: str):
        """
        Generate a playbook for vertical × title combination.
        
        Args:
            vertical: Vertical identifier (e.g., 'healthcare')
            title: Title cluster identifier (e.g., 'cfo_cluster')
        """
        from .prompts import build_playbook_prompt, get_layer_1_context, get_layer_2_context, get_layer_3_context
        
        agent_name = f"playbook_{vertical}_{title}"
        
        try:
            self.logger.info(f"Starting playbook: {vertical} × {title}")
            self.state.mark_in_progress(agent_name, 'integrations')
            
            # Verify all layer dependencies
            if not self.state.is_layer_complete('layer_1'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 1 not complete")
                return
            
            if not self.state.is_layer_complete('layer_2'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 2 not complete")
                return
            
            if not self.state.is_layer_complete('layer_3'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 3 not complete")
                return
            
            # Extract context from all three layers
            layer_1_context = get_layer_1_context(self.state)
            layer_2_context = get_layer_2_context(self.state, self.config['verticals'])
            layer_3_context = get_layer_3_context(self.state, self.config['title_clusters'])
            
            # Build playbook prompt
            prompt = build_playbook_prompt(
                vertical, title,
                layer_1_context, layer_2_context, layer_3_context
            )
            
            # Resolve model for playbook
            model = get_model_for_agent(self.config, 'integrations', agent_name)
            model_config = get_model_config(self.config, model)
            max_searches = get_search_budget_for_model(self.config, model)
            
            self.logger.info(
                f"[{agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}, "
                f"Max searches: {max_searches}"
            )
            
            # Execute research session
            session = ResearchSession(
                agent_name=agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )
            
            result = await session.execute_research(
                prompt=prompt,
                context={
                    'layer_1': layer_1_context,
                    'layer_2': layer_2_context,
                    'layer_3': layer_3_context
                },
                max_turns=50
            )
            
            # Save output
            output_path = self._save_agent_output(agent_name, 'integrations', result)
            
            # Mark complete in state
            self.state.mark_complete(
                agent_name=agent_name,
                outputs={
                    'output_path': str(output_path),
                    'searches_performed': result['searches_performed'],
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='integrations'
            )
            
            # Update budget tracking
            self.budget['current_searches'] += result['searches_performed']
            self.budget['current_cost_usd'] += result.get('estimated_cost_usd', 0.0)
            
            self.logger.info(f"Completed playbook: {vertical} × {title}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            
            # Check budget limits
            if self.budget['current_searches'] >= self.budget['max_total_searches']:
                self.logger.error("SEARCH BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Search budget exceeded: {self.budget['current_searches']}/{self.budget['max_total_searches']}"
                )
            
            if self.budget['current_cost_usd'] >= self.budget['max_total_cost_usd']:
                self.logger.error("COST BUDGET EXCEEDED - halting execution")
                raise BudgetExceededError(
                    f"Cost budget exceeded: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}"
                )
            
        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Playbook {vertical}_{title} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='integrations')
            raise
    
    def _get_agent_prompt(self, agent_name: str) -> str:
        """Get prompt template for agent."""
        prompt_map = {
            'buyer_journey': BUYER_JOURNEY_PROMPT,
            'channels_competitive': CHANNELS_COMPETITIVE_PROMPT,
            'customer_expansion': CUSTOMER_EXPANSION_PROMPT,
            'messaging_positioning': MESSAGING_POSITIONING_PROMPT,
            'gtm_synthesis': GTM_SYNTHESIS_PROMPT
        }
        
        if agent_name not in prompt_map:
            raise ValueError(f"No prompt defined for agent: {agent_name}")
        
        return prompt_map[agent_name]
    
    def _save_agent_output(self, agent_name: str, layer: str, result: Dict[str, Any]) -> Path:
        """Save agent output to markdown file."""
        # Determine output directory
        if layer == 'layer_1':
            output_dir = self.output_dir / 'layer_1'
        elif layer == 'layer_2':
            output_dir = self.output_dir / 'layer_2'
        elif layer == 'layer_3':
            output_dir = self.output_dir / 'layer_3'
        elif layer == 'integrations':
            output_dir = self.output_dir / 'playbooks'
        else:
            output_dir = self.output_dir / layer
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output file
        output_file = output_dir / f"{agent_name}.md"
        
        # Write deliverables (handle None case)
        deliverables = result.get('deliverables')
        if deliverables is None:
            deliverables = f"# {agent_name} - Research Failed\n\nResearch execution failed. Check logs for details.\n\nError: {result.get('error', 'Unknown error')}"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(deliverables)
        
        self.logger.info(f"Output saved: {output_file}")
        
        return output_file
    
    def _prompt_for_review(self, layer_name: str) -> bool:
        """Prompt user for review and approval to proceed."""
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"{layer_name} Complete - Human Review Gate")
        self.logger.info("=" * 80)
        
        # Show output directory
        if layer_name == "Layer 1":
            output_dir = self.output_dir / 'layer_1'
        elif layer_name == "Layer 2":
            output_dir = self.output_dir / 'layer_2'
        elif layer_name == "Layer 3":
            output_dir = self.output_dir / 'layer_3'
        else:
            output_dir = self.output_dir
        
        self.logger.info(f"Review outputs in: {output_dir}")
        self.logger.info("")
        
        # Prompt for continuation
        response = input(f"Review complete. Continue to next layer? (y/n): ").strip().lower()
        
        return response == 'y'
    
    def _print_layer_status(self, layer: str):
        """Print status summary for a layer."""
        status = self.state.get_layer_status(layer)
        self.logger.info(f"\n{layer.upper()} Status:")
        self.logger.info(f"  Total: {status['total']}")
        self.logger.info(f"  Complete: {status['complete']}")
        self.logger.info(f"  In Progress: {status['in_progress']}")
        self.logger.info(f"  Pending: {status['pending']}")
        self.logger.info(f"  Failed: {status['failed']}")
    
    def _print_execution_summary(self):
        """Print overall execution summary."""
        summary = self.state.get_execution_summary()
        
        self.logger.info("Execution Summary:")
        self.logger.info(f"  Execution ID: {summary['execution_id']}")
        self.logger.info(f"  Started: {summary['started_at']}")
        self.logger.info(f"  Completed: {summary['last_updated']}")
        self.logger.info("")
        self.logger.info("Layer Status:")
        
        for layer_name in ['layer_1_status', 'layer_2_status', 'layer_3_status', 'integration_status']:
            status = summary[layer_name]
            layer_label = layer_name.replace('_status', '').replace('_', ' ').title()
            self.logger.info(f"  {layer_label}: {status['complete']}/{status['total']} complete")
        
        self.logger.info(f"\nOutputs directory: {self.output_dir}")
        self.logger.info(f"Checkpoint file: {summary['checkpoint_file']}")
