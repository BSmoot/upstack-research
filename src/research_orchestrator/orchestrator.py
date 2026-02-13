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
from typing import Any
from datetime import datetime

from .research_session import ResearchSession
from .state.tracker import StateTracker
from .utils.logging_setup import setup_logging
from .utils.config import load_config, get_priority_combinations, get_priority_combinations_3d
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
    get_context_section,
    format_layer_1_prompt
)
from .prompts.context_helpers import get_layer_0_context
from .utils.brand_context import BrandContextLoader
from .utils.brand_assets import BrandAssetsLoader
from .utils.strategic_messaging import StrategicMessagingLoader
from .utils.target_context import TargetContextLoader
from .prompts.brand_alignment import build_brand_alignment_prompt
from .prompts.target_alignment import build_target_alignment_prompt
from .prompts.validation import build_validation_prompt


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
        execution_id: str | None = None,
        force_agents: list[str] | None = None
    ):
        """
        Initialize research orchestrator.

        Args:
            config_path: Path to configuration YAML file
            execution_id: Optional execution ID for resume
            force_agents: Optional list of agent names to force re-run (even if complete)
        """
        self.force_agents = force_agents or []
        # Store config path for later path resolution
        self.config_path = Path(config_path)
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
        
        # Initialize state tracker with timestamped execution ID
        checkpoint_config = self.config['execution_settings']['checkpointing']
        base_id = execution_id or self.config['execution']['id']
        self._run_timestamp = datetime.utcnow().strftime('%y%m%d_%H%M')
        timestamped_id = f"{base_id}_{self._run_timestamp}"
        self.state = StateTracker(
            checkpoint_dir=Path(checkpoint_config['directory']),
            execution_id=timestamped_id,
            logger=self.logger
        )
        
        # Initialize Layer 0 (service categories) if configured
        service_categories = self.config.get('service_categories', [])
        if service_categories:
            self.state.initialize_layer_0(service_categories)

        # Initialize layers in state
        self.state.initialize_layer_2(self.config['verticals'])
        self.state.initialize_layer_3(self.config['title_clusters'])
        
        # Priority combinations for integration
        combinations = get_priority_combinations(self.config)
        self.state.initialize_integrations(combinations)
        
        # Output directory (scoped to execution ID to prevent overwrites)
        base_output_dir = Path(self.config['execution_settings']['outputs']['directory'])
        self.output_dir = base_output_dir / self.state.execution_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create layer output directories
        for layer in ['layer_0', 'layer_1', 'layer_2', 'layer_3', 'playbooks', 'validation', 'brand_alignment', 'target_aligned']:
            (self.output_dir / layer).mkdir(parents=True, exist_ok=True)

        # Initialize brand context and assets loaders
        # Loaders are needed for EITHER company_context (early injection) OR brand_alignment (late pass)
        company_ctx_config = self.config.get('company_context', {})
        brand_config = self.config.get('brand_alignment', {})

        # Determine context_files: company_context takes priority, fallback to brand_alignment
        context_files = (
            company_ctx_config.get('context_files')
            or brand_config.get('context_files', {})
        )

        # Determine assets_file: company_context takes priority, fallback to brand_alignment
        assets_file = (
            company_ctx_config.get('assets_file')
            or brand_config.get('assets_file', '')
        )

        # Determine strategic_messaging_file: company_context only
        strategic_messaging_file = company_ctx_config.get('strategic_messaging_file', '')

        needs_loaders = (
            company_ctx_config.get('enabled', False)
            or brand_config.get('enabled', False)
        )

        if needs_loaders and context_files:
            config_dir = Path(config_path).parent
            self.brand_context_loader = BrandContextLoader(
                config_dir=config_dir,
                context_files=context_files,
                logger=self.logger
            )

            # Initialize brand assets loader (optional — degrades gracefully)
            if assets_file:
                self.brand_assets_loader = BrandAssetsLoader(
                    config_dir=config_dir,
                    file_path=assets_file,
                    logger=self.logger
                )
            else:
                self.brand_assets_loader = None

            # Initialize strategic messaging loader (optional — degrades gracefully)
            if strategic_messaging_file:
                self.strategic_messaging_loader = StrategicMessagingLoader(
                    config_dir=config_dir,
                    file_path=strategic_messaging_file,
                    logger=self.logger
                )
            else:
                self.strategic_messaging_loader = None
        else:
            self.brand_context_loader = None
            self.brand_assets_loader = None
            self.strategic_messaging_loader = None

        # Initialize target context loader if target alignment enabled
        target_config = self.config.get('target_alignment', {})
        if target_config.get('enabled', False):
            target_file = target_config.get('target_file', '')
            config_dir = Path(config_path).parent
            if target_file:
                self.target_context_loader = TargetContextLoader(
                    config_dir=config_dir,
                    file_path=target_file,
                    logger=self.logger
                )
            else:
                self.logger.warning("Target alignment enabled but no target_file configured")
                self.target_context_loader = None
        else:
            self.target_context_loader = None

        # Process force_agents: reset completed agents for re-run
        if self.force_agents:
            self._process_force_agents()

        self.logger.info(f"Configuration loaded: {config_path}")
        self.logger.info(f"Execution ID: {self.state.execution_id}")
        self.logger.info(f"Checkpoint file: {self.state.checkpoint_file}")
        if self.force_agents:
            self.logger.info(f"Force re-run agents: {', '.join(self.force_agents)}")

    def _process_force_agents(self) -> None:
        """
        Process force_agents list: reset completed agents for re-execution.

        For each agent in force_agents:
        1. Save checkpoint history
        2. Preserve prior output file
        3. Mark agent for rerun
        """
        if not self.force_agents:
            return

        self.logger.info(f"Processing {len(self.force_agents)} agents for force re-run")

        # Save checkpoint history before modifications
        self.state.save_checkpoint_history()

        for agent_name in self.force_agents:
            # Get agent output to find prior file path
            agent_output = self.state.get_agent_output(agent_name)

            if agent_output and 'output_path' in agent_output:
                # Preserve prior output file
                self._preserve_prior_output(agent_output['output_path'])

            # Mark agent for rerun (resets status to pending)
            self.state.mark_for_rerun(agent_name)

    def _preserve_prior_output(self, output_path: str) -> Path | None:
        """
        Preserve prior output file by renaming it with timestamp.

        Args:
            output_path: Path to the existing output file

        Returns:
            Path to the preserved file, or None if preservation failed
        """
        prior_path = Path(output_path)
        if not prior_path.exists():
            return None

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        preserved_name = f"{prior_path.stem}_prior_{timestamp}{prior_path.suffix}"
        preserved_path = prior_path.parent / preserved_name

        try:
            prior_path.rename(preserved_path)
            self.logger.info(f"Preserved prior output: {preserved_path}")
            return preserved_path
        except Exception as e:
            self.logger.error(f"Failed to preserve prior output {output_path}: {e}")
            return None

    def _update_budget(self, searches: int, cost: float) -> None:
        """
        Update budget tracking with new usage.

        Args:
            searches: Number of searches performed
            cost: Estimated cost in USD
        """
        self.budget['current_searches'] += searches
        self.budget['current_cost_usd'] += cost

    def _check_budget_limits(self) -> None:
        """
        Check if budget limits exceeded and raise BudgetExceededError if so.

        Raises:
            BudgetExceededError: If search count or cost exceeds configured limits
        """
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

    def _check_gather_results(self, results: list[Any]) -> None:
        """
        Check asyncio.gather() results for BudgetExceededError and propagate.

        Args:
            results: List of results from asyncio.gather(..., return_exceptions=True)

        Raises:
            BudgetExceededError: If any result is a BudgetExceededError

        Notes:
            - Other exception types remain captured (handled by mark_failed in agent methods)
            - Logs which agent(s) exceeded budget before raising
        """
        budget_errors = []

        for idx, result in enumerate(results):
            if isinstance(result, BudgetExceededError):
                budget_errors.append((idx, result))

        if budget_errors:
            # Log all budget errors found
            for idx, error in budget_errors:
                self.logger.error(f"Task {idx} exceeded budget: {error}")

            # Re-raise the first budget error to halt execution
            raise budget_errors[0][1]

    async def execute_full_research(self):
        """
        Execute complete three-layer research program.
        Includes human review gates between layers.
        """
        try:
            self.logger.info("Starting full research program")

            # Layer 0: Service Category Research (optional - if configured)
            service_categories = self.config.get('service_categories', [])
            if service_categories:
                self.logger.info("\n" + "=" * 80)
                self.logger.info("LAYER 0: Service Category Research")
                self.logger.info("=" * 80)
                await self.execute_layer_0_parallel()

                # Human review gate (optional)
                if self.config['execution_settings']['review_gates'].get('after_layer_0', False):
                    if not self._prompt_for_review("Layer 0"):
                        self.logger.info("Research halted by user after Layer 0")
                        return

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

            # Validation: Quality gate (if enabled)
            validation_enabled = self.config['execution_settings'].get('validation', {}).get('enabled', True)
            if validation_enabled:
                # Human review gate before validation (optional)
                if self.config['execution_settings']['review_gates'].get('after_playbooks', False):
                    if not self._prompt_for_review("Playbooks"):
                        self.logger.info("Research halted by user after Playbooks")
                        return

                self.logger.info("\n" + "=" * 80)
                self.logger.info("VALIDATION: Quality Gate Assessment")
                self.logger.info("=" * 80)
                await self.execute_validation()

                # Human review gate after validation (optional)
                if self.config['execution_settings']['review_gates'].get('after_validation', False):
                    if not self._prompt_for_review("Validation"):
                        self.logger.info("Research halted by user after Validation")
                        return

            # Brand Alignment (if enabled)
            brand_config = self.config.get('brand_alignment', {})
            if brand_config.get('enabled', False):
                # Human review gate before brand alignment (optional)
                if brand_config.get('review_gates', {}).get('after_playbooks', False):
                    if not self._prompt_for_review("Playbooks"):
                        self.logger.info("Research halted by user after Playbooks")
                        return

                self.logger.info("\n" + "=" * 80)
                self.logger.info("BRAND ALIGNMENT: Aligning Outputs")
                self.logger.info("=" * 80)
                await self.execute_brand_alignment()

            # Target Company Alignment (if configured)
            target_config = self.config.get('target_alignment', {})
            if target_config.get('enabled', False):
                self.logger.info("\n" + "=" * 80)
                self.logger.info("TARGET ALIGNMENT: Personalizing for Target Company")
                self.logger.info("=" * 80)
                await self.execute_target_alignment()

            # Final summary
            self.logger.info("\n" + "=" * 80)
            self.logger.info("RESEARCH PROGRAM COMPLETE")
            self.logger.info("=" * 80)
            self._print_execution_summary()
            
        except Exception as e:
            self.logger.error(f"Research program failed: {e}", exc_info=True)
            raise
    
    async def execute_layer_0_parallel(self):
        """
        Execute service category research agents in parallel.

        Layer 0 provides baseline market intelligence on service categories
        before horizontal research begins. This layer is optional and skipped
        if no service_categories are configured.
        """
        service_categories = self.config.get('service_categories', [])

        if not service_categories:
            self.logger.info("No service categories configured, skipping Layer 0")
            return

        self.logger.info("Executing Layer 0: Service Category Research")
        self.logger.info(f"Launching {len(service_categories)} service category agents in parallel")

        tasks = []
        for category in service_categories:
            agent_name = f"service_category_{category}"
            if not self.state.is_agent_complete(agent_name):
                tasks.append(self._execute_service_category_agent(category))
            else:
                self.logger.info(f"Skipping {category} (already complete)")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._check_gather_results(results)

        self.logger.info("Layer 0 complete!")
        self._print_layer_status('layer_0')

    async def _execute_service_category_agent(self, category: str):
        """
        Execute a single service category research agent (Layer 0).

        Args:
            category: Service category identifier (e.g., 'security', 'customer_experience')
        """
        from .prompts.service_category import build_service_category_prompt
        from .prompts.context_injector import ResearchContextInjector

        agent_name = f"service_category_{category}"

        try:
            self.logger.info(f"Starting service category agent: {category}")
            self.state.mark_in_progress(agent_name, 'layer_0')

            # Initialize context injector with baseline path from config
            context_files = self.config.get('company_context', {}).get('context_files', {})
            baseline_relative = context_files.get('baseline', 'context/baseline.yaml')
            baseline_path = (self.config_path.parent / baseline_relative).resolve()
            context_injector = ResearchContextInjector(baseline_path, self.logger)

            # Build service category-specific prompt
            prompt = build_service_category_prompt(category, context_injector)

            # Resolve model for this agent
            model = get_model_for_agent(self.config, 'layer_0', agent_name)
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
                context={'category': category},
                max_turns=50
            )

            # Check for errors
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Service category agent {category} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer='layer_0')
                return

            # Save output
            output_path = self._save_agent_output(agent_name, 'layer_0', result)

            # Mark complete
            self.state.mark_complete(
                agent_name=agent_name,
                outputs={
                    'output_path': str(output_path),
                    'searches_performed': result['searches_performed'],
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='layer_0'
            )

            # Update budget
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))
            self._check_budget_limits()

            self.logger.info(f"Completed service category agent: {category}")

        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Service category agent {category} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='layer_0')
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
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._check_gather_results(results)
        
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
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._check_gather_results(results)
        
        self.logger.info("Layer 2 complete!")
        self._print_layer_status('layer_2')
    
    async def _staggered_gather(self, coroutines: list, stagger_delay: float = 2.0):
        """
        Execute coroutines in parallel with staggered start times.

        Prevents rate limiting by adding delay between concurrent API calls.

        Args:
            coroutines: List of coroutine functions (not awaited yet)
            stagger_delay: Seconds between starting each coroutine

        Returns:
            List of results (same as asyncio.gather with return_exceptions=True)
        """
        async def delayed_start(coro_func, delay: float):
            """Wrap coroutine with initial delay."""
            if delay > 0:
                await asyncio.sleep(delay)
            return await coro_func

        # Create tasks with staggered delays
        tasks = []
        for i, coro in enumerate(coroutines):
            delay = i * stagger_delay
            tasks.append(delayed_start(coro, delay))

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _sequential_execute(self, coroutines: list, cooldown: float = 5.0):
        """
        Execute coroutines sequentially (one at a time) with cooldown between each.

        Prevents API overload by ensuring only one agent runs at a time.

        Args:
            coroutines: List of coroutine objects to execute
            cooldown: Seconds to wait between completing one and starting next

        Returns:
            List of results (or exceptions) matching asyncio.gather semantics
        """
        results = []
        for i, coro in enumerate(coroutines):
            if i > 0 and cooldown > 0:
                self.logger.info(f"Cooling down {cooldown}s before next agent...")
                await asyncio.sleep(cooldown)
            try:
                result = await coro
                results.append(result)
            except Exception as e:
                results.append(e)
        return results

    async def execute_layer_3_parallel(self):
        """Execute all configured title clusters sequentially to avoid API overload."""
        self.logger.info("Executing Layer 3: Title Research")

        # Check if Layer 1 and 2 are complete
        if not self.state.is_layer_complete('layer_1'):
            self.logger.error("Cannot execute Layer 3: Layer 1 not complete")
            return

        if not self.state.is_layer_complete('layer_2'):
            self.logger.error("Cannot execute Layer 3: Layer 2 not complete")
            return

        title_clusters = self.config['title_clusters']
        self.logger.info(f"Launching {len(title_clusters)} title agents sequentially")

        # Build list of coroutines (not executed yet)
        coroutines = []
        for title_cluster in title_clusters:
            agent_name = f"title_{title_cluster}"
            if not self.state.is_agent_complete(agent_name):
                coroutines.append(self._execute_title_agent(title_cluster))
            else:
                self.logger.info(f"Skipping {title_cluster} (already complete)")

        if coroutines:
            # Execute sequentially to prevent API overload (5s cooldown between agents)
            results = await self._sequential_execute(coroutines, cooldown=5.0)
            self._check_gather_results(results)

        self.logger.info("Layer 3 complete!")
        self._print_layer_status('layer_3')
    
    async def generate_playbooks_parallel(self):
        """Generate playbooks for priority vertical x title (and optionally service category) combinations."""
        self.logger.info("Generating integration playbooks")

        # Phase 1: Generate 2D playbooks (V × T)
        combinations_2d = get_priority_combinations(self.config)
        self.logger.info(f"Generating {len(combinations_2d)} 2D playbooks (V × T)")

        tasks_2d = []
        for vertical, title in combinations_2d:
            agent_name = f"playbook_{vertical}_{title}"
            if not self.state.is_agent_complete(agent_name):
                tasks_2d.append(self._execute_playbook(vertical, title))
            else:
                self.logger.info(f"Skipping {vertical}_{title} playbook (already complete)")

        if tasks_2d:
            # Execute sequentially to prevent API overload
            results = await self._sequential_execute(tasks_2d, cooldown=5.0)
            self._check_gather_results(results)

        # Phase 2: Generate 3D playbooks (V × T × SC) if priority_service_categories configured
        combinations_3d = get_priority_combinations_3d(self.config)
        if combinations_3d:
            self.logger.info(f"Generating {len(combinations_3d)} 3D playbooks (V × T × SC)")

            # Initialize 3D playbook tracking in state
            agent_names_3d = [
                f"playbook_{v}_{t}_{sc}"
                for v, t, sc in combinations_3d
            ]
            self.state.initialize_integrations_3d(agent_names_3d)

            tasks_3d = []
            for vertical, title, service_category in combinations_3d:
                agent_name = f"playbook_{vertical}_{title}_{service_category}"
                if not self.state.is_agent_complete(agent_name):
                    tasks_3d.append(self._execute_playbook_3d(vertical, title, service_category))
                else:
                    self.logger.info(f"Skipping {vertical}_{title}_{service_category} 3D playbook (already complete)")

            if tasks_3d:
                # Execute sequentially to prevent API overload
                results = await self._sequential_execute(tasks_3d, cooldown=5.0)
                self._check_gather_results(results)

        self.logger.info("Integration complete!")
        self._print_layer_status('integrations')

    async def execute_validation(self):
        """
        Execute validation agents for completed playbooks.

        Runs quality gate assessment on all completed playbooks, producing
        validation reports with scores and recommendations.
        """
        self.logger.info("Executing validation quality gate")

        # Get all completed playbooks
        integrations = self.state.state.get('integrations', {})
        playbooks_to_validate = []

        for agent_name, agent_data in integrations.items():
            if agent_data.get('status') == 'complete' and agent_name.startswith('playbook_'):
                playbooks_to_validate.append(agent_name)

        if not playbooks_to_validate:
            self.logger.warning("No playbooks found to validate")
            return

        self.logger.info(
            "Validating playbooks",
            extra={"playbook_count": len(playbooks_to_validate)}
        )

        # Initialize validation tracking
        validation_agent_names = [f"validate_{name}" for name in playbooks_to_validate]
        self.state.initialize_validation(validation_agent_names)

        # Execute validation agents in parallel
        tasks = []
        for playbook_name in playbooks_to_validate:
            validation_agent_name = f"validate_{playbook_name}"
            if not self.state.is_agent_complete(validation_agent_name):
                tasks.append(self._execute_validation_agent(playbook_name))
            else:
                self.logger.info(f"Skipping {playbook_name} validation (already complete)")

        if tasks:
            # Execute sequentially to prevent API overload
            results = await self._sequential_execute(tasks, cooldown=5.0)
            self._check_gather_results(results)

        self.logger.info("Validation complete!")
        self._print_layer_status('validation')

    async def _execute_validation_agent(self, playbook_name: str):
        """
        Execute validation for a single playbook.

        Args:
            playbook_name: Name of the playbook agent to validate
        """
        from .prompts.vertical import VERTICALS
        from .prompts.title import TITLE_CLUSTERS

        validation_agent_name = f"validate_{playbook_name}"

        try:
            self.logger.info(f"Starting validation: {playbook_name}")
            self.state.mark_in_progress(validation_agent_name, 'validation')

            # Load playbook output
            playbook_output = self.state.get_agent_output(playbook_name)
            if not playbook_output or 'output_path' not in playbook_output:
                self.logger.error(f"Cannot validate {playbook_name}: no output found")
                self.state.mark_failed(validation_agent_name, "No playbook output found", layer='validation')
                return

            playbook_path = Path(playbook_output['output_path'])
            if not playbook_path.exists():
                self.logger.error(f"Cannot validate {playbook_name}: file not found at {playbook_path}")
                self.state.mark_failed(validation_agent_name, f"File not found: {playbook_path}", layer='validation')
                return

            with open(playbook_path, 'r', encoding='utf-8') as f:
                playbook_content = f.read()

            # Parse playbook name to extract vertical, title, and optional service category
            # Format: playbook_{vertical}_{title} or playbook_{vertical}_{title}_{service_category}
            parts = playbook_name.replace('playbook_', '').split('_')

            # Handle various naming patterns
            vertical_key = parts[0] if parts else "unknown"
            title_key = parts[1] if len(parts) > 1 else "unknown"
            service_category_key = parts[2] if len(parts) > 2 else None

            # Get display names
            vertical_name = VERTICALS.get(vertical_key, {}).get('name', vertical_key)
            title_name = TITLE_CLUSTERS.get(title_key, {}).get('name', title_key)
            service_category_name = service_category_key

            # Build company context for brand alignment validation
            brand_context_str = self._build_company_context(
                vertical=vertical_key,
                service_category=service_category_key
            )

            # Build validation prompt
            prompt = build_validation_prompt(
                playbook_content=playbook_content,
                vertical_name=vertical_name,
                title_name=title_name,
                service_category_name=service_category_name,
                brand_context=brand_context_str
            )

            # Get validation model configuration (use haiku for fast validation)
            validation_config = self.config['execution_settings'].get('validation', {})
            model = validation_config.get('model', 'claude-haiku-4-5-20251001')
            model_config = get_model_config(self.config, model)
            max_searches = 1  # Validation doesn't need search

            self.logger.info(
                f"[{validation_agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}"
            )

            # Execute validation session
            session = ResearchSession(
                agent_name=validation_agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )

            result = await session.execute_research(
                prompt=prompt,
                context={'playbook_content': playbook_content},
                max_turns=5  # Validation should be quick
            )

            # Check if validation session ended in error
            if result.get('completion_status') == 'error':
                error_msg = f"Validation session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Validation {playbook_name} failed: {error_msg}")
                self.state.mark_failed(validation_agent_name, error_msg, layer='validation')
                return

            # Save validation report
            output_path = self._save_agent_output(validation_agent_name, 'validation', result)

            # Mark complete in state
            self.state.mark_complete(
                agent_name=validation_agent_name,
                outputs={
                    'output_path': str(output_path),
                    'playbook_validated': playbook_name,
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='validation'
            )

            # Update budget tracking (minimal cost for validation)
            self._update_budget(0, result.get('estimated_cost_usd', 0.0))

            self.logger.info(f"Completed validation: {playbook_name}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Output: {output_path}")

        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Validation {playbook_name} failed: {e}", exc_info=True)
            self.state.mark_failed(validation_agent_name, str(e), layer='validation')
            raise

    async def execute_brand_alignment(self):
        """Execute brand alignment for configured targets."""
        self.logger.info("Executing brand alignment")

        brand_config = self.config.get('brand_alignment', {})
        align_targets = brand_config.get('align_targets', ['playbooks'])

        # Determine which outputs to align
        agents_to_align = []

        if 'playbooks' in align_targets:
            # Align all completed playbooks
            integrations = self.state.state.get('integrations', {})
            for agent_name, agent_data in integrations.items():
                if agent_data.get('status') == 'complete' and agent_name.startswith('playbook_'):
                    agents_to_align.append(agent_name)

        if not agents_to_align:
            self.logger.warning("No outputs found to align")
            return

        self.logger.info(f"Aligning {len(agents_to_align)} outputs")

        # Initialize brand alignment tracking
        alignment_agent_names = [f"align_{name}" for name in agents_to_align]
        self.state.initialize_brand_alignment(alignment_agent_names)

        # Execute alignment agents in parallel
        tasks = []
        for agent_name in agents_to_align:
            alignment_agent_name = f"align_{agent_name}"
            if not self.state.is_agent_complete(alignment_agent_name):
                tasks.append(self._execute_alignment_agent(agent_name))
            else:
                self.logger.info(f"Skipping {agent_name} alignment (already complete)")

        if tasks:
            # Execute sequentially to prevent API overload
            results = await self._sequential_execute(tasks, cooldown=5.0)
            self._check_gather_results(results)

        self.logger.info("Brand alignment complete!")
        self._print_layer_status('brand_alignment')

    async def _execute_alignment_agent(self, original_agent_name: str):
        """
        Execute brand alignment for a single output.

        Args:
            original_agent_name: Name of the original agent whose output will be aligned
        """
        alignment_agent_name = f"align_{original_agent_name}"

        try:
            self.logger.info(f"Starting brand alignment: {original_agent_name}")
            self.state.mark_in_progress(alignment_agent_name, 'brand_alignment')

            # Load original output
            original_output = self.state.get_agent_output(original_agent_name)
            if not original_output or 'output_path' not in original_output:
                self.logger.error(f"Cannot align {original_agent_name}: no output found")
                return

            original_path = Path(original_output['output_path'])
            if not original_path.exists():
                self.logger.error(f"Cannot align {original_agent_name}: output file not found at {original_path}")
                return

            with open(original_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Load brand context
            if self.brand_context_loader is None:
                self.logger.error("Brand context loader not initialized")
                return

            brand_context_data = self.brand_context_loader.load_all()
            brand_context_formatted = self.brand_context_loader.format_for_prompt(brand_context_data)

            # Load filtered brand assets (if available)
            brand_assets_formatted = ""
            if self.brand_assets_loader is not None:
                # Parse playbook name to extract vertical, title, and optional service category
                # Format: playbook_{vertical}_{title} or playbook_{vertical}_{title}_{service_category}
                parts = original_agent_name.replace('playbook_', '').split('_')
                vertical_key = parts[0] if parts else None
                service_category_key = parts[2] if len(parts) > 2 else None

                assets_data = self.brand_assets_loader.load()
                if assets_data:
                    brand_assets_formatted = self.brand_assets_loader.format_for_prompt(
                        context=assets_data,
                        vertical=vertical_key,
                        service_category=service_category_key
                    )
                    self.logger.info(
                        f"[{alignment_agent_name}] Loaded brand assets "
                        f"(vertical={vertical_key}, service_category={service_category_key})"
                    )

            # Build alignment prompt
            prompt = build_brand_alignment_prompt(
                original_content=original_content,
                brand_context=brand_context_formatted,
                brand_assets=brand_assets_formatted
            )

            # Get brand alignment model configuration
            brand_config = self.config.get('brand_alignment', {})
            model = brand_config.get('model', 'claude-sonnet-4-5-20250929')
            model_config = get_model_config(self.config, model)
            # Set max_searches=1 to allow API call (model won't use search for alignment)
            # Note: max_searches=0 causes immediate exit before any API call
            max_searches = 1

            self.logger.info(
                f"[{alignment_agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}"
            )

            # Execute alignment session (no search tools needed)
            session = ResearchSession(
                agent_name=alignment_agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )

            result = await session.execute_research(
                prompt=prompt,
                context={'original_content': original_content},
                max_turns=5  # Alignment should be quick
            )

            # Check if alignment session ended in error
            if result.get('completion_status') == 'error':
                error_msg = f"Alignment session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Alignment {original_agent_name} failed: {error_msg}")
                self.state.mark_failed(alignment_agent_name, error_msg, layer='brand_alignment')
                return

            # Save aligned output
            output_path = self._save_agent_output(alignment_agent_name, 'brand_alignment', result)

            # Mark complete in state
            self.state.mark_complete(
                agent_name=alignment_agent_name,
                outputs={
                    'output_path': str(output_path),
                    'original_agent': original_agent_name,
                    'original_path': str(original_path),
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='brand_alignment'
            )

            # Update budget tracking (minimal cost for alignment)
            self._update_budget(0, result.get('estimated_cost_usd', 0.0))

            self.logger.info(f"Completed brand alignment: {original_agent_name}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")

        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Brand alignment {original_agent_name} failed: {e}", exc_info=True)
            self.state.mark_failed(alignment_agent_name, str(e), layer='brand_alignment')
            raise

    async def execute_target_alignment(self):
        """Execute target company alignment for configured outputs."""
        self.logger.info("Executing target company alignment")

        target_config = self.config.get('target_alignment', {})
        align_targets = target_config.get('align_targets', ['brand_alignment'])

        if self.target_context_loader is None:
            self.logger.error("Target context loader not initialized")
            return

        # Determine which outputs to personalize
        agents_to_align = []

        if 'brand_alignment' in align_targets:
            # Align brand-aligned outputs
            brand_alignment_data = self.state.state.get('brand_alignment', {})
            for agent_name, agent_data in brand_alignment_data.items():
                if agent_data.get('status') == 'complete' and agent_name.startswith('align_'):
                    agents_to_align.append(agent_name)

        if 'playbooks' in align_targets and not agents_to_align:
            # Fall back to raw playbooks if no brand-aligned outputs
            integrations = self.state.state.get('integrations', {})
            for agent_name, agent_data in integrations.items():
                if agent_data.get('status') == 'complete' and agent_name.startswith('playbook_'):
                    agents_to_align.append(agent_name)

        if not agents_to_align:
            self.logger.warning("No outputs found for target alignment")
            return

        self.logger.info(f"Target-aligning {len(agents_to_align)} outputs")

        # Initialize target alignment tracking
        target_agent_names = [f"target_{name}" for name in agents_to_align]
        self.state.initialize_target_alignment(target_agent_names)

        # Execute target alignment agents in parallel
        tasks = []
        for agent_name in agents_to_align:
            target_agent_name = f"target_{agent_name}"
            if not self.state.is_agent_complete(target_agent_name):
                tasks.append(self._execute_target_alignment_agent(agent_name))
            else:
                self.logger.info(f"Skipping {agent_name} target alignment (already complete)")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self._check_gather_results(results)

        self.logger.info("Target alignment complete!")
        self._print_layer_status('target_alignment')

    async def _execute_target_alignment_agent(self, source_agent_name: str):
        """
        Execute target alignment for a single output.

        Args:
            source_agent_name: Name of the source agent whose output will be personalized
                (either an align_* agent or a playbook_* agent)
        """
        target_agent_name = f"target_{source_agent_name}"

        try:
            self.logger.info(f"Starting target alignment: {source_agent_name}")
            self.state.mark_in_progress(target_agent_name, 'target_alignment')

            # Load source output
            source_output = self.state.get_agent_output(source_agent_name)
            if not source_output or 'output_path' not in source_output:
                self.logger.error(f"Cannot target-align {source_agent_name}: no output found")
                self.state.mark_failed(
                    target_agent_name, "No source output found", layer='target_alignment'
                )
                return

            source_path = Path(source_output['output_path'])
            if not source_path.exists():
                self.logger.error(
                    f"Cannot target-align {source_agent_name}: "
                    f"output file not found at {source_path}"
                )
                self.state.mark_failed(
                    target_agent_name,
                    f"File not found: {source_path}",
                    layer='target_alignment'
                )
                return

            with open(source_path, 'r', encoding='utf-8') as f:
                enriched_content = f.read()

            # Load target context
            if self.target_context_loader is None:
                self.logger.error("Target context loader not initialized")
                self.state.mark_failed(
                    target_agent_name, "Target context loader not initialized",
                    layer='target_alignment'
                )
                return

            target_data = self.target_context_loader.load()
            if not target_data:
                self.logger.error("Target context is empty — skipping target alignment")
                self.state.mark_failed(
                    target_agent_name, "Empty target context", layer='target_alignment'
                )
                return

            target_context_formatted = self.target_context_loader.format_for_prompt(target_data)

            # Build target alignment prompt
            prompt = build_target_alignment_prompt(
                enriched_content=enriched_content,
                target_context=target_context_formatted
            )

            # Get target alignment model configuration
            target_config = self.config.get('target_alignment', {})
            model = target_config.get('model', 'claude-sonnet-4-5-20250929')
            model_config = get_model_config(self.config, model)
            max_searches = 1

            self.logger.info(
                f"[{target_agent_name}] Model: {model}, "
                f"Max tokens: {model_config.get('max_tokens', self.max_tokens)}"
            )

            # Execute target alignment session
            session = ResearchSession(
                agent_name=target_agent_name,
                anthropic_client=self.client,
                model=model,
                max_tokens=model_config.get('max_tokens', self.max_tokens),
                max_searches=max_searches,
                logger=self.logger
            )

            result = await session.execute_research(
                prompt=prompt,
                context={'enriched_content': enriched_content},
                max_turns=5
            )

            # Check if session ended in error
            if result.get('completion_status') == 'error':
                error_msg = (
                    f"Target alignment session ended in error "
                    f"after {result['total_turns']} turns"
                )
                self.logger.error(f"Target alignment {source_agent_name} failed: {error_msg}")
                self.state.mark_failed(target_agent_name, error_msg, layer='target_alignment')
                return

            # Save target-aligned output
            output_path = self._save_agent_output(
                target_agent_name, 'target_alignment', result
            )

            # Mark complete in state
            self.state.mark_complete(
                agent_name=target_agent_name,
                outputs={
                    'output_path': str(output_path),
                    'source_agent': source_agent_name,
                    'source_path': str(source_path),
                    'total_turns': result['total_turns'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'completion_status': result['completion_status']
                },
                layer='target_alignment'
            )

            # Update budget tracking
            self._update_budget(0, result.get('estimated_cost_usd', 0.0))

            self.logger.info(f"Completed target alignment: {source_agent_name}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")

        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(
                f"Target alignment {source_agent_name} failed: {e}", exc_info=True
            )
            self.state.mark_failed(target_agent_name, str(e), layer='target_alignment')
            raise

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
            prompt_template = self._get_agent_prompt(agent_name)

            # Get context from prior agents
            context = self.state.get_context_for_agent(agent_name)

            # Get Layer 0 context if available (for Layer 1 agents)
            service_categories = self.config.get('service_categories', [])
            layer_0_context = None
            if service_categories and self.state.is_layer_complete('layer_0'):
                layer_0_context = get_layer_0_context(self.state, service_categories)
                if layer_0_context:
                    self.logger.info(
                        "Injecting Layer 0 context",
                        extra={"category_count": len(layer_0_context)}
                    )

            # Build company context for all Layer 1 agents
            company_context_str = self._build_company_context()

            # Format prompt with Layer 0, prior agent, and company context
            prompt = format_layer_1_prompt(
                prompt_template=prompt_template,
                layer_0_context=layer_0_context,
                prior_agent_context=context,
                company_context=company_context_str
            )
            
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

            # Check if research session ended in error (e.g., API errors)
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Agent {agent_name} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer=layer)
                return

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
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))

            # Check budget limits
            self._check_budget_limits()

            self.logger.info(f"Completed agent: {agent_name}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")
            
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

            # Build company context for this vertical
            company_context_str = self._build_company_context(vertical=vertical)

            # Build vertical-specific prompt
            prompt = build_vertical_prompt(vertical, layer_1_context, company_context=company_context_str)
            
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

            # Check if research session ended in error (e.g., API errors)
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Vertical agent {vertical} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer='layer_2')
                return

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
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))

            # Check budget limits
            self._check_budget_limits()

            self.logger.info(f"Completed vertical agent: {vertical}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")
            
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

            # Get verticals from config, or extract from checkpoint if empty
            # (Phase 3 config may have verticals: [] but checkpoint has Layer 2 data)
            verticals_for_context = self.config['verticals']
            if not verticals_for_context:
                # Extract vertical names from checkpoint's layer_2 keys
                layer_2_data = self.state.state.get('layer_2', {})
                verticals_for_context = [
                    key.replace('vertical_', '')
                    for key in layer_2_data.keys()
                    if key.startswith('vertical_')
                ]
                if verticals_for_context:
                    self.logger.info(f"Using verticals from checkpoint: {verticals_for_context}")

            layer_2_context = get_layer_2_context(self.state, verticals_for_context)

            # Build company context (cross-vertical, no vertical param)
            company_context_str = self._build_company_context()

            # Build title-specific prompt
            prompt = build_title_prompt(title_cluster, layer_1_context, layer_2_context, company_context=company_context_str)
            
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

            # Check if research session ended in error (e.g., API errors)
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Title agent {title_cluster} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer='layer_3')
                return

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
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))

            # Check budget limits
            self._check_budget_limits()

            self.logger.info(f"Completed title agent: {title_cluster}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")
            
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
            
            # Build company context for early injection
            company_context_str = self._build_company_context(vertical=vertical)

            # Build playbook prompt
            prompt = build_playbook_prompt(
                vertical, title,
                layer_1_context, layer_2_context, layer_3_context,
                company_context=company_context_str
            )
            
            # Resolve model for playbook
            model = get_model_for_agent(self.config, 'playbooks', agent_name)
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

            # Check if research session ended in error (e.g., API errors)
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"Playbook {vertical}_{title} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer='integrations')
                return

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
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))

            # Check budget limits
            self._check_budget_limits()

            self.logger.info(f"Completed playbook: {vertical} × {title}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")
            
        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Playbook {vertical}_{title} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='integrations')
            raise

    async def _execute_playbook_3d(self, vertical: str, title: str, service_category: str):
        """
        Generate a 3D playbook for vertical × title × service_category combination.

        Args:
            vertical: Vertical identifier (e.g., 'healthcare')
            title: Title cluster identifier (e.g., 'cfo_cluster')
            service_category: Service category key (e.g., 'security')
        """
        from .prompts import build_playbook_prompt_3d, get_layer_0_context, get_layer_1_context, get_layer_2_context, get_layer_3_context
        from .prompts.context_injector import ResearchContextInjector

        agent_name = f"playbook_{vertical}_{title}_{service_category}"

        try:
            self.logger.info(f"Starting 3D playbook: {vertical} × {title} × {service_category}")
            self.state.mark_in_progress(agent_name, 'integrations')

            # Verify all layer dependencies (including Layer 0)
            service_categories = self.config.get('service_categories', [])
            if service_categories and not self.state.is_layer_complete('layer_0'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 0 not complete")
                return

            if not self.state.is_layer_complete('layer_1'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 1 not complete")
                return

            if not self.state.is_layer_complete('layer_2'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 2 not complete")
                return

            if not self.state.is_layer_complete('layer_3'):
                self.logger.error(f"Cannot generate {agent_name}: Layer 3 not complete")
                return

            # Load service category config from baseline.yaml
            context_files = self.config.get('company_context', {}).get('context_files', {})
            baseline_relative = context_files.get('baseline', 'context/baseline.yaml')
            baseline_path = (self.config_path.parent / baseline_relative).resolve()
            context_injector = ResearchContextInjector(baseline_path, self.logger)
            service_category_config = context_injector.get_service_category(service_category)

            if not service_category_config:
                self.logger.error(f"Cannot generate {agent_name}: Service category '{service_category}' not found in baseline.yaml")
                self.state.mark_failed(agent_name, f"Service category not found: {service_category}", layer='integrations')
                return

            # Extract context from all four layers
            layer_0_context = get_layer_0_context(self.state, service_categories)
            layer_1_context = get_layer_1_context(self.state)

            # Get verticals for context (may need to extract from checkpoint)
            verticals_for_context = self.config['verticals']
            if not verticals_for_context:
                layer_2_data = self.state.state.get('layer_2', {})
                verticals_for_context = [
                    key.replace('vertical_', '')
                    for key in layer_2_data.keys()
                    if key.startswith('vertical_')
                ]

            layer_2_context = get_layer_2_context(self.state, verticals_for_context)
            layer_3_context = get_layer_3_context(self.state, self.config['title_clusters'])

            # Build company context for early injection
            company_context_str = self._build_company_context(
                vertical=vertical, service_category=service_category
            )

            # Build 3D playbook prompt
            prompt = build_playbook_prompt_3d(
                vertical_key=vertical,
                title_key=title,
                service_category=service_category_config,
                service_category_key=service_category,
                layer_0_context=layer_0_context,
                layer_1_context=layer_1_context,
                layer_2_context=layer_2_context,
                layer_3_context=layer_3_context,
                company_context=company_context_str
            )

            # Resolve model for playbook
            model = get_model_for_agent(self.config, 'playbooks', agent_name)
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
                    'layer_0': layer_0_context,
                    'layer_1': layer_1_context,
                    'layer_2': layer_2_context,
                    'layer_3': layer_3_context,
                    'service_category': service_category
                },
                max_turns=50
            )

            # Check if research session ended in error
            if result.get('completion_status') == 'error':
                error_msg = f"Research session ended in error after {result['total_turns']} turns"
                self.logger.error(f"3D Playbook {vertical}_{title}_{service_category} failed: {error_msg}")
                self.state.mark_failed(agent_name, error_msg, layer='integrations')
                return

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
                    'completion_status': result['completion_status'],
                    'service_category': service_category
                },
                layer='integrations'
            )

            # Update budget tracking
            self._update_budget(result['searches_performed'], result.get('estimated_cost_usd', 0.0))

            # Check budget limits
            self._check_budget_limits()

            self.logger.info(f"Completed 3D playbook: {vertical} × {title} × {service_category}")
            self.logger.info(f"  Searches: {result['searches_performed']}")
            self.logger.info(f"  Turns: {result['total_turns']}")
            self.logger.info(f"  Time: {result['execution_time_seconds']:.1f}s")
            self.logger.info(f"  Cost: ${result.get('estimated_cost_usd', 0.0):.2f}")
            self.logger.info(f"  Output: {output_path}")
            self.logger.info(f"Budget Status:")
            self.logger.info(f"  Total searches: {self.budget['current_searches']}/{self.budget['max_total_searches']}")
            self.logger.info(f"  Total cost: ${self.budget['current_cost_usd']:.2f}/${self.budget['max_total_cost_usd']:.2f}")

        except BudgetExceededError:
            raise
        except Exception as e:
            self.logger.error(f"3D Playbook {vertical}_{title}_{service_category} failed: {e}", exc_info=True)
            self.state.mark_failed(agent_name, str(e), layer='integrations')
            raise

    def _build_company_context(
        self,
        vertical: str | None = None,
        service_category: str | None = None
    ) -> str:
        """
        Build compact company context string from loaders.

        Combines company fact sheet (from baseline.yaml) with verified proof points
        (from brand-assets.yaml) into a single string for prompt injection.

        Args:
            vertical: Optional vertical for proof point filtering
            service_category: Optional service category for proof point filtering

        Returns:
            Formatted company context string, or empty string if loaders unavailable
        """
        company_ctx_config = self.config.get('company_context', {})
        if not company_ctx_config.get('enabled', False):
            return ""

        parts: list[str] = []

        if self.brand_context_loader:
            ctx = self.brand_context_loader.load_all()
            company_text = self.brand_context_loader.format_company_context(ctx)
            if company_text:
                parts.append(company_text)

        if self.brand_assets_loader:
            assets = self.brand_assets_loader.load()
            if assets:
                compact = self.brand_assets_loader.format_compact_proof_points(
                    vertical=vertical,
                    service_category=service_category
                )
                if compact:
                    parts.append(compact)

        if self.strategic_messaging_loader:
            messaging_data = self.strategic_messaging_loader.load()
            if messaging_data:
                if vertical or service_category:
                    formatted = self.strategic_messaging_loader.format_for_playbook(
                        vertical=vertical
                    )
                else:
                    formatted = self.strategic_messaging_loader.format_for_research()
                if formatted:
                    parts.append(formatted)

        return "\n\n".join(parts)

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
    
    def _save_agent_output(self, agent_name: str, layer: str, result: dict[str, Any]) -> Path:
        """Save agent output to markdown file."""
        # Determine output directory
        if layer == 'layer_0':
            output_dir = self.output_dir / 'layer_0'
        elif layer == 'layer_1':
            output_dir = self.output_dir / 'layer_1'
        elif layer == 'layer_2':
            output_dir = self.output_dir / 'layer_2'
        elif layer == 'layer_3':
            output_dir = self.output_dir / 'layer_3'
        elif layer == 'integrations':
            output_dir = self.output_dir / 'playbooks'
        elif layer == 'validation':
            output_dir = self.output_dir / 'validation'
        elif layer == 'brand_alignment':
            output_dir = self.output_dir / 'brand_alignment'
        elif layer == 'target_alignment':
            output_dir = self.output_dir / 'target_aligned'
        else:
            output_dir = self.output_dir / layer
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output file
        output_file = output_dir / f"{agent_name}_{self._run_timestamp}.md"
        
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
        if layer_name == "Layer 0":
            output_dir = self.output_dir / 'layer_0'
        elif layer_name == "Layer 1":
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

        for layer_name in ['layer_0_status', 'layer_1_status', 'layer_2_status', 'layer_3_status', 'integration_status', 'validation_status', 'brand_alignment_status', 'target_alignment_status']:
            status = summary[layer_name]
            layer_label = layer_name.replace('_status', '').replace('_', ' ').title()
            self.logger.info(f"  {layer_label}: {status['complete']}/{status['total']} complete")
        
        self.logger.info(f"\nOutputs directory: {self.output_dir}")
        self.logger.info(f"Checkpoint file: {summary['checkpoint_file']}")
